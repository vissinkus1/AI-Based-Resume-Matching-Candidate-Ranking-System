"""
routers/resumes.py — Candidate / Resume management endpoints.

Endpoints:
    POST   /api/resumes/upload  — Batch upload resumes (PDF/DOCX, up to 50 files)
    GET    /api/resumes         — List all parsed candidates
    GET    /api/resumes/{id}    — Get candidate by ID with full parsed details
    DELETE /api/resumes/{id}    — Delete a single candidate
    DELETE /api/resumes         — Clear all candidates (testing/reset)
"""

import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.repositories.candidate_repository import CandidateRepository
from app.schemas.candidate import (
    CandidateResponse,
    CandidateListItem,
    SingleUploadResult,
    BatchUploadResponse,
    ParsedResumeData,
)
from app.services.resume_parser import parse_resume
from app.core.exceptions import ResumeMatcherError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/resumes", tags=["Resumes & Candidates"])

MAX_FILES_PER_BATCH = 50
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


@router.post(
    "/upload",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Batch upload resumes (PDF/DOCX)",
)
async def upload_resumes(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload and parse a batch of up to 50 resumes (PDF / DOCX).

    Each file is processed independently in isolation: a single corrupt or
    invalid file will NOT abort processing of the remaining files.
    """
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for upload.",
        )

    if len(files) > MAX_FILES_PER_BATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Too many files: maximum allowed is {MAX_FILES_PER_BATCH} per batch (received {len(files)}).",
        )

    repo = CandidateRepository(db)
    results: list[SingleUploadResult] = []
    successful_count = 0
    failed_count = 0

    for upload_file in files:
        filename = upload_file.filename or "unknown_resume"
        ext = Path(filename).suffix.lower()

        # Validate file extension
        if ext not in ALLOWED_EXTENSIONS:
            failed_count += 1
            results.append(
                SingleUploadResult(
                    filename=filename,
                    status="failed",
                    error=f"Unsupported file type '{ext}'. Only PDF and DOCX files are supported.",
                )
            )
            continue

        try:
            content = await upload_file.read()
            if len(content) > MAX_FILE_SIZE_BYTES:
                failed_count += 1
                results.append(
                    SingleUploadResult(
                        filename=filename,
                        status="failed",
                        error=f"File exceeds maximum size of 5 MB ({len(content) / (1024*1024):.1f} MB).",
                    )
                )
                continue

            # Parse the resume
            parsed = parse_resume(file_bytes=content, filename=filename)
            raw_text = parsed.sections.get("full_text", "")
            if not raw_text:
                # Fallback to combining available text
                raw_text = "\n".join(parsed.sections.values())

            parsed_dict = parsed.to_dict()

            # Save to database
            candidate = repo.create(
                filename=filename,
                name=parsed.name or None,
                email=parsed.email or None,
                phone=parsed.phone or None,
                total_experience_years=parsed.total_experience_years,
                parsed_json=parsed_dict,
                raw_text=raw_text,
            )

            successful_count += 1
            results.append(
                SingleUploadResult(
                    filename=filename,
                    status="parsed",
                    candidate_id=candidate.id,
                    name=candidate.name,
                )
            )

        except ResumeMatcherError as e:
            logger.warning("Domain error parsing %s: %s", filename, e.message)
            failed_count += 1
            results.append(
                SingleUploadResult(
                    filename=filename,
                    status="failed",
                    error=e.message,
                )
            )
        except Exception as e:
            logger.exception("Unexpected error processing resume %s", filename)
            failed_count += 1
            results.append(
                SingleUploadResult(
                    filename=filename,
                    status="failed",
                    error=f"Processing failed: {str(e)}",
                )
            )

    return BatchUploadResponse(
        total_files=len(files),
        successful=successful_count,
        failed=failed_count,
        results=results,
    )


@router.get(
    "",
    response_model=list[CandidateListItem],
    summary="List all candidates",
)
def list_candidates(db: Session = Depends(get_db)):
    """Return summary list of all uploaded candidates."""
    repo = CandidateRepository(db)
    candidates = repo.list_all()

    items = []
    for c in candidates:
        parsed = c.parsed_json or {}
        skills = parsed.get("skills", [])
        top_skills = [s["name"] for s in skills[:5] if isinstance(s, dict) and "name" in s]
        warnings = parsed.get("parse_warnings", [])

        items.append(
            CandidateListItem(
                id=c.id,
                filename=c.filename,
                name=c.name,
                email=c.email,
                phone=c.phone,
                total_experience_years=c.total_experience_years or 0.0,
                top_skills=top_skills,
                skills_count=len(skills),
                warnings_count=len(warnings),
                created_at=c.created_at,
            )
        )

    return items


@router.get(
    "/{candidate_id}",
    response_model=CandidateResponse,
    summary="Get full candidate details",
)
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Return full parsed candidate data by ID."""
    repo = CandidateRepository(db)
    candidate = repo.get_by_id(candidate_id)
    if not candidate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found.",
        )

    parsed_data = candidate.parsed_json or {}
    return CandidateResponse(
        id=candidate.id,
        filename=candidate.filename,
        name=candidate.name,
        email=candidate.email,
        phone=candidate.phone,
        total_experience_years=candidate.total_experience_years,
        parsed=ParsedResumeData(**parsed_data),
        raw_text=candidate.raw_text,
        created_at=candidate.created_at,
    )


@router.delete(
    "/{candidate_id}",
    summary="Delete a candidate",
)
def delete_candidate(candidate_id: int, db: Session = Depends(get_db)):
    """Delete a single candidate by ID."""
    repo = CandidateRepository(db)
    deleted = repo.delete(candidate_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Candidate with ID {candidate_id} not found.",
        )
    return {"detail": "Candidate deleted successfully", "id": candidate_id}


@router.delete(
    "",
    summary="Clear all candidates",
)
def clear_all_candidates(db: Session = Depends(get_db)):
    """Delete all candidates from database."""
    repo = CandidateRepository(db)
    count = repo.delete_all()
    return {"detail": f"Successfully deleted {count} candidates.", "deleted_count": count}
