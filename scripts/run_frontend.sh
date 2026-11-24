#!/usr/bin/env bash
# scripts/run_frontend.sh - Run Vite Frontend on port 5173 (macOS / Linux)
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/frontend"

cd "$FRONTEND_DIR"
echo "Starting Vite Frontend on http://localhost:5173..."
exec npm run dev -- --port 5173
