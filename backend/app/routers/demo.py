"""
routers/demo.py — One-click demonstration endpoint for evaluators and recruiters.

POST /api/demo/seed?jd=java|react|aiml&reset=true
"""

import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.jd_repository import JDRepository
from app.models.match import MatchRun, MatchResultDB
from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd
from app.services.resume_parser import parse_resume
from app.services.match_service import MatchService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/demo", tags=["Demo"])


class DemoSeedResponse(BaseModel):
    success: bool
    jd_id: int
    jd_title: str
    run_id: int
    candidate_count: int
    duration_ms: float = 0.0
    message: str


def _get_sample_data_dir() -> Path:
    # Try relative to this file: backend/app/routers/demo.py -> 3 levels up is backend, 4 is project root
    candidate = Path(__file__).resolve().parents[3] / "sample_data"
    if candidate.exists():
        return candidate
    candidate_cwd = Path.cwd() / "sample_data"
    if candidate_cwd.exists():
        return candidate_cwd
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Sample data directory not found. Looked at {candidate} and {candidate_cwd}",
    )


JD_MAP = {
    "java": ("java_backend_jd.txt", "Senior Java Backend Engineer"),
    "react": ("react_frontend_jd.docx", "Lead React Frontend Developer"),
    "aiml": ("aiml_engineer_jd.pdf", "Senior AI/ML Engineer"),
}


@router.post("/seed", response_model=DemoSeedResponse, status_code=status.HTTP_200_OK)
def seed_demo(
    jd: str = Query("java", description="One of: java, react, aiml"),
    reset: bool = Query(True, description="Whether to reset previous candidates and demo runs"),
    db: Session = Depends(get_db),
) -> DemoSeedResponse:
    """
    One-click instant demo environment seeder:
    1. Loads the selected sample JD (Java, React, or AI/ML).
    2. Seeds all 12 candidate resumes.
    3. Runs AI matching and candidate ranking.
    4. Returns the created run_id for instant dashboard loading.
    """
    jd_key = jd.lower().strip()
    if jd_key not in JD_MAP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JD key '{jd}'. Must be one of: {list(JD_MAP.keys())}",
        )

    sample_dir = _get_sample_data_dir()
    jds_dir = sample_dir / "jds"
    resumes_dir = sample_dir / "resumes"

    candidate_repo = CandidateRepository(db)
    jd_repo = JDRepository(db)

    # 1. Reset if requested
    if reset:
        logger.info("Demo seed: resetting database tables for clean run...")
        # Clear match runs and results
        db.query(MatchResultDB).delete(synchronize_session=False)
        db.query(MatchRun).delete(synchronize_session=False)
        candidate_repo.delete_all()
        db.commit()

    # 2. Ingest or find the target JD
    jd_filename, default_title = JD_MAP[jd_key]
    jd_file_path = jds_dir / jd_filename
    if not jd_file_path.exists():
        # Fallback to .txt if docx/pdf not found
        txt_alt = jds_dir / f"{jd_key}_backend_jd.txt" if jd_key == "java" else (
            jds_dir / "react_frontend_jd.txt" if jd_key == "react" else jds_dir / "aiml_engineer_jd.txt"
        )
        if txt_alt.exists():
            jd_file_path = txt_alt
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Sample JD file not found: {jd_file_path}",
            )

    # Read and parse JD
    jd_bytes = jd_file_path.read_bytes()
    jd_text = extract_text(jd_bytes, jd_file_path.name)
    parsed_jd_obj = parse_jd(jd_text)

    jd_db = jd_repo.create(
        raw_text=jd_text,
        parsed_json=parsed_jd_obj.to_dict(),
        source="demo_seed",
        filename=jd_file_path.name,
        title=parsed_jd_obj.title or default_title,
    )

    # 3. Seed candidate resumes if needed
    existing_candidates = candidate_repo.list_all()
    if len(existing_candidates) < 12:
        resume_files = sorted(
            [f for f in resumes_dir.iterdir() if f.suffix.lower() in {".pdf", ".docx"} and f.name.startswith("candidate_")]
        )
        for rf in resume_files:
            file_bytes = rf.read_bytes()
            parsed_res = parse_resume(file_bytes=file_bytes, filename=rf.name)
            raw_text = parsed_res.sections.get("full_text", "")
            if not raw_text:
                raw_text = "\n".join(parsed_res.sections.values())
            candidate_repo.create(
                filename=rf.name,
                name=parsed_res.name or None,
                email=parsed_res.email or None,
                phone=parsed_res.phone or None,
                total_experience_years=parsed_res.total_experience_years,
                parsed_json=parsed_res.to_dict(),
                raw_text=raw_text,
            )

    # 4. Run matching
    match_service = MatchService(db)
    run = match_service.run_match(jd_id=jd_db.id)

    return DemoSeedResponse(
        success=True,
        jd_id=jd_db.id,
        jd_title=jd_db.title,
        run_id=run.id,
        candidate_count=run.candidate_count,
        duration_ms=run.duration_ms,
        message=f"Demo successfully seeded with {run.candidate_count} candidates for '{jd_db.title}'.",
    )
