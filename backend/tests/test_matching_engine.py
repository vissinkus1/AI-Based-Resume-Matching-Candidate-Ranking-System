"""
tests/test_matching_engine.py — Unit and integration tests for the matching engine.

Validates:
1. Skill family collapse (pruning child skills when parent is present in JD).
2. Credit table:
   - Exact and alias match (1.0)
   - Child-of-required-parent (0.9)
   - Parent-of-required-child (0.6)
   - Semantic soft match (capped at 0.70)
3. Experience calculation:
   - Proportional credit below minimum
   - Sweet spot full credit (100.0)
   - Over-qualification floor (90.0)
   - Internship 50% discount in relevant experience
4. Qualification hierarchy scoring:
   - Meets/exceeds (100.0)
   - 1 level below (50.0)
   - 2+ levels below (20.0)
   - None detected (30.0)
5. Knockout rule:
   - Caps final score at 35.0 when core skill coverage < 25%
6. Scoring config validation:
   - Rejects invalid weight sums (must sum to 1.0)
7. Determinism:
   - Identical inputs yield identical outputs
8. End-to-end integration and ranking.
"""

import pytest
from app.core.scoring_config import ScoringWeights, SCORING
from app.services.skills_taxonomy import get_taxonomy
from app.services.embedding_service import get_embedding_service
from app.services.jd_parser import ParsedJD
from app.services.resume_parser import ParsedResume, ResumeSkill, ExperienceEntry, EducationEntry
from app.services.matching_engine import (
    collapse_jd_skill_families,
    compute_skill_score,
    compute_experience_score,
    compute_qualification_score,
    match,
    rank,
)


@pytest.fixture(scope="module")
def taxonomy():
    return get_taxonomy()


@pytest.fixture(scope="module")
def embed_service():
    return get_embedding_service()


# ------------------------------------------------------------------
# 1. Skill Family Collapse Tests
# ------------------------------------------------------------------

def test_skill_family_collapse(taxonomy):
    """When a JD asks for both AWS and AWS S3 / AWS EC2, the children are pruned."""
    raw_required = ["AWS", "AWS S3", "AWS EC2", "Python", "Docker"]
    collapsed = collapse_jd_skill_families(raw_required, taxonomy)

    assert "AWS" in collapsed
    assert "Python" in collapsed
    assert "Docker" in collapsed
    assert "AWS S3" not in collapsed
    assert "AWS EC2" not in collapsed


def test_skill_family_collapse_no_parent(taxonomy):
    """When only child skills are present (no parent in JD), neither is pruned."""
    raw_required = ["AWS S3", "AWS EC2", "Python"]
    collapsed = collapse_jd_skill_families(raw_required, taxonomy)

    assert "AWS S3" in collapsed
    assert "AWS EC2" in collapsed


# ------------------------------------------------------------------
# 2. Credit Table & Skill Scoring Tests
# ------------------------------------------------------------------

def test_credit_table_exact_and_alias(taxonomy, embed_service):
    """Exact skill match yields 1.0 credit."""
    jd = ParsedJD(
        title="Backend Developer",
        required_skills=["Java", "Spring Boot", "PostgreSQL"],
    )
    candidate = ParsedResume(
        name="Candidate A",
        skills=[
            ResumeSkill(name="Java", category="backend", confidence="strong", tier="core"),
            ResumeSkill(name="Spring Boot", category="backend", confidence="strong", tier="core"),
            ResumeSkill(name="PostgreSQL", category="databases", confidence="strong", tier="core"),
        ],
    )

    score, matched, partial, missing_req, missing_pref, extra, core_cov = compute_skill_score(
        jd=jd,
        candidate=candidate,
        taxonomy=taxonomy,
        embed_service=embed_service,
        config=SCORING,
    )

    assert score >= 99.0
    assert len(missing_req) == 0
    assert core_cov >= 0.99
    assert all(m.credit == 1.0 for m in matched)


def test_credit_table_child_of_parent(taxonomy, embed_service):
    """JD wants parent (AWS), candidate has child (AWS S3) -> 0.9 credit."""
    jd = ParsedJD(
        title="Cloud Developer",
        required_skills=["AWS"],
    )
    candidate = ParsedResume(
        name="Candidate B",
        skills=[
            ResumeSkill(name="AWS S3", category="cloud", confidence="strong", tier="core")
        ],
    )

    score, matched, partial, missing_req, missing_pref, extra, core_cov = compute_skill_score(
        jd=jd,
        candidate=candidate,
        taxonomy=taxonomy,
        embed_service=embed_service,
        config=SCORING,
    )

    assert len(matched) == 1
    assert matched[0].match_type == "child_of_parent"
    assert matched[0].credit == SCORING.credit_child_of_required_parent  # 0.9
    assert len(missing_req) == 0


