"""
routers/health.py — Health-check endpoint.

Returns the API and database status.  The frontend calls this on load
to display backend connectivity.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> dict:
    """
    GET /health

    Returns:
        {
            "status": "healthy" | "unhealthy",
            "api": true,
            "database": true | false,
            "database_error": "..." (only when database is false)
        }

    The endpoint always returns HTTP 200 so monitoring tools can
    distinguish between "app is up but DB is down" and "app is down".
    """
    result = {
        "status": "healthy",
        "api": True,
        "database": False,
    }

    try:
        # Execute a trivial query to verify the DB connection works.
        db.execute(text("SELECT 1"))
        result["database"] = True
    except Exception as exc:
        result["status"] = "unhealthy"
        result["database_error"] = str(exc)

    return result
