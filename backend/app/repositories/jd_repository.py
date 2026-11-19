"""
repositories/jd_repository.py — Data access layer for Job Descriptions.

Encapsulates all database operations for the JobDescription model.
Business logic and API routes should use this repository instead of
querying SQLAlchemy directly — this keeps the DB layer swappable and
testable.
"""

from sqlalchemy.orm import Session

from app.models.jd import JobDescription


class JDRepository:
    """Repository for JobDescription CRUD operations."""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        raw_text: str,
        parsed_json: dict,
        source: str = "paste",
        filename: str | None = None,
        title: str | None = None,
    ) -> JobDescription:
        """
        Create and persist a new JobDescription record.

        Args:
            raw_text:    Full text of the JD.
            parsed_json: Structured parse result dict.
            source:      "paste" or "upload".
            filename:    Original filename (upload only).
            title:       Extracted job title.

        Returns:
            The created JobDescription ORM object.
        """
        jd = JobDescription(
            title=title,
            raw_text=raw_text,
            parsed_json=parsed_json,
            source=source,
            filename=filename,
        )
        self.db.add(jd)
        self.db.commit()
        self.db.refresh(jd)
        return jd

    def get_by_id(self, jd_id: int) -> JobDescription | None:
        """Return a JD by its primary key, or None if not found."""
        return self.db.query(JobDescription).filter(
            JobDescription.id == jd_id
        ).first()

    def list_all(self) -> list[JobDescription]:
        """Return all JDs, newest first."""
        return (
            self.db.query(JobDescription)
            .order_by(JobDescription.created_at.desc())
            .all()
        )

    def update(self, jd_id: int, update_data: dict) -> JobDescription | None:
        """
        Update a JD's parsed data (and optionally title).

        Args:
            jd_id:       ID of the JD to update.
            update_data: Dict of fields to merge into parsed_json.

        Returns:
            The updated JobDescription, or None if not found.
        """
        jd = self.get_by_id(jd_id)
        if jd is None:
            return None

        # Update title if provided at the top level
        if "title" in update_data and update_data["title"] is not None:
            jd.title = update_data["title"]

        # Merge remaining fields into parsed_json
        current_parsed = dict(jd.parsed_json) if jd.parsed_json else {}
        for key, value in update_data.items():
            if value is not None:
                # Convert Pydantic models to dicts if needed
                if hasattr(value, "model_dump"):
                    current_parsed[key] = value.model_dump()
                elif isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                    current_parsed[key] = [v.model_dump() for v in value]
                else:
                    current_parsed[key] = value

        jd.parsed_json = current_parsed
        self.db.commit()
        self.db.refresh(jd)
        return jd

    def delete(self, jd_id: int) -> bool:
        """
        Delete a JD by ID.

        Returns:
            True if deleted, False if not found.
        """
        jd = self.get_by_id(jd_id)
        if jd is None:
            return False
        self.db.delete(jd)
        self.db.commit()
        return True
