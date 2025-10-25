@echo off
echo 🚀 FocusMind Windows Setup with Real Camera Access
echo ================================================

REM Check if Python is installed
py --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Create virtual environment
echo 📦 Creating virtual environment...
py -m venv focusmind_env

REM Activate virtual environment and install packages
echo 📋 Installing Python packages...
call focusmind_env\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

echo ✅ Setup complete!
echo.
echo 🎯 To start FocusMind with REAL camera tracking:
echo.
echo 1. Backend: 
echo    focusmind_env\Scripts\activate.bat
echo    py main.py
echo.
echo 2. Face Tracking (in another terminal):
echo    focusmind_env\Scripts\activate.bat  
echo    py face_focus_tracker.py --source 0
echo.
echo 3. Frontend (install Node.js first if needed):
echo    cd frontend
echo    npm install
echo    npm start
echo.
echo 🌐 Then open http://localhost:3003 in your browser
echo 📹 Your camera will automatically start during Pomodoro sessions!
echo.
pause