"""
schemas package — Pydantic models for request and response validation.
"""

from app.schemas.jd import (
    JDTextRequest,
    JDUpdateRequest,
    JDResponse,
    ParsedJDData,
    QualificationSchema,
)
from app.schemas.candidate import (
    CandidateResponse,
    CandidateListItem,
    BatchUploadResponse,
)
from app.schemas.match import (
    MatchRunRequest,
    MatchRunResponse,
    MatchRunListItem,
    MatchResultSummary,
    MatchResultsPage,
    MatchRunDetailResponse,
    CandidateDetailResultResponse,
    ScoringConfigResponse,
)

__all__ = [
    "JDTextRequest",
    "JDUpdateRequest",
    "JDResponse",
    "ParsedJDData",
    "QualificationSchema",
    "CandidateResponse",
    "CandidateListItem",
    "BatchUploadResponse",
    "MatchRunRequest",
    "MatchRunResponse",
    "MatchRunListItem",
    "MatchResultSummary",
    "MatchResultsPage",
    "MatchRunDetailResponse",
    "CandidateDetailResultResponse",
    "ScoringConfigResponse",
]
