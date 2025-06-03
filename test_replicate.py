import os
import time
import replicate
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get the API token
api_token = os.getenv('REPLICATE_API_TOKEN')
if not api_token:
    raise ValueError("REPLICATE_API_TOKEN not found in environment variables")

# Set the API token in the environment
os.environ['REPLICATE_API_TOKEN'] = api_token

def test_replicate_comic():
    """Test Replicate API for comic-style image generation."""
    try:
        print("Testing Replicate API for comic generation...")
        start_time = time.time()
        
        # Create a prompt for a comic panel
        prompt = "A simple black and white comic panel showing a superhero flying through clouds"
        
        # Use a fast comic-style model
        output = replicate.run(
            "stability-ai/sdxl:latest",
            input={
                "prompt": prompt,
                "width": 512,
                "height": 512,
                "num_outputs": 1,
                "num_inference_steps": 25,  # Fewer steps for speed
                "guidance_scale": 7.5,
                "negative_prompt": "color, detailed, complex, photorealistic"
            }
        )
        
        print(f"API Response: {output}")
        
        if output and len(output) > 0:
            image_url = output[0]
            print(f"Image URL: {image_url}")
            
            # Try downloading the image
            response = requests.get(image_url)
            if response.status_code == 200:
                with open('test_comic_image.jpg', 'wb') as f:
                    f.write(response.content)
                end_time = time.time()
                print(f"SUCCESS: Image downloaded successfully to test_comic_image.jpg")
                print(f"Total time: {end_time - start_time:.2f} seconds")
            else:
                print(f"ERROR: Failed to download image: {response.status_code}")
        else:
            print("ERROR: No output received from API")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

def test_replicate_fast():
    """Test Replicate API with a faster model."""
    try:
        print("Testing Replicate API with a faster model...")
        start_time = time.time()
        
        # Create a prompt for a comic panel
        prompt = "A simple black and white comic panel showing a superhero flying through clouds"
        
        # Use a faster model (SDXL Lightning)
        output = replicate.run(
            "stability-ai/sdxl-lightning:latest",
            input={
                "prompt": prompt,
                "width": 512,
                "height": 512,
                "num_outputs": 1,
                "guidance_scale": 7.5,
                "negative_prompt": "color, detailed, complex, photorealistic"
            }
        )
        
        print(f"API Response: {output}")
        
        if output and len(output) > 0:
            image_url = output[0]
            print(f"Image URL: {image_url}")
            
            # Try downloading the image
            response = requests.get(image_url)
            if response.status_code == 200:
                with open('test_fast_image.jpg', 'wb') as f:
                    f.write(response.content)
                end_time = time.time()
                print(f"SUCCESS: Image downloaded successfully to test_fast_image.jpg")
                print(f"Total time: {end_time - start_time:.2f} seconds")
            else:
                print(f"ERROR: Failed to download image: {response.status_code}")
        else:
            print("ERROR: No output received from API")
            
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    # Test both methods
    test_replicate_comic()
    print("\n" + "-"*50 + "\n")
    test_replicate_fast()
