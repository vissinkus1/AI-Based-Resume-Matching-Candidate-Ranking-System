# scripts/setup.ps1 - Automated Setup for Windows
$ErrorActionPreference = "Stop"

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host " AI-Based Resume Matcher - Environment Setup (Windows)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$BACKEND_DIR = Join-Path $ROOT_DIR "backend"
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"

# 1. Backend Python Virtual Environment
Write-Host "`n[1/4] Setting up Python virtual environment in backend/venv..." -ForegroundColor Yellow
Set-Location $BACKEND_DIR
if (-not (Test-Path "venv")) {
    python -m venv venv
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

$VENV_PYTHON = Join-Path $BACKEND_DIR "venv\Scripts\python.exe"
$VENV_PIP = Join-Path $BACKEND_DIR "venv\Scripts\pip.exe"

Write-Host "`n[2/4] Installing backend dependencies..." -ForegroundColor Yellow
& $VENV_PIP install --upgrade pip
& $VENV_PIP install -r requirements.txt

Write-Host "Installing spaCy English language model (en_core_web_sm)..." -ForegroundColor Yellow
& $VENV_PYTHON -m spacy download en_core_web_sm

# 2. Frontend Dependencies
Write-Host "`n[3/4] Installing frontend npm packages..." -ForegroundColor Yellow
Set-Location $FRONTEND_DIR
npm install

# 3. Environment Variables
Write-Host "`n[4/4] Checking environment configurations..." -ForegroundColor Yellow
Set-Location $ROOT_DIR
if (-not (Test-Path "backend\.env") -and (Test-Path "backend\.env.example")) {
    Copy-Item "backend\.env.example" "backend\.env"
    Write-Host "Created backend/.env from backend/.env.example" -ForegroundColor Green
}
if (-not (Test-Path "frontend\.env") -and (Test-Path "frontend\.env.example")) {
    Copy-Item "frontend\.env.example" "frontend\.env"
    Write-Host "Created frontend/.env from frontend/.env.example" -ForegroundColor Green
}

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host " Setup complete! To start the application:" -ForegroundColor Green
Write-Host "   Backend:  .\scripts\run_backend.ps1   (http://127.0.0.1:8080)" -ForegroundColor White
Write-Host "   Frontend: .\scripts\run_frontend.ps1  (http://localhost:5173)" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
