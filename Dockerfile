# -------------------------------------------------
# 1️⃣ Base image – Python 3.11 (slim)
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# 2️⃣ System deps (OpenCV, curl, gnupg, node, etc.)
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl gnupg build-essential git libgl1 libglib2.0-0 ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# 3️⃣ Install Node (LTS) – needed for building the React app
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
# 6️⃣ Copy source code (including start.sh if you use it)
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# 7️⃣ Build the React front‑end (production)
# -------------------------------------------------
WORKDIR /app/frontend
RUN npm install && npm run build  

# -------------------------------------------------
# 8️⃣ Return to project root for runtime
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# 9️⃣ Ensure the audio directory exists (optional)
# -------------------------------------------------
RUN mkdir -p audio_files

# -------------------------------------------------
# 🔟 Expose a placeholder port (Render rewrites it with $PORT)
# -------------------------------------------------
EXPOSE 8080

# -------------------------------------------------
# 🟢 Run uvicorn in the foreground – this is the only CMD
# -------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
