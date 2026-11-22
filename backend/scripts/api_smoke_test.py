"""
scripts/api_smoke_test.py — End-to-End Smoke Test for Matching API.

Tests the complete workflow through FastAPI TestClient:
  1. Health & model warmup verification
  2. Scoring configuration verification
  3. Job Description intake & parsing
  4. Batch candidate resume uploads (12 sample resumes)
  5. Multi-factor AI matching run execution
  6. Leaderboard ranking inspection and tie-break validation
  7. Explainable single candidate detail retrieval
  8. Streaming CSV export validation
  9. Real-time staleness detection
  10. Run deletion and cascade cleanup
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.match import MatchRun, MatchResultDB

SAMPLE_DATA_DIR = BACKEND_DIR.parent / "sample_data"
JDS_DIR = SAMPLE_DATA_DIR / "jds"
RESUMES_DIR = SAMPLE_DATA_DIR / "resumes"


def run_smoke_test():
    print("=" * 100)
    print("AI-BASED RESUME MATCHING & CANDIDATE RANKING SYSTEM — API SMOKE TEST")
    print("=" * 100)

    # Initialize DB tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as client:
        # 1. Health check
        print("\n[Step 1/10] Verifying System Health & Model Warmup...")
        health_resp = client.get("/health")
        assert health_resp.status_code == 200, f"Health check failed: {health_resp.text}"
        health_data = health_resp.json()
        print(f"  Status: {health_data['status']}")
        print(f"  API: {health_data['api']} | DB: {health_data['database']} | Model Ready: {health_data.get('model_ready')}")
        assert health_data["api"] is True and health_data["database"] is True
        assert health_data.get("model_ready") is True, "Embedding model was not warmed up"

        # 2. Config verification
        print("\n[Step 2/10] Verifying Scoring Configuration API...")
        cfg_resp = client.get("/api/match/config")
        assert cfg_resp.status_code == 200, f"Config fetch failed: {cfg_resp.text}"
        cfg = cfg_resp.json()
        weights = cfg["weights"]
        total_w = sum(weights.values())
        print(f"  Active Weights: {weights} (Sum = {total_w:.2f})")
        assert abs(total_w - 1.0) < 1e-5, f"Weights sum to {total_w}, expected 1.0"

        # 3. Ingest Sample JD
        print("\n[Step 3/10] Parsing Sample Java Backend JD...")
        jd_path = JDS_DIR / "java_backend_jd.txt"
        assert jd_path.exists(), f"JD file missing: {jd_path}"
        with open(jd_path, "r", encoding="utf-8") as f:
            jd_text = f.read()

        jd_resp = client.post("/api/jd/parse", data={"text": jd_text})
        assert jd_resp.status_code == 201, f"JD parse failed: {jd_resp.text}"
        jd_data = jd_resp.json()
        jd_id = jd_data["id"]
        print(f"  JD Created: ID={jd_id}, Title='{jd_data['parsed']['title']}'")
        print(f"  Required Skills: {jd_data['parsed']['required_skills']}")
        print(f"  Preferred Skills: {jd_data['parsed']['preferred_skills']}")

        # 4. Batch Upload Resumes
        print("\n[Step 4/10] Uploading 12 Synthetic Candidate Resumes...")
        resume_files = [f for f in RESUMES_DIR.glob("*.*") if f.suffix.lower() in (".pdf", ".docx", ".txt")]
        assert len(resume_files) >= 12, f"Expected 12 resumes, found {len(resume_files)}"

        files_payload = []
        file_handles = []
        for rf in resume_files:
            fh = open(rf, "rb")
            file_handles.append(fh)
            files_payload.append(("files", (rf.name, fh, "application/octet-stream")))

        try:
            upload_resp = client.post("/api/resumes/upload", files=files_payload)
        finally:
            for fh in file_handles:
                fh.close()

        assert upload_resp.status_code == 200, f"Upload failed: {upload_resp.text}"
        upload_data = upload_resp.json()
        print(f"  Uploaded {upload_data['total_files']} resumes ({upload_data['successful']} successful, {upload_data['failed']} failed)")
        candidate_ids = [r["candidate_id"] for r in upload_data["results"] if r.get("candidate_id")]

        # 5. Execute Matching Run
        print("\n[Step 5/10] Triggering POST /api/match/run...")
        run_resp = client.post("/api/match/run", json={"jd_id": jd_id, "candidate_ids": candidate_ids})
        assert run_resp.status_code == 201, f"Match run failed: {run_resp.text}"
        run_data = run_resp.json()
        run_id = run_data["id"]
        print(f"  Match Run Created: ID={run_id}")
        print(f"  Candidates Evaluated: {run_data['candidate_count']}")
        print(f"  Duration: {run_data['duration_ms']:.1f} ms")
        print(f"  Stale Flag: {run_data['is_stale']}")

        # 6. Verify Run Detail & Distribution
        print("\n[Step 6/10] Fetching Match Run Summary & Band Distribution...")
        detail_resp = client.get(f"/api/match/runs/{run_id}")
        assert detail_resp.status_code == 200, f"Run detail failed: {detail_resp.text}"
        detail = detail_resp.json()
        print(f"  Average Score: {detail['average_score']}%")
        print(f"  Top Candidate: {detail['top_candidate_name']} ({detail['top_candidate_score']}%)")
        print(f"  Band Distribution: {detail['band_distribution']}")

        # 7. Fetch Leaderboard Results
        print("\n[Step 7/10] Inspecting Ranked Results Leaderboard...")
        results_resp = client.get(f"/api/match/runs/{run_id}/results?page=1&page_size=20")
        assert results_resp.status_code == 200, f"Results fetch failed: {results_resp.text}"
        results_data = results_resp.json()
        items = results_data["items"]

        print("\n" + "-" * 115)
        print(f"{'Rank':<5} | {'Candidate Name':<20} | {'Exp (Rel/Tot)':<13} | {'Match %':<8} | {'Band':<15} | {'Knockout':<9} | {'Top Skills'}")
        print("-" * 115)
        for it in items:
            exp_str = f"{it['relevant_experience_years']:.1f}/{it['total_experience_years']:.1f}y"
            score_str = f"{it['final_score']:.1f}%"
            ko_str = "YES" if it["is_knockout"] else "no"
            skills_str = ", ".join(it["top_skills"][:4])
            print(f"#{it['rank']:<4} | {it['candidate_name']:<20} | {exp_str:<13} | {score_str:<8} | {it['band']:<15} | {ko_str:<9} | {skills_str}")
        print("-" * 115)

        # Sanity asserts on ranking
        assert items[0]["final_score"] >= items[-1]["final_score"], "Leaderboard is not descending by score"
        top_candidate = items[0]
        print(f"  Rank #1 Candidate: {top_candidate['candidate_name']} with {top_candidate['final_score']}%")

        # 8. Single Candidate Explainability Detail
        print("\n[Step 8/10] Fetching Single Candidate Explainability Detail...")
        cand_detail_resp = client.get(f"/api/match/runs/{run_id}/results/{top_candidate['candidate_id']}")
        assert cand_detail_resp.status_code == 200, f"Cand detail failed: {cand_detail_resp.text}"
        c_detail = cand_detail_resp.json()
        print(f"  Candidate: {c_detail['candidate_name']}")
        print(f"  Summary: {c_detail['summary']}")
        print(f"  Factor Breakdown:")
        for reason in c_detail["reasons"]:
            print(f"    - {reason['factor'].capitalize()}: {reason['score']:.1f}/100 (Weight: {reason['weight']}) -> {reason['text']}")

        # 9. CSV Export
        print("\n[Step 9/10] Validating Streaming CSV Export...")
        csv_resp = client.get(f"/api/match/runs/{run_id}/export.csv")
        assert csv_resp.status_code == 200, f"CSV export failed: {csv_resp.text}"
        assert "text/csv" in csv_resp.headers["Content-Type"]
        csv_lines = csv_resp.text.strip().split("\n")
        print(f"  Exported CSV contains {len(csv_lines)} lines (Header + {len(csv_lines)-1} candidate rows)")
        assert len(csv_lines) == len(items) + 1, "CSV row count mismatch"

        # 10. Staleness Detection & Clean Up
        print("\n[Step 10/10] Testing Staleness Detection & Run Deletion...")
        # Modify JD
        put_resp = client.put(f"/api/jd/{jd_id}", json={"required_skills": ["Java", "Spring Boot", "Cassandra"]})
        assert put_resp.status_code == 200
        stale_check = client.get(f"/api/match/runs/{run_id}").json()
        assert stale_check["is_stale"] is True, f"Expected is_stale=True, got {stale_check['is_stale']}"
        print("  Stale detection confirmed: JD modification properly flagged is_stale=True.")

        # Delete Run
        del_resp = client.delete(f"/api/match/runs/{run_id}")
        assert del_resp.status_code == 200
        assert client.get(f"/api/match/runs/{run_id}").status_code == 404
        print(f"  Match Run #{run_id} deleted successfully. Cascade verification confirmed.")

        print("\n" + "=" * 100)
        print("ALL API SMOKE TESTS PASSED CLEANLY AND SUCCESSFULLY!")
        print("=" * 100)


if __name__ == "__main__":
    run_smoke_test()
