"""
scripts/test_reconciliation.py — Reconcile Java JD vs 12 resumes across:
(a) run_matching.py (direct memory rank)
(b) POST /api/demo/seed?jd_key=java
(c) Manual upload through API endpoints (POST /api/jd/parse, POST /api/resumes/upload, POST /api/match/run)
"""

import sys
import json
from pathlib import Path
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.db.database import SessionLocal
from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd
from app.services.resume_parser import parse_resume
from app.services.embedding_service import get_embedding_service
from app.services.skills_taxonomy import get_taxonomy
from app.services.matching_engine import rank
from app.core.scoring_config import SCORING

SAMPLE_DIR = BACKEND_DIR.parent / "sample_data"
RESUMES_DIR = SAMPLE_DIR / "resumes"
JDS_DIR = SAMPLE_DIR / "jds"

def run_way_a():
    """Way A: Direct in-memory run_matching.py logic"""
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

    rows = []
    for rank_idx, (cand, r) in enumerate(ranked_results, start=1):
        d = r.to_dict()
        scores = d["scores"]
        rows.append({
            "rank": rank_idx,
            "name": cand.name or r.candidate_name,
            "final_score": r.final_score,
            "skill": round(scores.get("skill", 0), 1),
            "semantic": round(scores.get("semantic", 0), 1),
            "experience": round(scores.get("experience", 0), 1),
            "qualification": round(scores.get("qualification", 0), 1),
            "title": round(scores.get("title", 0), 1),
            "band": r.recommendation_band,
        })
    return rows

def run_way_b(client):
    """Way B: POST /api/demo/seed?jd=java"""
    resp = client.post("/api/demo/seed?jd=java&reset=true")
    assert resp.status_code == 200, resp.text
    run_id = resp.json()["run_id"]

    results_resp = client.get(f"/api/match/runs/{run_id}/results?limit=50")
    assert results_resp.status_code == 200, results_resp.text
    items = results_resp.json()["items"]

    # Also fetch full component scores for each candidate
    rows = []
    for item in items:
        cand_id = item["candidate_id"]
        detail_resp = client.get(f"/api/match/runs/{run_id}/results/{cand_id}")
        assert detail_resp.status_code == 200, detail_resp.text
        d = detail_resp.json()
        scores = d["scores"]
        rows.append({
            "rank": item["rank"],
            "name": item["name"],
            "final_score": item["final_score"],
            "skill": round(scores.get("skill", 0), 1),
            "semantic": round(scores.get("semantic", 0), 1),
            "experience": round(scores.get("experience", 0), 1),
            "qualification": round(scores.get("qualification", 0), 1),
            "title": round(scores.get("title", 0), 1),
            "band": item["band"],
        })
    return rows, run_id

def run_way_c(client):
    """Way C: Upload JD file and 12 resumes manually through API, then POST /api/match/run"""
    # 1. Reset DB
    client.post("/api/demo/seed?jd=java&reset=true")
    # Clean out candidate and JD tables
    from app.models.candidate import Candidate
    from app.models.jd import JobDescription
    from app.models.match import MatchRun, MatchResultDB
    db = SessionLocal()
    db.query(MatchResultDB).delete()
    db.query(MatchRun).delete()
    db.query(Candidate).delete()
    db.query(JobDescription).delete()
    db.commit()

    # 2. Upload JD
    jd_path = JDS_DIR / "java_backend_jd.txt"
    with open(jd_path, "rb") as f:
        jd_resp = client.post(
            "/api/jd/parse",
            files={"file": (jd_path.name, f.read(), "text/plain")},
        )
    assert jd_resp.status_code == 201, jd_resp.text
    jd_id = jd_resp.json()["id"]

    # 3. Upload 12 resumes in batch
    resume_files = sorted(
        [f for f in RESUMES_DIR.iterdir() if f.suffix.lower() in {".pdf", ".docx"} and f.name.startswith("candidate_")]
    )
    upload_files = []
    for rf in resume_files:
        mime = "application/pdf" if rf.suffix.lower() == ".pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        upload_files.append(("files", (rf.name, rf.read_bytes(), mime)))

    res_resp = client.post("/api/resumes/upload", files=upload_files)
    assert res_resp.status_code in (200, 201), res_resp.text

    # 4. Trigger match run
    match_resp = client.post("/api/match/run", json={"jd_id": jd_id})
    assert match_resp.status_code == 201, match_resp.text
    run_id = match_resp.json()["id"]

    results_resp = client.get(f"/api/match/runs/{run_id}/results?limit=50")
    assert results_resp.status_code == 200, results_resp.text
    items = results_resp.json()["items"]

    rows = []
    for item in items:
        cand_id = item["candidate_id"]
        detail_resp = client.get(f"/api/match/runs/{run_id}/results/{cand_id}")
        assert detail_resp.status_code == 200, detail_resp.text
        d = detail_resp.json()
        scores = d["scores"]
        rows.append({
            "rank": item["rank"],
            "name": item["name"],
            "final_score": item["final_score"],
            "skill": round(scores.get("skill", 0), 1),
            "semantic": round(scores.get("semantic", 0), 1),
            "experience": round(scores.get("experience", 0), 1),
            "qualification": round(scores.get("qualification", 0), 1),
            "title": round(scores.get("title", 0), 1),
            "band": item["band"],
        })
    db.close()
    return rows

