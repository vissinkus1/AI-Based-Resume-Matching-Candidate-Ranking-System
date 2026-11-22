"""
scripts/evaluate_parsing.py — Evaluate resume parser accuracy against ground truth.

Runs parse_resume() on all 12 sample resumes in sample_data/resumes/
and compares extracted fields to sample_data/resumes/ground_truth.json:
  - Name accuracy %
  - Email accuracy %
  - Phone accuracy %
  - Experience accuracy (within ±0.5 years) %
  - Education level accuracy %
  - Skills Precision, Recall, and F1 score %
  - Overall accuracy %

Target: All individual and overall metrics >= 85%.
"""

import json
import sys
from pathlib import Path

# Add backend to sys.path so app modules import cleanly
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.resume_parser import parse_resume

RESUMES_DIR = BACKEND_DIR.parent / "sample_data" / "resumes"
GROUND_TRUTH_FILE = RESUMES_DIR / "ground_truth.json"


def normalize_phone(phone: str | None) -> str:
    """Strip all non-digits from phone number for robust comparison."""
    if not phone:
        return ""
    digits = "".join(c for c in phone if c.isdigit())
    # Return last 10 digits
    return digits[-10:] if len(digits) >= 10 else digits


def normalize_str(s: str | None) -> str:
    return (s or "").strip().lower()


