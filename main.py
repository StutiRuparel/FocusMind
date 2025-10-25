import os
import subprocess
import json
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from pydantic import BaseModel
import random

# Global attention score variable (shared state)
attention_score = 100

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="FocusMind API", description="Motivational Study Coach API")

# Add CORS middleware to allow React frontend to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=api_key)

class MotivationResponse(BaseModel):
    message: str
    attention_score: int

@app.get("/")
async def root():
    return {"message": "FocusMind API is running"}

@app.get("/motivation", response_model=MotivationResponse)
async def get_motivation(reset: bool = False):
    """Get a motivational quote from David Goggins style coach"""
    global attention_score
    
    # Reset attention score to 100 if requested (page refresh)
    if reset:
        attention_score = 100
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a David Goggins motivational study coach. Give intense, motivational study advice in his style. Keep it under 100 words."},
                {"role": "user", "content": "Give me motivation to study hard"}
            ],
            max_completion_tokens=150
        )
        
        message = response.choices[0].message.content
        
        return MotivationResponse(message=message, attention_score=attention_score)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating motivation: {str(e)}")

@app.get("/attention-score")
async def get_attention_score():
    """Get current attention score"""
    global attention_score
    return {"attention_score": attention_score}

@app.post("/decrease-attention")
async def decrease_attention():
    """Decrease attention score by 15"""
    global attention_score
    attention_score = max(0, attention_score - 15)  # Don't go below 0
    return {"attention_score": attention_score, "message": f"Attention score decreased to {attention_score}"}

@app.post("/get-nudge-quote")
async def get_nudge_quote():
    """Get a motivational quote by running nudge.py script"""
    try:
        # Run nudge.py script and capture output
        result = subprocess.run(
            ["python", "nudge.py"], 
            capture_output=True, 
            text=True, 
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            # Parse JSON output from nudge.py
            output_data = json.loads(result.stdout.strip())
            if output_data.get("success"):
                return {
                    "success": True,
                    "message": output_data["message"],
                    "source": output_data.get("source", "David Goggins AI")
                }
            else:
                raise HTTPException(status_code=500, detail=f"Nudge script error: {output_data.get('error', 'Unknown error')}")
        else:
            raise HTTPException(status_code=500, detail=f"Script execution failed: {result.stderr}")
            
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse script output: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running nudge script: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
