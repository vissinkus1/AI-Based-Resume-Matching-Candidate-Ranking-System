"""
db/database.py — SQLAlchemy engine, session factory, and declarative Base.

The connection string comes from the DATABASE_URL env var (via Settings).
Defaults to SQLite for local development.  Swap to PostgreSQL by setting
the env var — no business-logic changes required.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings


# ── Engine ──
# For SQLite we need `check_same_thread=False` so FastAPI (threaded) can
# use the connection.  This is safe for our single-process dev server.
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,          # Set True to log every SQL statement (noisy)
)

# ── Session factory ──
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# ── Declarative base ──
# All ORM models will inherit from this.
Base = declarative_base()
