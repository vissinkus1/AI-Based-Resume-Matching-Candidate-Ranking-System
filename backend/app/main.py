"""
main.py — FastAPI application entry point.

Creates the app, registers middleware (CORS), includes routers,
triggers DB table creation on startup, and warms up the embedding model.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.database import engine, Base
from app.models.jd import JobDescription  # noqa: F401 — registers table with Base
from app.models.candidate import Candidate  # noqa: F401 — registers table with Base
from app.models.match import MatchRun, MatchResultDB  # noqa: F401 — registers table with Base
from app.services.embedding_service import get_embedding_service
from app.routers import health, jd, resumes, match

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Lifespan: runs once on startup and once on shutdown.
# ------------------------------------------------------------------
@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    - On startup: create all SQLAlchemy tables that don't exist yet,
      and warm up the SentenceTransformer model weights.
    - On shutdown: dispose of the engine connection pool.
    """
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    logger.info("Pre-warming embedding model...")
    try:
        emb_service = get_embedding_service()
        emb_service.warmup()
        logger.info("Embedding model warmed up successfully.")
    except Exception as e:
        logger.warning("Embedding model warmup failed (will lazy load on demand): %s", e)

    yield

    logger.info("Disposing database engine...")
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
app.include_router(jd.router)
app.include_router(resumes.router)
app.include_router(match.router)
