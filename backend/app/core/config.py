"""
core/config.py — Centralised application settings.

Reads from environment variables (and an optional .env file).
Defaults are tuned for local development with SQLite.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from env vars / .env."""

    # ── General ──
    PROJECT_NAME: str = "Resume Matcher"
    VERSION: str = "0.1.0"

    # ── Database ──
    # Default: SQLite file in the backend directory.
    # Override with DATABASE_URL env var for PostgreSQL, etc.
    DATABASE_URL: str = "sqlite:///./resume_matcher.db"

    # ── CORS ──
    # Origins allowed to call the API (React dev server by default).
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Singleton instance used throughout the app via `from app.core.config import settings`
settings = Settings()
