"""
repositories package — Data access objects.
"""

from app.repositories.jd_repository import JDRepository
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.match_repository import MatchRepository, compute_jd_hash

__all__ = ["JDRepository", "CandidateRepository", "MatchRepository", "compute_jd_hash"]
