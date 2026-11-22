"""
models package — SQLAlchemy ORM models.
"""

from app.models.jd import JobDescription
from app.models.candidate import Candidate

__all__ = ["JobDescription", "Candidate"]
