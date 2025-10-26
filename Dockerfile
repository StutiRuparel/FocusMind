# -------------------------------------------------
# 1️⃣ Base image – Python 3.11 (slim)
# -------------------------------------------------
FROM python:3.11-slim


# -------------------------------------------------
# 2️⃣ System dependencies – only what OpenCV needs
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \                # <-- correct package name for the slim image
        build-essential \
        git \
        libgl1 \               # <-- replaces libgl1-mesa-glx
        libglib2.0-0 \
        ca-certificates \      # ensures HTTPS works for curl / Node installer
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# 3️⃣ Install Node (LTS) – required for the React build
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
# 6️⃣ Copy the whole source tree
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# 7️⃣ Build the React front‑end (production)
# -------------------------------------------------
WORKDIR /app/frontend
RUN npm install
RUN npm run build           

# -------------------------------------------------
# 8️⃣ Return to project root for runtime
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# 9️⃣ Expose a placeholder port (Render will replace $PORT)
# -------------------------------------------------
EXPOSE 8080  

# -------------------------------------------------
# 🔟 Runtime – start FastAPI with uvicorn on $PORT
# -------------------------------------------------
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]

