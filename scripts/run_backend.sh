#!/usr/bin/env bash
# scripts/run_backend.sh - Run FastAPI backend on port 8080 (macOS / Linux)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_PYTHON="$BACKEND_DIR/venv/bin/python"

cd "$BACKEND_DIR"
echo "Starting FastAPI Backend on http://127.0.0.1:8080 (Docs: http://127.0.0.1:8080/docs)..."
exec "$VENV_PYTHON" -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
