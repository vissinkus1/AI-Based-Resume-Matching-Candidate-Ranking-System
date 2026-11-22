"""
routers/match.py — REST API endpoints for Match Runs, Results, and Explanations.
"""

import csv
import io
import math
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.match_repository import MatchRepository
from app.services.match_service import MatchService
from app.core.scoring_config import SCORING
from app.schemas.match import (
    MatchRunRequest,
    MatchRunResponse,
    MatchRunListItem,
    MatchResultRow,
    MatchResultsPage,
    MatchRunDetailResponse,
    CandidateDetailResultResponse,
    ScoringConfigResponse,
)

router = APIRouter(prefix="/api/match", tags=["match"])


# ------------------------------------------------------------------
# POST /api/match/run — Trigger a new matching execution
# ------------------------------------------------------------------

@router.post("/run", response_model=MatchRunResponse, status_code=status.HTTP_201_CREATED)
def run_match_endpoint(
    req: MatchRunRequest, db: Session = Depends(get_db)
) -> MatchRunResponse:
    """
    Execute AI matching and candidate ranking for a Job Description against
    either a specific candidate list or all candidates in the database.
    """
    service = MatchService(db)
    try:
        run = service.run_match(
            jd_id=req.jd_id, candidate_ids=req.candidate_ids
        )
    except ValueError as exc:
        msg = str(exc)
        if "not found" in msg.lower():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    return MatchRunResponse(
        id=run.id,
        jd_id=run.jd_id,
        jd_title=run.jd.title if run.jd else None,
        candidate_count=run.candidate_count,
        duration_ms=run.duration_ms,
        is_stale=False,
        stale_reason=None,
        created_at=run.created_at,
    )


# ------------------------------------------------------------------
# GET /api/match/runs/latest — Retrieve most recent match run (A4)
# ------------------------------------------------------------------

@router.get("/runs/latest", response_model=MatchRunDetailResponse)
def get_latest_run_endpoint(
    jd_id: int | None = Query(None, description="Optional JD filter"),
    db: Session = Depends(get_db),
) -> MatchRunDetailResponse:
    """Convenience endpoint to retrieve the latest run overall or for a specific JD."""
    repo = MatchRepository(db)
    run, is_stale, stale_reason = repo.get_latest_run(jd_id=jd_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching runs found.",
        )

    items, filtered_count, total, band_counts = repo.get_run_results_advanced(
        run_id=run.id, limit=500, offset=0
    )

    total_score = sum(r.final_score for r in items)
    top_cand_name = items[0].candidate.name if items and items[0].candidate else "Top Candidate"
    top_cand_score = items[0].final_score if items else None
    avg_score = round(total_score / total, 2) if total > 0 else 0.0

    return MatchRunDetailResponse(
        id=run.id,
        jd_id=run.jd_id,
        jd_title=run.jd.title if run.jd else None,
        candidate_count=run.candidate_count,
        duration_ms=run.duration_ms,
        is_stale=is_stale,
        stale_reason=stale_reason,
        created_at=run.created_at,
        config_snapshot=run.config_snapshot,
        band_distribution=band_counts,
        average_score=avg_score,
        top_candidate_name=top_cand_name,
        top_candidate_score=top_cand_score,
    )


# ------------------------------------------------------------------
# GET /api/match/runs — List past match runs
# ------------------------------------------------------------------

@router.get("/runs", response_model=list[MatchRunListItem])
def list_runs_endpoint(
    jd_id: int | None = Query(None, description="Optional JD filter"),
    limit: int = Query(50, ge=1, le=200, description="Max runs to return"),
    db: Session = Depends(get_db),
) -> list[MatchRunListItem]:
    """Retrieve history of previous match runs."""
    repo = MatchRepository(db)
    runs_with_stale = repo.list_runs(jd_id=jd_id, limit=limit)
    return [
        MatchRunListItem(
            id=run.id,
            jd_id=run.jd_id,
            jd_title=run.jd.title if run.jd else None,
            candidate_count=run.candidate_count,
            duration_ms=run.duration_ms,
            is_stale=stale,
            stale_reason=reason,
            created_at=run.created_at,
        )
        for run, stale, reason in runs_with_stale
    ]


# ------------------------------------------------------------------
# GET /api/match/runs/{run_id} — Summary and distribution for a run
# ------------------------------------------------------------------

