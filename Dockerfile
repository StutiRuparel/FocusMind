# -------------------------------------------------
# 1️⃣ Base image – Python 3.11 (change if you need another)
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# 2️⃣ System dependencies (OpenCV GL libs + Node)
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg build-essential git \
        libgl1-mesa-glx libglib2.0-0 \
        # optional but useful for other CV wheels
        libglib2.0-dev libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# 3️⃣ Install Node (LTS) – needed for the React build
# -------------------------------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# -------------------------------------------------
# 4️⃣ Working directory
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# 5️⃣ Python dependencies
# -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
# 6️⃣ Copy source code
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# 7️⃣ Build the React front‑end (production)
# -------------------------------------------------
WORKDIR /app/frontend
RUN npm install
RUN npm run build        # creates ./build

# -------------------------------------------------
# 8️⃣ Return to project root for runtime
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# 9️⃣ Expose a placeholder port (Render rewrites with $PORT)
# -------------------------------------------------
EXPOSE 8080   # any non‑privileged number works

# -------------------------------------------------
# 🔟 Runtime – start the FastAPI app with uvicorn
# -------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