def print_table(title, rows):
    print(f"\n{title}")
    print(f"{'Rnk':<4} | {'Candidate':<24} | {'Score':<6} | {'Skill':<6} | {'Sem':<6} | {'Exp':<6} | {'Qual':<6} | {'Title':<6} | {'Band':<14}")
    print("-" * 90)
    for r in rows:
        print(f"{r['rank']:<4} | {r['name']:<24} | {r['final_score']:>5.1f}% | {r['skill']:>5.1f}% | {r['semantic']:>5.1f}% | {r['experience']:>5.1f}% | {r['qualification']:>5.1f}% | {r['title']:>5.1f}% | {r['band']:<14}")

if __name__ == "__main__":
    client = TestClient(app)

    print("Running Way A (run_matching.py in-memory)...")
    rows_a = run_way_a()

    print("Running Way B (POST /api/demo/seed first run)...")
    rows_b1, run_id_1 = run_way_b(client)

    print("Running Way B (POST /api/demo/seed second run for determinism)...")
    rows_b2, run_id_2 = run_way_b(client)

    print("Running Way C (manual upload via API + POST /api/match/run)...")
    rows_c = run_way_c(client)

    print_table("WAY (A): backend/scripts/run_matching.py", rows_a)
    print_table("WAY (B): POST /api/demo/seed (Live API)", rows_b1)
    print_table("WAY (C): Manual API Upload & POST /api/match/run", rows_c)

    # Compare B1 vs B2 (Determinism)
    diff_b1_b2 = []
    for r1, r2 in zip(rows_b1, rows_b2):
        if r1["final_score"] != r2["final_score"] or r1["name"] != r2["name"]:
            diff_b1_b2.append((r1["name"], r1["final_score"], r2["final_score"]))

    print("\n--- DETERMINISM CHECK (Way B run 1 vs run 2) ---")
    if not diff_b1_b2:
        print("✓ PERFECT DETERMINISM: Run 1 and Run 2 produced 100% identical scores to 1 decimal place across all 12 candidates!")
    else:
        print(f"✗ Determinism differences found: {diff_b1_b2}")

    # Compare A vs B
    diff_a_b = []
    for ra, rb in zip(rows_a, rows_b1):
        if abs(ra["final_score"] - rb["final_score"]) > 0.05 or ra["name"] != rb["name"]:
            diff_a_b.append((ra["name"], rb["name"], ra["final_score"], rb["final_score"]))

    print("\n--- DIFF CHECK: Way A vs Way B ---")
    if not diff_a_b:
        print("✓ PERFECT MATCH: Way A and Way B produce identical ranks and scores!")
    else:
        print("Differences found between Way A and Way B:")
        for d in diff_a_b:
            print("  ", d)

    # Compare B vs C
    diff_b_c = []
    for rb, rc in zip(rows_b1, rows_c):
        if abs(rb["final_score"] - rc["final_score"]) > 0.05 or rb["name"] != rc["name"]:
            diff_b_c.append((rb["name"], rc["name"], rb["final_score"], rc["final_score"]))

    print("\n--- DIFF CHECK: Way B vs Way C ---")
    if not diff_b_c:
        print("✓ PERFECT MATCH: Way B and Way C produce identical ranks and scores!")
    else:
        print("Differences found between Way B and Way C:")
        for d in diff_b_c:
            print("  ", d)
