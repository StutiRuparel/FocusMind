# FocusMind - Motivational Study Coach

A minimalist web application that provides David Goggins-style motivational quotes and tracks your attention score with intelligent monitoring.

## Features

- **Smart Motivational System**: AI-generated David Goggins quotes that appear automatically when focus drops
- **Attention Score Tracking**: Visual circular progress indicator (0-100) with color-coded feedback
- **On-Demand Motivation**: "Get Nudge Quote" button for instant motivation via `nudge.py` script
- **Auto-Reset**: Attention score resets to 100 on page refresh
- **Minimalist Design**: Clean, modern UI focused on productivity

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 14+
- OpenAI API Key

### 1. Clone and Setup Backend

```bash
git clone <your-repo-url>
cd FocusMind

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo "OPENAI_API_KEY=your_openai_api_key_here" > .env
```

### 2. Setup Frontend

```bash
cd frontend
npm install
```

### 3. Run the Application

**Terminal 1 - Backend:**
```bash
# From project root, with venv activated
python main.py
```

**Terminal 2 - Frontend:**
```bash
# From frontend directory
npm start
```

**Access:** Open `http://localhost:3000` in your browser

## How It Works

1. **Start**: Attention score begins at 100%
2. **Simulate Distraction**: Click "Decrease Attention (-15)" to simulate focus loss
3. **Auto-Motivation**: When score drops below 80, get automatic David Goggins motivation
4. **Manual Motivation**: Click "Get Nudge Quote 💪" anytime for fresh motivation from `nudge.py`
5. **Reset**: Refresh page to reset attention score to 100

## API Endpoints

- `GET /` - Health check
- `GET /motivation?reset=true` - Get motivational quote and attention score (with optional reset)
- `GET /attention-score` - Get current attention score
- `POST /decrease-attention` - Decrease attention score by 15
- `POST /get-nudge-quote` - Execute nudge.py script for fresh motivation

## Project Structure

```
FocusMind/
├── main.py              # FastAPI backend server
├── nudge.py             # Standalone motivation script
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create this)
├── .gitignore          # Git ignore rules
└── frontend/           # React TypeScript app
    ├── src/
    │   ├── components/
    │   └── App.tsx
    └── package.json
```

## Tech Stack

- **Backend**: FastAPI, OpenAI GPT-4, Python subprocess
- **Frontend**: React, TypeScript, Axios
- **Styling**: CSS3 with modern gradients and animations
- **AI**: OpenAI GPT-4 for David Goggins-style motivation

## Environment Variables

Create a `.env` file in the project root:
```
OPENAI_API_KEY=your_openai_api_key_here
```

## Troubleshooting

- **Port conflicts**: Kill processes with `lsof -ti:8000 | xargs kill -9` and `lsof -ti:3000 | xargs kill -9`
- **Missing dependencies**: Ensure virtual environment is activated before `pip install`
- **API errors**: Verify your OpenAI API key is valid and has credits