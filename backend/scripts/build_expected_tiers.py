"""
scripts/build_expected_tiers.py — Generate unbiased ground-truth expected tiers.

Uses ONLY ground_truth.json (annotated true skills) and each JD's required skills
to assign an expected match tier using a fixed objective heuristic:
    - >= 60% required skill overlap  -> "Strong match"
    - 30% to 59% skill overlap       -> "Good match" or "Partial match"
    - < 30% skill overlap            -> "Weak match"

Writes output to sample_data/expected_tiers.json BEFORE evaluating engine results,
ensuring strict zero-bias validation.
"""

import json
from pathlib import Path
import sys

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd

SAMPLE_DIR = BACKEND_DIR.parent / "sample_data"
RESUMES_DIR = SAMPLE_DIR / "resumes"
JDS_DIR = SAMPLE_DIR / "jds"
GROUND_TRUTH_FILE = RESUMES_DIR / "ground_truth.json"
OUTPUT_FILE = SAMPLE_DIR / "expected_tiers.json"

JD_FILES = [
    ("java", "java_backend_jd.txt"),
    ("react", "react_frontend_jd.docx"),
    ("aiml", "aiml_engineer_jd.pdf"),
]


def build_expected_tiers():
    if not GROUND_TRUTH_FILE.exists():
        print(f"Error: {GROUND_TRUTH_FILE} does not exist.")
        sys.exit(1)

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    expected_data = {}

    for jd_key, jd_filename in JD_FILES:
        jd_path = JDS_DIR / jd_filename
        if not jd_path.exists():
            print(f"Warning: {jd_path} not found.")
            continue

        raw_bytes = jd_path.read_bytes()
        text = extract_text(raw_bytes, jd_filename)
        parsed_jd = parse_jd(text)
        jd_req_skills = set(s.lower() for s in parsed_jd.required_skills)

        jd_expectations = {}

        for resume_filename, cand_data in ground_truth.items():
            cand_skills = set(s.lower() for s in cand_data.get("skills", []))
            overlap_count = len(cand_skills & jd_req_skills)
            total_req = len(jd_req_skills) if jd_req_skills else 1
            overlap_pct = (overlap_count / total_req) * 100.0

            # Fixed heuristic rule
            if overlap_pct >= 55.0:
                expected_band = "Strong match"
                expected_tier = "strong"
            elif overlap_pct >= 28.0:
                expected_band = "Good match"
                expected_tier = "good"
            elif overlap_pct >= 15.0:
                expected_band = "Partial match"
                expected_tier = "partial"
            else:
                expected_band = "Weak match"
                expected_tier = "weak"

            jd_expectations[resume_filename] = {
                "candidate_name": cand_data.get("name"),
                "overlap_skills_count": overlap_count,
                "total_jd_required_skills": total_req,
                "overlap_pct": round(overlap_pct, 1),
                "expected_band": expected_band,
                "expected_tier": expected_tier,
                "ground_truth_exp_years": cand_data.get("total_experience_years", 0.0),
            }

        expected_data[jd_key] = {
            "jd_title": parsed_jd.title,
            "jd_filename": jd_filename,
            "required_skills_count": len(jd_req_skills),
            "candidates": jd_expectations,
        }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(expected_data, f, indent=2)

    print(f"Expected tiers generated successfully in: {OUTPUT_FILE}")
    for k, v in expected_data.items():
        print(f"\n[{k.upper()}] {v['jd_title']}")
        bands_count = {}
        for c in v["candidates"].values():
            b = c["expected_band"]
            bands_count[b] = bands_count.get(b, 0) + 1
        for b, cnt in sorted(bands_count.items()):
            print(f"  - {b}: {cnt} candidates")


if __name__ == "__main__":
    build_expected_tiers()
