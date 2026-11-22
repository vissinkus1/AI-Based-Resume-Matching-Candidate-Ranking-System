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
    stale_reason: str | None = None
    created_at: datetime


class MatchRunListItem(BaseModel):
    """Metadata item in the match runs history list."""
    id: int
    jd_id: int
    jd_title: str | None = None
    candidate_count: int
    duration_ms: float
    is_stale: bool = False
    stale_reason: str | None = None
    created_at: datetime


class MatchResultRow(BaseModel):
    """Row item in the ranking dashboard results table."""
    id: int
    rank: int                            # Original rank, never renumbered
    original_rank: int | None = None
    candidate_id: int | None = None
    name: str = "Unknown Candidate"
    candidate_name: str | None = None
    email: str | None = None
    total_experience_years: float = 0.0
    relevant_years: float = 0.0
    relevant_experience_years: float = 0.0
    match_percent: float = 0.0           # final_score
    final_score: float = 0.0
    band: str = "Weak match"
    matched_top: list[str] = Field(default_factory=list)          # Max 6 skills
    matched_top_skills: list[str] = Field(default_factory=list)
    missing_required_count: int = 0
    missing_required_skills: list[str] = Field(default_factory=list)
    is_knockout: bool = False
    knockout_reason: str | None = None
    skill_score: float = 0.0
    semantic_score: float = 0.0
    experience_score: float = 0.0
    qualification_score: float = 0.0
    title_score: float = 0.0
    summary: str = ""


# Backward-compatible alias for MatchResultRow
MatchResultSummary = MatchResultRow


class MatchResultsPage(BaseModel):
    """Paginated and filtered collection of candidate match results."""
    run_id: int
    items: list[MatchResultRow]
    total: int                          # Total in run before filters
    filtered_count: int                 # Count matching current filters
    applied_filters: dict[str, Any]     # Active filter parameters
    band_counts: dict[str, int]         # Total counts per band across whole run
    limit: int
    offset: int


class MatchRunDetailResponse(BaseModel):
    """Comprehensive details and distribution statistics for a MatchRun."""
    id: int
    jd_id: int
    jd_title: str | None = None
    candidate_count: int
    duration_ms: float
    is_stale: bool = False
    stale_reason: str | None = None
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
    rank: int
    total_candidates: int
    prev_candidate_id: int | None = None
    next_candidate_id: int | None = None

    # Candidate profile
    name: str = "Unknown Candidate"
    candidate_name: str | None = None
    email: str | None = None
    phone: str | None = None
    links: dict[str, str | None] = Field(default_factory=dict)
    location: str | None = None
    education: list[dict[str, Any]] = Field(default_factory=list)
    experience_entries: list[dict[str, Any]] = Field(default_factory=list)
    candidate_skills: list[dict[str, Any]] = Field(default_factory=list)
    summary: str = ""
    parse_warnings: list[str] = Field(default_factory=list)
    raw_resume_text: str | None = None

    # Overall Match Status
    final_score: float
    uncapped_score: float
    band: str
    is_knockout: bool
    knockout_reason: str | None = None

    # Score components & contributions
    scores: dict[str, float]
    contributions: dict[str, float]
    weights: dict[str, float]

    # Explainable factor sections
    skills_breakdown: dict[str, Any] = Field(default_factory=dict)
    semantic_breakdown: dict[str, Any] = Field(default_factory=dict)
    experience_breakdown: dict[str, Any] = Field(default_factory=dict)
    qualification_breakdown: dict[str, Any] = Field(default_factory=dict)
    title_breakdown: dict[str, Any] = Field(default_factory=dict)

    # Narrative
    narrative_summary: str = ""
    strengths: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    reasons: list[dict[str, Any]] = Field(default_factory=list)

    # Backward compatibility fields
    skills: dict[str, Any] = Field(default_factory=dict)
    semantic: dict[str, Any] = Field(default_factory=dict)
    experience: dict[str, Any] = Field(default_factory=dict)
    qualification: dict[str, Any] = Field(default_factory=dict)
    title: dict[str, Any] = Field(default_factory=dict)

    # JD Comparison Context
    jd_title: str | None = None
    jd_min_experience_years: float | None = None
    jd_max_experience_years: float | None = None
    jd_min_required_qualification: str | None = None
    jd_preferred_qualification: str | None = None
    jd_required_skills: list[str] = Field(default_factory=list)
    jd_preferred_skills: list[str] = Field(default_factory=list)


class ScoringConfigResponse(BaseModel):
    """Active algorithm weights, thresholds, and calibration constants."""
    weights: dict[str, float]
    required_vs_preferred: dict[str, float]
    skill_tier_weights: dict[str, float]
    confidence_multipliers: dict[str, float]
    credit_table: dict[str, float]
    thresholds: dict[str, Any]
    knockout_safeguards: dict[str, Any]
