"""
tests/test_reconciliation.py — Regression test asserting 100% score reconciliation
between in-memory ranking (CLI runner) and the API matching engine (POST /api/demo/seed).
"""

from pathlib import Path
from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd
from app.services.resume_parser import parse_resume
from app.services.embedding_service import get_embedding_service
from app.services.skills_taxonomy import get_taxonomy
from app.services.matching_engine import rank

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data"
RESUMES_DIR = SAMPLE_DIR / "resumes"
JDS_DIR = SAMPLE_DIR / "jds"


def test_cli_script_and_api_produce_identical_scores():
    # 1. Way A: In-memory ranking
    emb_service = get_embedding_service()
    taxonomy = get_taxonomy()

    resume_files = sorted(
        [f for f in RESUMES_DIR.iterdir() if f.suffix.lower() in {".pdf", ".docx"} and f.name.startswith("candidate_")]
    )
    parsed_candidates = [
        parse_resume(rf.read_bytes(), rf.name, today=(2026, 11))
        for rf in resume_files
    ]

    jd_path = JDS_DIR / "java_backend_jd.txt"
    jd_text = extract_text(jd_path.read_bytes(), jd_path.name)
    parsed_jd = parse_jd(jd_text)

    ranked_results = rank(
        parsed_jd,
        parsed_candidates,
        taxonomy=taxonomy,
        embed_service=emb_service,
    )
    script_scores = {
        (cand.name or r.candidate_name): r.final_score
        for cand, r in ranked_results
    }

    # 2. Way B: Direct API Seeder Execution
    from app.db.database import SessionLocal
    from app.routers.demo import seed_demo
    db = SessionLocal()
    try:
        seed_resp = seed_demo(jd="java", reset=True, db=db)
        run_id = seed_resp.run_id

        from app.models.match import MatchResultDB
        from sqlalchemy.orm import joinedload
        results = (
            db.query(MatchResultDB)
            .options(joinedload(MatchResultDB.candidate))
            .filter(MatchResultDB.run_id == run_id)
            .all()
        )
        api_scores = {r.candidate.name: r.final_score for r in results if r.candidate}
    finally:
        db.close()

    # 3. Assert identity
    assert len(script_scores) == 12
    assert len(api_scores) == 12

    for name, s_score in script_scores.items():
        assert name in api_scores, f"Candidate {name} missing in API results"
        a_score = api_scores[name]
        assert abs(s_score - a_score) < 0.05, (
            f"Score mismatch for {name}: script={s_score}, api={a_score}"
        )