@router.get("/runs/{run_id}", response_model=MatchRunDetailResponse)
def get_run_endpoint(
    run_id: int, db: Session = Depends(get_db)
) -> MatchRunDetailResponse:
    """Retrieve detailed metadata, staleness reasons, and band distributions for a run."""
    repo = MatchRepository(db)
    run, is_stale, stale_reason = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match run {run_id} not found.",
        )

    # Compute band distribution and average score
    items, filtered_count, total, band_counts = repo.get_run_results_advanced(
        run_id=run_id, limit=500, offset=0
    )

    total_score = sum(r.final_score for r in items)
    top_cand_name = items[0].candidate.name if items and items[0].candidate else "Top Candidate"
    top_cand_score = items[0].final_score if items else None
    avg_score = round(total_score / total, 2) if total > 0 else 0.0

    return MatchRunDetailResponse(
        id=run.id,
        jd_id=run.jd_id,
        jd_title=run.jd.title if run.jd else None,
        candidate_count=run.candidate_count,
        duration_ms=run.duration_ms,
        is_stale=is_stale,
        stale_reason=stale_reason,
        created_at=run.created_at,
        config_snapshot=run.config_snapshot,
        band_distribution=band_counts,
        average_score=avg_score,
        top_candidate_name=top_cand_name,
        top_candidate_score=top_cand_score,
    )


# ------------------------------------------------------------------
# GET /api/match/runs/{run_id}/results — Filtered & sorted candidate results (A1)
# ------------------------------------------------------------------

@router.get("/runs/{run_id}/results", response_model=MatchResultsPage)
def get_run_results_endpoint(
    run_id: int,
    sort_by: str = Query("rank", pattern="^(rank|score|final_score|experience|name)$"),
    order: str = Query("asc", pattern="^(asc|desc)$"),
    min_score: float | None = Query(None, ge=0.0, le=100.0, description="Min final score"),
    max_score: float | None = Query(None, ge=0.0, le=100.0, description="Max final score"),
    band: str | None = Query(None, description="Filter by band name"),
    min_experience: float | None = Query(None, ge=0.0, description="Min experience years"),
    skill: str | None = Query(None, description="Candidate must have matched this skill"),
    search: str | None = Query(None, description="Search name or email"),
    limit: int = Query(25, ge=1, le=200, description="Limit rows returned"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: Session = Depends(get_db),
) -> MatchResultsPage:
    """Fetch paginated, filtered, and sorted candidate ranking results."""
    repo = MatchRepository(db)
    run, _, _ = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match run {run_id} not found.",
        )

    paged_items, filtered_count, total_count, band_counts = repo.get_run_results_advanced(
        run_id=run_id,
        sort_by=sort_by,
        order=order,
        min_score=min_score,
        max_score=max_score,
        band=band,
        min_experience=min_experience,
        skill=skill,
        search=search,
        limit=limit,
        offset=offset,
    )

    rows: list[MatchResultRow] = []
    for r in paged_items:
        r_json = r.result_json or {}
        scores = r_json.get("scores", {})
        exp = r_json.get("experience", {})
        skills = r_json.get("skills", {})
        narrative = r_json.get("narrative", {})

        top_skills = [
            m.get("candidate_skill") or m.get("jd_skill")
            for m in (skills.get("matched_top") or skills.get("matched", [])[:6])
        ][:6]

        cand_name = r.candidate.name if r.candidate and r.candidate.name else r_json.get("name", "Unknown Candidate")
        cand_email = r.candidate.email if r.candidate else None

        missing_req_raw = skills.get("missing_required", [])
        missing_req_list = [
            m if isinstance(m, str) else m.get("skill", "")
            for m in missing_req_raw
        ]

        rows.append(
            MatchResultRow(
                id=r.id,
                rank=r.rank,  # Original rank, never renumbered
                original_rank=r.rank,
                candidate_id=r.candidate_id,
                name=cand_name,
                candidate_name=cand_name,
                email=cand_email,
                total_experience_years=exp.get("total_years", r.candidate.total_experience_years if r.candidate else 0.0),
                relevant_years=exp.get("relevant_years", 0.0),
                relevant_experience_years=exp.get("relevant_years", 0.0),
                match_percent=r.final_score,
                final_score=r.final_score,
                band=r.band,
                matched_top=top_skills,
                matched_top_skills=top_skills,
                missing_required_count=len(missing_req_raw),
                missing_required_skills=missing_req_list,
                is_knockout=r.is_knockout,
                knockout_reason=r_json.get("knockout_reason"),
                skill_score=scores.get("skill", 0.0),
                semantic_score=scores.get("semantic", 0.0),
                experience_score=scores.get("experience", 0.0),
                qualification_score=scores.get("qualification", 0.0),
                title_score=scores.get("title", 0.0),
                summary=narrative.get("summary") or r_json.get("summary", ""),
            )
        )

    applied_filters = {
        "sort_by": sort_by,
        "order": order,
        "min_score": min_score,
        "max_score": max_score,
        "band": band,
        "min_experience": min_experience,
        "skill": skill,
        "search": search,
    }

    return MatchResultsPage(
        run_id=run_id,
        items=rows,
        total=total_count,
        filtered_count=filtered_count,
        applied_filters=applied_filters,
        band_counts=band_counts,
        limit=limit,
        offset=offset,
    )


