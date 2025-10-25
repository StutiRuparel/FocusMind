#!/usr/bin/env zsh
set -euo pipefail

# Create a virtual environment in .venv and install dependencies
python3 -m venv .venv
echo "Created virtual environment at .venv"

# Use the venv's pip to avoid activation in non-interactive shells
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "Dependencies installed. To activate the environment in this shell run:"
echo "  source .venv/bin/activate"