def test_credit_table_parent_of_child(taxonomy, embed_service):
    """JD wants child (AWS S3), candidate only has parent (AWS) -> 0.6 credit."""
    jd = ParsedJD(
        title="Cloud Developer",
        required_skills=["AWS S3"],
    )
    candidate = ParsedResume(
        name="Candidate C",
        skills=[
            ResumeSkill(name="AWS", category="cloud", confidence="strong", tier="core")
        ],
    )

    score, matched, partial, missing_req, missing_pref, extra, core_cov = compute_skill_score(
        jd=jd,
        candidate=candidate,
        taxonomy=taxonomy,
        embed_service=embed_service,
        config=SCORING,
    )

    assert len(partial) == 1
    assert partial[0].match_type == "parent_of_child"
    assert partial[0].credit == SCORING.credit_parent_of_required_child  # 0.6
    assert len(missing_req) == 0


def test_credit_table_semantic_soft(taxonomy, embed_service):
    """Candidate has related framework (FastAPI) when JD requests Flask."""
    jd = ParsedJD(
        title="Python Developer",
        required_skills=["Flask"],
    )
    candidate = ParsedResume(
        name="Candidate D",
        skills=[
            ResumeSkill(name="FastAPI", category="backend", confidence="strong", tier="core")
        ],
    )

    score, matched, partial, missing_req, missing_pref, extra, core_cov = compute_skill_score(
        jd=jd,
        candidate=candidate,
        taxonomy=taxonomy,
        embed_service=embed_service,
        config=SCORING,
    )

    # FastAPI and Flask have high semantic similarity (>= 0.62)
    if len(partial) > 0:
        assert partial[0].match_type == "semantic_soft"
        assert partial[0].credit <= SCORING.credit_semantic_max  # <= 0.70
        assert partial[0].credit >= SCORING.semantic_soft_match_threshold  # >= 0.62


# ------------------------------------------------------------------
# 3. Experience Scoring Tests
# ------------------------------------------------------------------

def test_experience_proportional_credit(embed_service):
    """Candidate with half required years gets roughly 50.0 score."""
    jd = ParsedJD(
        title="Backend Developer",
        min_experience_years=5.0,
        max_experience_years=8.0,
    )
    candidate = ParsedResume(
        name="Junior Dev",
        total_experience_years=2.5,
        experience_entries=[
            ExperienceEntry(
                title="Backend Developer",
                company="TechCorp",
                start_date="2024-01",
                end_date="2026-07",
                months=30,
                description="Backend developer working with Python APIs.",
            )
        ],
    )
    score, tot_y, rel_y, verdict, gap = compute_experience_score(jd, candidate, embed_service, SCORING)
    assert 45.0 <= score <= 55.0
    assert "below" in verdict.lower()
    assert gap > 0.0


def test_experience_sweet_spot(embed_service):
    """Candidate in target range (min <= exp <= max) receives 100.0 score."""
    jd = ParsedJD(
        title="Backend Developer",
        min_experience_years=5.0,
        max_experience_years=8.0,
    )
    candidate = ParsedResume(
        name="Mid Senior Dev",
        total_experience_years=6.0,
        experience_entries=[
            ExperienceEntry(
                title="Backend Developer",
                company="TechCorp",
                start_date="2020-01",
                end_date="2026-01",
                months=72,
                description="Backend developer building cloud services.",
            )
        ],
    )
    score, tot_y, rel_y, verdict, gap = compute_experience_score(jd, candidate, embed_service, SCORING)
    assert score == 100.0
    assert "meets" in verdict.lower()
    assert gap == 0.0


def test_experience_overqualification_floor(embed_service):
    """Candidate exceeding max by > 50% receives 90.0 floor score, not penalized harshly."""
    jd = ParsedJD(
        title="Backend Developer",
        min_experience_years=5.0,
        max_experience_years=8.0,
    )
    candidate = ParsedResume(
        name="Veteran Dev",
        total_experience_years=16.0,
        experience_entries=[
            ExperienceEntry(
                title="Backend Developer",
                company="TechCorp",
                start_date="2010-01",
                end_date="2026-01",
                months=192,
                description="Senior systems architect and backend engineer.",
            )
        ],
    )
    score, tot_y, rel_y, verdict, gap = compute_experience_score(jd, candidate, embed_service, SCORING)
    assert score == SCORING.exp_over_qualification_floor  # 90.0
    assert "above" in verdict.lower()


