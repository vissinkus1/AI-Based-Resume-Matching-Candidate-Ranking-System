"""
models/match.py — SQLAlchemy ORM models for Matching Runs and Candidate Results.
"""

from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class MatchRun(Base):
    """
    Represents an execution of the matching engine for a Job Description
    against a cohort of candidates.

    Columns:
        id:                 Auto-increment primary key.
        jd_id:              Foreign key to job_descriptions.id (cascade delete).
        jd_snapshot_hash:   SHA-256 hash of the parsed JD content at execution time.
        candidate_count:    Number of candidates evaluated in this run.
        duration_ms:        Total matching execution time in milliseconds.
        config_snapshot:    JSON snapshot of active ScoringWeights and thresholds.
        created_at:         Timestamp when the run was executed.
    """

    __tablename__ = "match_runs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    jd_id = Column(
        Integer,
        ForeignKey("job_descriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    jd_snapshot_hash = Column(String(64), nullable=False)
    candidate_count = Column(Integer, nullable=False, default=0)
    duration_ms = Column(Float, nullable=False, default=0.0)
    config_snapshot = Column(JSON, nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    jd = relationship("JobDescription", backref="match_runs")
    results = relationship(
        "MatchResultDB",
        back_populates="run",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MatchResultDB.rank",
    )

    def __repr__(self) -> str:
        return f"<MatchRun id={self.id} jd_id={self.jd_id} candidates={self.candidate_count}>"


class MatchResultDB(Base):
    """
    Stores an individual candidate's match score and explainable breakdown
    within a specific MatchRun.

    Columns:
        id:            Auto-increment primary key.
        run_id:        Foreign key to match_runs.id (cascade delete).
        candidate_id:  Foreign key to candidates.id (set null if candidate deleted).
        rank:          Candidate rank within this run (1 = best match).
        final_score:   Overall composite score (0 - 100).
        band:          Recommendation band ("Strong match", "Good match", etc.).
        is_knockout:   Whether the knockout safeguard cap was applied.
        result_json:   Full JSON serialization of MatchResult.to_dict().
        created_at:    Timestamp when this result was recorded.
    """

    __tablename__ = "match_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    run_id = Column(
        Integer,
        ForeignKey("match_runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    candidate_id = Column(
        Integer,
        ForeignKey("candidates.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    rank = Column(Integer, nullable=False)
    final_score = Column(Float, nullable=False)
    band = Column(String(50), nullable=False)
    is_knockout = Column(Boolean, nullable=False, default=False)
    result_json = Column(JSON, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    run = relationship("MatchRun", back_populates="results")
    candidate = relationship("Candidate")

    __table_args__ = (
        Index("ix_match_results_run_rank", "run_id", "rank"),
    )

    def __repr__(self) -> str:
        return (
            f"<MatchResultDB id={self.id} run_id={self.run_id} "
            f"candidate_id={self.candidate_id} rank={self.rank} score={self.final_score}>"
        )
