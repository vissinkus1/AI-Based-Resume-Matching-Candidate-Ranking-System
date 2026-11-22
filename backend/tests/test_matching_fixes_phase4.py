"""
tests/test_matching_fixes_phase4.py — Unit tests verifying Phase 4 Part A matching fixes (A1-A7).

Validates:
  A1: JD skill integrity (Java and Spring Boot kept, strict separation of req/pref, narrative count).
  A2: Relevant experience generic skills exclusion (Docker/SQL/Git don't grant domain relevance).
  A3: Title normalization (seniority tokens stripped before embedding).
  A4: Concept skills inferred credit for supporting/soft tiers only, never core.
  A5: Real duty sentence filtering (drop boilerplate, require verb, >= 6 words) & narrative polish.
  A6: Skill sorting for display (tier weight -> credit -> name) & matched_top max 6.
  A7: Calibration bounds (no saturation at 100).
"""

import pytest
from app.core.scoring_config import SCORING, GENERIC_SKILLS, ScoringWeights
from app.services.skills_taxonomy import get_taxonomy
from app.services.embedding_service import get_embedding_service, calibrate_cosine
from app.services.jd_parser import ParsedJD
from app.services.resume_parser import ParsedResume, ResumeSkill, ExperienceEntry, EducationEntry
from app.services.matching_engine import (
    collapse_jd_skill_families,
    compute_skill_score,
    compute_experience_score,
    compute_title_relevance_score,
    normalize_title,
    _is_real_duty_sentence,
    match,
    MatchedSkillItem,
)


@pytest.fixture(scope="module")
def taxonomy():
    return get_taxonomy()


@pytest.fixture(scope="module")
def embed_service():
    return get_embedding_service()


# ------------------------------------------------------------------
# A1. JD Skill Integrity & Separate Required/Preferred Lists
# ------------------------------------------------------------------

def test_a1_java_and_spring_boot_kept_after_collapse(taxonomy):
    """Java and Spring Boot must BOTH be kept in required list after family collapse."""
    java_jd_skills = [
        "Java", "Spring Boot", "PostgreSQL", "Redis", "MongoDB",
        "Microservices", "Distributed Systems", "Docker", "Kubernetes",
        "Git", "GitHub Actions", "CI/CD", "Jenkins", "REST API",
        "Data Structures", "Algorithms", "Clean Architecture",
        "Object-Oriented Programming"
    ]
    collapsed = collapse_jd_skill_families(java_jd_skills, taxonomy)

    # Both Java and Spring Boot must be preserved
    assert "Java" in collapsed, "Java was dropped from required skills!"
    assert "Spring Boot" in collapsed, "Spring Boot was dropped from required skills!"

    # Tool platforms like GitHub Actions and Jenkins collapse into CI/CD
    assert "CI/CD" in collapsed
    assert "GitHub Actions" not in collapsed
    assert "Jenkins" not in collapsed


def test_a1_strictly_separate_required_and_preferred(taxonomy, embed_service):
    """Ensure matched_required, matched_preferred, missing_required, missing_preferred are strictly disjoint."""
    jd = ParsedJD(
        title="Senior Java Developer",
        required_skills=["Java", "Kubernetes", "PostgreSQL"],
        preferred_skills=["AWS", "Docker", "GraphQL"],
    )
    candidate = ParsedResume(
        name="Test Java Dev",
        skills=[
            ResumeSkill(name="Java", confidence="strong", tier="core"),
            ResumeSkill(name="Docker", confidence="strong", tier="core"),
        ],
    )

    result = match(jd, candidate, taxonomy=taxonomy, embed_service=embed_service)

    matched_req_names = {m.jd_skill for m in result.matched_required}
    matched_pref_names = {m.jd_skill for m in result.matched_preferred}
    missing_req_names = set(result.missing_required_skills)
    missing_pref_names = set(result.missing_preferred_skills)

    # Strictly disjoint
    assert "Java" in matched_req_names
    assert "Java" not in matched_pref_names
    assert "Java" not in missing_req_names

    assert "Docker" in matched_pref_names
    assert "Docker" not in matched_req_names
    assert "Docker" not in missing_pref_names

    assert "Kubernetes" in missing_req_names
    assert "PostgreSQL" in missing_req_names
    assert "GraphQL" in missing_pref_names

    # Narrative strictly counts required skills only
    # Candidate matches 1 of 3 required (Java)
    skill_reason = next(r for r in result.reasons if r.factor == "skill")
    assert "Covers 1 of 3 required skills" in skill_reason.text
    assert "Docker" not in skill_reason.text.split("Missing:")[0]  # Docker is preferred, not counted in required coverage


# ------------------------------------------------------------------
# A2. Relevant Experience Generic Skills Exclusion
# ------------------------------------------------------------------

