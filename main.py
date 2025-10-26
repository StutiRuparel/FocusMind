import os
import subprocess
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from openai import OpenAI
from pydantic import BaseModel
import random

# ---- Your own modules -------------------------------------------------
from FocusScore import generate_focus_chart_base64, generate_session_stats
from face_focus_tracker import FaceFocusTracker
# ---------------------------------------------------------------------

# Global state ---------------------------------------------------------
attention_score = 100
focus_score_history = []
face_tracker = None
tracking_active = False
# ---------------------------------------------------------------------

# Load .env ------------------------------------------------------------
load_dotenv()
# ---------------------------------------------------------------------

# --------------------------- FastAPI app -------------------------------
app = FastAPI(
    title="FocusMind API",
    description="Motivational Study Coach API"
)

# --------------------------- Static mounts -----------------------------
# 1️⃣  Audio files (already present)
app.mount("/audio", StaticFiles(directory="audio_files"), name="audio")

# 2️⃣  React front‑end (served at root)
# `html=True` makes FastAPI fall back to `index.html` for any unknown path –
# perfect for a single‑page app.
app.mount(
    "/",                                 # root URL
    StaticFiles(directory="frontend/build", html=True),
    name="frontend"
)

# ---------------------------------------------------------------------
# (Optional) add a very small health‑check that does **not** sit on `/`
@app.get("/health")
async def health():
    """Simple health‑check – returns 200 OK."""
    return {"status": "ok"}
# ---------------------------------------------------------------------

# --------------------------- CORS middleware -------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000", "http://localhost:3001", "http://localhost:3002",
        "http://localhost:3003", "http://localhost:3004", "http://localhost:3005",
        "http://localhost:3006", "http://localhost:3007", "http://localhost:3008"
        # you can also add your Render URL here, e.g.
        # "https://tfl-cnsg.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ---------------------------------------------------------------------

# --------------------------- OpenAI client ---------------------------
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is required")
client = OpenAI(api_key=api_key)
# ---------------------------------------------------------------------

# --------------------------- Pydantic models ------------------------
class MotivationResponse(BaseModel):
    message: str
    attention_score: int

class VoiceAudioRequest(BaseModel):
    message: str
# ---------------------------------------------------------------------

# --------------------------- Endpoints ------------------------------
# NOTE: The original `@app.get("/")` endpoint has been removed.
# All other endpoints stay exactly as you wrote them.
# (Only the doc‑string/comments have been trimmed for brevity.)

@app.get("/motivation", response_model=MotivationResponse)
async def get_motivation(reset: bool = False):
    """Get a motivational quote from a David‑Goggins‑style coach."""
    global attention_score, focus_score_history

    if reset:
        attention_score = 100
        focus_score_history = []

    if not focus_score_history:
        now = datetime.now().strftime("%H:%M:%S")
        focus_score_history.append(
            {"timestamp": now, "focus_score": attention_score}
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a study coach loosely inspired by David Goggins. "
                        "Give intense, motivational study advice in a strictly PG version "
                        "of his style. (No swearing). Keep it under 30 words."
                    ),
                },
                {"role": "user", "content": "Give me motivation to study hard"},
            ],
            max_tokens=150,
        )
        msg = response.choices[0].message.content
        return MotivationResponse(message=msg, attention_score=attention_score)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating motivation: {str(e)}"
        )


@app.get("/attention-score")
async def get_attention_score():
    return {"attention_score": attention_score}


@app.post("/decrease-attention")
async def decrease_attention():
    global attention_score, focus_score_history
    attention_score = max(0, attention_score - 15)

    now = datetime.now().strftime("%H:%M:%S")
    focus_score_history.append(
        {"timestamp": now, "focus_score": attention_score}
    )
    return {
        "attention_score": attention_score,
        "message": f"Attention score decreased to {attention_score}",
    }


@app.post("/get-focus-chart")
async def get_focus_chart():
    global focus_score_history
    if not focus_score_history:
        return {"success": False, "error": "No focus data available for chart generation"}

    try:
        png_path, chart_b64_bytes = generate_focus_chart_base64(focus_score_history)
        session_stats = generate_session_stats(focus_score_history)

        return {
            "success": True,
            "chart_base64": chart_b64_bytes.decode("ascii"),
            "session_stats": session_stats,
            "png_filename": png_path,
            "data_points": len(focus_score_history),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating focus chart: {str(e)}"
        )


@app.post("/reset-focus-session")
async def reset_focus_session():
    global focus_score_history
    focus_score_history = []
    return {"success": True, "message": "Focus session reset"}


@app.get("/focus-session-stats")
async def get_focus_session_stats():
    if not focus_score_history:
        return {"data_points": 0, "session_active": False}

    stats = generate_session_stats(focus_score_history)
    return {
        "data_points": len(focus_score_history),
        "session_active": True,
        "stats": stats,
    }


