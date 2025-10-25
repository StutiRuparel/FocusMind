import os
import json
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print(json.dumps({"error": "OPENAI_API_KEY not found in environment variables"}))
    exit(1)

client = OpenAI(api_key=api_key)

def generate_motivational_quote():
    """Generate a motivational quote using OpenAI"""
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are David Goggins. Give an intense, motivational message to get someone focused on studying. Be direct and powerful. Keep it under 100 words."},
                {"role": "user", "content": "I need motivation to stay focused and study hard."}
            ],
            max_completion_tokens=150
        )
        
        message = response.choices[0].message.content
        
        # Return as JSON for easy parsing
        result = {
            "success": True,
            "message": message,
            "source": "David Goggins AI"
        }
        
        print(json.dumps(result))
        
    except Exception as e:
        error_result = {
            "success": False,
            "error": str(e)
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    generate_motivational_quote()