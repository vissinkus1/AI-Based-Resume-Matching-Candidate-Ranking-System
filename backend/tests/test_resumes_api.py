"""
tests/test_resumes_api.py — Integration tests for Resumes & Candidates API endpoints.

Covers:
  - POST /api/resumes/upload with valid PDF/DOCX
  - POST /api/resumes/upload batch isolation (one invalid file does not fail batch)
  - POST /api/resumes/upload file limits (unsupported format, oversize)
  - GET /api/resumes (list candidates with summary fields)
  - GET /api/resumes/{id} (full parsed candidate details & 404 handling)
  - DELETE /api/resumes/{id} (single candidate deletion & 404 handling)
  - DELETE /api/resumes (clear all candidates)
"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)
client = TestClient(app)

SAMPLE_RESUMES_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data" / "resumes"


class TestResumesAPI:
    """Test suite for /api/resumes router."""

    def setup_method(self):
        """Clean database before each test."""
        client.delete("/api/resumes")

    def test_upload_single_valid_resume_pdf(self):
        """Upload a valid PDF resume and verify parsed candidate response."""
        pdf_path = SAMPLE_RESUMES_DIR / "candidate_01_aravind_sharma_java.pdf"
        if not pdf_path.exists():
            pytest.skip(f"Sample file {pdf_path} not found")

        with open(pdf_path, "rb") as f:
            files = [("files", ("candidate_01_aravind_sharma_java.pdf", f.read(), "application/pdf"))]
            response = client.post("/api/resumes/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 1
        assert data["successful"] == 1
        assert data["failed"] == 0
        assert data["results"][0]["status"] == "parsed"
        assert "aravind" in (data["results"][0]["name"] or "").lower()
        candidate_id = data["results"][0]["candidate_id"]
        assert candidate_id is not None

        # Verify candidate exists via GET /api/resumes/{id}
        get_res = client.get(f"/api/resumes/{candidate_id}")
        assert get_res.status_code == 200
        cand_data = get_res.json()
        assert cand_data["id"] == candidate_id
        assert cand_data["parsed"]["total_experience_years"] >= 5.0
        assert len(cand_data["parsed"]["skills"]) >= 5

    def test_upload_single_valid_resume_docx(self):
        """Upload a valid DOCX resume."""
        docx_path = SAMPLE_RESUMES_DIR / "candidate_02_priya_patel_react.docx"
        if not docx_path.exists():
            pytest.skip(f"Sample file {docx_path} not found")

        with open(docx_path, "rb") as f:
            files = [("files", ("candidate_02_priya_patel_react.docx", f.read(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document"))]
            response = client.post("/api/resumes/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["successful"] == 1
        assert data["results"][0]["status"] == "parsed"

    def test_batch_upload_with_isolated_failure(self):
        """One invalid file (.exe) must not abort the valid files in the batch."""
        pdf_path = SAMPLE_RESUMES_DIR / "candidate_05_deepak_nair_fresher.pdf"
        if not pdf_path.exists():
            pytest.skip(f"Sample file {pdf_path} not found")

        with open(pdf_path, "rb") as f:
            valid_bytes = f.read()

        files = [
            ("files", ("candidate_05_deepak_nair_fresher.pdf", valid_bytes, "application/pdf")),
            ("files", ("malicious_payload.exe", b"binarycontent", "application/octet-stream")),
        ]
        response = client.post("/api/resumes/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["total_files"] == 2
        assert data["successful"] == 1
        assert data["failed"] == 1

        res_map = {r["filename"]: r for r in data["results"]}
        assert res_map["candidate_05_deepak_nair_fresher.pdf"]["status"] == "parsed"
        assert res_map["malicious_payload.exe"]["status"] == "failed"
        assert "Unsupported file type" in res_map["malicious_payload.exe"]["error"]

    def test_upload_oversized_file_rejected(self):
        """Files exceeding 5 MB should fail with size limit error."""
        oversized_bytes = b"0" * (5 * 1024 * 1024 + 1024)  # 5 MB + 1 KB
        files = [("files", ("huge_resume.pdf", oversized_bytes, "application/pdf"))]
        response = client.post("/api/resumes/upload", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["failed"] == 1
        assert "exceeds maximum size" in data["results"][0]["error"]

    def test_list_candidates_summary(self):
        """GET /api/resumes returns candidates with top skills and warning counts."""
        pdf_path = SAMPLE_RESUMES_DIR / "candidate_01_aravind_sharma_java.pdf"
        if not pdf_path.exists():
            pytest.skip(f"Sample file {pdf_path} not found")

        with open(pdf_path, "rb") as f:
            client.post("/api/resumes/upload", files=[("files", ("cand1.pdf", f.read(), "application/pdf"))])

        res = client.get("/api/resumes")
        assert res.status_code == 200
        items = res.json()
        assert len(items) == 1
        item = items[0]
        assert "id" in item
        assert "name" in item
        assert "email" in item
        assert "total_experience_years" in item
        assert "top_skills" in item
        assert isinstance(item["top_skills"], list)

    def test_get_candidate_by_id_not_found(self):
        """GET /api/resumes/99999 returns 404."""
        response = client.get("/api/resumes/99999")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_candidate_by_id(self):
        """DELETE /api/resumes/{id} deletes the candidate record."""
        pdf_path = SAMPLE_RESUMES_DIR / "candidate_01_aravind_sharma_java.pdf"
        if not pdf_path.exists():
            pytest.skip(f"Sample file {pdf_path} not found")

        with open(pdf_path, "rb") as f:
            upload_res = client.post(
                "/api/resumes/upload",
                files=[("files", ("cand1.pdf", f.read(), "application/pdf"))],
            )
        cand_id = upload_res.json()["results"][0]["candidate_id"]

        del_res = client.delete(f"/api/resumes/{cand_id}")
        assert del_res.status_code == 200
        assert del_res.json()["id"] == cand_id

        # Verify candidate is gone
        get_res = client.get(f"/api/resumes/{cand_id}")
        assert get_res.status_code == 404

    def test_delete_candidate_not_found(self):
        """DELETE /api/resumes/99999 returns 404."""
        del_res = client.delete("/api/resumes/99999")
        assert del_res.status_code == 404

    def test_clear_all_candidates(self):
        """DELETE /api/resumes empties the candidates database."""
        pdf_path = SAMPLE_RESUMES_DIR / "candidate_01_aravind_sharma_java.pdf"
        if not pdf_path.exists():
            pytest.skip(f"Sample file {pdf_path} not found")

        with open(pdf_path, "rb") as f:
            client.post("/api/resumes/upload", files=[("files", ("cand1.pdf", f.read(), "application/pdf"))])

        assert len(client.get("/api/resumes").json()) == 1

        clear_res = client.delete("/api/resumes")
        assert clear_res.status_code == 200
        assert clear_res.json()["deleted_count"] >= 1

        assert len(client.get("/api/resumes").json()) == 0
