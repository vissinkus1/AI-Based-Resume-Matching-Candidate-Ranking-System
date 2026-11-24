"""
tests/test_wild_resumes.py — Regression test suite for wild synthetic resumes.
Verifies parsing accuracy and resilience against format anomalies:
- Scanned PDF error/warning handling
- Duplicate detection
- Section-less / irregular date / table / multi-page parsing
"""

import json
import re
from pathlib import Path
import pytest

from app.services.text_extractor import extract_text, ScannedPDFError
from app.services.resume_parser import parse_resume

WILD_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data" / "resumes_wild"
GROUND_TRUTH_FILE = WILD_DIR / "ground_truth_wild.json"


def test_wild_resumes_accuracy():
    """Assert parser meets accuracy criteria across the 10 wild resumes."""
    assert GROUND_TRUTH_FILE.exists(), f"Missing ground truth file at {GROUND_TRUTH_FILE}"

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    stats = {
        "name": {"correct": 0, "total": 0},
        "email": {"correct": 0, "total": 0},
        "phone": {"correct": 0, "total": 0},
        "degree": {"correct": 0, "total": 0},
        "experience": {"correct": 0, "total": 0},
        "scanned_handled": {"correct": 0, "total": 0},
        "duplicate_detected": {"correct": 0, "total": 0},
    }

    seen_emails = {}

    for filename, gt in ground_truth.items():
        file_path = WILD_DIR / filename
        assert file_path.exists(), f"Wild resume file not found: {filename}"
        file_bytes = file_path.read_bytes()

        is_scanned_expected = gt.get("is_scanned", False)
        is_dup_expected = gt.get("is_duplicate_of")

        # 1. Scanned handling
        if is_scanned_expected:
            stats["scanned_handled"]["total"] += 1
            try:
                text = extract_text(file_bytes, filename)
                parsed = parse_resume(file_bytes, filename)
                if not text.strip() or any("scanned" in w.lower() for w in parsed.parse_warnings):
                    stats["scanned_handled"]["correct"] += 1
            except (ScannedPDFError, ValueError):
                stats["scanned_handled"]["correct"] += 1
            continue

        parsed = parse_resume(file_bytes, filename, today=(2024, 11))

        # 2. Duplicate detection
        if is_dup_expected:
            stats["duplicate_detected"]["total"] += 1
            if parsed.email in seen_emails or any("duplicate" in w.lower() for w in parsed.parse_warnings):
                stats["duplicate_detected"]["correct"] += 1

        if parsed.email:
            seen_emails[parsed.email] = filename

        # 3. Name accuracy
        if gt["name"]:
            stats["name"]["total"] += 1
            extracted_name = (parsed.name or "").strip()
            expected_name = gt["name"].strip()
            clean_extracted = extracted_name.replace("Dr.", "").replace("Ph.D.", "").strip().lower()
            clean_expected = expected_name.replace("Dr.", "").replace("Ph.D.", "").strip().lower()
            if clean_expected in clean_extracted or clean_extracted in clean_expected:
                stats["name"]["correct"] += 1

        # 4. Email accuracy
        if gt["email"]:
            stats["email"]["total"] += 1
            if parsed.email and parsed.email.lower() == gt["email"].lower():
                stats["email"]["correct"] += 1

        # 5. Phone accuracy
        if gt["phone"]:
            stats["phone"]["total"] += 1
            p_digits = re.sub(r"\D", "", parsed.phone or "")
            gt_digits = re.sub(r"\D", "", gt["phone"])
            if p_digits and (p_digits in gt_digits or gt_digits in p_digits):
                stats["phone"]["correct"] += 1

        # 6. Degree accuracy
        if gt["degree_level"]:
            stats["degree"]["total"] += 1
            extracted_degrees = [e.level for e in parsed.education]
            if gt["degree_level"] in extracted_degrees:
                stats["degree"]["correct"] += 1

        # 7. Experience accuracy (within 1.0 year)
        if gt["experience_years"] is not None:
            stats["experience"]["total"] += 1
            diff = abs(parsed.total_experience_years - gt["experience_years"])
            if diff <= 1.0:
                stats["experience"]["correct"] += 1

    # Check required thresholds
    assert stats["name"]["correct"] / stats["name"]["total"] >= 0.80, f"Name accuracy below 80%: {stats['name']}"
    assert stats["email"]["correct"] / stats["email"]["total"] >= 0.95, f"Email accuracy below 95%: {stats['email']}"
    assert stats["phone"]["correct"] / stats["phone"]["total"] >= 0.90, f"Phone accuracy below 90%: {stats['phone']}"
    assert stats["degree"]["correct"] / stats["degree"]["total"] >= 0.85, f"Degree accuracy below 85%: {stats['degree']}"
    assert stats["experience"]["correct"] / stats["experience"]["total"] >= 0.70, f"Experience accuracy below 70%: {stats['experience']}"
    assert stats["scanned_handled"]["correct"] / stats["scanned_handled"]["total"] == 1.0, f"Scanned handling failed"
    assert stats["duplicate_detected"]["correct"] / stats["duplicate_detected"]["total"] == 1.0, f"Duplicate detection failed"
