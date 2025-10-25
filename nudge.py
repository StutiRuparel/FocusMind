import os
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize client with API key from environment variables
api_key = os.getenv("OPENAI_API_KEY")
#print(f"API Key loaded: {'Yes' if api_key else 'No'}")
#print(f"API Key starts with: {api_key[:10] + '...' if api_key else 'None'}")

client = OpenAI(api_key=api_key)

try:
    # Send a request to GPT-4 (more reliable than GPT-5)
    response = client.chat.completions.create(
        model="gpt-4",  # Changed to gpt-4 for better compatibility
        messages=[
            {"role": "system", "content": "You are a David Goggins motivational study coach."},
            {"role": "user", "content": "Write a motivational study quote"}
        ],
        max_completion_tokens=1500  # response length limit
    )
    
    print(response.choices[0].message.content)
    
except Exception as e:
    print(f"Error occurred: {e}")
    print(f"Error type: {type(e).__name__}")