def evaluate():
    if not GROUND_TRUTH_FILE.exists():
        print(f"Error: {GROUND_TRUTH_FILE} does not exist. Run generate_sample_resumes.py first.")
        sys.exit(1)

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    total_candidates = len(ground_truth)
    if total_candidates == 0:
        print("No ground truth records found.")
        sys.exit(1)

    name_matches = 0
    email_matches = 0
    phone_matches = 0
    exp_matches = 0
    edu_matches = 0

    total_tp = 0
    total_fp = 0
    total_fn = 0

    results_table = []

    print("\n" + "=" * 90)
    print(f"EVALUATING RESUME PARSING ACCURACY ({total_candidates} SYNTHETIC RESUMES)")
    print("=" * 90)

    for filename, gt in ground_truth.items():
        filepath = RESUMES_DIR / filename
        if not filepath.exists():
            print(f"File missing: {filepath}")
            continue

        file_bytes = filepath.read_bytes()
        # Parse resume with fixed today (Nov 2026) to match ground truth baseline
        parsed = parse_resume(file_bytes=file_bytes, filename=filename, today=(2026, 11))

        # 1. Name Match
        gt_name = normalize_str(gt.get("name"))
        pred_name = normalize_str(parsed.name)
        # Check if either contains the other or exact match
        name_ok = (gt_name == pred_name) or (gt_name in pred_name) or (pred_name in gt_name and len(pred_name) > 3)
        if name_ok:
            name_matches += 1

        # 2. Email Match
        gt_email = normalize_str(gt.get("email"))
        pred_email = normalize_str(parsed.email)
        email_ok = (gt_email == pred_email)
        if email_ok:
            email_matches += 1

        # 3. Phone Match
        gt_phone = normalize_phone(gt.get("phone"))
        pred_phone = normalize_phone(parsed.phone)
        phone_ok = (gt_phone == pred_phone) and (len(gt_phone) >= 7)
        if phone_ok:
            phone_matches += 1

        # 4. Experience Match (within ±0.5 years)
        gt_exp = float(gt.get("total_experience_years", 0.0))
        pred_exp = float(parsed.total_experience_years)
        exp_diff = abs(gt_exp - pred_exp)
        exp_ok = (exp_diff <= 0.5)
        if exp_ok:
            exp_matches += 1

        # 5. Education Level Match
        gt_edu = normalize_str(gt.get("education_level"))
        pred_edu = ""
        if parsed.education:
            # Highest or first detected degree level
            levels = [e.level for e in parsed.education if e.level]
            pred_edu = levels[0] if levels else ""
        edu_ok = (gt_edu == pred_edu)
        if edu_ok:
            edu_matches += 1

        # 6. Skills Precision & Recall
        gt_skills = {normalize_str(s) for s in gt.get("skills", [])}
        pred_skills = {normalize_str(s.name) for s in parsed.skills}

        tp = len(gt_skills & pred_skills)
        fp = len(pred_skills - gt_skills)
        fn = len(gt_skills - pred_skills)

        total_tp += tp
        total_fp += fp
        total_fn += fn

        p_skill = (tp / (tp + fp)) * 100 if (tp + fp) > 0 else (100.0 if not gt_skills else 0.0)
        r_skill = (tp / (tp + fn)) * 100 if (tp + fn) > 0 else (100.0 if not gt_skills else 0.0)

        results_table.append({
            "file": filename[:30],
            "name": f"{parsed.name or 'N/A'} {'✓' if name_ok else '✗'}",
            "email": "✓" if email_ok else "✗",
            "phone": "✓" if phone_ok else "✗",
            "exp": f"{pred_exp:.1f}y (gt:{gt_exp:.1f}) {'✓' if exp_ok else '✗'}",
            "edu": f"{pred_edu or 'none'} {'✓' if edu_ok else '✗'}",
            "skills_f1": f"P:{p_skill:.0f}% R:{r_skill:.0f}%",
        })

    # Summary Calculations
    name_acc = (name_matches / total_candidates) * 100
    email_acc = (email_matches / total_candidates) * 100
    phone_acc = (phone_matches / total_candidates) * 100
    exp_acc = (exp_matches / total_candidates) * 100
    edu_acc = (edu_matches / total_candidates) * 100

    skill_prec = (total_tp / (total_tp + total_fp) * 100) if (total_tp + total_fp) > 0 else 100.0
    skill_rec = (total_tp / (total_tp + total_fn) * 100) if (total_tp + total_fn) > 0 else 100.0
    skill_f1 = (2 * skill_prec * skill_rec / (skill_prec + skill_rec)) if (skill_prec + skill_rec) > 0 else 0.0

    overall_score = (name_acc + email_acc + phone_acc + exp_acc + edu_acc + skill_f1) / 6

    # Print Table
    print(f"\n{'Resume File':<32} | {'Name':<22} | {'Email':<6} | {'Phone':<6} | {'Exp (±0.5y)':<18} | {'Edu Level':<14} | {'Skills'}")
    print("-" * 115)
    for r in results_table:
        print(f"{r['file']:<32} | {r['name']:<22} | {r['email']:<6} | {r['phone']:<6} | {r['exp']:<18} | {r['edu']:<14} | {r['skills_f1']}")

    print("\n" + "=" * 90)
    print("PARSER EVALUATION METRICS SUMMARY")
    print("=" * 90)
    print(f"  Name Extraction Accuracy:     {name_acc:6.1f}%   (Target: >= 85%) {'✅ PASS' if name_acc >= 85 else '❌ FAIL'}")
    print(f"  Email Extraction Accuracy:    {email_acc:6.1f}%   (Target: >= 85%) {'✅ PASS' if email_acc >= 85 else '❌ FAIL'}")
    print(f"  Phone Extraction Accuracy:    {phone_acc:6.1f}%   (Target: >= 85%) {'✅ PASS' if phone_acc >= 85 else '❌ FAIL'}")
    print(f"  Experience Accuracy (±0.5y):  {exp_acc:6.1f}%   (Target: >= 85%) {'✅ PASS' if exp_acc >= 85 else '❌ FAIL'}")
    print(f"  Education Level Accuracy:     {edu_acc:6.1f}%   (Target: >= 85%) {'✅ PASS' if edu_acc >= 85 else '❌ FAIL'}")
    print(f"  Skill Precision:              {skill_prec:6.1f}%")
    print(f"  Skill Recall:                 {skill_rec:6.1f}%   (Target: >= 85%) {'✅ PASS' if skill_rec >= 85 else '❌ FAIL'}")
    print(f"  Skill F1 Score:               {skill_f1:6.1f}%")
    print("-" * 90)
    print(f"  OVERALL SYSTEM ACCURACY:      {overall_score:6.1f}%   (Target: >= 85%) {'✅ PASS' if overall_score >= 85 else '❌ FAIL'}")
    print("=" * 90 + "\n")

    return overall_score >= 85.0


if __name__ == "__main__":
    success = evaluate()
    if not success:
        sys.exit(1)
