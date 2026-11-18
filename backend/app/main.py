"""
main.py — FastAPI application entry point.

Creates the app, registers middleware (CORS), includes routers,
and triggers DB table creation on startup.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, Base
from app.routers import health


# ------------------------------------------------------------------
# Lifespan: runs once on startup and once on shutdown.
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    - On startup: create all SQLAlchemy tables that don't exist yet.
    - On shutdown: dispose of the engine connection pool.
    """
    # Create tables (safe to call repeatedly — only creates missing ones)
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()


# ------------------------------------------------------------------
# App factory
# ------------------------------------------------------------------
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AI-Based Resume Matching & Candidate Ranking System",
    lifespan=lifespan,
)

# ------------------------------------------------------------------
# CORS — allow the React dev server to call the API
# ------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,   # ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------
# Routers
# ------------------------------------------------------------------
app.include_router(health.router)
