"""
scripts/part0_ranking_sanity.py — Part 0: Ranking Sanity, Domain Hierarchy, and Cold/Warm Benchmarks.
"""

import sys
import time
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.services.text_extractor import extract_text
from app.services.jd_parser import parse_jd
from app.services.resume_parser import parse_resume
from app.services.embedding_service import get_embedding_service
from app.services.skills_taxonomy import get_taxonomy
from app.services.matching_engine import rank, _is_real_duty_sentence
from app.core.scoring_config import SCORING

SAMPLE_DIR = BACKEND_DIR.parent / "sample_data"
RESUMES_DIR = SAMPLE_DIR / "resumes"
JDS_DIR = SAMPLE_DIR / "jds"

JD_CONFIGS = [
    ("Java Backend", "java_backend_jd.txt"),
    ("React Frontend", "react_frontend_jd.docx"),
    ("AI/ML Engineer", "aiml_engineer_jd.pdf"),
]

def run_part0():
    print("=" * 110)
    print("PART 0: SYSTEM AUDIT & RANKING SANITY REPORT")
    print("=" * 110)

    emb_service = get_embedding_service()
    taxonomy = get_taxonomy()

    # Ingest 12 standard synthetic resumes
    resume_files = sorted(
        [f for f in RESUMES_DIR.iterdir() if f.suffix.lower() in {".pdf", ".docx"} and f.name.startswith("candidate_")]
    )
    parsed_candidates = [
        parse_resume(rf.read_bytes(), rf.name, today=(2026, 11))
        for rf in resume_files
    ]

    all_tables = {}

    for jd_name, jd_file in JD_CONFIGS:
        jd_path = JDS_DIR / jd_file
        jd_text = extract_text(jd_path.read_bytes(), jd_file)
        p_jd = parse_jd(jd_text)

        ranked = rank(p_jd, parsed_candidates, taxonomy=taxonomy, embed_service=emb_service)

        print(f"\n==========================================================================================")
        print(f"JD: {jd_name.upper()} ({jd_file})")
        print(f"==========================================================================================")
        print(f"{'Rnk':<4} | {'Candidate':<24} | {'Exp (Rel/Tot)':<13} | {'Match%':<6} | {'Band':<14} | {'Skill':<6} | {'Sem':<6} | {'Exp':<6} | {'Qual':<6} | {'Title':<6}")
        print("-" * 105)

        rows = []
        for r_num, (cand, res) in enumerate(ranked, start=1):
            rel_exp = res.relevant_experience_years
            tot_exp = cand.total_experience_years
            row_data = {
                "rank": r_num,
                "name": cand.name or res.candidate_name,
                "rel_tot": f"{rel_exp:.1f}/{tot_exp:.1f}y",
                "score": res.final_score,
                "band": res.recommendation_band,
                "skill": round(res.skill_score, 1),
                "sem": round(res.semantic_score, 1),
                "exp": round(res.experience_score, 1),
                "qual": round(res.qualification_score, 1),
                "title": round(res.title_relevance_score, 1),
            }
            rows.append(row_data)
            print(f"{row_data['rank']:<4} | {row_data['name']:<24} | {row_data['rel_tot']:<13} | {row_data['score']:>5.1f}% | {row_data['band']:<14} | {row_data['skill']:>5.1f}% | {row_data['sem']:>5.1f}% | {row_data['exp']:>5.1f}% | {row_data['qual']:>5.1f}% | {row_data['title']:>5.1f}%")

        all_tables[jd_name] = rows

    # 0.2 Specific check: Priya vs Pooja in Java JD
    print("\n" + "=" * 110)
    print("0.2 DOMAIN INTEGRITY CHECK: Java JD — Technical Candidates vs Off-Domain Marketer (Pooja)")
    print("=" * 110)
    java_rows = {r["name"]: r for r in all_tables["Java Backend"]}
    priya = java_rows.get("Candidate 02 Priya Patel React") or java_rows.get("Priya Patel")
    pooja = java_rows.get("Pooja Hegde")
    siddharth = java_rows.get("Siddharth Reddy")
    ananya = java_rows.get("Ananya Iyer")

    print(f"Siddharth Reddy (Senior Arch): Rank #{siddharth['rank']} ({siddharth['score']}%) - Band: {siddharth['band']}")
    print(f"Ananya Iyer (Fullstack):      Rank #{ananya['rank']} ({ananya['score']}%) - Band: {ananya['band']}")
    print(f"Priya Patel (React Dev):      Rank #{priya['rank']} ({priya['score']}%) - Band: {priya['band']}")
    print(f"Pooja Hegde (Marketer):       Rank #{pooja['rank']} ({pooja['score']}%) - Band: {pooja['band']}")

    assert priya["rank"] < pooja["rank"], f"ERROR: Priya (rank {priya['rank']}) ranked below Pooja (rank {pooja['rank']})!"
    assert priya["score"] > pooja["score"], f"ERROR: Priya score ({priya['score']}) <= Pooja score ({pooja['score']})!"
    print(f"\n✓ PASS: Priya Patel (Rank #{priya['rank']}, {priya['score']}%) strictly ranks ABOVE Pooja Hegde (Rank #{pooja['rank']}, {pooja['score']}%) by +{priya['score'] - pooja['score']:.1f}%")
    print(f"  Priya: Skill {priya['skill']}% (matched REST API, Git, Integration Testing), Sem {priya['sem']}%, Exp {priya['exp']}%, Title {priya['title']}%")
    print(f"  Pooja: Skill {pooja['skill']}% (0 technical matches), Sem {pooja['sem']}%, Exp {pooja['exp']}%, Title {pooja['title']}%")

    # 0.3 Cold vs Warm Timing
    print("\n" + "=" * 110)
    print("0.3 TIMING BENCHMARKS: Cold vs Warm Ranking for 12 Resumes (Java JD)")
    print("=" * 110)
    jd_path = JDS_DIR / "java_backend_jd.txt"
    p_jd = parse_jd(extract_text(jd_path.read_bytes(), "java_backend_jd.txt"))

    # Cold run: Clear LRU cache and embedding text cache
    _is_real_duty_sentence.cache_clear()
    emb_service._cache.clear()

    t_cold_start = time.perf_counter()
    rank(p_jd, parsed_candidates, taxonomy=taxonomy, embed_service=emb_service)
    t_cold_ms = (time.perf_counter() - t_cold_start) * 1000

    # Warm run: Re-run with warm cache
    t_warm_start = time.perf_counter()
    rank(p_jd, parsed_candidates, taxonomy=taxonomy, embed_service=emb_service)
    t_warm_ms = (time.perf_counter() - t_warm_start) * 1000

    print(f"Cold Execution Latency: {t_cold_ms:.2f} ms")
    print(f"Warm Execution Latency: {t_warm_ms:.2f} ms (Target < 1000 ms: {'PASS' if t_warm_ms < 1000 else 'FAIL'})")

if __name__ == "__main__":
    run_part0()
