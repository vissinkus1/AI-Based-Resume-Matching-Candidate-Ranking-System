@echo off
echo ========================================================
echo Starting AI Resume Matcher & Candidate Ranking System
echo ========================================================
echo.

:: Start backend in a separate window
echo Starting Backend API on http://localhost:8080 ...
start "Resume Matcher - Backend API" cmd /k "backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8080 --app-dir backend"

:: Start frontend in a separate window
echo Starting Frontend UI on http://localhost:5173 ...
start "Resume Matcher - Frontend UI" cmd /k "cd frontend && npm run dev"

echo.
echo Both servers are launching in separate terminal windows!
echo - Frontend UI:  http://localhost:5173
echo - Backend Docs: http://localhost:8080/docs
echo.
pause
