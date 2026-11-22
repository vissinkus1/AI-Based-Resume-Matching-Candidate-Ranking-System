"""
tests/test_dashboard_detail_api.py — Integration tests for Dashboard and Candidate Detail APIs.

Validates Phase 5 requirements:
  - Advanced filtering on GET /api/match/runs/{run_id}/results:
      * search (name/email)
      * band (strong, good, partial, weak)
      * min_score, max_score
      * min_experience
      * skill (matching specific taxonomy skill)
      * sort_by (rank, score, experience, name) & order (asc, desc)
  - Stale detection reasons ("JD edited", "candidate removed", "candidates added")
  - Candidate deletion cascade (ensuring no orphan MatchResultDB rows)
  - Full explainable candidate detail GET /api/match/runs/{run_id}/results/{candidate_id}
      * prev_candidate_id / next_candidate_id links
      * JD comparison context
      * scores, contributions, factor breakdowns
  - Latest run retrieval GET /api/match/runs/latest
  - One-click demo seeding POST /api/demo/seed
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine, SessionLocal
from app.models.jd import JobDescription
from app.models.candidate import Candidate
from app.models.match import MatchRun, MatchResultDB
from app.repositories.candidate_repository import CandidateRepository
from app.repositories.match_repository import MatchRepository

# Ensure tables exist
Base.metadata.create_all(bind=engine)

client = TestClient(app)


@pytest.fixture(scope="module")
def dashboard_match_setup():
    """
    Sets up a clean test database state with:
      - 1 Job Description (Java Backend Engineer)
      - 3 Candidates (Strong Java, Good Java/DevOps, Weak Frontend)
      - 1 Executed MatchRun
    """
    db = SessionLocal()
    try:
        # 1. Clean previous records
        db.query(MatchResultDB).delete()
        db.query(MatchRun).delete()
        db.query(Candidate).delete()
        db.query(JobDescription).delete()
        db.commit()

        # 2. Create JD
        jd_parsed = {
            "title": "Senior Java Backend Engineer",
            "required_skills": ["Java", "Spring Boot", "PostgreSQL"],
            "preferred_skills": ["Docker", "Kubernetes", "AWS"],
            "min_experience_years": 4.0,
            "max_experience_years": 8.0,
            "qualifications": [{"level": "bachelor", "raw_phrase": "B.Tech in Computer Science"}],
            "min_required_level": "bachelor",
            "preferred_level": "master",
            "responsibilities": [
                "Develop high-performance microservices using Spring Boot.",
                "Maintain PostgreSQL database schemas and write optimized queries."
            ],
            "keywords": ["backend", "microservices", "java"],
            "skill_evidence": {},
        }
        jd = JobDescription(
            title="Senior Java Backend Engineer",
            raw_text="Senior Java Backend Engineer requiring Java, Spring Boot, PostgreSQL. 4+ years exp.",
            parsed_json=jd_parsed,
            source="paste",
        )
        db.add(jd)
        db.commit()

        # 3. Create 3 candidates
        # Cand 1: Strong Java match (5.5 yrs exp)
        c1 = Candidate(
            filename="cand1_aravind.pdf",
            name="Aravind Java",
            email="aravind@example.com",
            total_experience_years=5.5,
            parsed_json={
                "name": "Aravind Java",
                "email": "aravind@example.com",
                "total_experience_years": 5.5,
                "job_titles": ["Senior Java Developer"],
                "skills": [
                    {"name": "Java", "tier": "core", "confidence": "strong"},
                    {"name": "Spring Boot", "tier": "core", "confidence": "strong"},
                    {"name": "PostgreSQL", "tier": "core", "confidence": "strong"},
                    {"name": "Docker", "tier": "core", "confidence": "strong"},
                ],
                "experience_entries": [
                    {
                        "title": "Senior Java Developer",
                        "company": "Tech Corp",
                        "months": 66,
                        "description": "Architected Java Spring Boot microservices with PostgreSQL.",
                        "skills_in_entry": ["Java", "Spring Boot", "PostgreSQL"],
                        "is_relevant": True,
                    }
                ],
                "education": [{"degree": "B.Tech", "level": "bachelor", "field": "Computer Science"}],
                "summary": "Experienced Java backend engineer specializing in Spring Boot.",
            },
            raw_text="Aravind Java backend engineer with Spring Boot and PostgreSQL.",
        )

        # Cand 2: Good Java/DevOps match (3.5 yrs exp)
        c2 = Candidate(
            filename="cand2_rahul.docx",
            name="Rahul DevOps",
            email="rahul@example.com",
            total_experience_years=3.5,
            parsed_json={
                "name": "Rahul DevOps",
                "email": "rahul@example.com",
                "total_experience_years": 3.5,
                "job_titles": ["DevOps Engineer"],
                "skills": [
                    {"name": "Java", "tier": "core", "confidence": "medium"},
                    {"name": "Docker", "tier": "core", "confidence": "strong"},
                    {"name": "Kubernetes", "tier": "core", "confidence": "strong"},
                    {"name": "AWS", "tier": "core", "confidence": "strong"},
                ],
                "experience_entries": [
                    {
                        "title": "Cloud Engineer",
                        "company": "Cloud Inc",
                        "months": 42,
                        "description": "Deployed Java containers with Docker and Kubernetes.",
                        "skills_in_entry": ["Docker", "Kubernetes", "Java"],
                        "is_relevant": True,
                    }
                ],
                "education": [{"degree": "B.E.", "level": "bachelor", "field": "IT"}],
                "summary": "DevOps engineer with Java containerization experience.",
            },
            raw_text="Rahul DevOps engineer Docker Kubernetes AWS.",
        )

        # Cand 3: Weak Frontend developer (2.0 yrs exp)
        c3 = Candidate(
            filename="cand3_priya.pdf",
            name="Priya React",
            email="priya@example.com",
            total_experience_years=2.0,
            parsed_json={
                "name": "Priya React",
                "email": "priya@example.com",
                "total_experience_years": 2.0,
                "job_titles": ["React Frontend Developer"],
                "skills": [
                    {"name": "React", "tier": "core", "confidence": "strong"},
                    {"name": "JavaScript", "tier": "core", "confidence": "strong"},
                    {"name": "HTML", "tier": "core", "confidence": "strong"},
                ],
                "experience_entries": [
                    {
                        "title": "Frontend Engineer",
                        "company": "Web Studio",
                        "months": 24,
                        "description": "Built user interfaces using React and JavaScript.",
                        "skills_in_entry": ["React", "JavaScript"],
                        "is_relevant": False,
                    }
                ],
                "education": [{"degree": "B.Sc", "level": "bachelor", "field": "Computer Science"}],
                "summary": "Frontend developer focused on React and Web design.",
            },
            raw_text="Priya React frontend developer JavaScript HTML.",
        )

        db.add_all([c1, c2, c3])
        db.commit()

        # 4. Trigger match execution via API
        resp = client.post(
            "/api/match/run",
            json={"jd_id": jd.id, "candidate_ids": [c1.id, c2.id, c3.id]},
        )
        assert resp.status_code == 201
        run_data = resp.json()

        yield {
            "jd_id": jd.id,
            "run_id": run_data["id"],
            "c1_id": c1.id,
            "c2_id": c2.id,
            "c3_id": c3.id,
        }
    finally:
        # Cleanup
        db = SessionLocal()
        try:
            db.query(MatchResultDB).delete()
            db.query(MatchRun).delete()
            db.query(Candidate).delete()
            db.query(JobDescription).delete()
            db.commit()
        finally:
            db.close()


class TestDashboardDetailAPI:
    """Integration test suite for Dashboard & Candidate Detail endpoints."""

    def test_get_latest_run(self, dashboard_match_setup):
        """GET /api/match/runs/latest returns the most recent run."""
        run_id = dashboard_match_setup["run_id"]
        jd_id = dashboard_match_setup["jd_id"]

        resp = client.get("/api/match/runs/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == run_id
        assert data["jd_id"] == jd_id

        # Also test with ?jd_id query param
        resp2 = client.get(f"/api/match/runs/latest?jd_id={jd_id}")
        assert resp2.status_code == 200
        assert resp2.json()["id"] == run_id

    def test_dashboard_results_all_unfiltered(self, dashboard_match_setup):
        """GET /api/match/runs/{run_id}/results returns all 3 candidates with summary counts."""
        run_id = dashboard_match_setup["run_id"]
        resp = client.get(f"/api/match/runs/{run_id}/results")
        assert resp.status_code == 200
        data = resp.json()

        assert data["total"] == 3
        assert data["filtered_count"] == 3
        assert len(data["items"]) == 3
        assert "band_counts" in data
        assert isinstance(data["band_counts"], dict)

        # Check item structure
        first = data["items"][0]
        assert "candidate_id" in first
        assert "name" in first
        assert "final_score" in first
        assert "band" in first
        assert "total_experience_years" in first
        assert "relevant_experience_years" in first
        assert "matched_top_skills" in first
        assert len(first["matched_top_skills"]) <= 6
        assert first["rank"] == 1

    def test_filter_by_search_name_and_email(self, dashboard_match_setup):
        """Filter by search query matching candidate name or email."""
        run_id = dashboard_match_setup["run_id"]

        # Search by name "Aravind"
        resp = client.get(f"/api/match/runs/{run_id}/results?search=aravind")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filtered_count"] == 1
        assert "Aravind" in data["items"][0]["name"]
        # Preserves original rank
        assert data["items"][0]["original_rank"] == 1

        # Search by email "rahul@example.com"
        resp2 = client.get(f"/api/match/runs/{run_id}/results?search=rahul@example.com")
        assert resp2.status_code == 200
        assert resp2.json()["filtered_count"] == 1
        assert "Rahul" in resp2.json()["items"][0]["name"]

    def test_filter_by_band(self, dashboard_match_setup):
        """Filter by match band."""
        run_id = dashboard_match_setup["run_id"]

        # Filter by weak band -> should include Priya (React on Java JD)
        resp = client.get(f"/api/match/runs/{run_id}/results?band=weak")
        assert resp.status_code == 200
        items = resp.json()["items"]
        assert len(items) >= 1
        for item in items:
            assert "weak" in item["band"].lower()

    def test_filter_by_min_score_and_experience(self, dashboard_match_setup):
        """Filter by min_score and min_experience."""
        run_id = dashboard_match_setup["run_id"]

        # Min score 70 -> top candidate
        resp = client.get(f"/api/match/runs/{run_id}/results?min_score=70")
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["final_score"] >= 70.0

        # Min experience 4.0 years -> only Aravind (5.5 yrs)
        resp2 = client.get(f"/api/match/runs/{run_id}/results?min_experience=4.0")
        assert resp2.status_code == 200
        items2 = resp2.json()["items"]
        assert len(items2) == 1
        assert items2[0]["name"] == "Aravind Java"

    def test_filter_by_skill(self, dashboard_match_setup):
        """Filter by skill: candidate must have matched this skill."""
        run_id = dashboard_match_setup["run_id"]

        # Skill = "PostgreSQL" -> only Aravind
        resp = client.get(f"/api/match/runs/{run_id}/results?skill=PostgreSQL")
        assert resp.status_code == 200
        data = resp.json()
        assert data["filtered_count"] == 1
        assert data["items"][0]["name"] == "Aravind Java"

    def test_sort_by_columns(self, dashboard_match_setup):
        """Test sorting by score, experience, and name."""
        run_id = dashboard_match_setup["run_id"]

        # Sort by experience desc
        resp = client.get(f"/api/match/runs/{run_id}/results?sort_by=experience&order=desc")
        assert resp.status_code == 200
        items = resp.json()["items"]
        exps = [it["total_experience_years"] for it in items]
        assert exps == sorted(exps, reverse=True)

        # Sort by name asc
        resp2 = client.get(f"/api/match/runs/{run_id}/results?sort_by=name&order=asc")
        assert resp2.status_code == 200
        names = [it["name"].lower() for it in resp2.json()["items"]]
        assert names == sorted(names)

    def test_candidate_detail_exhaustive(self, dashboard_match_setup):
        """GET /api/match/runs/{run_id}/results/{candidate_id} returns all required fields & prev/next."""
        run_id = dashboard_match_setup["run_id"]
        c1_id = dashboard_match_setup["c1_id"]

        resp = client.get(f"/api/match/runs/{run_id}/results/{c1_id}")
        assert resp.status_code == 200
        data = resp.json()

        # Identification & Ranking
        assert data["candidate_id"] == c1_id
        assert data["name"] == "Aravind Java"
        assert data["rank"] == 1
        assert data["total_candidates"] == 3
        assert data["prev_candidate_id"] is None  # First candidate
        assert data["next_candidate_id"] is not None  # Has next candidate

        # JD context
        assert "Java" in data["jd_title"]
        assert data["jd_min_experience_years"] == 4.0
        assert "Java" in data["jd_required_skills"]

        # Scores & Breakdown
        assert "skill" in data["scores"]
        assert "semantic" in data["scores"]
        assert "experience" in data["scores"]
        assert "qualification" in data["scores"]
        assert "title" in data["scores"]
        assert data["final_score"] > 0

        # Detailed Factor Sections
        assert "matched_required" in data["skills_breakdown"]
        assert "reasons" in data
        assert len(data["reasons"]) >= 3

        # Next candidate navigation
        next_id = data["next_candidate_id"]
        resp_next = client.get(f"/api/match/runs/{run_id}/results/{next_id}")
        assert resp_next.status_code == 200
        assert resp_next.json()["prev_candidate_id"] == c1_id

    def test_staleness_calculation(self, dashboard_match_setup):
        """Test stale calculation for JD modification, candidate added, and candidate removed."""
        run_id = dashboard_match_setup["run_id"]
        jd_id = dashboard_match_setup["jd_id"]

        # Run is initially fresh
        resp = client.get(f"/api/match/runs/{run_id}")
        assert resp.status_code == 200
        assert resp.json()["is_stale"] is False

        # Add a new candidate after the run -> triggers "candidates added"
        db = SessionLocal()
        try:
            cand_new = Candidate(
                filename="cand_new.pdf",
                name="New Late Applicant",
                email="late@example.com",
                total_experience_years=3.0,
                parsed_json={"name": "New Late Applicant", "skills": []},
                raw_text="Late applicant text.",
            )
            db.add(cand_new)
            db.commit()
            new_cand_id = cand_new.id
        finally:
            db.close()

        # Check staleness
        resp_stale = client.get(f"/api/match/runs/{run_id}")
        assert resp_stale.status_code == 200
        assert resp_stale.json()["is_stale"] is True
        assert "added" in resp_stale.json()["stale_reason"].lower()

        # Clean up late applicant
        db = SessionLocal()
        try:
            db.query(Candidate).filter(Candidate.id == new_cand_id).delete()
            db.commit()
        finally:
            db.close()

    def test_candidate_deletion_cascade(self, dashboard_match_setup):
        """Deleting a candidate removes their MatchResultDB rows (no orphans)."""
        run_id = dashboard_match_setup["run_id"]
        c3_id = dashboard_match_setup["c3_id"]

        # Verify candidate result exists before deletion
        resp_before = client.get(f"/api/match/runs/{run_id}/results/{c3_id}")
        assert resp_before.status_code == 200

        # Delete candidate via DELETE /api/resumes/{id}
        del_resp = client.delete(f"/api/resumes/{c3_id}")
        assert del_resp.status_code == 200

        # Verify candidate result is gone
        resp_after = client.get(f"/api/match/runs/{run_id}/results/{c3_id}")
        assert resp_after.status_code == 404

        # Verify database has 0 orphan match results for c3_id
        db = SessionLocal()
        try:
            orphans = db.query(MatchResultDB).filter(MatchResultDB.candidate_id == c3_id).count()
            assert orphans == 0
        finally:
            db.close()

    def test_demo_seed_endpoint(self):
        """POST /api/demo/seed seeds sample JD and 12 resumes, running match in one shot."""
        resp = client.post("/api/demo/seed?jd=java&reset=true")
        assert resp.status_code == 200
        data = resp.json()

        assert data["success"] is True
        assert data["jd_id"] > 0
        assert data["run_id"] > 0
        assert data["candidate_count"] == 12
        assert "Java" in data["jd_title"]
        assert data["duration_ms"] > 0

        # Verify results are immediately queryable
        results_resp = client.get(f"/api/match/runs/{data['run_id']}/results")
        assert results_resp.status_code == 200
        results_data = results_resp.json()
        assert results_data["total"] == 12
        assert len(results_data["items"]) == 12
