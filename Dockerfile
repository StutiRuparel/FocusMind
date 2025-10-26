# -------------------------------------------------
# Base image – pick the exact Python version you need.
# Change 3.11‑slim to 3.10‑slim, 3.12‑slim, etc. if required.
# -------------------------------------------------
FROM python:3.11-slim

# -------------------------------------------------
# Install OS utilities needed for Node and builds
# -------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gnupg \
        build-essential \
        git \
    && rm -rf /var/lib/apt/lists/*

# -------------------------------------------------
# Install Node (LTS) from the official repository
# -------------------------------------------------
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g npm@latest   # optional – newest npm

# -------------------------------------------------
# Set the working directory inside the container
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# Install Python dependencies (build step)
# -------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# -------------------------------------------------
# Copy the whole source tree into the image
# -------------------------------------------------
COPY . .

# -------------------------------------------------
# Install frontend (Node) dependencies
# -------------------------------------------------
WORKDIR /app/frontend
RUN npm install

# -------------------------------------------------
# Return to the project root for the runtime command
# -------------------------------------------------
WORKDIR /app

# -------------------------------------------------
# Expose a placeholder port (Render will inject $PORT at runtime)
# -------------------------------------------------
EXPOSE 8080   # any numeric value works; Render rewrites it to $PORT

# -------------------------------------------------
# Runtime: launch backend and frontend together
# -------------------------------------------------
# The sh -c string runs both commands in the background (&)
# and then `wait`s so the container stays alive while either runs.
CMD ["sh", "-c", "\
    python main.py & \
    cd frontend && npm start & \
    wait\
"]
