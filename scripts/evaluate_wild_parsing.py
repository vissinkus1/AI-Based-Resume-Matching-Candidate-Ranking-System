"""
scripts/evaluate_wild_parsing.py — Evaluate parser accuracy against sample_data/resumes_wild/
"""

import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.text_extractor import extract_text, ScannedPDFError
from app.services.resume_parser import parse_resume

WILD_DIR = BACKEND_DIR.parent / "sample_data" / "resumes_wild"
GROUND_TRUTH_FILE = WILD_DIR / "ground_truth_wild.json"


def evaluate():
    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    print("=" * 100)
    print("EVALUATING PARSER ACCURACY ON 10 WILD SYNTHETIC RESUMES")
    print("=" * 100)

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
        file_bytes = file_path.read_bytes()

        is_scanned_expected = gt.get("is_scanned", False)
        is_dup_expected = gt.get("is_duplicate_of")

        print(f"\n--- Testing: {filename} ---")

        # 1. Scanned handling
        if is_scanned_expected:
            stats["scanned_handled"]["total"] += 1
            try:
                text = extract_text(file_bytes, filename)
                parsed = parse_resume(file_bytes, filename)
                if not text.strip() or any("scanned" in w.lower() for w in parsed.parse_warnings):
                    print("  [Scanned PDF]: Handled cleanly with warning.")
                    stats["scanned_handled"]["correct"] += 1
                else:
                    print("  [Scanned PDF]: Warning not emitted.")
            except (ScannedPDFError, ValueError) as exc:
                print(f"  [Scanned PDF]: Raised clean error: {exc}")
                stats["scanned_handled"]["correct"] += 1
            continue

        try:
            parsed = parse_resume(file_bytes, filename, today=(2024, 11))
        except Exception as e:
            print(f"  FAILED to parse {filename}: {e}")
            continue

        # 2. Duplicate detection
        if is_dup_expected:
            stats["duplicate_detected"]["total"] += 1
            if parsed.email in seen_emails or any("duplicate" in w.lower() for w in parsed.parse_warnings):
                print(f"  [Duplicate]: Detected as duplicate of {parsed.email}")
                stats["duplicate_detected"]["correct"] += 1
            else:
                print(f"  [Duplicate]: NOT flagged.")

        if parsed.email:
            seen_emails[parsed.email] = filename

        # 3. Name accuracy
        if gt["name"]:
            stats["name"]["total"] += 1
            extracted_name = (parsed.name or "").strip()
            expected_name = gt["name"].strip()
            # Check equality or containment (accounting for Dr., Ph.D., etc.)
            clean_extracted = extracted_name.replace("Dr.", "").replace("Ph.D.", "").strip().lower()
            clean_expected = expected_name.replace("Dr.", "").replace("Ph.D.", "").strip().lower()
            if clean_expected in clean_extracted or clean_extracted in clean_expected:
                stats["name"]["correct"] += 1
                print(f"  Name: [PASS] '{extracted_name}' (expected '{expected_name}')")
            else:
                print(f"  Name: [FAIL] '{extracted_name}' != '{expected_name}'")

        # 4. Email accuracy
        if gt["email"]:
            stats["email"]["total"] += 1
            if parsed.email and parsed.email.lower() == gt["email"].lower():
                stats["email"]["correct"] += 1
                print(f"  Email: [PASS] {parsed.email}")
            else:
                print(f"  Email: [FAIL] '{parsed.email}' != '{gt['email']}'")

        # 5. Phone accuracy
        if gt["phone"]:
            stats["phone"]["total"] += 1
            # Normalize digits
            import re
            p_digits = re.sub(r"\D", "", parsed.phone or "")
            gt_digits = re.sub(r"\D", "", gt["phone"])
            if p_digits and (p_digits in gt_digits or gt_digits in p_digits):
                stats["phone"]["correct"] += 1
                print(f"  Phone: [PASS] {parsed.phone}")
            else:
                print(f"  Phone: [FAIL] '{parsed.phone}' != '{gt['phone']}'")

        # 6. Degree accuracy
        if gt["degree_level"]:
            stats["degree"]["total"] += 1
            extracted_degrees = [e.level for e in parsed.education]
            if gt["degree_level"] in extracted_degrees:
                stats["degree"]["correct"] += 1
                print(f"  Degree: [PASS] {gt['degree_level']} found in {extracted_degrees}")
            else:
                print(f"  Degree: [FAIL] {gt['degree_level']} not in {extracted_degrees}")

        # 7. Experience accuracy
        if gt["experience_years"] is not None:
            stats["experience"]["total"] += 1
            diff = abs(parsed.total_experience_years - gt["experience_years"])
            if diff <= 1.2:
                stats["experience"]["correct"] += 1
                print(f"  Experience: [PASS] {parsed.total_experience_years:.1f}y (gt: {gt['experience_years']}y, diff: {diff:.1f}y)")
            else:
                print(f"  Experience: [FAIL] {parsed.total_experience_years:.1f}y != {gt['experience_years']}y (diff: {diff:.1f}y)")

    print("\n" + "=" * 100)
    print("WILD RESUME PARSING ACCURACY SUMMARY:")
    print("=" * 100)
    for field, counts in stats.items():
        corr = counts["correct"]
        tot = counts["total"]
        pct = (corr / tot * 100) if tot > 0 else 0
        print(f"  {field.capitalize():<20}: {corr}/{tot} ({pct:.1f}%)")


if __name__ == "__main__":
    evaluate()
