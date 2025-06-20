import os
import uuid
import time  # Add time import for timing operations
import replicate
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.core.mail import EmailMessage
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from io import BytesIO
import requests
import threading

from .models import User, Theme, Story, StoryResponse
from .forms import UserForm, StoryForm, StoryResponseForm

# Initialize OpenAI API
from openai import OpenAI

# Create OpenAI client instance - handle empty API key gracefully
def get_openai_client():
    # Debug environment variables
    import os
    print("\nDEBUG: Environment variables:")
    print(f"1. Direct os.getenv: {os.getenv('OPENAI_API_KEY')}")
    print(f"2. Settings OPENAI_API_KEY: {settings.OPENAI_API_KEY}")
    print(f"3. All env vars containing 'OPENAI': {[k for k in os.environ.keys() if 'OPENAI' in k]}")

    if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
        print("WARNING: OPENAI_API_KEY is not set or empty")
        return None

    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        print("DEBUG: Successfully created OpenAI client")
        test_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": "Say 'OK' if you can hear me"}],
            max_tokens=5
        )
        print(f"DEBUG: Test response received: {test_response.choices[0].message.content}")
        return client
    except Exception as e:
        print(f"ERROR initializing OpenAI client: {e}")
        print(f"ERROR type: {type(e).__name__}")
        return None

# Set Replicate API token
if settings.REPLICATE_API_TOKEN and settings.REPLICATE_API_TOKEN.strip():
    try:
        os.environ['REPLICATE_API_TOKEN'] = settings.REPLICATE_API_TOKEN
    except Exception as e:
        print(f"ERROR setting Replicate API token: {e}")
else:
    # Remove token from environment if it exists but is empty in settings
    if 'REPLICATE_API_TOKEN' in os.environ:
        del os.environ['REPLICATE_API_TOKEN']
    print("WARNING: REPLICATE_API_TOKEN is not set. Image generation will not work.")

def index(request):
    """Home page view."""
    # Get or create user
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            user, created = User.objects.get_or_create(email=email)
            request.session['user_id'] = user.id
            return redirect('create_story')
    else:
        form = UserForm()
    
    return render(request, 'storyapp/index.html', {'form': form})


def create_story(request):
    """Create a new story."""
    # Check if user is in session
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
    
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        form = StoryForm(request.POST)
        if form.is_valid():
            # Get form data
            theme = form.cleaned_data['theme']
            character_name = form.cleaned_data['character_name']
            
            try:
                # Generate story plot using GPT
                plot_text = generate_story_plot(theme.description, character_name)
                
                # Generate plot image using Stable Diffusion
                plot_image_path = generate_plot_image(plot_text)
                
                # Create story object
                story = Story.objects.create(
                    user=user,
                    theme=theme,
                    character_name=character_name,
                    plot_text=plot_text,
                    plot_image_path=plot_image_path
                )
                
                return redirect('continue_story', story_id=story.id)
            except Exception as e:
                print(f"Error creating story: {e}")
                messages.error(request, f"Error creating story: {str(e)}")
                
                # Create story without image if generation fails
                story = Story.objects.create(
                    user=user,
                    theme=theme,
                    character_name=character_name,
                    plot_text=plot_text
                )
                
                return redirect('continue_story', story_id=story.id)
    else:
        form = StoryForm()
    
    # Get all available themes
    themes = Theme.objects.all()
    
    return render(request, 'storyapp/create_story.html', {
        'form': form,
        'themes': themes,
        'user': user
    })


