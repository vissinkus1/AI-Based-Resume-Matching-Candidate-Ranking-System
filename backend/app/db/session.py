"""
db/session.py — FastAPI dependency that provides a DB session per request.

Usage in a router:
    from app.db.session import get_db

    @router.get("/items")
    def list_items(db: Session = Depends(get_db)):
        ...

The session is committed/closed automatically via the generator lifecycle.
"""

from typing import Generator

from sqlalchemy.orm import Session

from app.db.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """
    Yield a SQLAlchemy session and ensure it is closed after the request.

    FastAPI's Depends() runs the generator: code before `yield` runs
    before the route handler, code after `yield` runs after it finishes
    (or raises).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