# ------------------------------------------------------------------
# GET /api/match/runs/{run_id}/results/{candidate_id} — Single result (A2)
# ------------------------------------------------------------------

@router.get(
    "/runs/{run_id}/results/{candidate_id}",
    response_model=CandidateDetailResultResponse,
)
def get_candidate_result_endpoint(
    run_id: int, candidate_id: int, db: Session = Depends(get_db)
) -> CandidateDetailResultResponse:
    """Retrieve full explainable breakdown, profile info, and navigation context."""
    repo = MatchRepository(db)
    ctx = repo.get_candidate_detail_context(run_id=run_id, candidate_id=candidate_id)
    if not ctx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate {candidate_id} result not found for run {run_id}.",
        )

    res = ctx["result"]
    cand = res.candidate
    jd = ctx["jd"]
    r_json = res.result_json or {}
    cand_parsed = cand.parsed_json or {} if cand else {}
    narrative = r_json.get("narrative", {})

    # JD context
    jd_parsed = jd.parsed_json or {} if jd else {}

    return CandidateDetailResultResponse(
        run_id=run_id,
        candidate_id=res.candidate_id,
        rank=ctx["rank"],
        total_candidates=ctx["total_candidates"],
        prev_candidate_id=ctx["prev_candidate_id"],
        next_candidate_id=ctx["next_candidate_id"],

        # Candidate profile
        name=cand.name if cand and cand.name else r_json.get("name", "Unknown Candidate"),
        candidate_name=cand.name if cand and cand.name else r_json.get("name", "Unknown Candidate"),
        email=cand.email if cand else None,
        phone=cand.phone if cand else None,
        links={
            "linkedin": cand_parsed.get("linkedin_url"),
            "github": cand_parsed.get("github_url"),
        },
        location=cand_parsed.get("location"),
        education=cand_parsed.get("education", []),
        experience_entries=cand_parsed.get("experience_entries", []),
        candidate_skills=cand_parsed.get("skills", []),
        summary=cand_parsed.get("summary", ""),
        parse_warnings=cand_parsed.get("parse_warnings", []),
        raw_resume_text=cand.raw_text if cand else None,

        # Overall Status
        final_score=res.final_score,
        uncapped_score=r_json.get("uncapped_score", res.final_score),
        band=res.band,
        is_knockout=res.is_knockout,
        knockout_reason=r_json.get("knockout_reason"),

        # Scores & Breakdown
        scores=r_json.get("scores", {}),
        contributions=r_json.get("contributions", {}),
        weights=r_json.get("weights", {}),
        skills_breakdown=r_json.get("skills", {}),
        semantic_breakdown=r_json.get("semantic", {}),
        experience_breakdown=r_json.get("experience", {}),
        qualification_breakdown=r_json.get("qualification", {}),
        title_breakdown=r_json.get("title", {}),

        # Backward compatibility
        skills=r_json.get("skills", {}),
        semantic=r_json.get("semantic", {}),
        experience=r_json.get("experience", {}),
        qualification=r_json.get("qualification", {}),
        title=r_json.get("title", {}),

        # Narrative
        narrative_summary=narrative.get("summary") or r_json.get("summary", ""),
        strengths=narrative.get("strengths") or r_json.get("strengths", []),
        gaps=narrative.get("gaps") or r_json.get("gaps", []),
        reasons=narrative.get("reasons") or r_json.get("reasons", []),

        # JD Requirements context
        jd_title=jd.title if jd else None,
        jd_min_experience_years=jd_parsed.get("min_experience_years"),
        jd_max_experience_years=jd_parsed.get("max_experience_years"),
        jd_min_required_qualification=jd_parsed.get("min_required_level"),
        jd_preferred_qualification=jd_parsed.get("preferred_level"),
        jd_required_skills=jd_parsed.get("required_skills", []),
        jd_preferred_skills=jd_parsed.get("preferred_skills", []),
    )


# ------------------------------------------------------------------
# GET /api/match/runs/{run_id}/export.csv — Stream CSV export
# ------------------------------------------------------------------

