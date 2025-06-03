import os
from dotenv import load_dotenv
from pathlib import Path

# Get the base directory
base_dir = Path(__file__).resolve().parent

# Load environment variables
env_path = os.path.join(base_dir, '.env')
print(f"Looking for .env file at: {env_path}")
print(f"File exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("Loading environment variables...")
    load_dotenv(env_path, override=True)
    
    # Check OpenAI API key
    api_key = os.getenv('OPENAI_API_KEY', '')
    if api_key:
        masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "[TOO SHORT]"
        print(f"OpenAI API Key found: {masked_key}")
        
        # Test OpenAI API
        from openai import OpenAI
        try:
            client = OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": "Say 'OK' if you can hear me"}],
                max_tokens=5
            )
            print(f"OpenAI API Test Response: {response.choices[0].message.content}")
        except Exception as e:
            print(f"Error testing OpenAI API: {type(e).__name__}: {str(e)}")
    else:
        print("No OpenAI API key found in environment variables")
else:
    print("No .env file found")
