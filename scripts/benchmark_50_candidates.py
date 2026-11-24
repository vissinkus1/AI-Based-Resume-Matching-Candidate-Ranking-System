"""
scripts/benchmark_50_candidates.py — Benchmark 50 synthetic resumes matching latency (Part B6).
"""

import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd
from app.services.resume_parser import parse_resume
from app.services.matching_engine import rank
from app.services.embedding_service import get_embedding_service
from app.services.skills_taxonomy import get_taxonomy

SAMPLE_DIR = BACKEND_DIR.parent / "sample_data"
JD_PATH = SAMPLE_DIR / "jds" / "java_backend_jd.txt"
RESUMES_DIR = SAMPLE_DIR / "resumes"


def run_benchmark():
    print("=" * 90)
    print("PART B6: 50-CANDIDATE BATCH MATCHING LATENCY BENCHMARK")
    print("=" * 90)

    emb_service = get_embedding_service()
    taxonomy = get_taxonomy()

    jd_text = extract_text(JD_PATH.read_bytes(), "java_backend_jd.txt")
    p_jd = parse_jd(jd_text)

    # 1. Parse the 12 base candidates
    resume_files = sorted(
        [f for f in RESUMES_DIR.iterdir() if f.suffix.lower() in {".pdf", ".docx"} and f.name.startswith("candidate_")]
    )
    base_parsed = [
        parse_resume(rf.read_bytes(), rf.name, today=(2026, 11))
        for rf in resume_files
    ]

    # 2. Expand to 50 candidates by creating variant clones
    candidates_50 = []
    import copy
    idx = 1
    while len(candidates_50) < 50:
        for c in base_parsed:
            clone = copy.deepcopy(c)
            clone.name = f"{c.name} (Variant {idx})"
            clone.email = f"variant_{idx}_{c.email}"
            candidates_50.append(clone)
            idx += 1
            if len(candidates_50) >= 50:
                break

    print(f"Candidate cohort prepared: {len(candidates_50)} parsed candidates")

    # Warm-up run with 1 candidate to ensure all models and embedding caches are hot
    rank(p_jd, candidates_50[:1], taxonomy=taxonomy, embed_service=emb_service)

    # Benchmark 50 candidates run
    start_time = time.perf_counter()
    results = rank(p_jd, candidates_50, taxonomy=taxonomy, embed_service=emb_service)
    end_time = time.perf_counter()

    elapsed_ms = (end_time - start_time) * 1000.0
    ms_per_candidate = elapsed_ms / len(candidates_50)

    print(f"\nExecution Benchmark Results:")
    print(f"  Total Candidates Ranked : {len(results)}")
    print(f"  Total Execution Time    : {elapsed_ms:.2f} ms ({elapsed_ms / 1000.0:.3f} s)")
    print(f"  Latency Per Candidate   : {ms_per_candidate:.2f} ms")
    print(f"  Top Candidate           : {results[0][0].name} (Score: {results[0][1].final_score:.1f}%)")
    print(f"  Lowest Candidate        : {results[-1][0].name} (Score: {results[-1][1].final_score:.1f}%)")

    # Assertions
    assert len(results) == 50, f"Expected 50 results, got {len(results)}"
    assert elapsed_ms < 5000.0, f"Benchmark took too long: {elapsed_ms:.2f} ms > 5000 ms"

    print("\n" + "=" * 90)
    print("SUCCESS: 50-candidate batch processed well within performance bounds.")
    print("=" * 90)


if __name__ == "__main__":
    run_benchmark()
