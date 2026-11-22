"""
services/match_service.py — Orchestrates Match Engine executions with DB integration.
"""

import time
import logging
from typing import Any
from sqlalchemy.orm import Session

from app.models.jd import JobDescription
from app.models.candidate import Candidate
from app.models.match import MatchRun
from app.repositories.match_repository import MatchRepository, compute_jd_hash
from app.services.jd_parser import ParsedJD, QualificationInfo, parse_jd
from app.services.resume_parser import (
    ParsedResume,
    ResumeSkill,
    ExperienceEntry,
    EducationEntry,
    parse_resume,
)
from app.services.embedding_service import get_embedding_service
from app.services.skills_taxonomy import get_taxonomy
from app.services.matching_engine import rank, MatchResult
from app.core.scoring_config import SCORING

logger = logging.getLogger(__name__)


def hydrate_parsed_jd(jd: JobDescription) -> ParsedJD:
    """
    Reconstruct a ParsedJD instance from a JobDescription ORM model.
    Falls back to re-parsing raw_text if parsed_json is missing.
    """
    data = jd.parsed_json or {}
    if not data and jd.raw_text:
        return parse_jd(jd.raw_text)

    # Reconstruct QualificationInfo list
    raw_quals = data.get("qualifications", [])
    quals: list[QualificationInfo] = []
    for q in raw_quals:
        if isinstance(q, dict):
            quals.append(
                QualificationInfo(
                    level=q.get("level", "bachelor"),
                    raw_phrase=q.get("raw_phrase", ""),
                )
            )

    return ParsedJD(
        title=jd.title or data.get("title"),
        required_skills=list(data.get("required_skills", [])),
        preferred_skills=list(data.get("preferred_skills", [])),
        min_experience_years=data.get("min_experience_years"),
        max_experience_years=data.get("max_experience_years"),
        qualifications=quals,
        min_required_level=data.get("min_required_level"),
        preferred_level=data.get("preferred_level"),
        responsibilities=list(data.get("responsibilities", [])),
        keywords=list(data.get("keywords", [])),
        skill_evidence=dict(data.get("skill_evidence", {})),
    )


def hydrate_parsed_resume(cand: Candidate) -> ParsedResume:
    """
    Reconstruct a ParsedResume instance from a Candidate ORM model.
    Falls back to re-parsing raw_text if parsed_json is missing.
    """
    data = cand.parsed_json or {}
    if not data and cand.raw_text:
        return parse_resume(cand.raw_text.encode("utf-8"), cand.filename)

    # Reconstruct ResumeSkill list
    skills = [
        ResumeSkill(
            name=s.get("name", ""),
            category=s.get("category", ""),
            tier=s.get("tier", "core"),
            parent=s.get("parent"),
            section=s.get("section", ""),
            confidence=s.get("confidence", "strong"),
            evidence=s.get("evidence", ""),
        )
        for s in data.get("skills", [])
        if isinstance(s, dict)
    ]

    # Reconstruct ExperienceEntry list
    exp_entries = [
        ExperienceEntry(
            title=e.get("title", ""),
            company=e.get("company", ""),
            start_date=e.get("start_date", ""),
            end_date=e.get("end_date", ""),
            months=e.get("months", 0),
            is_current=e.get("is_current", False),
            is_internship=e.get("is_internship", False),
            description=e.get("description", ""),
            skills_in_entry=list(e.get("skills_in_entry", [])),
        )
        for e in data.get("experience_entries", [])
        if isinstance(e, dict)
    ]

    # Reconstruct EducationEntry list
    edu_entries = [
        EducationEntry(
            degree=ed.get("degree", ""),
            level=ed.get("level", "bachelor"),
            field=ed.get("field", ""),
            institution=ed.get("institution", ""),
            year=ed.get("year"),
        )
        for ed in data.get("education", [])
        if isinstance(ed, dict)
    ]

    return ParsedResume(
        name=cand.name or data.get("name", ""),
        email=cand.email or data.get("email"),
        phone=cand.phone or data.get("phone"),
        linkedin_url=data.get("linkedin_url"),
        github_url=data.get("github_url"),
        location=data.get("location"),
        total_experience_years=cand.total_experience_years or data.get("total_experience_years", 0.0),
        internship_months=data.get("internship_months", 0),
        experience_source=data.get("experience_source", "date_ranges"),
        job_titles=list(data.get("job_titles", [])),
        skills=skills,
        experience_entries=exp_entries,
        education=edu_entries,
        summary=data.get("summary", ""),
        sections=dict(data.get("sections", {})),
        parse_warnings=list(data.get("parse_warnings", [])),
    )