def continue_story(request, story_id):
    """Continue an existing story."""
    # Check if user is in session
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('index')
    
    story = get_object_or_404(Story, id=story_id)
    responses = StoryResponse.objects.filter(story=story).order_by('created_at')
    
    # Get the latest response for image status checking
    latest_response = responses.last()
    
    # Initialize context variables
    context = {
        'form': StoryResponseForm(),
        'story': story,
        'responses': responses,
        'processing': False,
        'current_user_input': None,
        'current_ai_response': None,
        'current_user_img': None,
        'current_ai_img': None,
        'latest_response': latest_response,
    }
    
    if request.method == 'POST':
        form = StoryResponseForm(request.POST)
        if form.is_valid():
            # Get user input
            user_input = form.cleaned_data['user_input']
            
            # Generate AI response using GPT
            story_context = f"Theme: {story.theme.name}\nCharacter: {story.character_name}\nPlot: {story.plot_text}\n"
            
            # Add previous responses for context
            for resp in responses:
                story_context += f"User: {resp.user_input}\nAI: {resp.ai_response}\n"
            
            # Add current user input
            story_context += f"User: {user_input}\n"
            
            # Generate AI response using GPT
            ai_response = generate_ai_response(story_context)
            
            # Create response object first (without images)
            response = StoryResponse.objects.create(
                story=story,
                user_input=user_input,
                ai_response=ai_response
            )
            
            # Set processing flag and current inputs for template
            context['processing'] = True
            context['current_user_input'] = user_input
            context['current_ai_response'] = ai_response
            
            # Start a background thread to generate images
            def generate_images_thread():
                try:
                    # Generate user image
                    print("Generating user image...")
                    user_img_path = generate_user_image(user_input, story.character_name)
                    if user_img_path:
                        response.user_img_path = user_img_path
                        response.save()
                        print(f"User image saved: {user_img_path}")
                    else:
                        print("Failed to generate user image")
                    
                    # Generate AI image
                    print("Generating AI image...")
                    ai_img_path = generate_ai_image(ai_response)
                    if ai_img_path:
                        response.ai_img_path = ai_img_path
                        response.save()
                        print(f"AI image saved: {ai_img_path}")
                    else:
                        print("Failed to generate AI image")
                    
                except Exception as e:
                    print(f"Error generating images: {e}")
            
            # Start the thread for image generation
            image_thread = threading.Thread(target=generate_images_thread)
            image_thread.daemon = True
            image_thread.start()
            
            # If we have 10 responses, generate PDF and send email
            if responses.count() >= 9:  # 9 existing + 1 new = 10 total
                pdf_path = generate_pdf(story)
                send_email(story)
                return redirect('story_complete', story_id=story.id)
            
            # Redirect to refresh the page and show the new response
            return redirect('continue_story', story_id=story.id)
    
    return render(request, 'storyapp/continue_story.html', context)

# Add a new view to check image generation status
def check_image_status(request, response_id):
    """AJAX endpoint to check if images have been generated."""
    response = get_object_or_404(StoryResponse, id=response_id)
    
    return JsonResponse({
        'user_img_ready': bool(response.user_img_path),
        'ai_img_ready': bool(response.ai_img_path),
        'user_img_path': response.user_img_path if response.user_img_path else None,
        'ai_img_path': response.ai_img_path if response.ai_img_path else None,
    })


def story_complete(request, story_id):
    """Show completed story."""
    story = get_object_or_404(Story, id=story_id)
    responses = StoryResponse.objects.filter(story=story).order_by('created_at')
    
    return render(request, 'storyapp/story_complete.html', {
        'story': story,
        'responses': responses
    })


def generate_story_plot(theme_description, character_name):
    """Generate story plot using OpenAI's GPT."""
    # Get a fresh OpenAI client
    client = get_openai_client()
    if client is None:
        return f"Once upon a time, there was a character named {character_name} in a {theme_description} world. \nPlease set your OpenAI API key in the .env file to generate real stories."

    try:
        # Create the prompt
        prompt = f"Create an exciting comic book story introduction about a character named {character_name} in the following setting: {theme_description}. Make it engaging and suitable for children. Keep it under 200 words."

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative comic book writer who creates engaging stories for children."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating story plot: {e}")
        return f"Once upon a time, there was a character named {character_name} in a {theme_description} world. \nAn error occurred while generating the story."


def generate_ai_response(story_context):
    """Generate AI response using OpenAI's GPT."""
    # Get a fresh OpenAI client
    client = get_openai_client()
    if client is None:
        return "The adventure continues... \nPlease set your OpenAI API key in the .env file to generate real story continuations."

    try:
        # Create the prompt
        prompt = f"Continue this comic book story in an engaging way. Keep your response concise (around 100 words) and exciting. Previous story context:\n{story_context}"

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a creative comic book writer who creates engaging stories for children. Keep your responses concise and exciting."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating AI response: {e}")
        return "The adventure continues... \nAn error occurred while generating the story continuation."


