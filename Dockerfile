# -------------------------------------------------
#  Base image – pick the exact Python version you need
#  (change 3.11‑slim to 3.10‑slim, 3.12‑slim, etc.)
# -------------------------------------------------
FROM python:3.11-slim

# ---- Install OS utilities needed for Node and builds ----
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# ---- Install Node (LTS) from the official repo ----------
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest   # optional – newest npm

# -------------------------------------------------
#  Working directory inside the container
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
#  1️⃣ Install Python dependencies (build step)
# -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
#  2️⃣ Copy the whole source tree
# -------------------------------------------------
COPY . .

# -------------------------------------------------
#  3️⃣ Install the frontend (Node) dependencies
# -------------------------------------------------
WORKDIR /app/frontend
RUN npm install

# -------------------------------------------------
#  Return to project root for the runtime command
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
#  Expose a port – Render injects $PORT at runtime
# -------------------------------------------------
EXPOSE 10000   # any number; Render rewrites it to $PORT

# -------------------------------------------------
#  4️⃣ Runtime – launch backend and frontend together
# -------------------------------------------------
# The `sh -c` string runs both commands in background (`&`)
# and then `wait`s so the container stays alive as long as either
# process runs.
CMD ["sh", "-c", "\
    python main.py & \
    cd frontend && npm start & \
    wait\
"]