class MatchService:
    """Orchestrates matching runs between JDs and candidate pools."""

    def __init__(self, db: Session):
        self.db = db
        self.repo = MatchRepository(db)
        self.taxonomy = get_taxonomy()
        self.embedding_service = get_embedding_service()

    def run_match(
        self, jd_id: int, candidate_ids: list[int] | None = None
    ) -> MatchRun:
        """
        Execute full matching & ranking for a JD against specified candidates
        (or all candidates in DB if None/empty).
        """
        jd = self.db.query(JobDescription).filter(JobDescription.id == jd_id).first()
        if not jd:
            raise ValueError(f"Job Description with id {jd_id} not found.")

        # Query candidates
        cand_query = self.db.query(Candidate)
        if candidate_ids:
            cand_query = cand_query.filter(Candidate.id.in_(candidate_ids))
        candidates: list[Candidate] = cand_query.all()

        if not candidates:
            raise ValueError("No candidates found to match against.")

        # Hydrate ParsedJD and calculate hash
        parsed_jd = hydrate_parsed_jd(jd)
        jd_hash = compute_jd_hash(jd.parsed_json)

        # Hydrate candidates and map back to DB IDs
        parsed_resumes: list[ParsedResume] = []
        cand_map: dict[int, int] = {}  # id(parsed_resume) -> candidate.id

        for c in candidates:
            pr = hydrate_parsed_resume(c)
            setattr(pr, "_candidate_id", c.id)
            cand_map[id(pr)] = c.id
            parsed_resumes.append(pr)

        # Execute ranking engine with timing
        t0 = time.perf_counter()
        ranked_results: list[tuple[ParsedResume, MatchResult]] = rank(
            jd=parsed_jd,
            candidates=parsed_resumes,
            taxonomy=self.taxonomy,
            embed_service=self.embedding_service,
            config=SCORING,
        )
        duration_ms = (time.perf_counter() - t0) * 1000.0

        # Build results payload
        results_data: list[dict[str, Any]] = []
        for rank_idx, (pr, m_res) in enumerate(ranked_results, start=1):
            cand_id = cand_map.get(id(pr), getattr(pr, "_candidate_id", None))
            results_data.append(
                {
                    "candidate_id": cand_id,
                    "rank": rank_idx,
                    "final_score": m_res.final_score,
                    "band": m_res.recommendation_band,
                    "is_knockout": m_res.is_knockout_applied,
                    "result_json": m_res.to_dict(),
                }
            )

        # Config snapshot
        config_snapshot = {
            "weights": {
                "skill": SCORING.w_skill,
                "semantic": SCORING.w_semantic,
                "experience": SCORING.w_experience,
                "qualification": SCORING.w_qualification,
                "title": SCORING.w_title,
            },
            "thresholds": {
                "knockout_safeguard_threshold": SCORING.knockout_core_coverage_threshold,
                "knockout_cap_score": SCORING.knockout_score_cap,
                "inferred_concept_threshold": SCORING.inferred_concept_threshold,
                "semantic_raw_cos_low": SCORING.semantic_raw_cos_low,
                "semantic_raw_cos_high": SCORING.semantic_raw_cos_high,
                "title_raw_cos_low": SCORING.title_raw_cos_low,
                "title_raw_cos_high": SCORING.title_raw_cos_high,
            },
        }

        # Persist run and results
        match_run = self.repo.create_run(
            jd_id=jd.id,
            jd_snapshot_hash=jd_hash,
            candidate_count=len(results_data),
            duration_ms=duration_ms,
            config_snapshot=config_snapshot,
            results_data=results_data,
        )

        return match_run
