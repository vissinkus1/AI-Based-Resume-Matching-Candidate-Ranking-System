"""
schemas/candidate.py — Pydantic schemas for Candidate / Resume data validation.
"""

from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# ------------------------------------------------------------------
# Sub-schemas for Parsed Resume
# ------------------------------------------------------------------

class ResumeSkillSchema(BaseModel):
    name: str
    category: str = ""
    tier: str = "core"
    parent: str | None = None
    section: str = ""
    confidence: str = "strong"
    evidence: str = ""


class ExperienceEntrySchema(BaseModel):
    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    months: int = 0
    is_current: bool = False
    is_internship: bool = False
    description: str = ""
    skills_in_entry: list[str] = []


class EducationEntrySchema(BaseModel):
    degree: str = ""
    level: str = ""
    field: str = ""
    institution: str = ""
    year: int | None = None


class ParsedResumeData(BaseModel):
    name: str = ""
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    location: str | None = None
    total_experience_years: float = 0.0
    internship_months: int = 0
    experience_source: str = "date_ranges"
    job_titles: list[str] = []
    skills: list[ResumeSkillSchema] = []
    experience_entries: list[ExperienceEntrySchema] = []
    education: list[EducationEntrySchema] = []
    summary: str = ""
    parse_warnings: list[str] = []


# ------------------------------------------------------------------
# Candidate API Response Schemas
# ------------------------------------------------------------------

class CandidateResponse(BaseModel):
    """Full candidate detail response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float = 0.0
    parsed: ParsedResumeData
    raw_text: str
    created_at: datetime


class CandidateListItem(BaseModel):
    """Summary item for the candidates list table."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    name: str | None = None
    email: str | None = None
    phone: str | None = None
    total_experience_years: float = 0.0
    top_skills: list[str] = []
    skills_count: int = 0
    warnings_count: int = 0
    created_at: datetime


class SingleUploadResult(BaseModel):
    """Per-file outcome in batch upload."""
    filename: str
    status: str  # "parsed" | "failed"
    candidate_id: int | None = None
    name: str | None = None
    error: str | None = None


class BatchUploadResponse(BaseModel):
    """Aggregate result of batch resume upload."""
    total_files: int
    successful: int
    failed: int
    results: list[SingleUploadResult]
