"""
models/jd.py — SQLAlchemy ORM model for Job Descriptions.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.db.database import Base


class JobDescription(Base):
    """
    Stores a Job Description along with its parsed structured data.

    Columns:
        id:          Auto-increment primary key.
        title:       Extracted job title (may be edited by recruiter).
        raw_text:    Full original text of the JD.
        parsed_json: Structured parse result (skills, experience, etc.).
        source:      How the JD was provided — "paste" or "upload".
        filename:    Original filename if uploaded, None if pasted.
        created_at:  Timestamp when the record was created.
    """

    __tablename__ = "job_descriptions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=False)
    parsed_json = Column(JSON, nullable=True)
    source = Column(String(20), nullable=False, default="paste")  # "paste" or "upload"
    filename = Column(String(500), nullable=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def __repr__(self) -> str:
        return f"<JobDescription id={self.id} title='{self.title}'>"
