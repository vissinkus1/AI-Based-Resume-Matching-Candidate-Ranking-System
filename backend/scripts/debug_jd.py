"""
scripts/debug_jd.py — Inspect skill extraction, classification and evidence.

Prints for each of the 3 sample JDs:
  skill -> classification (required/preferred) -> evidence sentence / section
"""
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent / "sample_data" / "jds"

def debug_jd(filename: str):
    path = SAMPLE_DIR / filename
    print("=" * 80)
    print(f"DEBUGGING JD: {filename}")
    print("=" * 80)

    raw_bytes = path.read_bytes()
    text = extract_text(raw_bytes, filename)
    parsed = parse_jd(text)

    print(f"TITLE: {parsed.title}")
    print(f"EXPERIENCE: min={parsed.min_experience_years}, max={parsed.max_experience_years}")
    print(f"QUALIFICATIONS: min_required_level={parsed.min_required_level}, preferred_level={parsed.preferred_level}")
    for q in parsed.qualifications:
        print(f"  - [{q.level}] {q.raw_phrase}")

    print("\n--- REQUIRED SKILLS & EVIDENCE ---")
    for skill in parsed.required_skills:
        ev = parsed.skill_evidence.get(skill, {})
        sec = ev.get("section", "unknown")
        sent = ev.get("sentence", "no sentence")
        print(f"  [REQ] {skill:<25} | sec: {sec:<16} | sent: {sent}")

    print("\n--- PREFERRED SKILLS & EVIDENCE ---")
    for skill in parsed.preferred_skills:
        ev = parsed.skill_evidence.get(skill, {})
        sec = ev.get("section", "unknown")
        sent = ev.get("sentence", "no sentence")
        print(f"  [PREF] {skill:<24} | sec: {sec:<16} | sent: {sent}")

    print("\n" + "=" * 80 + "\n")

def main():
    for f in ["java_backend_jd.txt", "react_frontend_jd.docx", "aiml_engineer_jd.pdf"]:
        debug_jd(f)

if __name__ == "__main__":
    main()
