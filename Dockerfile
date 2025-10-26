# -------------------------------------------------
#  Base image – change the version if you need another
# -------------------------------------------------
FROM python:3.11-slim   # replace with 3.10‑slim, 3.12‑slim, etc.

# ---- System utilities needed for Node and builds ----
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# ---- Install Node (LTS) ---------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest

# ---- Working directory ----------------------------
WORKDIR /app

# ---- Install Python dependencies -------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Copy the whole source tree --------------------
COPY . .

# ---- Install frontend (Node) dependencies ----------
WORKDIR /app/frontend
RUN npm install

# ---- Return to project root -----------------------
WORKDIR /app

# ---- Expose a port (Render will inject $PORT) ----
# Choose any numeric placeholder; Render overwrites it.
EXPOSE 8080

# ---- Runtime command – launch backend & frontend ----
CMD ["sh", "-c", "\
    python main.py & \
    cd frontend && npm start & \
    wait\
"]
