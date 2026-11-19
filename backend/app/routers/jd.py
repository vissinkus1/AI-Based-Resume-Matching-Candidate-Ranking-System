"""
routers/jd.py — API endpoints for Job Description management.

Prefix: /api/jd

Endpoints:
    POST   /api/jd/parse   — Parse a JD (text or file upload), save to DB
    GET    /api/jd          — List all JDs
    GET    /api/jd/{id}     — Get a single JD with parsed data
    PUT    /api/jd/{id}     — Update parsed fields (recruiter edits)
    DELETE /api/jd/{id}     — Delete a JD
"""

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from app.core.exceptions import ResumeMatcherError
from app.db.session import get_db
from app.repositories.jd_repository import JDRepository
from app.schemas.jd import (
    JDListItem,
    JDParseResponse,
    JDResponse,
    JDUpdateRequest,
    ParsedJDData,
)
from app.services.jd_parser import parse_jd
from app.services.text_extractor import extract_text


router = APIRouter(prefix="/api/jd", tags=["Job Descriptions"])

# Maximum upload file size: 5 MB
MAX_FILE_SIZE = 5 * 1024 * 1024


# ------------------------------------------------------------------
# POST /api/jd/parse — Parse a JD from text or file
# ------------------------------------------------------------------

@router.post("/parse", response_model=JDParseResponse, status_code=201)
async def parse_jd_endpoint(
    text: str | None = Form(default=None),
    file: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
) -> JDParseResponse:
    """
    Parse a Job Description and save it to the database.

    Accepts EITHER:
      - A `text` form field with the raw JD text, OR
      - A `file` upload (PDF, DOCX, or TXT).

    Returns the parsed result with the new JD's database ID.
    """
    # Validate: at least one input must be provided
    if not text and file is None:
        raise HTTPException(
            status_code=400,
            detail="Provide either 'text' (form field) or 'file' (upload).",
        )

    source = "paste"
    filename = None
    jd_text = ""

    if file is not None:
        # ── File upload path ──
        source = "upload"
        filename = file.filename or "unknown"

        # Read and check file size
        file_bytes = await file.read()
        if len(file_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)} MB.",
            )

        # Extract text from the file
        try:
            jd_text = extract_text(file_bytes, filename)
        except ResumeMatcherError as exc:
            raise HTTPException(status_code=400, detail=exc.message)
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to process file: {str(exc)}",
            )
    else:
        # ── Text paste path ──
        jd_text = text.strip()
        if len(jd_text) < 10:
            raise HTTPException(
                status_code=400,
                detail="JD text is too short. Please provide a meaningful job description.",
            )

    # Parse the JD text
    try:
        parsed = parse_jd(jd_text)
    except Exception as exc:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse JD: {str(exc)}",
        )

    # Save to database
    repo = JDRepository(db)
    jd_record = repo.create(
        raw_text=jd_text,
        parsed_json=parsed.to_dict(),
        source=source,
        filename=filename,
        title=parsed.title,
    )

    return JDParseResponse(
        id=jd_record.id,
        title=parsed.title,
        parsed=ParsedJDData(**parsed.to_dict()),
    )


# ------------------------------------------------------------------
# GET /api/jd — List all JDs
# ------------------------------------------------------------------

@router.get("", response_model=list[JDListItem])
def list_jds(db: Session = Depends(get_db)) -> list[JDListItem]:
    """Return all saved JDs (lightweight: no raw_text or parsed data)."""
    repo = JDRepository(db)
    jds = repo.list_all()
    return [
        JDListItem(
            id=jd.id,
            title=jd.title,
            source=jd.source,
            filename=jd.filename,
            created_at=jd.created_at,
        )
        for jd in jds
    ]


# ------------------------------------------------------------------
# GET /api/jd/{id} — Get a single JD
# ------------------------------------------------------------------

@router.get("/{jd_id}", response_model=JDResponse)
def get_jd(jd_id: int, db: Session = Depends(get_db)) -> JDResponse:
    """Return a single JD with its full parsed data."""
    repo = JDRepository(db)
    jd = repo.get_by_id(jd_id)
    if jd is None:
        raise HTTPException(status_code=404, detail=f"JD with id {jd_id} not found.")

    return JDResponse(
        id=jd.id,
        title=jd.title,
        raw_text=jd.raw_text,
        parsed=ParsedJDData(**(jd.parsed_json or {})),
        source=jd.source,
        filename=jd.filename,
        created_at=jd.created_at,
    )


# ------------------------------------------------------------------
# PUT /api/jd/{id} — Update parsed fields
# ------------------------------------------------------------------

@router.put("/{jd_id}", response_model=JDResponse)
def update_jd(
    jd_id: int,
    update: JDUpdateRequest,
    db: Session = Depends(get_db),
) -> JDResponse:
    """
    Update a JD's parsed fields (after recruiter review).

    Only provided (non-null) fields are updated; others are left unchanged.
    """
    repo = JDRepository(db)

    # Build update dict from non-None fields
    update_data = update.model_dump(exclude_none=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update.")

    jd = repo.update(jd_id, update_data)
    if jd is None:
        raise HTTPException(status_code=404, detail=f"JD with id {jd_id} not found.")

    return JDResponse(
        id=jd.id,
        title=jd.title,
        raw_text=jd.raw_text,
        parsed=ParsedJDData(**(jd.parsed_json or {})),
        source=jd.source,
        filename=jd.filename,
        created_at=jd.created_at,
    )


# ------------------------------------------------------------------
# DELETE /api/jd/{id}
# ------------------------------------------------------------------

@router.delete("/{jd_id}")
def delete_jd(jd_id: int, db: Session = Depends(get_db)) -> dict:
    """Delete a JD by ID."""
    repo = JDRepository(db)
    deleted = repo.delete(jd_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"JD with id {jd_id} not found.")
    return {"message": f"JD {jd_id} deleted.", "id": jd_id}
