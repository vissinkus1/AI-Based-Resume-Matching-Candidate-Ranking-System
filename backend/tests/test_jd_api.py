"""
tests/test_jd_api.py — Integration tests for Job Description API endpoints.

Covers:
  - POST /api/jd/parse with text
  - POST /api/jd/parse with file upload (txt, docx, pdf)
  - GET /api/jd/{id}
  - GET /api/jd (listing)
  - PUT /api/jd/{id} (updating skills/experience)
  - DELETE /api/jd/{id}
  - Error responses (empty input, unsupported file, non-existent ID)
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine

# Ensure tables exist for tests
Base.metadata.create_all(bind=engine)

client = TestClient(app)

SAMPLE_JDS_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data" / "jds"


class TestJDAPI:
    """Test suite for /api/jd router."""

    def test_parse_jd_text_success(self):
        """POST /api/jd/parse with raw text."""
        jd_text = """
Software Engineer

Requirements:
- 3+ years experience with Python and FastAPI
- Familiarity with PostgreSQL

Nice to Have:
- Docker and Kubernetes experience

Responsibilities:
- Build reliable microservices
- Write unit tests
"""
        response = client.post(
            "/api/jd/parse",
            data={"text": jd_text},
        )
        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert data["id"] > 0
        assert "parsed" in data
        assert "Python" in data["parsed"]["required_skills"]
        assert "FastAPI" in data["parsed"]["required_skills"]
        assert "Docker" in data["parsed"]["preferred_skills"]

    def test_parse_jd_file_txt(self):
        """POST /api/jd/parse with .txt upload."""
        txt_path = SAMPLE_JDS_DIR / "java_backend_jd.txt"
        with open(txt_path, "rb") as f:
            response = client.post(
                "/api/jd/parse",
                files={"file": ("java_backend_jd.txt", f, "text/plain")},
            )
        assert response.status_code == 201
        data = response.json()
        assert "Java" in data["parsed"]["required_skills"]
        assert data["parsed"]["min_experience_years"] == 5.0

    def test_parse_jd_file_docx(self):
        """POST /api/jd/parse with .docx upload."""
        docx_path = SAMPLE_JDS_DIR / "react_frontend_jd.docx"
        with open(docx_path, "rb") as f:
            response = client.post(
                "/api/jd/parse",
                files={"file": ("react_frontend_jd.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            )
        assert response.status_code == 201
        data = response.json()
        assert "React" in data["parsed"]["required_skills"]

    def test_parse_jd_file_pdf(self):
        """POST /api/jd/parse with .pdf upload."""
        pdf_path = SAMPLE_JDS_DIR / "aiml_engineer_jd.pdf"
        with open(pdf_path, "rb") as f:
            response = client.post(
                "/api/jd/parse",
                files={"file": ("aiml_engineer_jd.pdf", f, "application/pdf")},
            )
        assert response.status_code == 201
        data = response.json()
        assert "Python" in data["parsed"]["required_skills"]

    def test_parse_jd_no_input(self):
        """POST /api/jd/parse with neither text nor file should return 400."""
        response = client.post("/api/jd/parse", data={})
        assert response.status_code == 400

    def test_parse_jd_short_text(self):
        """POST /api/jd/parse with too short text should return 400."""
        response = client.post("/api/jd/parse", data={"text": "hi"})
        assert response.status_code == 400

    def test_parse_jd_unsupported_file(self):
        """POST /api/jd/parse with unsupported extension should return 400."""
        response = client.post(
            "/api/jd/parse",
            files={"file": ("data.csv", b"col1,col2\nval1,val2", "text/csv")},
        )
        assert response.status_code == 400

    def test_get_jd_by_id(self):
        """GET /api/jd/{id} returns the full JD record."""
        # Create one first
        create_res = client.post(
            "/api/jd/parse",
            data={"text": "Backend Engineer\n\nRequirements:\n- Python 3+ years"},
        )
        jd_id = create_res.json()["id"]

        get_res = client.get(f"/api/jd/{jd_id}")
        assert get_res.status_code == 200
        data = get_res.json()
        assert data["id"] == jd_id
        assert "parsed" in data
        assert "raw_text" in data

    def test_get_jd_not_found(self):
        """GET /api/jd/999999 should return 404."""
        response = client.get("/api/jd/999999")
        assert response.status_code == 404

    def test_list_jds(self):
        """GET /api/jd returns list of JDs."""
        response = client.get("/api/jd")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_update_jd(self):
        """PUT /api/jd/{id} updates parsed skills/experience."""
        create_res = client.post(
            "/api/jd/parse",
            data={"text": "DevOps Engineer\n\nRequirements:\n- Linux\n- AWS"},
        )
        jd_id = create_res.json()["id"]

        update_payload = {
            "required_skills": ["Linux", "AWS", "Terraform"],
            "preferred_skills": ["Kubernetes"],
            "min_experience_years": 4.0,
        }
        put_res = client.put(f"/api/jd/{jd_id}", json=update_payload)
        assert put_res.status_code == 200
        updated = put_res.json()
        assert "Terraform" in updated["parsed"]["required_skills"]
        assert "Kubernetes" in updated["parsed"]["preferred_skills"]
        assert updated["parsed"]["min_experience_years"] == 4.0

    def test_delete_jd(self):
        """DELETE /api/jd/{id} deletes the record."""
        create_res = client.post(
            "/api/jd/parse",
            data={"text": "QA Engineer\n\nRequirements:\n- Selenium\n- pytest"},
        )
        jd_id = create_res.json()["id"]

        del_res = client.delete(f"/api/jd/{jd_id}")
        assert del_res.status_code == 200

        # Verify it's gone
        get_res = client.get(f"/api/jd/{jd_id}")
        assert get_res.status_code == 404
