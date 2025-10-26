# -------------------------------------------------
# 1️⃣ Base image – Python 3.11 (slim, Debian bookworm)
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# 2️⃣ System dependencies – only what OpenCV needs
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        build-essential \
        git \
        libgl1 \            # runtime OpenGL library for opencv‑python
        libglib2.0-0 \
        ca-certificates \   # needed for HTTPS (curl / node installer)
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# 3️⃣ Install Node (LTS) – required for the React build
# -------------------------------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest   # optional – newest npm

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
# 6️⃣ Copy the whole source tree (including start.sh)
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
# 9️⃣ Make the startup script executable
# -------------------------------------------------
COPY start.sh /usr/local/bin/start.sh
RUN chmod +x /usr/local/bin/start.sh

# -------------------------------------------------
# 🔟 Expose a placeholder port (Render will rewrite $PORT)
# -------------------------------------------------
EXPOSE 8080   

# -------------------------------------------------
# 🔟 Runtime – use the script to launch uvicorn
# -------------------------------------------------
CMD ["/usr/local/bin/start.sh"]
