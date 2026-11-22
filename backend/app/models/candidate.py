"""
models/candidate.py — SQLAlchemy ORM model for Candidates / Resumes.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, JSON

from app.db.database import Base


class Candidate(Base):
    """
    Stores a parsed candidate resume along with its extracted structured data.

    Columns:
        id:                      Auto-increment primary key.
        filename:                Original uploaded filename.
        name:                    Candidate's extracted full name.
        email:                   Candidate's extracted email address.
        phone:                   Candidate's extracted phone number.
        total_experience_years:  Calculated non-overlapping experience (years).
        parsed_json:             Full structured parse result (skills, education, etc.).
        raw_text:                Extracted raw text of the resume.
        created_at:              Timestamp when the resume was uploaded.
    """

    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    filename = Column(String(500), nullable=False)
    name = Column(String(200), nullable=True)
    email = Column(String(200), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    total_experience_years = Column(Float, nullable=False, default=0.0)
    parsed_json = Column(JSON, nullable=True)
    raw_text = Column(Text, nullable=False)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<Candidate id={self.id} name='{self.name}' filename='{self.filename}'>"