def test_a2_generic_skills_not_domain_experience(taxonomy, embed_service):
    """
    Candidate with only generic skills (Docker, Git, SQL) on an AI/ML JD gets ~0 relevant years.
    Java candidate retains full relevant years on Java JD.
    """
    aiml_jd = ParsedJD(
        title="AI/ML Engineer",
        required_skills=["Machine Learning", "Deep Learning", "PyTorch", "Python", "Docker", "SQL"],
        min_experience_years=3.0,
    )

    # Candidate with only generic skills
    devops_cand = ParsedResume(
        name="DevOps Dev",
        total_experience_years=5.0,
        experience_entries=[
            ExperienceEntry(
                title="DevOps Engineer",
                company="InfraCorp",
                start_date="2021-01",
                end_date="2026-01",
                months=60,
                description="Managed Docker containers and wrote SQL queries for database backups.",
                skills_in_entry=["Docker", "SQL", "Git", "Linux"],
            )
        ],
    )

    _, _, aiml_rel_years, _, _ = compute_experience_score(
        aiml_jd, devops_cand, embed_service, SCORING, taxonomy=taxonomy
    )
    # Generic tools alone cannot qualify experience as AI/ML
    assert aiml_rel_years == 0.0, f"Expected 0.0 relevant years for DevOps on AI/ML, got {aiml_rel_years}"

    # Java candidate on Java JD
    java_jd = ParsedJD(
        title="Senior Java Developer",
        required_skills=["Java", "Spring Boot", "Microservices", "PostgreSQL", "Docker", "Git"],
        min_experience_years=3.0,
    )
    java_cand = ParsedResume(
        name="Java Dev",
        total_experience_years=4.0,
        experience_entries=[
            ExperienceEntry(
                title="Backend Java Developer",
                company="BankSoft",
                start_date="2022-01",
                end_date="2026-01",
                months=48,
                description="Developed high-throughput financial microservices using Java and Spring Boot with PostgreSQL.",
                skills_in_entry=["Java", "Spring Boot", "Microservices", "PostgreSQL", "Docker"],
            )
        ],
    )
    _, _, java_rel_years, verdict, _ = compute_experience_score(
        java_jd, java_cand, embed_service, SCORING, taxonomy=taxonomy
    )
    # Retains full 4.0 relevant years on Java JD
    assert java_rel_years >= 3.8
    assert "meets" in verdict.lower()


# ------------------------------------------------------------------
# A3. Title Normalization
# ------------------------------------------------------------------

def test_a3_title_normalization_seniority_stripped(embed_service):
    """Seniority prefixes and punctuation are removed to prevent false cross-domain title matches."""
    raw_front = "Senior Frontend Developer"
    raw_java = "Senior Java/Spring Boot Backend Developer"

    norm_front = normalize_title(raw_front)
    norm_java = normalize_title(raw_java)

    assert "senior" not in norm_front
    assert "senior" not in norm_java
    assert norm_front == "frontend developer"
    assert norm_java == "java spring boot backend developer"

    # Compare raw vs normalized cosine
    e_front_raw = embed_service.embed_single(raw_front)
    e_java_raw = embed_service.embed_single(raw_java)
    cos_raw = embed_service.cosine_similarity(e_front_raw, e_java_raw)

    e_front_norm = embed_service.embed_single(norm_front)
    e_java_norm = embed_service.embed_single(norm_java)
    cos_norm = embed_service.cosine_similarity(e_front_norm, e_java_norm)

    # Removing "Senior" and punctuation drops false similarity significantly
    assert cos_norm < cos_raw
    assert cos_norm < 0.55


# ------------------------------------------------------------------
# A4. Concept Skills Inferred Credit (Supporting / Soft only)
# ------------------------------------------------------------------

def test_a4_concept_skills_inferred_credit(taxonomy, embed_service):
    """
    Supporting/soft concepts in experience descriptions receive inferred credit.
    Core tier skills (like Python, React, Java) are NEVER inferred from experience prose.
    """
    jd = ParsedJD(
        title="Software Engineer",
        required_skills=["Clean Architecture", "Unit Testing", "Java"],
    )

    # Candidate did not list "Clean Architecture" in explicit skills,
    # but described applying clean architectural principles in work experience
    candidate = ParsedResume(
        name="Architectural Dev",
        skills=[
            ResumeSkill(name="Java", confidence="strong", tier="core"),
        ],
        experience_entries=[
            ExperienceEntry(
                title="Software Engineer",
                company="TechCorp",
                start_date="2023-01",
                end_date="2025-01",
                months=24,
                description="Architected modular services following Clean Architecture principles, domain-driven design, and SOLID rules.",
            )
        ],
    )

    score, matched, partial, missing_req, _, _, _ = compute_skill_score(
        jd, candidate, taxonomy, embed_service, SCORING
    )

    # Clean Architecture is in partially_matched with inferred match_type
    arch_match = next((m for m in partial if m.jd_skill == "Clean Architecture"), None)
    assert arch_match is not None, "Clean Architecture should be inferred from experience description!"
    assert arch_match.match_type == "inferred_from_experience"
    assert arch_match.credit >= 0.50
    assert arch_match.evidence_snippet is not None

    # But core skills cannot be inferred
    jd_core = ParsedJD(title="Dev", required_skills=["Python"])
    cand_no_python = ParsedResume(
        name="Prose Dev",
        skills=[],
        experience_entries=[
            ExperienceEntry(
                title="Engineer",
                company="Co",
                start_date="2023-01",
                end_date="2025-01",
                months=24,
                description="Extensively wrote automated Python scripts and machine learning models every day.",
            )
        ],
    )
    _, matched_core, partial_core, missing_core, _, _, _ = compute_skill_score(
        jd_core, cand_no_python, taxonomy, embed_service, SCORING
    )
    assert "Python" in missing_core, "Core tier skill must never be inferred without explicit skill verification!"


