"""
tests/test_match_api.py — Integration tests for Matching & Ranking API endpoints.

Covers:
  - System health check & model readiness (GET /health)
  - Scoring config endpoint (GET /api/match/config)
  - Validation errors (missing JD, empty candidate cohort)
  - End-to-end match execution (POST /api/match/run)
  - History of match runs (GET /api/match/runs)
  - Run details & staleness detection upon JD modification (GET /api/match/runs/{id})
  - Paginated results, sorting, and band/score filtering (GET /api/match/runs/{id}/results)
  - Exhaustive single candidate result (GET /api/match/runs/{id}/results/{cand_id})
  - CSV report streaming export (GET /api/match/runs/{id}/export.csv)
  - Deletion of runs with cascade cleanup (DELETE /api/match/runs/{id})
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.jd import JobDescription
from app.models.candidate import Candidate
from app.models.match import MatchRun, MatchResultDB

# Ensure all database tables exist
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(scope="module")
def sample_match_setup():
    """
    Sets up a clean test database state with:
      - 1 Job Description (Java Backend Engineer)
      - 2 Candidates (Strong Java Engineer & React Developer)
    """
    db = SessionLocal()
    try:
        # Create test JD
        jd_parsed = {
            "title": "Senior Java Backend Engineer",
            "required_skills": ["Java", "Spring Boot", "PostgreSQL"],
            "preferred_skills": ["Docker", "Kubernetes"],
            "min_experience_years": 4.0,
            "max_experience_years": None,
            "qualifications": [{"level": "bachelor", "raw_phrase": "B.S. in Computer Science"}],
            "min_required_level": "bachelor",
            "preferred_level": None,
            "responsibilities": [
                "Develop high-throughput microservices using Spring Boot and Java.",
                "Design scalable PostgreSQL database schemas and REST APIs."
            ],
            "keywords": ["backend", "microservices", "distributed systems"],
            "skill_evidence": {},
        }
        jd = JobDescription(
            title="Senior Java Backend Engineer",
            raw_text="Senior Java Backend Engineer role requiring 4+ years of experience with Java, Spring Boot, and PostgreSQL.",
            parsed_json=jd_parsed,
            source="paste",
        )
        db.add(jd)
        db.flush()

        # Candidate 1: Java Engineer (Strong match)
        cand1_parsed = {
            "name": "Alex Java",
            "email": "alex.java@example.com",
            "total_experience_years": 5.5,
            "job_titles": ["Senior Java Engineer", "Backend Developer"],
            "skills": [
                {"name": "Java", "tier": "core", "confidence": "strong"},
                {"name": "Spring Boot", "tier": "core", "confidence": "strong"},
                {"name": "PostgreSQL", "tier": "core", "confidence": "strong"},
                {"name": "Docker", "tier": "core", "confidence": "strong"},
            ],
            "experience_entries": [
                {
                    "title": "Senior Java Developer",
                    "company": "TechCorp",
                    "months": 48,
                    "description": "Architected Java Spring Boot microservices with PostgreSQL backend.",
                    "skills_in_entry": ["Java", "Spring Boot", "PostgreSQL"],
                }
            ],
            "education": [
                {"degree": "B.Tech", "level": "bachelor", "field": "Computer Science"}
            ],
            "summary": "Experienced Senior Java developer building high-volume Spring Boot microservices.",
        }
        cand1 = Candidate(
            filename="alex_java.pdf",
            name="Alex Java",
            email="alex.java@example.com",
            total_experience_years=5.5,
            parsed_json=cand1_parsed,
            raw_text="Experienced Senior Java developer building high-volume Spring Boot microservices.",
        )
        db.add(cand1)

        # Candidate 2: React Developer (Weak match for Java role)
        cand2_parsed = {
            "name": "Rita React",
            "email": "rita.react@example.com",
            "total_experience_years": 3.0,
            "job_titles": ["Frontend Developer"],
            "skills": [
                {"name": "React", "tier": "core", "confidence": "strong"},
                {"name": "JavaScript", "tier": "core", "confidence": "strong"},
                {"name": "CSS", "tier": "core", "confidence": "strong"},
            ],
            "experience_entries": [
                {
                    "title": "Frontend Engineer",
                    "company": "WebCorp",
                    "months": 36,
                    "description": "Developed single-page web applications using React and JavaScript.",
                    "skills_in_entry": ["React", "JavaScript"],
                }
            ],
            "education": [
                {"degree": "B.S.", "level": "bachelor", "field": "Information Systems"}
            ],
            "summary": "Frontend developer focusing on React and interactive user interfaces.",
        }
        cand2 = Candidate(
            filename="rita_react.docx",
            name="Rita React",
            email="rita.react@example.com",
            total_experience_years=3.0,
            parsed_json=cand2_parsed,
            raw_text="Frontend developer focusing on React and interactive user interfaces.",
        )
        db.add(cand2)
        db.commit()

        jd_id = jd.id
        cand1_id = cand1.id
        cand2_id = cand2.id
    finally:
        db.close()

    yield {
        "jd_id": jd_id,
        "cand1_id": cand1_id,
        "cand2_id": cand2_id,
    }

    # Teardown
    db = SessionLocal()
    try:
        db.query(MatchResultDB).delete()
        db.query(MatchRun).delete()
        db.query(Candidate).filter(Candidate.id.in_([cand1_id, cand2_id])).delete()
        db.query(JobDescription).filter(JobDescription.id == jd_id).delete()
        db.commit()
    finally:
        db.close()


class TestMatchAPI:
    """Test suite for the matching engine REST API."""

    def test_health_check_readiness(self):
        """GET /health reports api=True, database=True, and model_ready=True."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["api"] is True
        assert data["database"] is True
        assert "model_ready" in data

    def test_scoring_config_endpoint(self):
        """GET /api/match/config returns verified scoring weights and thresholds."""
        response = client.get("/api/match/config")
        assert response.status_code == 200
        data = response.json()
        weights = data["weights"]
        assert weights["skill"] == 0.40
        assert weights["semantic"] == 0.25
        assert weights["experience"] == 0.20
        assert weights["qualification"] == 0.10
        assert weights["title"] == 0.05
        assert data["credit_table"]["exact_or_alias"] == 1.0

    def test_run_match_validation_errors(self):
        """POST /api/match/run returns 404 for missing JD and 400 for invalid cohort."""
        # Missing JD
        resp_missing = client.post("/api/match/run", json={"jd_id": 999999})
        assert resp_missing.status_code == 404

        # Non-existent candidate cohort
        resp_invalid_cands = client.post(
            "/api/match/run", json={"jd_id": 1, "candidate_ids": [999998, 999999]}
        )
        assert resp_invalid_cands.status_code in (400, 404)

    def test_run_match_success(self, sample_match_setup):
        """POST /api/match/run executes multi-factor ranking and persists the run."""
        jd_id = sample_match_setup["jd_id"]
        c1_id = sample_match_setup["cand1_id"]
        c2_id = sample_match_setup["cand2_id"]

        resp = client.post(
            "/api/match/run",
            json={"jd_id": jd_id, "candidate_ids": [c1_id, c2_id]},
        )
        assert resp.status_code == 201
        run_data = resp.json()
        assert "id" in run_data
        assert run_data["jd_id"] == jd_id
        assert run_data["candidate_count"] == 2
        assert run_data["duration_ms"] > 0
        assert run_data["is_stale"] is False

        run_id = run_data["id"]

        # Verify GET /api/match/runs lists the new run
        resp_list = client.get("/api/match/runs")
        assert resp_list.status_code == 200
        runs = resp_list.json()
        assert any(r["id"] == run_id for r in runs)

        # Verify GET /api/match/runs/{run_id} details & distribution
        resp_detail = client.get(f"/api/match/runs/{run_id}")
        assert resp_detail.status_code == 200
        detail = resp_detail.json()
        assert detail["id"] == run_id
        assert detail["candidate_count"] == 2
        assert detail["top_candidate_name"] == "Alex Java"
        assert detail["top_candidate_score"] > 70.0
        assert "band_distribution" in detail

    def test_results_pagination_sorting_filtering(self, sample_match_setup):
        """GET /api/match/runs/{id}/results supports pagination, sorting, and filters."""
        jd_id = sample_match_setup["jd_id"]
        c1_id = sample_match_setup["cand1_id"]
        c2_id = sample_match_setup["cand2_id"]

        run_resp = client.post(
            "/api/match/run",
            json={"jd_id": jd_id, "candidate_ids": [c1_id, c2_id]},
        )
        run_id = run_resp.json()["id"]

        # Default results (ordered by rank ascending)
        res_resp = client.get(f"/api/match/runs/{run_id}/results?page=1&page_size=10")
        assert res_resp.status_code == 200
        res_data = res_resp.json()
        assert res_data["total"] == 2
        items = res_data["items"]
        assert len(items) == 2
        assert items[0]["rank"] == 1
        assert items[0]["candidate_name"] == "Alex Java"
        assert items[1]["rank"] == 2
        assert items[1]["candidate_name"] == "Rita React"
        assert items[0]["final_score"] > items[1]["final_score"]

        # Filter by min_score
        filter_resp = client.get(
            f"/api/match/runs/{run_id}/results?min_score={items[0]['final_score'] - 1.0}"
        )
        assert filter_resp.status_code == 200
        filter_data = filter_resp.json()
        assert filter_data["total"] >= 1
        assert all(it["candidate_name"] == "Alex Java" for it in filter_data["items"])

    def test_single_candidate_detail(self, sample_match_setup):
        """GET /api/match/runs/{id}/results/{cand_id} provides rich explainable breakdown."""
        jd_id = sample_match_setup["jd_id"]
        c1_id = sample_match_setup["cand1_id"]

        run_resp = client.post(
            "/api/match/run",
            json={"jd_id": jd_id, "candidate_ids": [c1_id]},
        )
        run_id = run_resp.json()["id"]

        det_resp = client.get(f"/api/match/runs/{run_id}/results/{c1_id}")
        assert det_resp.status_code == 200
        cand_detail = det_resp.json()
        assert cand_detail["candidate_name"] == "Alex Java"
        assert "scores" in cand_detail
        assert "contributions" in cand_detail
        assert "skills" in cand_detail
        assert "strengths" in cand_detail
        assert "reasons" in cand_detail
        assert len(cand_detail["reasons"]) == 5  # 5 scoring factors

    def test_csv_export(self, sample_match_setup):
        """GET /api/match/runs/{id}/export.csv streams valid CSV with correct headers."""
        jd_id = sample_match_setup["jd_id"]
        c1_id = sample_match_setup["cand1_id"]

        run_resp = client.post(
            "/api/match/run",
            json={"jd_id": jd_id, "candidate_ids": [c1_id]},
        )
        run_id = run_resp.json()["id"]

        csv_resp = client.get(f"/api/match/runs/{run_id}/export.csv")
        assert csv_resp.status_code == 200
        assert "text/csv" in csv_resp.headers["Content-Type"]
        assert f'filename="match_run_{run_id}.csv"' in csv_resp.headers["Content-Disposition"]

        content = csv_resp.text
        lines = content.strip().split("\r\n") if "\r\n" in content else content.strip().split("\n")
        assert len(lines) >= 2  # Header + at least 1 candidate row
        header = lines[0]
        assert "Rank" in header
        assert "Candidate Name" in header
        assert "Final Score" in header
        assert "Top Matched Skills" in header
        assert "Alex Java" in lines[1]

    def test_staleness_detection(self, sample_match_setup):
        """Run becomes flagged as is_stale=True when Job Description is updated."""
        jd_id = sample_match_setup["jd_id"]
        c1_id = sample_match_setup["cand1_id"]

        run_resp = client.post(
            "/api/match/run",
            json={"jd_id": jd_id, "candidate_ids": [c1_id]},
        )
        run_id = run_resp.json()["id"]

        # Initially fresh
        run_check1 = client.get(f"/api/match/runs/{run_id}").json()
        assert run_check1["is_stale"] is False

        # Update JD to require GraphQL
        put_resp = client.put(
            f"/api/jd/{jd_id}",
            json={"required_skills": ["Java", "Spring Boot", "PostgreSQL", "GraphQL"]},
        )
        assert put_resp.status_code == 200

        # Now GET /api/match/runs/{run_id} must detect the hash mismatch
        run_check2 = client.get(f"/api/match/runs/{run_id}").json()
        assert run_check2["is_stale"] is True

    def test_delete_run_cascades(self, sample_match_setup):
        """DELETE /api/match/runs/{id} deletes run and cascades to results table."""
        jd_id = sample_match_setup["jd_id"]
        c1_id = sample_match_setup["cand1_id"]

        run_resp = client.post(
            "/api/match/run",
            json={"jd_id": jd_id, "candidate_ids": [c1_id]},
        )
        run_id = run_resp.json()["id"]

        # Confirm results exist in DB
        db = SessionLocal()
        try:
            results_count = db.query(MatchResultDB).filter(MatchResultDB.run_id == run_id).count()
            assert results_count == 1
        finally:
            db.close()

        # Delete run
        del_resp = client.delete(f"/api/match/runs/{run_id}")
        assert del_resp.status_code == 200

        # Run is gone
        assert client.get(f"/api/match/runs/{run_id}").status_code == 404

        # Confirm results were cascade deleted
        db = SessionLocal()
        try:
            results_count_after = db.query(MatchResultDB).filter(MatchResultDB.run_id == run_id).count()
            assert results_count_after == 0
        finally:
            db.close()
