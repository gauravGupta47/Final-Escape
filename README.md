# AI Story Wall

An interactive storytelling application that generates comic-style stories using OpenAI GPT-4 and Stable Diffusion image generation.

## Features

- Interactive story creation with AI-generated responses
- Comic-style image generation for each story segment
- PDF generation of completed stories
- Email delivery of final comic book

## Technical Stack

- Django 4.2
- OpenAI GPT-4 API for text generation
- Replicate API (Stable Diffusion) for image generation
- ReportLab for PDF creation
- Bootstrap 5 for frontend styling

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the project root directory with your API keys:

```
OPENAI_API_KEY=your_openai_api_key
REPLICATE_API_TOKEN=your_replicate_api_token
```

Or set them directly in your settings.py file (not recommended for production).

### 3. Database Setup

```bash
python manage.py migrate
python manage.py populate_themes  # Adds initial theme data
python manage.py createsuperuser  # Create admin user
```

### 4. Run the Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to access the application.

## Project Structure

- `storyapp/`: Main Django application
  - `models.py`: Database models (User, Theme, Story, StoryResponse)
  - `views.py`: View functions and helper methods for story generation
  - `forms.py`: Form definitions
  - `urls.py`: URL routing configuration
- `templates/`: Django templates
  - `base.html`: Base template with common layout
  - `storyapp/`: App-specific templates
- `static/`: Static files (CSS, JS)
- `media/`: User-generated content (images, PDFs)

## Usage Flow

1. User enters their email address
2. User selects a theme and character name
3. System generates a story introduction with images
4. User continues the story with their inputs
5. System generates AI responses and images
6. After 10 interactions, a PDF is generated and emailed

## Email Configuration

For development, emails are sent to the console. For production, configure email settings in settings.py:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'your_smtp_server'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your_email@example.com'
EMAIL_HOST_PASSWORD = 'your_email_password'
```
