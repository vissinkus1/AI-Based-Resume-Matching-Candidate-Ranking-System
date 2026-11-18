"""
run.py — Convenience script to start the backend server.

Usage:
    python run.py

Starts Uvicorn on 0.0.0.0:8000 with auto-reload enabled.
"""

import uvicorn


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",   # Import path to the FastAPI application
        host="0.0.0.0",
        port=8000,
        reload=True,       # Auto-reload on code changes (dev only)
    )
