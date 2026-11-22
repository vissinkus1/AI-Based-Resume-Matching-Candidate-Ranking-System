"""
repositories/candidate_repository.py — Data access layer for Candidates.

Encapsulates all database operations for Candidate records.
"""

from sqlalchemy.orm import Session

from app.models.candidate import Candidate


class CandidateRepository:
    """Repository for Candidate CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        filename: str,
        name: str | None,
        email: str | None,
        phone: str | None,
        total_experience_years: float,
        parsed_json: dict,
        raw_text: str,
    ) -> Candidate:
        """Create and persist a new Candidate record."""
        candidate = Candidate(
            filename=filename,
            name=name,
            email=email,
            phone=phone,
            total_experience_years=total_experience_years,
            parsed_json=parsed_json,
            raw_text=raw_text,
        )
        self.db.add(candidate)
        self.db.commit()
        self.db.refresh(candidate)
        return candidate

    def get_by_id(self, candidate_id: int) -> Candidate | None:
        """Find a single candidate by primary key."""
        return self.db.query(Candidate).filter(Candidate.id == candidate_id).first()

    def list_all(self) -> list[Candidate]:
        """Return all candidates, newest first."""
        return self.db.query(Candidate).order_by(Candidate.created_at.desc()).all()

    def count(self) -> int:
        """Return total number of candidates in database."""
        return self.db.query(Candidate).count()

    def delete(self, candidate_id: int) -> bool:
        """Delete candidate by id and cascade delete any match results."""
        candidate = self.get_by_id(candidate_id)
        if not candidate:
            return False
        from app.models.match import MatchResultDB
        self.db.query(MatchResultDB).filter(MatchResultDB.candidate_id == candidate_id).delete()
        self.db.delete(candidate)
        self.db.commit()
        return True

    def delete_all(self) -> int:
        """Delete all candidates and associated match results."""
        from app.models.match import MatchResultDB
        self.db.query(MatchResultDB).delete()
        count = self.db.query(Candidate).count()
        self.db.query(Candidate).delete()
        self.db.commit()
        return count
