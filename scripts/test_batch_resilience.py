"""
scripts/test_batch_resilience.py — Test uploading 15 mixed files in ONE batch (Part B1).
Includes valid resumes, wild resumes, scanned PDF, and corrupted files.
Verifies that valid files succeed while invalid files return individual failure payloads without failing the batch.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

RESUMES_DIR = BACKEND_DIR.parent / "sample_data" / "resumes"
WILD_DIR = BACKEND_DIR.parent / "sample_data" / "resumes_wild"


def test_15_file_batch():
    print("=" * 90)
    print("PART B1: 15-FILE UPLOAD RESILIENCE TEST")
    print("=" * 90)

    # 1. Gather 10 valid resumes
    valid_resumes = sorted([f for f in RESUMES_DIR.glob("*.*") if f.suffix.lower() in [".pdf", ".docx"]])[:10]

    # 2. Gather 3 wild resumes
    wild_resumes = [
        WILD_DIR / "wild_01_no_headings.txt",
        WILD_DIR / "wild_02_table_skills.docx",
        WILD_DIR / "wild_04_twocolumn_sidebar.pdf",
    ]

    # 3. 1 scanned PDF
    scanned_resume = WILD_DIR / "wild_09_scanned_image.pdf"

    # 4. 1 corrupted file
    corrupt_bytes = b"PK\x03\x04CORRUPTED_ZIP_STREAM_NOT_A_VALID_DOCX_HEADER_0000000000"

    files_payload = []
    for f in valid_resumes:
        files_payload.append(("files", (f.name, f.read_bytes(), "application/octet-stream")))
    for f in wild_resumes:
        files_payload.append(("files", (f.name, f.read_bytes(), "application/octet-stream")))
    files_payload.append(("files", (scanned_resume.name, scanned_resume.read_bytes(), "application/pdf")))
    files_payload.append(("files", ("corrupted_candidate.docx", corrupt_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")))

    print(f"Total files assembled for single batch upload: {len(files_payload)}")
    assert len(files_payload) == 15, f"Expected 15 files, got {len(files_payload)}"

    # Send POST to /api/resumes/upload
    response = client.post("/api/resumes/upload", files=files_payload)

    print(f"HTTP Status Code: {response.status_code}")
    assert response.status_code == 200, f"Batch upload failed with status {response.status_code}: {response.text}"

    data = response.json()
    print(f"Batch response summary:")
    print(f"  Total files: {data['total_files']}")
    print(f"  Successful : {data['successful']}")
    print(f"  Failed     : {data['failed']}")

    print("\nDetailed per-file outcomes:")
    for item in data["results"]:
        status = item["status"]
        fname = item["filename"]
        if status == "parsed":
            print(f"  [OK]     {fname:<30} -> Candidate ID: {item.get('candidate_id')}, Name: '{item.get('name')}'")
        else:
            print(f"  [FAILED] {fname:<30} -> Error: {item.get('error')}")

    # Assertions
    assert data["total_files"] == 15
    assert data["successful"] == 13, f"Expected 13 successful, got {data['successful']}"
    assert data["failed"] == 2, f"Expected 2 failures (scanned + corrupt), got {data['failed']}"

    failed_files = [item["filename"] for item in data["results"] if item["status"] == "failed"]
    assert "wild_09_scanned_image.pdf" in failed_files
    assert "corrupted_candidate.docx" in failed_files

    print("\n" + "=" * 90)
    print("SUCCESS: 15-file upload resilience verified. Valid files parsed cleanly; errors isolated.")
    print("=" * 90)


if __name__ == "__main__":
    test_15_file_batch()
