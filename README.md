# FocusMind - AI-Powered Productivity & Study Coach

A comprehensive web application that combines the **Pomodoro Technique** with **David Goggins-style AI motivation**, **real-time focus tracking**, and **performance analytics** to maximize your productivity and study effectiveness.

![FocusMind Banner](https://img.shields.io/badge/FocusMind-AI%20Study%20Coach-blue?style=for-the-badge&logo=brain&logoColor=white)

## 🚀 Features

### 📹 **AI-Powered Face Tracking** *(NEW!)*
- **Automated Focus Detection**: Real-time webcam monitoring using MediaPipe and OpenAI
- **Intelligent Scoring**: Computer vision algorithms assess attention levels automatically
- **Threshold-Based Interventions**: Automatic motivation when focus drops below 80%, 60%, 50%, 40%
- **No Manual Input Required**: Hands-free focus tracking during study sessions
- **Visual Feedback**: Live face tracking overlay with focus score visualization

### 🎯 **Smart Focus Management**
- **Attention Score Tracking**: Real-time focus monitoring (0-100) with visual feedback
- **Automatic Intervention**: AI-powered motivational coaching when focus drops
- **Voice Motivation**: Text-to-speech David Goggins quotes using OpenAI TTS
- **Intelligent Nudges**: Context-aware motivation based on current attention level

### ⏱️ **Pomodoro Technique Integration**
- **25-minute Focus Sessions**: Configurable Pomodoro timer with session tracking
- **Break Management**: Automatic break reminders with motivational audio
- **Session Counter**: Track completed focus sessions throughout your study day
- **Focus Chart**: Visual analytics showing attention patterns over time

### 🎤 **Advanced Audio System**
- **Voice Coaching**: David Goggins-style motivation read aloud automatically
- **Audio Management**: Smart system prevents overlapping audio tracks
- **Manual Voice Reading**: Click to hear any displayed quote read aloud
- **High-Quality TTS**: OpenAI "onyx" voice for authoritative coaching

### 📊 **Performance Analytics**
- **Focus Charts**: Matplotlib-generated graphs showing attention over time
- **Session Statistics**: Detailed analytics after each Pomodoro session
- **Progress Tracking**: Monitor improvement in focus consistency
- **Visual Feedback**: Color-coded attention indicators and progress bars

### 🎨 **Modern UI/UX**
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Updates**: Live attention score and timer displays
- **Smooth Animations**: CSS transitions for engaging user experience
- **Minimalist Interface**: Distraction-free design focused on productivity

## 📋 Prerequisites

- **Python 3.8+** 
- **Node.js 14+** 
- **OpenAI API Key** (with GPT-4 and TTS access)
- **Modern Web Browser** (Chrome, Firefox, Safari, Edge)
- **Webcam** (for AI face tracking features)
- **OpenCV & MediaPipe** (auto-installed with requirements.txt)

## ⚡ Quick Start

### 1. Clone and Setup

```bash
git clone https://github.com/5quidL0rd/FocusMind.git
cd FocusMind

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root:
```bash
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### 3. Setup Frontend

```bash
cd frontend
npm install
cd ..
```

### 4. Run the Application

**Option A: Manual Start**
```bash
# Terminal 1 - Backend (from project root)
python main.py

# Terminal 2 - Frontend (from frontend directory)
cd frontend && npm start
```

**Option B: Quick Start Script** (if available)
```bash
chmod +x start_backend.sh
./start_backend.sh
```

### 5. Access the App

Open your browser and navigate to:
- **Frontend**: `http://localhost:3000` (or displayed port)
- **Backend API**: `http://localhost:8000`

## 🎮 How to Use

### 🤖 AI-Powered Workflow (Recommended)

1. **Start Session**: Open FocusMind and see your initial motivational quote
2. **Enable Face Tracking**: Run `./start_face_tracking.sh` in a separate terminal
3. **Begin Pomodoro**: Click "Start Pomodoro" for a 25-minute focus session
4. **Hands-Free Monitoring**: AI automatically tracks your focus using your webcam
5. **Automatic Interventions**: When focus drops below thresholds (80%, 60%, 50%, 40%), get instant David Goggins motivation
6. **Stay Focused**: Your attention score updates in real-time based on:
   - Face detection and presence
   - Eye movement and gaze direction
   - Blink rate and eye openness
   - Head position and movement
7. **Complete Session**: View your detailed focus performance chart
8. **Take Break**: Automatic break nudges guide your recovery

### 📱 Manual Workflow (Alternative)

1. **Start Session**: Open FocusMind and see your initial motivational quote
2. **Begin Pomodoro**: Click "Start Pomodoro" for a 25-minute focus session
3. **Self-Monitor**: Click "Decrease Attention" when you notice distractions
4. **Get Motivated**: Automatic voice coaching triggers when attention score drops
5. **Manual Motivation**: Click "Get Voice Nudge" to hear current quote read aloud
6. **Complete Session**: When timer ends, view your focus performance chart
7. **Take Break**: Listen to break nudge audio and prepare for next session

### 🚀 Quick Start Commands

```bash
# Terminal 1: Start Backend
python main.py

# Terminal 2: Start Frontend  
cd frontend && npm start

# Terminal 3: Start AI Face Tracking (Recommended)
./start_face_tracking.sh
```

### Advanced Features

- **Timer Customization**: Modify timer duration in `frontend/src/App.tsx` (line 44)
- **Focus Analytics**: View detailed charts after each completed session
- **Audio Controls**: All audio tracks are managed to prevent overlapping
- **Session Tracking**: Monitor daily progress with session counters

## 🔧 API Reference

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Health check and basic info |
| `GET` | `/motivation?reset=true` | Get motivational quote with optional score reset |
| `POST` | `/decrease-attention` | Simulate distraction (decreases score by 15) |
| `POST` | `/get-voice-nudge` | Generate new motivational quote with audio |
| `POST` | `/generate-voice-audio` | Convert existing text to speech |

### Pomodoro & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/get-break-nudge` | Get break-time motivational audio |
| `GET` | `/get-focus-chart` | Generate focus performance chart |
| `GET` | `/focus-session-stats` | Get current session statistics |
| `POST` | `/reset-focus-session` | Reset focus tracking data |

### 🤖 AI Face Tracking

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/update-focus-score` | Receive real-time focus scores from face tracker |
| `POST` | `/trigger-auto-motivation` | Auto-trigger motivation when focus drops |
| `GET` | `/face-tracking-status` | Get current face tracking status |
| `POST` | `/start-face-tracking` | Signal to start face tracking |
| `POST` | `/stop-face-tracking` | Signal to stop face tracking |

### Static Files

| Path | Description |
|------|-------------|
| `/audio/` | Generated TTS audio files |

## 📁 Project Structure

```
FocusMind/
├── main.py                   # FastAPI backend server
├── nudge.py                 # AI motivation generation script
├── FocusScore.py            # Focus tracking and analytics
├── face_focus_tracker.py    # 🤖 AI-powered face tracking system
├── face_track.py            # Core face tracking utilities
├── face_tracking_utils.py   # Face tracking helper functions
├── calibration.py           # Gaze calibration system
├── ema_smoother.py          # Smoothing algorithms for tracking
├── start_face_tracking.sh   # 🚀 Easy startup script for face tracking
├── requirements.txt         # Python dependencies (includes OpenCV & MediaPipe)
├── .env                     # Environment variables (create this)
├── .gitignore              # Git ignore rules
├── audio_files/            # Generated TTS audio files
├── gaze_calibration_parameters.json  # Gaze tracking calibration data
└── frontend/               # React TypeScript application
    ├── public/
    │   ├── index.html
    │   └── manifest.json
    ├── src/
    │   ├── components/
    │   │   ├── Dashboard.tsx      # Main control panel
    │   │   ├── Header.tsx         # Quote display
    │   │   └── AttentionScore.tsx # Focus indicator
    │   ├── App.tsx               # Main application logic (with face tracking)
    │   ├── App.css              # Styling and animations
    │   └── index.tsx            # React entry point
    ├── package.json
    └── tsconfig.json
```

## 🛠️ Tech Stack

### Backend
- **FastAPI**: High-performance Python web framework
- **OpenAI GPT-4**: Advanced AI for motivational content generation
- **OpenAI TTS**: Text-to-speech with "onyx" voice model
- **Matplotlib**: Focus performance chart generation
- **Pandas/NumPy**: Data processing and analytics
- **Python subprocess**: Script execution for audio generation

### Frontend
- **React 18**: Modern JavaScript UI library
- **TypeScript**: Type-safe JavaScript development
- **Axios**: HTTP client for API communication
- **CSS3**: Advanced styling with animations and gradients
- **HTML5 Audio**: Native audio playback control

### Development Tools
- **CORS Middleware**: Cross-origin resource sharing
- **Hot Reload**: Automatic development server restart
- **Environment Variables**: Secure API key management
- **Git**: Version control with comprehensive .gitignore

## ⚙️ Configuration

### Timer Customization

Edit `frontend/src/App.tsx` to change session duration:

```typescript
// Line 44: Change timer duration
const [pomodoroTime, setPomodoroTime] = useState(25 * 60); // 25 minutes

// For different durations:
// 10 seconds (testing): useState(10)
// 5 minutes: useState(5 * 60)  
// 50 minutes: useState(50 * 60)
```

### Voice Model Customization

Edit `nudge.py` to change TTS voice:

```python
# Current voice (David Goggins-like)
voice="onyx"

# Other options: "alloy", "echo", "fable", "nova", "shimmer"
```

## 🚨 Troubleshooting

### Common Issues

**Port Already in Use**
```bash
# Kill processes on backend port
lsof -ti:8000 | xargs kill -9

# Kill processes on frontend port  
lsof -ti:3000 | xargs kill -9
```

**OpenAI API Errors**
- Verify API key is correct in `.env`
- Check API usage limits and billing
- Ensure GPT-4 and TTS access are enabled

**Audio Not Playing**
- Check browser audio permissions
- Verify audio files in `audio_files/` directory
- Ensure `/audio/` endpoint is accessible

**Frontend Build Errors**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm start
```

**Python Environment Issues**
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Performance Optimization

- **Audio Files**: Auto-generated files accumulate; clean `audio_files/` periodically
- **Memory**: Restart backend if memory usage grows high during long sessions
- **Browser**: Use Chrome/Firefox for best audio performance

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **David Goggins**: Inspiration for the motivational coaching style
- **OpenAI**: GPT-4 and TTS technology powering the AI features
- **Pomodoro Technique**: Francesco Cirillo's time management method
- **React Community**: For the excellent development tools and ecosystem

---

**Built with 💪 by [5quidL0rd](https://github.com/5quidL0rd)**

*"Stay hard, stay focused, and dominate your goals!"* - FocusMind AI Coach
