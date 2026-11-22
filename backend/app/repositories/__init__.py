"""
repositories package — Data access objects.
"""

from app.repositories.jd_repository import JDRepository
from app.repositories.candidate_repository import CandidateRepository

__all__ = ["JDRepository", "CandidateRepository"]
