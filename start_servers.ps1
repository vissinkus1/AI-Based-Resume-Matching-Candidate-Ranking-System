Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "Starting AI Resume Matcher & Candidate Ranking System" -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan
Write-Host ""

# Start backend API
Write-Host "Starting Backend API on http://localhost:8080 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --app-dir backend"

# Start frontend UI
Write-Host "Starting Frontend UI on http://localhost:5173 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host ""
Write-Host "Both servers are launching in separate terminal windows!" -ForegroundColor Yellow
Write-Host "  - Frontend UI:  http://localhost:5173" -ForegroundColor Yellow
Write-Host "  - Backend Docs: http://localhost:8080/docs" -ForegroundColor Yellow
Write-Host ""