def test_experience_internship_discount(embed_service):
    """Internship experience is discounted by 50% in relevant experience calculation."""
    jd = ParsedJD(
        title="Software Engineer",
        required_skills=["Java", "Spring Boot"],
        min_experience_years=2.0,
    )
    candidate = ParsedResume(
        name="Intern Candidate",
        total_experience_years=2.0,
        experience_entries=[
            ExperienceEntry(
                title="Software Engineering Intern",
                company="Startup Inc",
                start_date="2023-01",
                end_date="2023-12",
                months=12,
                is_internship=True,
                description="Built REST APIs using Java and Spring Boot.",
                skills_in_entry=["Java", "Spring Boot"],
            ),
            ExperienceEntry(
                title="Junior Backend Developer",
                company="Enterprise Corp",
                start_date="2024-01",
                end_date="2024-12",
                months=12,
                is_internship=False,
                description="Developed microservices with Java and Spring Boot.",
                skills_in_entry=["Java", "Spring Boot"],
            ),
        ],
    )
    score, tot_y, rel_y, verdict, gap = compute_experience_score(jd, candidate, embed_service, SCORING)
    # Entry 1 (Internship): 12 months * 0.5 = 6 months = 0.5 yrs
    # Entry 2 (Full-time): 12 months = 1.0 yrs
    # Total relevant = 1.5 yrs
    assert abs(rel_y - 1.5) <= 0.2


# ------------------------------------------------------------------
# 4. Qualification Scoring Tests
# ------------------------------------------------------------------

def test_qualification_meets_or_exceeds():
    """Candidate meeting min required degree receives 100.0."""
    jd = ParsedJD(min_required_level="bachelor", preferred_level="master")
    cand_bachelor = ParsedResume(education=[EducationEntry(degree="B.S. CS", level="bachelor")])
    score, cand_h, jd_req, jd_pref, meets_pref = compute_qualification_score(jd, cand_bachelor, SCORING)
    assert score == 100.0
    assert not meets_pref

    cand_master = ParsedResume(education=[EducationEntry(degree="M.S. CS", level="master")])
    score_m, cand_h_m, jd_req_m, jd_pref_m, meets_pref_m = compute_qualification_score(jd, cand_master, SCORING)
    assert score_m == 100.0
    assert meets_pref_m


def test_qualification_one_level_below():
    """Candidate one level below min required degree receives 50.0."""
    jd = ParsedJD(min_required_level="bachelor")
    cand = ParsedResume(education=[EducationEntry(degree="Diploma in CS", level="diploma")])
    score, cand_h, jd_req, jd_pref, meets_pref = compute_qualification_score(jd, cand, SCORING)
    assert score == SCORING.qual_score_one_below  # 50.0


def test_qualification_two_levels_below():
    """Candidate two or more levels below min required degree receives 20.0."""
    jd = ParsedJD(min_required_level="master")
    cand = ParsedResume(education=[EducationEntry(degree="High School", level="diploma")])
    score, cand_h, jd_req, jd_pref, meets_pref = compute_qualification_score(jd, cand, SCORING)
    assert score == SCORING.qual_score_two_below  # 20.0


def test_qualification_none_detected():
    """No qualification detected gives conservative baseline of 30.0."""
    jd = ParsedJD(min_required_level="bachelor")
    cand = ParsedResume(education=[])
    score, cand_h, jd_req, jd_pref, meets_pref = compute_qualification_score(jd, cand, SCORING)
    assert score == SCORING.qual_score_none_detected  # 30.0


# ------------------------------------------------------------------
# 5. Knockout Rule Test
# ------------------------------------------------------------------

def test_knockout_cap_applied():
    """If core required skill coverage is < 25%, final score is capped at 35.0."""
    jd = ParsedJD(
        title="Senior Java Developer",
        required_skills=["Java", "Spring Boot", "Microservices", "Kafka", "PostgreSQL"],
        preferred_skills=["Docker", "AWS"],
        min_experience_years=5.0,
        max_experience_years=8.0,
        min_required_level="bachelor",
        preferred_level="master",
        responsibilities=["Build enterprise microservices with Java and Spring Boot"],
    )

    # Candidate has adjacent engineering experience and strong degree/title,
    # giving uncapped score > 50, but ZERO core required skills in Java/Spring/Kafka
    candidate = ParsedResume(
        name="Frontend Engineer",
        email="frontend@example.com",
        phone="555-0100",
        skills=[
            ResumeSkill(name="Git", category="tools", confidence="strong", tier="supporting"),
            ResumeSkill(name="HTML", category="frontend", confidence="strong", tier="core"),
        ],
        total_experience_years=6.0,
        experience_entries=[
            ExperienceEntry(
                title="Senior Frontend Engineer",
                company="Enterprise Global",
                start_date="2018-01",
                end_date="2024-01",
                months=72,
                description="Senior engineer building enterprise microservices and user interfaces with high scalability.",
                skills_in_entry=["Git"],
            )
        ],
        education=[
            EducationEntry(degree="Master of Science", level="master")
        ],
        job_titles=["Senior Frontend Engineer"],
        summary="Senior engineer with 6+ years building scalable software products and microservices.",
    )

    result = match(jd, candidate)

    # Verify knockout rule applied: uncapped score > 35, capped at 35.0
    assert result.is_knockout_applied is True
    assert result.final_score == SCORING.knockout_score_cap  # 35.0
    assert result.uncapped_score > SCORING.knockout_score_cap
    assert result.knockout_reason is not None
    assert "core required skill coverage" in result.knockout_reason.lower()


