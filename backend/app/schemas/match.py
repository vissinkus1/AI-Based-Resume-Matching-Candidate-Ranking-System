"""
schemas/match.py — Pydantic models for Match API request and response bodies.
"""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


# ------------------------------------------------------------------
# Request Schemas
# ------------------------------------------------------------------

class MatchRunRequest(BaseModel):
    """Payload to trigger an AI matching and ranking execution."""
    jd_id: int = Field(..., description="ID of the parsed Job Description to match against")
    candidate_ids: list[int] | None = Field(
        None,
        description="Optional list of Candidate IDs. If None or empty, matches all candidates in DB.",
    )


# ------------------------------------------------------------------
# Response Schemas
# ------------------------------------------------------------------

class MatchRunResponse(BaseModel):
    """Summary response returned immediately after running a match."""
    id: int
    jd_id: int
    jd_title: str | None = None
    candidate_count: int
    duration_ms: float
    is_stale: bool = False
    created_at: datetime


class MatchRunListItem(BaseModel):
    """Metadata item in the match runs history list."""
    id: int
    jd_id: int
    jd_title: str | None = None
    candidate_count: int
    duration_ms: float
    is_stale: bool = False
    created_at: datetime


class MatchResultSummary(BaseModel):
    """Summary of an individual candidate's match result for list/table display."""
    id: int
    candidate_id: int | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    rank: int
    final_score: float
    band: str
    is_knockout: bool
    skill_score: float
    semantic_score: float
    experience_score: float
    qualification_score: float
    title_score: float
    relevant_experience_years: float
    total_experience_years: float
    matched_skills_count: int
    missing_required_count: int
    top_skills: list[str] = []
    summary: str = ""


class MatchResultsPage(BaseModel):
    """Paginated collection of candidate match results."""
    run_id: int
    items: list[MatchResultSummary]
    total: int
    page: int
    page_size: int
    total_pages: int


class MatchRunDetailResponse(BaseModel):
    """Comprehensive details and distribution statistics for a MatchRun."""
    id: int
    jd_id: int
    jd_title: str | None = None
    candidate_count: int
    duration_ms: float
    is_stale: bool = False
    created_at: datetime
    config_snapshot: dict[str, Any] | None = None
    band_distribution: dict[str, int]
    average_score: float
    top_candidate_name: str | None = None
    top_candidate_score: float | None = None


class CandidateDetailResultResponse(BaseModel):
    """Exhaustive explainable result for a single candidate within a match run."""
    run_id: int
    candidate_id: int | None = None
    candidate_name: str | None = None
    candidate_email: str | None = None
    candidate_phone: str | None = None
    candidate_location: str | None = None
    rank: int
    final_score: float
    uncapped_score: float
    band: str
    is_knockout: bool
    knockout_reason: str | None = None
    scores: dict[str, float]
    contributions: dict[str, float]
    weights: dict[str, float]
    skills: dict[str, Any]
    semantic: dict[str, Any]
    experience: dict[str, Any]
    qualification: dict[str, Any]
    title: dict[str, Any]
    summary: str
    strengths: list[str]
    gaps: list[str]
    reasons: list[dict[str, Any]]
    raw_resume_text: str | None = None


class ScoringConfigResponse(BaseModel):
    """Active algorithm weights, thresholds, and calibration constants."""
    weights: dict[str, float]
    required_vs_preferred: dict[str, float]
    skill_tier_weights: dict[str, float]
    confidence_multipliers: dict[str, float]
    credit_table: dict[str, float]
    thresholds: dict[str, Any]
    knockout_safeguards: dict[str, Any]