def generate_plot_image(plot_text):
    """Generate a 3-panel comic image for the plot using Replicate."""
    # Check if Replicate API token is set
    if not settings.REPLICATE_API_TOKEN:
        print("Cannot generate image: REPLICATE_API_TOKEN is not set")
        return None
        
    # Create prompt for a 3-panel comic based on the plot
    prompt = f"Create a comic-style black and white storyboard with 3 panels showing: {plot_text[:300]}"
    print(f"Plot image prompt: {prompt}")
    
    # Use Replicate API to generate image
    try:
        print("Generating image with Replicate...")
        start_time = time.time()
        
        output = replicate.run(
            "stability-ai/sdxl-lightning:latest",  # Faster model
            input={
                "prompt": prompt,
                "width": 768,
                "height": 384,  # Wider format for 3 panels
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "negative_prompt": "color, detailed, complex, photorealistic"
            }
        )
        
        # Download the image
        if output and len(output) > 0:
            image_url = output[0]
            print(f"Image generated, URL: {image_url}")
            
            response = requests.get(image_url)
            if response.status_code != 200:
                print(f"Failed to download image: {response.status_code}")
                return None
            
            # Create a unique filename
            filename = f"plot_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(settings.MEDIA_ROOT, 'plots', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            end_time = time.time()
            print(f"Image saved to: {filepath}")
            print(f"Total time: {end_time - start_time:.2f} seconds")
            
            # Return the path relative to MEDIA_ROOT
            return os.path.join('plots', filename)
    except Exception as e:
        print(f"Error generating plot image: {type(e).__name__}: {e}")
    
    return None


def generate_user_image(user_input, character_name):
    """Generate an image for user input using Replicate."""
    # Check if Replicate API token is set
    if not settings.REPLICATE_API_TOKEN:
        print("Cannot generate user image: REPLICATE_API_TOKEN is not set")
        return None
        
    # Create prompt for a single comic panel
    prompt = f"Comic-style black and white panel showing {character_name}: {user_input[:200]}"
    print(f"User image prompt: {prompt}")
    
    # Use Replicate API to generate image
    try:
        print("Generating image with Replicate...")
        start_time = time.time()
        
        output = replicate.run(
            "stability-ai/sdxl-lightning:latest",  # Faster model
            input={
                "prompt": prompt,
                "width": 512,
                "height": 512,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "negative_prompt": "color, detailed, complex, photorealistic"
            }
        )
        
        # Download the image
        if output and len(output) > 0:
            image_url = output[0]
            print(f"Image generated, URL: {image_url}")
            
            response = requests.get(image_url)
            if response.status_code != 200:
                print(f"Failed to download image: {response.status_code}")
                return None
            
            # Create a unique filename
            filename = f"user_{uuid.uuid4().hex}.jpg"
            filepath = os.path.join(settings.MEDIA_ROOT, 'responses', filename)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # Save the image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            end_time = time.time()
            print(f"Image saved to: {filepath}")
            print(f"Total time: {end_time - start_time:.2f} seconds")
            
            # Return the path relative to MEDIA_ROOT
            return os.path.join('responses', filename)
    except Exception as e:
        print(f"Error generating user image: {type(e).__name__}: {e}")
    
    return None


def generate_ai_image(ai_response):
    """Generate a 2-panel comic image for AI response using Replicate."""
    # Check if Replicate API token is set
    if not settings.REPLICATE_API_TOKEN:
        print("Cannot generate AI image: REPLICATE_API_TOKEN is not set")
        return None
        
    # Create prompt for a 2-panel comic
    prompt = f"Black-and-white comic 2-panel scene showing: {ai_response[:300]}"
    print(f"AI image prompt: {prompt}")
    
    # Use Replicate API to generate image
    try:
        print("Generating image with Replicate...")
        start_time = time.time()
        
        output = replicate.run(
            "stability-ai/sdxl-lightning:latest",  # Faster model
            input={
                "prompt": prompt,
                "width": 768,
                "height": 384,  # Wider format for 2 panels
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "negative_prompt": "color, detailed, complex, photorealistic"
            }
        )
        
        if output and len(output) > 0:
            image_url = output[0]
            print(f"Image generated, URL: {image_url}")
            
            # Download and save the image
            response = requests.get(image_url)
            if response.status_code == 200:
                # Create a unique filename
                filename = f"ai_{uuid.uuid4().hex}.jpg"
                filepath = os.path.join(settings.MEDIA_ROOT, 'responses', filename)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                
                # Save the image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                end_time = time.time()
                print(f"Image saved to: {filepath}")
                print(f"Total time: {end_time - start_time:.2f} seconds")
                
                # Return the path relative to MEDIA_ROOT
                return os.path.join('responses', filename)
    except Exception as e:
        print(f"Error generating AI image: {type(e).__name__}: {e}")
    
    return None


