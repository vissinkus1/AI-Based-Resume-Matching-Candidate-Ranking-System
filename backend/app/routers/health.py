"""
routers/health.py — Health-check endpoint.

Returns the API, database, and embedding model status. The frontend calls this
on load to display system readiness.
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.embedding_service import get_embedding_service

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
            "model_ready": true | false,
            "database_error": "..." (only when database is false)
        }
    """
    result = {
        "status": "healthy",
        "api": True,
        "database": False,
        "model_ready": False,
    }

    try:
        # Verify DB connection
        db.execute(text("SELECT 1"))
        result["database"] = True
    except Exception as exc:
        result["status"] = "unhealthy"
        result["database_error"] = str(exc)

    try:
        result["model_ready"] = get_embedding_service().is_ready()
    except Exception:
        result["model_ready"] = False

    return result
