#!/usr/bin/env bash
# scripts/setup.sh - Automated Setup for macOS / Linux
set -euo pipefail

echo "=========================================================="
echo " AI-Based Resume Matcher - Environment Setup (macOS/Linux)"
echo "=========================================================="

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"

# 1. Backend Python Virtual Environment
echo ""
echo "[1/4] Setting up Python virtual environment in backend/venv..."
cd "$BACKEND_DIR"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "Virtual environment created."
else
    echo "Virtual environment already exists."
fi

VENV_PYTHON="$BACKEND_DIR/venv/bin/python"
VENV_PIP="$BACKEND_DIR/venv/bin/pip"

echo ""
echo "[2/4] Installing backend dependencies..."
"$VENV_PIP" install --upgrade pip
"$VENV_PIP" install -r requirements.txt

echo "Installing spaCy English language model (en_core_web_sm)..."
"$VENV_PYTHON" -m spacy download en_core_web_sm

# 2. Frontend Dependencies
echo ""
echo "[3/4] Installing frontend npm packages..."
cd "$FRONTEND_DIR"
npm install

# 3. Environment Variables
echo ""
echo "[4/4] Checking environment configurations..."
cd "$ROOT_DIR"
if [ ! -f "backend/.env" ] && [ -f "backend/.env.example" ]; then
    cp "backend/.env.example" "backend/.env"
    echo "Created backend/.env from backend/.env.example"
fi
if [ ! -f "frontend/.env" ] && [ -f "frontend/.env.example" ]; then
    cp "frontend/.env.example" "frontend/.env"
    echo "Created frontend/.env from frontend/.env.example"
fi

echo ""
echo "=========================================================="
echo " Setup complete! To start the application:"
echo "   Backend:  ./scripts/run_backend.sh   (http://127.0.0.1:8080)"
echo "   Frontend: ./scripts/run_frontend.sh  (http://localhost:5173)"
echo "=========================================================="
