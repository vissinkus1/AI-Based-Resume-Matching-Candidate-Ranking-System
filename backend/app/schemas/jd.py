"""
schemas/jd.py — Pydantic schemas for JD request / response validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Sub-schemas
# ------------------------------------------------------------------

class QualificationSchema(BaseModel):
    """A single extracted qualification."""
    level: str = Field(..., description="Normalised level: bachelor/master/phd/diploma/any")
    raw_phrase: str = Field(..., description="Original phrase from the JD text")


class ParsedJDData(BaseModel):
    """Structured data extracted from a JD."""
    title: str | None = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    qualifications: list[QualificationSchema] = []
    responsibilities: list[str] = []
    keywords: list[str] = []


# ------------------------------------------------------------------
# Request schemas
# ------------------------------------------------------------------

class JDTextRequest(BaseModel):
    """Request body for pasting JD text directly."""
    text: str = Field(..., min_length=10, description="Raw JD text (minimum 10 chars)")


class JDUpdateRequest(BaseModel):
    """
    Request body for updating a JD's parsed data after recruiter review.

    All fields are optional — only provided fields are updated.
    """
    title: str | None = None
    required_skills: list[str] | None = None
    preferred_skills: list[str] | None = None
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    qualifications: list[QualificationSchema] | None = None
    responsibilities: list[str] | None = None
    keywords: list[str] | None = None


# ------------------------------------------------------------------
# Response schemas
# ------------------------------------------------------------------

class JDResponse(BaseModel):
    """Full JD record returned by the API."""
    id: int
    title: str | None
    raw_text: str
    parsed: ParsedJDData
    source: str
    filename: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JDListItem(BaseModel):
    """Lightweight JD record for list endpoints."""
    id: int
    title: str | None
    source: str
    filename: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JDParseResponse(BaseModel):
    """Response after parsing a JD (includes id and parsed data)."""
    id: int
    title: str | None
    parsed: ParsedJDData
    message: str = "JD parsed and saved successfully."
