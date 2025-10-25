#!/bin/bash

# Script to start the FocusMind backend with port conflict handling

echo "🚀 Starting FocusMind Backend..."

# Kill any existing processes on port 8000
echo "🔍 Checking for existing processes on port 8000..."
EXISTING_PID=$(lsof -ti:8000)

if [ ! -z "$EXISTING_PID" ]; then
    echo "⚠️  Found existing process $EXISTING_PID on port 8000. Killing it..."
    kill -9 $EXISTING_PID
    sleep 2
    echo "✅ Killed existing process"
else
    echo "✅ Port 8000 is free"
fi

# Kill any existing python3 main.py processes
echo "🔍 Checking for existing main.py processes..."
pkill -f "python3.*main.py" 2>/dev/null
sleep 1

# Start the backend
echo "🚀 Starting FastAPI backend..."
cd /home/squidlord/FocusMind
python3 main.py