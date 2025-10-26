#!/usr/bin/env bash
# -------------------------------------------------
# start.sh – launch the FastAPI app on the correct port
# -------------------------------------------------

# Render injects $PORT; if it isn’t set (e.g. local testing) default to 8000
PORT=${PORT:-8000}

# Exec replaces the shell process with uvicorn so signals are handled correctly
exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