# ------------------------------------------------------------------
# A5. Evidence & Duty Text Quality
# ------------------------------------------------------------------

def test_a5_duty_sentence_filter():
    """Boilerplate company/intro sentences are rejected; real actionable duties are kept."""
    boilerplate1 = "We are looking for an experienced Senior Java Developer to join our team."
    boilerplate2 = "About TechSoft Solutions Pvt. Ltd."
    boilerplate3 = "Location: Bangalore, India"
    too_short = "Java developer"
    real_duty1 = "Design, develop, and maintain high-performance RESTful APIs using Spring Boot."
    real_duty2 = "Collaborate with cross-functional teams to deliver scalable cloud microservices."

    assert not _is_real_duty_sentence(boilerplate1)
    assert not _is_real_duty_sentence(boilerplate2)
    assert not _is_real_duty_sentence(boilerplate3)
    assert not _is_real_duty_sentence(too_short)
    assert _is_real_duty_sentence(real_duty1)
    assert _is_real_duty_sentence(real_duty2)


def test_a5_narrative_template_no_including_none(taxonomy, embed_service):
    """When a candidate matches 0 required skills, narrative does not say 'including none'."""
    jd = ParsedJD(
        title="Rust Systems Engineer",
        required_skills=["Rust", "Actix", "Tokio", "WebAssembly"],
    )
    marketing_cand = ParsedResume(
        name="Marketing Lead",
        skills=[
            ResumeSkill(name="SEO", confidence="strong", tier="soft"),
        ],
    )
    result = match(jd, marketing_cand, taxonomy=taxonomy, embed_service=embed_service)
    skill_reason = next(r for r in result.reasons if r.factor == "skill")

    assert "including none" not in skill_reason.text
    assert "0 of 4 required skills verified" in skill_reason.text


# ------------------------------------------------------------------
# A6. Display Sorting & Top Skills
# ------------------------------------------------------------------

def test_a6_matched_skills_sorting_and_top(taxonomy, embed_service):
    """Matched skills are sorted by tier weight (core first), then credit, then name. matched_top <= 6."""
    jd = ParsedJD(
        title="Full Stack Engineer",
        required_skills=["Java", "Git", "Clean Architecture", "Spring Boot", "Docker", "Teamwork", "SQL", "PostgreSQL"],
    )
    candidate = ParsedResume(
        name="Versatile Dev",
        skills=[
            ResumeSkill(name="Teamwork", confidence="strong", tier="soft"),
            ResumeSkill(name="Git", confidence="strong", tier="supporting"),
            ResumeSkill(name="Java", confidence="strong", tier="core"),
            ResumeSkill(name="Spring Boot", confidence="strong", tier="core"),
            ResumeSkill(name="PostgreSQL", confidence="strong", tier="core"),
            ResumeSkill(name="Docker", confidence="strong", tier="core"),
            ResumeSkill(name="SQL", confidence="strong", tier="core"),
        ],
    )
    result = match(jd, candidate, taxonomy=taxonomy, embed_service=embed_service)

    # Core skills must come before supporting and soft
    tiers = [m.tier for m in result.matched_skills]
    core_indices = [i for i, t in enumerate(tiers) if t == "core"]
    supp_indices = [i for i, t in enumerate(tiers) if t == "supporting"]
    soft_indices = [i for i, t in enumerate(tiers) if t == "soft"]

    if core_indices and supp_indices:
        assert max(core_indices) < min(supp_indices)
    if supp_indices and soft_indices:
        assert max(supp_indices) < min(soft_indices)

    # matched_top is capped at 6
    assert len(result.matched_top) <= 6
    assert result.matched_top == result.matched_skills[:6]


# ------------------------------------------------------------------
# A7. Calibration Bounds
# ------------------------------------------------------------------

def test_a7_calibration_bounds():
    """Verify calibrated upper bound is set to 0.70 to avoid 100% saturation on general titles."""
    assert SCORING.title_raw_cos_high == 0.70
    assert SCORING.semantic_raw_cos_high == 0.70

    # A cosine of 0.65 now maps to ~91%, not 100%
    score_65 = calibrate_cosine(0.65, SCORING.title_raw_cos_low, SCORING.title_raw_cos_high)
    assert 90.0 <= score_65 <= 92.0