@app.post("/get-voice-nudge")
async def get_voice_nudge():
    global attention_score
    try:
        result = subprocess.run(
            ["py", "nudge.py", "voice", str(attention_score)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        data = json.loads(result.stdout.strip())
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Unknown error"))

        audio_file = data.get("audio_file")
        audio_url = f"/audio/{audio_file}" if audio_file else None

        return {
            "success": True,
            "message": data["message"],
            "audio_url": audio_url,
            "audio_file": audio_file,
            "source": data.get("source", "David Goggins AI"),
            "nudge_type": "voice",
            "attention_score": attention_score,
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice nudge error: {str(e)}")


@app.post("/generate-voice-audio")
async def generate_voice_audio(request: VoiceAudioRequest):
    try:
        result = subprocess.run(
            ["py", "nudge.py", "generate_audio", request.message],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        data = json.loads(result.stdout.strip())
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Unknown error"))

        audio_file = data.get("audio_file")
        audio_url = f"/audio/{audio_file}" if audio_file else None

        return {
            "success": True,
            "message": request.message,
            "audio_url": audio_url,
            "audio_file": audio_file,
            "source": "David Goggins AI",
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio generation error: {str(e)}")


@app.post("/get-notification-nudge")
async def get_notification_nudge():
    global attention_score
    try:
        result = subprocess.run(
            ["py", "nudge.py", "notification", str(attention_score)],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        data = json.loads(result.stdout.strip())
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Unknown error"))

        return {
            "success": True,
            "message": data["message"],
            "source": data.get("source", "AI study coach"),
            "nudge_type": "notification",
            "platform": data.get("platform", "unknown"),
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Notification nudge error: {str(e)}")


@app.post("/get-break-nudge")
async def get_break_nudge():
    try:
        result = subprocess.run(
            ["py", "nudge.py", "break"],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        data = json.loads(result.stdout.strip())
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Unknown error"))

        audio_file = data.get("audio_file")
        audio_url = f"/audio/{audio_file}" if audio_file else None

        return {
            "success": True,
            "message": data["message"],
            "audio_url": audio_url,
            "audio_file": audio_file,
            "source": data.get("source", "David Goggins Break Coach"),
            "nudge_type": "break",
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Break nudge error: {str(e)}")


@app.post("/get-nudge-quote")
async def get_nudge_quote():
    """Backward‑compatible endpoint – just forwards to voice nudge."""
    return await get_voice_nudge()


# --------------------------- Face‑tracking API -----------------------
class FocusScoreUpdate(BaseModel):
    focus_score: float


class AutoMotivationTrigger(BaseModel):
    threshold: int
    focus_score: float


@app.post("/update-focus-score")
async def update_focus_score(request: FocusScoreUpdate):
    global attention_score, focus_score_history
    attention_score = max(0, min(100, request.focus_score))

    focus_score_history.append(
        {"timestamp": datetime.now(), "score": attention_score}
    )
    # keep recent history only
    if len(focus_score_history) > 1000:
        focus_score_history = focus_score_history[-1000:]

    return {
        "success": True,
        "updated_score": attention_score,
        "message": "Focus score updated successfully",
    }


@app.post("/trigger-auto-motivation")
async def trigger_auto_motivation(request: AutoMotivationTrigger):
    global attention_score
    try:
        print(
            f"🚨 Auto‑motivation triggered! Focus dropped below {request.threshold}% "
            f"(current: {request.focus_score:.1f}%)"
        )
        result = subprocess.run(
            ["py", "nudge.py", "voice", str(int(request.focus_score))],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        if result.returncode != 0:
            raise RuntimeError(result.stderr)

        data = json.loads(result.stdout.strip())
        if not data.get("success"):
            raise RuntimeError(data.get("error", "Unknown error"))

        audio_file = data.get("audio_file")
        audio_url = f"/audio/{audio_file}" if audio_file else None

        return {
            "success": True,
            "message": data["message"],
            "audio_url": audio_url,
            "audio_file": audio_file,
            "source": data.get("source", "David Goggins AI"),
            "nudge_type": "auto_voice",
            "threshold": request.threshold,
            "focus_score": request.focus_score,
        }
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=500, detail=f"JSON parse error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Auto‑motivation error: {str(e)}")


@app.get("/face-tracking-status")
async def get_face_tracking_status():
    if face_tracker is None:
        return {
            "active": False,
            "score": None,
            "last_update": None,
            "message": "Face tracking not initialized",
        }

    return {
        "active": tracking_active,
        "score": focus_score_history[-1]["score"]
        if focus_score_history
        else None,
        "last_update": focus_score_history[-1]["timestamp"]
        if focus_score_history
        else None,
        "message": "Face tracking active"
        if tracking_active
        else "Face tracking paused",
    }


@app.post("/start-face-tracking")
async def start_face_tracking():
    return {
        "success": True,
        "message": "Face tracking start signal sent. Please run face_focus_tracker.py manually.",
        "command": "python3 face_focus_tracker.py --source 0",
    }


@app.post("/stop-face-tracking")
async def stop_face_tracking():
    return {"success": True, "message": "Face tracking stop signal sent."}


# --------------------------- Entry point -----------------------------
if __name__ == "__main__":
    # Render injects $PORT; default to 8000 for local testing
    port = int(os.getenv("PORT", 8000))
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=port)