def generate_pdf(story):
    """Generate a PDF comic book from the story and responses."""
    responses = StoryResponse.objects.filter(story=story).order_by('created_at')
    
    # Create a unique filename for the PDF
    filename = f"comic_{story.id}_{uuid.uuid4().hex}.pdf"
    filepath = os.path.join(settings.MEDIA_ROOT, 'pdfs', filename)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Create A4 PDF
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4  # 595.2, 841.8 points (72 points = 1 inch)
    
    # Add title page
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(width/2, height-100, f"{story.character_name}'s {story.theme.name} Adventure")
    
    c.setFont("Helvetica", 12)
    c.drawCentredString(width/2, height-150, f"Created on {story.created_at.strftime('%B %d, %Y')}" )
    
    # Load and draw the plot image on the title page
    plot_image_path = os.path.join(settings.MEDIA_ROOT, story.plot_image_path)
    if os.path.exists(plot_image_path):
        c.drawImage(plot_image_path, 100, height-400, width-200, 200)
    
    # Add plot text
    text_object = c.beginText(100, height-450)
    text_object.setFont("Helvetica", 12)
    
    # Word wrap the plot text
    words = story.plot_text.split()
    lines = []
    current_line = []
    
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > 70:  # adjust based on your font size and page width
            lines.append(' '.join(current_line[:-1]))
            current_line = [current_line[-1]]
    
    if current_line:
        lines.append(' '.join(current_line))
    
    for line in lines:
        text_object.textLine(line)
    
    c.drawText(text_object)
    
    # Move to the next page
    c.showPage()
    
    # Process responses in pairs (for layout purposes)
    response_pairs = [responses[i:i+2] for i in range(0, len(responses), 2)]
    
    for pair_index, pair in enumerate(response_pairs):
        y_position = height - 100  # Starting Y position
        
        for response in pair:
            # Add user input and response images side by side
            user_image_path = os.path.join(settings.MEDIA_ROOT, response.user_img_path)
            ai_image_path = os.path.join(settings.MEDIA_ROOT, response.ai_img_path)
            
            # Add user text
            c.setFont("Helvetica-Bold", 12)
            c.drawString(50, y_position, f"{story.character_name}:")
            
            # Add user input text with word wrap
            c.setFont("Helvetica", 10)
            text_object = c.beginText(50, y_position - 20)
            
            words = response.user_input.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 70:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [current_line[-1]]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                text_object.textLine(line)
            
            c.drawText(text_object)
            
            # Determine where to place images based on text height
            text_height = len(lines) * 12  # Approximate height of text block
            image_y = y_position - text_height - 160  # Position images below text
            
            # Draw user image
            if os.path.exists(user_image_path):
                c.drawImage(user_image_path, 50, image_y, 200, 150)
            
            # Add AI response text
            c.setFont("Helvetica-Bold", 12)
            c.drawString(300, y_position, "AI:")
            
            # Add AI response text with word wrap
            c.setFont("Helvetica", 10)
            text_object = c.beginText(300, y_position - 20)
            
            words = response.ai_response.split()
            lines = []
            current_line = []
            
            for word in words:
                current_line.append(word)
                if len(' '.join(current_line)) > 70:
                    lines.append(' '.join(current_line[:-1]))
                    current_line = [current_line[-1]]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines:
                text_object.textLine(line)
            
            c.drawText(text_object)
            
            # Draw AI image
            if os.path.exists(ai_image_path):
                c.drawImage(ai_image_path, 300, image_y, 250, 150)
            
            # Update Y position for next response pair
            y_position = image_y - 50
            
            # If we're running out of space on the page, create a new page
            if y_position < 100:
                c.showPage()
                y_position = height - 100
        
        # After each pair, add a new page unless it's the last pair
        if pair_index < len(response_pairs) - 1:
            c.showPage()
    
    # Save the PDF
    c.save()
    
    # Update the story's PDF path
    story.pdf_path = os.path.join('pdfs', filename)
    story.save()
    
    return story.pdf_path


def send_email(story):
    """Send the comic book PDF via email."""
    if not story.pdf_path:
        return False
    
    pdf_path = os.path.join(settings.MEDIA_ROOT, story.pdf_path)
    
    if not os.path.exists(pdf_path):
        return False
    
    subject = f"Your Comic Story: {story.character_name}'s {story.theme.name} Adventure"
    body = f"""Hello!

Thank you for creating a story with AI Story Wall.

Attached is your comic book featuring {story.character_name} in a {story.theme.name} adventure.

Enjoy your comic!

Best regards,
AI Story Wall Team"""
    
    email = EmailMessage(
        subject=subject,
        body=body,
        to=[story.user.email],
    )
    
    # Attach the PDF
    with open(pdf_path, 'rb') as f:
        email.attach(f"{story.character_name}_comic.pdf", f.read(), 'application/pdf')
    
    # Send the email
    email.send()
    
    # Mark email as sent
    story.email_sent = True
    story.save()
    
    return True
