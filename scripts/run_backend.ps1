# scripts/run_backend.ps1 - Run FastAPI backend on port 8080 (Windows)
$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
$VENV_PYTHON = Join-Path $BACKEND_DIR "venv\Scripts\python.exe"

Set-Location $BACKEND_DIR
Write-Host "Starting FastAPI Backend on http://127.0.0.1:8080 (Docs: http://127.0.0.1:8080/docs)..." -ForegroundColor Cyan
& $VENV_PYTHON -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --reload