@router.get("/runs/{run_id}/export.csv")
def export_results_csv(
    run_id: int, db: Session = Depends(get_db)
) -> StreamingResponse:
    """Export complete candidate ranking list as a formatted CSV file."""
    repo = MatchRepository(db)
    run, _, _ = repo.get_run(run_id)
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match run {run_id} not found.",
        )

    results, _, _, _ = repo.get_run_results_advanced(
        run_id=run_id, sort_by="rank", order="asc", limit=1000, offset=0
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "Rank",
            "Candidate Name",
            "Email",
            "Final Score",
            "Band",
            "Knockout Applied",
            "Skill Score",
            "Semantic Score",
            "Experience Score",
            "Qualification Score",
            "Title Score",
            "Relevant Exp (Years)",
            "Total Exp (Years)",
            "Top Matched Skills",
            "Missing Required Skills",
            "Summary",
        ]
    )

    for r in results:
        r_json = r.result_json or {}
        scores = r_json.get("scores", {})
        exp = r_json.get("experience", {})
        skills = r_json.get("skills", {})
        narrative = r_json.get("narrative", {})

        top_skills = "; ".join(
            [
                m.get("candidate_skill") or m.get("jd_skill")
                for m in (skills.get("matched_top") or skills.get("matched", [])[:6])
            ]
        )
        missing_req = "; ".join(skills.get("missing_required", []))

        cand_name = r.candidate.name if r.candidate and r.candidate.name else r_json.get("name", "Unknown Candidate")
        cand_email = r.candidate.email if r.candidate and r.candidate.email else ""
        summary_text = (narrative.get("summary") or r_json.get("summary", "")).replace("\n", " ")

        writer.writerow(
            [
                r.rank,
                cand_name,
                cand_email,
                f"{r.final_score:.1f}",
                r.band,
                "YES" if r.is_knockout else "NO",
                f"{scores.get('skill', 0.0):.1f}",
                f"{scores.get('semantic', 0.0):.1f}",
                f"{scores.get('experience', 0.0):.1f}",
                f"{scores.get('qualification', 0.0):.1f}",
                f"{scores.get('title', 0.0):.1f}",
                f"{exp.get('relevant_years', 0.0):.1f}",
                f"{exp.get('total_years', 0.0):.1f}",
                top_skills,
                missing_req,
                summary_text,
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f'attachment; filename="match_run_{run_id}.csv"',
            "Content-Type": "text/csv; charset=utf-8",
        },
    )


# ------------------------------------------------------------------
# DELETE /api/match/runs/{run_id} — Delete run and cascade results
# ------------------------------------------------------------------

@router.delete("/runs/{run_id}", status_code=status.HTTP_200_OK)
def delete_run_endpoint(
    run_id: int, db: Session = Depends(get_db)
) -> dict[str, str]:
    """Delete a match run along with all associated ranking results."""
    repo = MatchRepository(db)
    success = repo.delete_run(run_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Match run {run_id} not found.",
        )
    return {"message": f"Match run {run_id} and all associated results deleted."}


# ------------------------------------------------------------------
# GET /api/match/config — Active algorithm weights and thresholds
# ------------------------------------------------------------------

@router.get("/config", response_model=ScoringConfigResponse)
def get_scoring_config_endpoint() -> ScoringConfigResponse:
    """Retrieve active matching engine weights, tier parameters, and thresholds."""
    return ScoringConfigResponse(
        weights={
            "skill": SCORING.w_skill,
            "semantic": SCORING.w_semantic,
            "experience": SCORING.w_experience,
            "qualification": SCORING.w_qualification,
            "title": SCORING.w_title,
        },
        required_vs_preferred={
            "required": SCORING.skill_required_weight,
            "preferred": SCORING.skill_preferred_weight,
        },
        skill_tier_weights={
            "core": SCORING.tier_weight_core,
            "supporting": SCORING.tier_weight_supporting,
            "soft": SCORING.tier_weight_soft,
        },
        confidence_multipliers={
            "strong": SCORING.confidence_mult_strong,
            "medium": SCORING.confidence_mult_medium,
            "basic": SCORING.confidence_mult_basic,
        },
        credit_table={
            "exact_or_alias": SCORING.credit_exact_or_alias,
            "child_of_required_parent": SCORING.credit_child_of_required_parent,
            "parent_of_required_child": SCORING.credit_parent_of_required_child,
            "semantic_soft_max": SCORING.credit_semantic_soft_match_max,
        },
        thresholds={
            "semantic_soft_min_threshold": SCORING.skill_soft_match_threshold,
            "inferred_concept_threshold": SCORING.inferred_concept_threshold,
            "semantic_raw_cos_low": SCORING.semantic_raw_cos_low,
            "semantic_raw_cos_high": SCORING.semantic_raw_cos_high,
            "title_raw_cos_low": SCORING.title_raw_cos_low,
            "title_raw_cos_high": SCORING.title_raw_cos_high,
            "relevance_experience_sim_threshold": SCORING.exp_relevance_threshold,
        },
        knockout_safeguards={
            "coverage_threshold": SCORING.knockout_core_coverage_threshold,
            "cap_score": SCORING.knockout_score_cap,
        },
    )
