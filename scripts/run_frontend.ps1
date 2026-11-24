# scripts/run_frontend.ps1 - Run Vite Frontend on port 5173 (Windows)
$ROOT_DIR = Split-Path -Parent $PSScriptRoot
$FRONTEND_DIR = Join-Path $ROOT_DIR "frontend"

Set-Location $FRONTEND_DIR
Write-Host "Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Cyan
node node_modules/vite/bin/vite.js --port 5173