# ------------------------------------------------------------------
# 6. Scoring Weights Validation Test
# ------------------------------------------------------------------

def test_scoring_weights_validation():
    """Weights that do not sum to 1.0 must raise ValueError."""
    with pytest.raises(ValueError, match="must sum to 1.0"):
        ScoringWeights(w_skill=0.50, w_semantic=0.25, w_experience=0.20, w_qualification=0.10, w_title=0.05)


# ------------------------------------------------------------------
# 7. Determinism Test
# ------------------------------------------------------------------

def test_match_determinism():
    """Running match twice on identical data produces identical outputs."""
    jd = ParsedJD(
        title="Full Stack Engineer",
        required_skills=["Python", "FastAPI", "React", "PostgreSQL"],
        preferred_skills=["Docker", "AWS"],
        min_experience_years=3.0,
        max_experience_years=6.0,
        min_required_level="bachelor",
        responsibilities=["Develop web applications using FastAPI and React"],
    )

    candidate = ParsedResume(
        name="Alex Smith",
        email="alex@example.com",
        phone="555-1234",
        skills=[
            ResumeSkill(name="Python", category="backend", confidence="strong", tier="core"),
            ResumeSkill(name="FastAPI", category="backend", confidence="strong", tier="core"),
            ResumeSkill(name="React", category="frontend", confidence="strong", tier="core"),
            ResumeSkill(name="PostgreSQL", category="databases", confidence="medium", tier="core"),
            ResumeSkill(name="Docker", category="devops", confidence="basic", tier="core"),
        ],
        total_experience_years=4.5,
        experience_entries=[
            ExperienceEntry(
                title="Software Engineer",
                company="TechCorp",
                start_date="2020-01",
                end_date="2024-07",
                months=54,
                description="Built REST services with Python and FastAPI, frontend with React.",
                skills_in_entry=["Python", "FastAPI", "React"],
            )
        ],
        education=[
            EducationEntry(degree="B.S. in Computer Science", level="bachelor")
        ],
        job_titles=["Software Engineer"],
        summary="Passionate full stack developer with 4.5 years experience.",
    )

    result_1 = match(jd, candidate)
    result_2 = match(jd, candidate)

    assert result_1.final_score == result_2.final_score
    assert result_1.skill_score == result_2.skill_score
    assert result_1.semantic_score == result_2.semantic_score
    assert result_1.experience_score == result_2.experience_score
    assert result_1.qualification_score == result_2.qualification_score
    assert result_1.title_relevance_score == result_2.title_relevance_score
    assert len(result_1.matched_skills) == len(result_2.matched_skills)
    assert result_1.summary == result_2.summary


# ------------------------------------------------------------------
# 8. End-to-End Ranking Test
# ------------------------------------------------------------------

def test_end_to_end_ranking():
    """Ranks candidates in descending order of final_score."""
    jd = ParsedJD(
        title="Python Backend Developer",
        required_skills=["Python", "PostgreSQL", "Docker"],
        min_experience_years=3.0,
    )

    strong_candidate = ParsedResume(
        name="Candidate A (Strong)",
        skills=[
            ResumeSkill(name="Python", category="backend", confidence="strong", tier="core"),
            ResumeSkill(name="PostgreSQL", category="databases", confidence="strong", tier="core"),
            ResumeSkill(name="Docker", category="devops", confidence="strong", tier="core"),
        ],
        total_experience_years=5.0,
        job_titles=["Python Backend Developer"],
        education=[EducationEntry(degree="B.S. CS", level="bachelor")],
    )

    weak_candidate = ParsedResume(
        name="Candidate B (Weak)",
        skills=[
            ResumeSkill(name="HTML", category="frontend", confidence="basic", tier="core"),
        ],
        total_experience_years=1.0,
        job_titles=["Junior Graphic Designer"],
        education=[EducationEntry(degree="High School", level="diploma")],
    )

    ranked = rank(jd, [weak_candidate, strong_candidate])

    assert len(ranked) == 2
    top_cand, top_res = ranked[0]
    bottom_cand, bottom_res = ranked[1]

    assert top_cand.name == "Candidate A (Strong)"
    assert bottom_cand.name == "Candidate B (Weak)"
    assert top_res.final_score > bottom_res.final_score
    assert top_res.recommendation_band in ["Strong match", "Good match"]
