"""
scripts/test_keyword_stuffing.py — Run keyword stuffing candidate vs Java JD with the 12 candidates.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.jd_parser import parse_jd
from app.services.resume_parser import parse_resume
from app.services.matching_engine import rank
from app.services.embedding_service import get_embedding_service
from app.services.skills_taxonomy import get_taxonomy

SAMPLE_DIR = BACKEND_DIR.parent / "sample_data"
JD_PATH = SAMPLE_DIR / "jds" / "java_backend_jd.txt"
RESUMES_DIR = SAMPLE_DIR / "resumes"
STUFFING_PATH = SAMPLE_DIR / "resumes_wild" / "wild_keyword_stuffing.txt"

def main():
    emb_service = get_embedding_service()
    taxonomy = get_taxonomy()

    jd_text = JD_PATH.read_text(encoding="utf-8")
    jd = parse_jd(jd_text)

    # Parse 12 original candidates
    resume_files = sorted(
        [f for f in RESUMES_DIR.iterdir() if f.suffix.lower() in {".pdf", ".docx"} and f.name.startswith("candidate_")]
    )
    parsed_candidates = [
        parse_resume(rf.read_bytes(), rf.name, today=(2026, 11))
        for rf in resume_files
    ]

    # Parse keyword stuffing candidate
    stuffing_parsed = parse_resume(STUFFING_PATH.read_bytes(), STUFFING_PATH.name, today=(2026, 11))
    all_parsed = parsed_candidates + [stuffing_parsed]

    # Rank all 13 candidates
    ranked = rank(
        jd,
        all_parsed,
        taxonomy=taxonomy,
        embed_service=emb_service,
    )

    print("=" * 115)
    print("KEYWORD STUFFING EXPERIMENT RESULTS (Java JD: 12 Real + 1 Keyword Stuffed)")
    print("=" * 115)
    print(f"{'Rank':<5} | {'Candidate':<28} | {'Score':<7} | {'Band':<12} | {'Skill':<6} | {'Sem':<6} | {'Exp':<6} | {'Qual':<6} | {'Title':<6} | Notes")
    print("-" * 115)

    for r_num, (cand, res) in enumerate(ranked, 1):
        is_stuffing = "Jordan Miller" in cand.name
        note = "<- KEYWORD STUFFED (No Exp/Degree)" if is_stuffing else ""
        print(f"{r_num:<5} | {cand.name:<28} | {res.final_score:<7.1f} | {res.recommendation_band:<12} | {res.skill_score:<6.1f} | {res.semantic_score:<6.1f} | {res.experience_score:<6.1f} | {res.qualification_score:<6.1f} | {res.title_relevance_score:<6.1f} | {note}")

    print("=" * 115)
    print("STUFFING CANDIDATE BREAKDOWN:")
    print(f"Total Exp: {stuffing_parsed.total_experience_years} years")
    print(f"Education: {len(stuffing_parsed.education)} degrees found")
    stuffing_cand, stuffing_res = next((c, r) for c, r in ranked if "Jordan Miller" in c.name)
    print(f"Skills matched: {len(stuffing_res.matched_skills)} / {len(jd.required_skills) + len(jd.preferred_skills)}")
    print(f"Knockout applied: {bool(stuffing_res.knockout_reason)} (Reason: {stuffing_res.knockout_reason})")
    print("=" * 115)

if __name__ == "__main__":
    main()
