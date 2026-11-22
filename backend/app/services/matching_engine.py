"""
services/matching_engine.py — Comprehensive Matching & Candidate Ranking Engine.

Implements the multi-factor explainable matching algorithm:
    final_score = 0.40 * skill_score
                + 0.25 * semantic_score
                + 0.20 * experience_score
                + 0.10 * qualification_score
                + 0.05 * title_relevance_score

Features:
  - Skill family collapse (prevents duplicate child penalties)
  - Hierarchical parent/child credit table & embedding-based soft matching
  - Dual semantic evaluation: requirement-unit coverage + whole-document cosine
  - Relevant experience calculation (entry-level relevance filtering)
  - Progressive degree ranking with penalty scaling
  - Calibrated cosine-to-score transformation (0-100)
  - Knockout safeguard cap (caps score at 35 if core skill coverage < 25%)
  - Deterministic plain-English narrative explanation generation (zero LLM calls)
  - Fast batch ranking with deterministic tie-breaking
"""

import math
import re
import functools
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.core.scoring_config import SCORING, ScoringWeights, GENERIC_SKILLS
from app.services.skills_taxonomy import get_taxonomy, SkillsTaxonomy
from app.services.embedding_service import get_embedding_service, EmbeddingService, calibrate_cosine
from app.services.jd_parser import ParsedJD
from app.services.resume_parser import ParsedResume, _merge_date_intervals


# ------------------------------------------------------------------
# Structured Output Dataclasses
# ------------------------------------------------------------------

@dataclass
class MatchedSkillItem:
    """Details of a matched or partially matched skill."""
    jd_skill: str
    candidate_skill: str
    match_type: str        # "exact" | "child_of_parent" | "parent_of_child" | "semantic_soft" | "inferred_from_experience"
    credit: float
    tier: str              # "core" | "supporting" | "soft"
    is_required: bool = True
    evidence_snippet: str | None = None


@dataclass
class ResponsibilityEvidence:
    """Evidence snippet showing alignment between JD duty and candidate experience."""
    jd_duty: str
    resume_snippet: str
    similarity: float


@dataclass
class FactorReason:
    """Structured breakdown and explanation for one scoring factor."""
    factor: str            # "skill" | "semantic" | "experience" | "qualification" | "title"
    score: float           # 0 - 100
    weight: float          # e.g. 0.40
    contribution: float    # score * weight
    verdict: str           # "strong" | "ok" | "weak"
    text: str              # Plain-English explanation sentence


@dataclass
class MatchResult:
    """Comprehensive explainable evaluation of a candidate against a job description."""

    # Final Overall Score & Status
    final_score: float
    uncapped_score: float
    is_knockout_applied: bool
    knockout_reason: str | None
    recommendation_band: str  # "Strong match" | "Good match" | "Partial match" | "Weak match"

    # Component Scores (0 - 100)
    skill_score: float
    semantic_score: float
    experience_score: float
    qualification_score: float
    title_relevance_score: float

    # Breakdown contributions (score * weight) and weights
    contributions: dict[str, float]
    weights: dict[str, float]

    # Skill Details
    matched_skills: list[MatchedSkillItem]
    partially_matched: list[MatchedSkillItem]
    missing_required_skills: list[str]
    missing_preferred_skills: list[str]
    extra_relevant_skills: list[str]
    core_required_coverage: float

    # Semantic Details
    requirement_coverage_score: float
    whole_doc_similarity_score: float
    responsibility_evidence: list[ResponsibilityEvidence]

    # Experience Details
    total_experience_years: float
    relevant_experience_years: float
    required_min_years: float | None
    required_max_years: float | None
    experience_verdict: str
    experience_gap_years: float

    # Qualification Details
    candidate_highest_level: str | None
    jd_min_required_level: str | None
    jd_preferred_level: str | None
    meets_preferred_qualification: bool

    # Title Details
    best_matching_title: str | None
    title_similarity: float
    used_summary_for_title: bool

    # Narrative Explanations (Zero LLM)
    summary: str
    strengths: list[str]
    gaps: list[str]
    reasons: list[FactorReason]

    # Extended Skill Separation & Display (Phase 4 A1, A6)
    matched_required: list[MatchedSkillItem] = field(default_factory=list)
    matched_preferred: list[MatchedSkillItem] = field(default_factory=list)
    partially_matched_required: list[MatchedSkillItem] = field(default_factory=list)
    partially_matched_preferred: list[MatchedSkillItem] = field(default_factory=list)
    matched_top: list[MatchedSkillItem] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert MatchResult to JSON-serializable dictionary."""
        return {
            "final_score": self.final_score,
            "uncapped_score": self.uncapped_score,
            "is_knockout_applied": self.is_knockout_applied,
            "knockout_reason": self.knockout_reason,
            "recommendation_band": self.recommendation_band,
            "scores": {
                "skill": self.skill_score,
                "semantic": self.semantic_score,
                "experience": self.experience_score,
                "qualification": self.qualification_score,
                "title": self.title_relevance_score,
            },
            "contributions": self.contributions,
            "weights": self.weights,
            "skills": {
                "core_required_coverage": round(self.core_required_coverage * 100, 1),
                "matched": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                        "is_required": m.is_required,
                    }
                    for m in self.matched_skills
                ],
                "matched_required": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                    }
                    for m in self.matched_required
                ],
                "matched_preferred": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                    }
                    for m in self.matched_preferred
                ],
                "matched_top": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                    }
                    for m in self.matched_top
                ],
                "partially_matched": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                        "is_required": m.is_required,
                    }
                    for m in self.partially_matched
                ],
                "partially_matched_required": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                    }
                    for m in self.partially_matched_required
                ],
                "partially_matched_preferred": [
                    {
                        "jd_skill": m.jd_skill,
                        "candidate_skill": m.candidate_skill,
                        "match_type": m.match_type,
                        "credit": m.credit,
                        "tier": m.tier,
                    }
                    for m in self.partially_matched_preferred
                ],
                "missing_required": self.missing_required_skills,
                "missing_preferred": self.missing_preferred_skills,
                "extra_relevant": self.extra_relevant_skills,
            },
            "semantic": {
                "requirement_coverage_score": self.requirement_coverage_score,
                "whole_doc_similarity_score": self.whole_doc_similarity_score,
                "top_evidence": [
                    {
                        "jd_duty": e.jd_duty,
                        "resume_snippet": e.resume_snippet,
                        "similarity": round(e.similarity, 2),
                    }
                    for e in self.responsibility_evidence
                ],
            },
            "experience": {
                "total_years": self.total_experience_years,
                "relevant_years": self.relevant_experience_years,
                "required_min": self.required_min_years,
                "required_max": self.required_max_years,
                "verdict": self.experience_verdict,
                "gap_years": self.experience_gap_years,
            },
            "qualification": {
                "candidate_highest": self.candidate_highest_level,
                "jd_required": self.jd_min_required_level,
                "jd_preferred": self.jd_preferred_level,
                "meets_preferred": self.meets_preferred_qualification,
            },
            "title": {
                "best_matching_title": self.best_matching_title,
                "similarity": self.title_similarity,
                "used_summary_fallback": self.used_summary_for_title,
            },
            "narrative": {
                "summary": self.summary,
                "strengths": self.strengths,
                "gaps": self.gaps,
                "reasons": [
                    {
                        "factor": r.factor,
                        "score": r.score,
                        "weight": r.weight,
                        "contribution": r.contribution,
                        "verdict": r.verdict,
                        "text": r.text,
                    }
                    for r in self.reasons
                ],
            },
        }


# ------------------------------------------------------------------
# Component 1: Skill Matching & Family Collapse
# ------------------------------------------------------------------

COLLAPSIBLE_FAMILIES: set[str] = {
    "AWS",
    "Amazon Web Services",
    "Azure",
    "Microsoft Azure",
    "GCP",
    "Google Cloud",
    "Google Cloud Platform",
    "Git",
    "CI/CD",
}


def collapse_jd_skill_families(
    jd_skills: list[str], taxonomy: SkillsTaxonomy
) -> list[str]:
    """
    Collapse skill families in JD requirements.

    Prunes child skills from JD requirements when their parent platform/infrastructure
    is also present (e.g., AWS + AWS S3 -> keep AWS, drop AWS S3; Git + GitHub -> keep Git).
    Crucially, programming language frameworks (Spring Boot, FastAPI, Django, React)
    are NEVER collapsed into their language parent because they represent independent
    core technical competencies that recruiters require separately.
    """
    skill_set = set(jd_skills)
    collapsed: list[str] = []

    for s in jd_skills:
        entry = taxonomy.get_entry(s)
        # Only collapse if parent is an infrastructure/tool platform in COLLAPSIBLE_FAMILIES
        # Never collapse core programming language frameworks
        if entry and entry.parent and entry.parent in skill_set and entry.parent in COLLAPSIBLE_FAMILIES:
            continue
        collapsed.append(s)

    return collapsed


def compute_skill_score(
    jd: ParsedJD,
    candidate: ParsedResume,
    taxonomy: SkillsTaxonomy,
    embed_service: EmbeddingService,
    config: ScoringWeights = SCORING,
) -> tuple[float, list[MatchedSkillItem], list[MatchedSkillItem], list[str], list[str], list[str], float]:
    """
    Calculate explainable skill score (0–100) using exact aliases, parent/child relationships,
    soft embedding similarities, and experience-inferred concepts for supporting/soft skills.

    Returns:
        (skill_score, matched_skills, partially_matched, missing_required, missing_preferred,
         extra_relevant, core_required_coverage)
    """
    # 1. Filter candidate skills: only strong or medium confidence
    cand_skill_entries = [
        s for s in candidate.skills if s.confidence in {"strong", "medium"}
    ]
    cand_skill_names = [s.name for s in cand_skill_entries]
    cand_skill_set = set(cand_skill_names)

    # 2. Collapse JD skill families (cloud/tool families only; never frameworks)
    req_skills = collapse_jd_skill_families(jd.required_skills, taxonomy)
    pref_skills = collapse_jd_skill_families(jd.preferred_skills, taxonomy)

    # Pre-embed candidate skills for soft matching
    cand_embeddings = (
        embed_service.embed(cand_skill_names) if cand_skill_names else np.empty((0, 384))
    )

    # Experience sentence snippets for inferring supporting/soft concepts (Fix A4)
    exp_snippets: list[str] = []
    for e in candidate.experience_entries:
        if not e.description:
            continue
        for line in e.description.split("\n"):
            line = line.strip(" -*•\t")
            if not line:
                continue
            for part in line.split(". "):
                part = part.strip().rstrip(".")
                if len(part) >= 15:
                    exp_snippets.append(part)
    exp_embeddings = (
        embed_service.embed(exp_snippets) if exp_snippets else np.empty((0, 384))
    )

    matched_skills: list[MatchedSkillItem] = []
    partially_matched: list[MatchedSkillItem] = []
    missing_required: list[str] = []
    missing_preferred: list[str] = []

    def evaluate_skill_list(
        target_skills: list[str], is_required: bool
    ) -> tuple[float, float, int, int]:
        total_weighted_credit = 0.0
        total_possible_weight = 0.0
        core_count = 0
        core_matched = 0

        # Pre-embed target skills in batch for fast cosine matching
        target_embeddings = (
            embed_service.embed(target_skills) if target_skills else np.empty((0, 384))
        )
        sim_matrix = (
            embed_service.cosine_matrix(target_embeddings, cand_embeddings)
            if target_embeddings.size > 0 and cand_embeddings.size > 0
            else np.empty((len(target_skills), len(cand_skill_names)))
        )

        for i, target in enumerate(target_skills):
            entry = taxonomy.get_entry(target)
            tier = entry.tier if entry else "core"

            # Tier weight
            if tier == "core":
                tier_w = config.tier_weight_core
                if is_required:
                    core_count += 1
            elif tier == "supporting":
                tier_w = config.tier_weight_supporting
            else:
                tier_w = config.tier_weight_soft

            total_possible_weight += tier_w

            best_credit = 0.0
            best_type = ""
            best_cand_skill = ""
            snippet_evidence = None

            # Check 1: Exact canonical or alias match
            if target in cand_skill_set:
                best_credit = config.credit_exact_or_alias
                best_type = "exact"
                best_cand_skill = target

            # Check 2: Child of required parent (JD wants AWS, candidate has AWS S3)
            if best_credit < config.credit_child_of_required_parent:
                for cs in cand_skill_entries:
                    cand_entry = taxonomy.get_entry(cs.name)
                    cand_parent = cs.parent or (cand_entry.parent if cand_entry else None)
                    if cand_parent and cand_parent.lower() == target.lower():
                        if config.credit_child_of_required_parent > best_credit:
                            best_credit = config.credit_child_of_required_parent
                            best_type = "child_of_parent"
                            best_cand_skill = cs.name

            # Check 3: Parent of required child (JD wants AWS S3, candidate has AWS)
            if best_credit < config.credit_parent_of_required_child:
                if entry and entry.parent and entry.parent in cand_skill_set:
                    if config.credit_parent_of_required_child > best_credit:
                        best_credit = config.credit_parent_of_required_child
                        best_type = "parent_of_child"
                        best_cand_skill = entry.parent

            # Check 4: Embedding-based semantic soft match (above threshold 0.62)
            # Only evaluate if no exact or hierarchical relationship matched
            if not best_type and best_credit < config.credit_semantic_soft_match_max and sim_matrix.size > 0:
                best_j = int(np.argmax(sim_matrix[i]))
                max_cos = float(sim_matrix[i, best_j])
                if max_cos >= config.skill_soft_match_threshold:
                    soft_credit = min(config.credit_semantic_soft_match_max, max_cos)
                    if soft_credit > best_credit:
                        best_credit = soft_credit
                        best_type = "semantic_soft"
                        best_cand_skill = cand_skill_names[best_j]

            # Check 5: Concept skills inferred credit (supporting / soft tier only) — Fix A4
            # Never infer for core tier skills (languages, frameworks, databases must be explicit)
            if (
                not best_type
                and best_credit < 0.40
                and tier in {"supporting", "soft"}
                and exp_embeddings.size > 0
            ):
                target_emb = target_embeddings[i:i+1] if target_embeddings.size > 0 else embed_service.embed_single(target)
                exp_sims = embed_service.cosine_matrix(target_emb, exp_embeddings)[0]
                best_snip_idx = int(np.argmax(exp_sims))
                best_snip_sim = float(exp_sims[best_snip_idx])
                if best_snip_sim >= config.inferred_concept_threshold:
                    inferred_credit = min(
                        config.inferred_concept_credit_max,
                        max(0.50, round(best_snip_sim, 2)),
                    )
                    if inferred_credit > best_credit:
                        best_credit = inferred_credit
                        best_type = "inferred_from_experience"
                        best_cand_skill = f"{target} (inferred)"
                        snippet_evidence = exp_snippets[best_snip_idx][:140]

            total_weighted_credit += best_credit * tier_w

            if is_required and tier == "core" and best_credit >= 0.50:
                core_matched += 1

            # Categorize into strictly disjoint lists (Fix A1)
            # Never count a skill twice (in both matched and partial)
            if best_credit >= 0.80:
                matched_skills.append(
                    MatchedSkillItem(
                        jd_skill=target,
                        candidate_skill=best_cand_skill,
                        match_type=best_type,
                        credit=round(best_credit, 2),
                        tier=tier,
                        is_required=is_required,
                        evidence_snippet=snippet_evidence,
                    )
                )
            elif best_credit >= 0.40:
                partially_matched.append(
                    MatchedSkillItem(
                        jd_skill=target,
                        candidate_skill=best_cand_skill,
                        match_type=best_type,
                        credit=round(best_credit, 2),
                        tier=tier,
                        is_required=is_required,
                        evidence_snippet=snippet_evidence,
                    )
                )
            else:
                if is_required:
                    missing_required.append(target)
                else:
                    missing_preferred.append(target)

        coverage = (
            (total_weighted_credit / total_possible_weight)
            if total_possible_weight > 0
            else 1.0
        )
        return coverage, total_weighted_credit, core_count, core_matched

    # Compute coverage for required and preferred
    req_cov, _, core_count, core_matched = evaluate_skill_list(req_skills, is_required=True)
    pref_cov, _, _, _ = evaluate_skill_list(pref_skills, is_required=False)

    core_required_coverage = (core_matched / core_count) if core_count > 0 else 1.0

    # Combine with 0.80 / 0.20 split (or 100% required if no preferred in JD)
    if pref_skills:
        skill_score = (
            config.skill_required_weight * (req_cov * 100.0)
            + config.skill_preferred_weight * (pref_cov * 100.0)
        )
    else:
        skill_score = req_cov * 100.0

    skill_score = round(max(0.0, min(100.0, skill_score)), 1)

    # Sort matched and partial lists for display (Fix A6):
    # Tier weight descending (core -> supporting -> soft), then credit descending, then name
    tier_order = {"core": 0, "supporting": 1, "soft": 2}
    matched_skills.sort(
        key=lambda m: (tier_order.get(m.tier, 9), -m.credit, m.jd_skill.lower())
    )
    partially_matched.sort(
        key=lambda m: (tier_order.get(m.tier, 9), -m.credit, m.jd_skill.lower())
    )

    # Extra relevant candidate skills (core skills not requested in JD)
    all_jd_skills = set(req_skills) | set(pref_skills)
    extra_relevant: list[str] = []
    for cs in cand_skill_entries:
        if cs.tier == "core" and cs.name not in all_jd_skills:
            # Check if cs wasn't already credited as child/parent
            if cs.name not in [m.candidate_skill for m in matched_skills]:
                extra_relevant.append(cs.name)
        if len(extra_relevant) >= config.max_extra_skills:
            break

    return (
        skill_score,
        matched_skills,
        partially_matched,
        missing_required,
        missing_preferred,
        extra_relevant,
        core_required_coverage,
    )


# ------------------------------------------------------------------
# Component 2: Semantic Similarity & Evidence Alignment
# ------------------------------------------------------------------

BOILERPLATE_DUTY_PREFIXES: tuple[str, ...] = (
    "we are looking",
    "about the role",
    "about our team",
    "about us",
    "about techsoft",
    "the ideal candidate",
    "role overview",
    "who you are",
    "company:",
    "location:",
    "employment type:",
    "what we offer",
    "benefits:",
)


@functools.lru_cache(maxsize=2048)
def _is_real_duty_sentence(text: str) -> bool:
    """
    Validate that a sentence is an actionable job duty, not boilerplate introductory prose.
    Must have >= 6 words, not start with boilerplate greetings/company intros, and contain a verb.
    """
    s = text.strip()
    words = s.split()
    if len(words) < 6:
        return False
    lower = s.lower()
    if any(lower.startswith(prefix) for prefix in BOILERPLATE_DUTY_PREFIXES):
        return False
    try:
        from app.services.jd_parser import _get_nlp
        nlp = _get_nlp()
        doc = nlp(s[:250])
        return any(token.pos_ in {"VERB", "AUX"} for token in doc)
    except Exception:
        return True


def compute_semantic_score(
    jd: ParsedJD,
    candidate: ParsedResume,
    embed_service: EmbeddingService,
    config: ScoringWeights = SCORING,
) -> tuple[float, float, float, list[ResponsibilityEvidence]]:
    """
    Calculate semantic similarity (0–100) using:
      1. Requirement-unit coverage (max cosine across resume chunks per filtered JD duty)
      2. Whole-document similarity (mean-pooled embeddings)
      3. Evidence snippet extraction for top JD responsibilities

    Returns:
        (semantic_score, req_coverage_score, whole_doc_score, top_evidence)
    """
    # 1. Build JD requirement units (filtered to genuine duty sentences; drop boilerplate)
    jd_units: list[str] = []
    for resp in jd.responsibilities:
        if resp.strip() and _is_real_duty_sentence(resp):
            jd_units.append(resp.strip())

    for skill, ev in jd.skill_evidence.items():
        sent = ev.get("sentence", "").strip()
        if sent and sent not in jd_units and _is_real_duty_sentence(sent):
            jd_units.append(sent)

    if not jd_units:
        # Fallback if no duties passed filter
        for resp in jd.responsibilities:
            if resp.strip():
                jd_units.append(resp.strip())
        if not jd_units:
            jd_units = [jd.title or "Software Professional"]

    # 2. Build resume chunks
    resume_chunks: list[str] = []
    if candidate.summary:
        resume_chunks.append(candidate.summary.strip())

    for e in candidate.experience_entries:
        if e.description:
            resume_chunks.append(e.description.strip())
        elif e.title:
            resume_chunks.append(f"{e.title} at {e.company}")

    proj_text = candidate.sections.get("projects", "").strip()
    if proj_text:
        resume_chunks.append(proj_text)

    # Add core skills summary chunk
    core_skills = [s.name for s in candidate.skills if s.tier == "core"]
    if core_skills:
        resume_chunks.append("Key skills: " + ", ".join(core_skills))

    if not resume_chunks:
        resume_chunks = [candidate.name or "Candidate"]

    # 3. Batch encode units and chunks
    unit_embeddings = embed_service.embed(jd_units)
    chunk_embeddings = embed_service.embed(resume_chunks)

    # 4. Requirement coverage: for each unit, take max cosine across chunks
    sim_matrix = embed_service.cosine_matrix(unit_embeddings, chunk_embeddings)
    max_sims_per_unit = np.max(sim_matrix, axis=1)
    mean_unit_cos = float(np.mean(max_sims_per_unit))
    req_coverage_score = calibrate_cosine(
        mean_unit_cos, config.semantic_raw_cos_low, config.semantic_raw_cos_high
    )

    # 5. Whole-document similarity: mean-pooled embeddings
    jd_pooled = np.mean(unit_embeddings, axis=0, keepdims=True)
    cand_pooled = np.mean(chunk_embeddings, axis=0, keepdims=True)
    whole_doc_cos = embed_service.cosine_similarity(jd_pooled, cand_pooled)
    whole_doc_score = calibrate_cosine(
        whole_doc_cos, config.semantic_raw_cos_low, config.semantic_raw_cos_high
    )

    # Blend 60% requirement coverage + 40% whole-document similarity
    semantic_score = (
        config.semantic_blend_req_coverage * req_coverage_score
        + config.semantic_blend_whole_doc * whole_doc_score
    )
    semantic_score = round(max(0.0, min(100.0, semantic_score)), 1)

    # 6. Extract top evidence for JD responsibilities
    top_evidence: list[ResponsibilityEvidence] = []
    for r_idx, resp in enumerate(jd.responsibilities[: config.top_responsibility_evidence_count]):
        if r_idx < len(jd_units):
            best_chunk_idx = int(np.argmax(sim_matrix[r_idx]))
            best_chunk_sim = float(sim_matrix[r_idx, best_chunk_idx])
            snippet = resume_chunks[best_chunk_idx]
            # Truncate snippet cleanly
            if len(snippet) > 160:
                snippet = snippet[:157] + "..."
            top_evidence.append(
                ResponsibilityEvidence(
                    jd_duty=resp,
                    resume_snippet=snippet,
                    similarity=best_chunk_sim,
                )
            )

    return semantic_score, round(req_coverage_score, 1), round(whole_doc_score, 1), top_evidence


# ------------------------------------------------------------------
# Component 3: Experience Evaluation & Relevant Experience
# ------------------------------------------------------------------

def compute_experience_score(
    jd: ParsedJD,
    candidate: ParsedResume,
    embed_service: EmbeddingService,
    config: ScoringWeights = SCORING,
    taxonomy: SkillsTaxonomy | None = None,
) -> tuple[float, float, float, str, float]:
    """
    Calculate experience match score (0–100) using:
      - Domain-relevant experience duration (generic tools excluded from domain count)
      - Proportional credit against min requirement
      - Cap / floor for over-qualification
      - Internship discounting at 50%

    Returns:
        (experience_score, total_years, relevant_years, verdict, gap_years)
    """
    tax = taxonomy or get_taxonomy()
    total_years = candidate.total_experience_years + (
        (candidate.internship_months / 12.0) * config.internship_credit_factor
    )

    jd_text = (jd.title or "") + " " + " ".join(jd.required_skills)

    # Configure generic skills set for this JD (Fix A2)
    # Python is treated as a generic scripting tool unless the JD explicitly targets a pure Python developer
    # (for AI/ML roles, true domain core skills are ML frameworks like PyTorch, TensorFlow, Deep Learning)
    generic = set(config.generic_skills)
    is_pure_python_dev = "python" in (jd.title or "").lower() and not any(
        kw in (jd.title or "").lower() for kw in ["ai", "ml", "machine learning", "deep learning", "data science"]
    )
    if not is_pure_python_dev:
        generic.add("Python")
    else:
        generic.discard("Python")

    # Domain core JD skills: required skills that are core tier and NOT generic (Fix A2)
    domain_jd_core_skills: set[str] = set()
    for s in jd.required_skills:
        entry = tax.get_entry(s)
        tier = entry.tier if entry else "core"
        if tier == "core" and s not in generic:
            domain_jd_core_skills.add(s)

    relevant_intervals: list[tuple[int, int]] = []
    relevant_internship_months = 0

    for e in candidate.experience_entries:
        if not e.start_date:
            continue

        try:
            s_yr, s_mo = [int(p) for p in e.start_date.split("-")]
            if e.end_date == "Present" or not e.end_date:
                e_yr, e_mo = (2026, 11)
            else:
                e_yr, e_mo = [int(p) for p in e.end_date.split("-")]
        except Exception:
            continue

        start_idx = s_yr * 12 + s_mo
        end_idx = e_yr * 12 + e_mo
        if end_idx < start_idx:
            continue

        # Check relevance
        entry_text = f"{e.title} {e.company}\n{e.description}"
        sim = embed_service.cosine_similarity(
            embed_service.embed_single(entry_text),
            embed_service.embed_single(jd_text),
        )

        if not domain_jd_core_skills:
            # Fallback when JD has no specific domain core skills (e.g. minimal test JD)
            is_relevant = sim >= config.exp_relevance_threshold
        else:
            # Rule A2: An entry is relevant if it has >= 2 DOMAIN core JD skills, OR
            # (semantic similarity >= threshold AND >= 1 domain core skill).
            domain_overlap = len(set(e.skills_in_entry) & domain_jd_core_skills)
            is_relevant = (domain_overlap >= config.exp_min_core_skills_for_relevance) or (
                sim >= config.exp_relevance_threshold and domain_overlap >= 1
            )

        if is_relevant:
            if e.is_internship:
                relevant_internship_months += (end_idx - start_idx + 1)
            else:
                relevant_intervals.append((start_idx, end_idx))

    merged_relevant_months = _merge_date_intervals(relevant_intervals)
    relevant_years = round(
        (merged_relevant_months / 12.0)
        + ((relevant_internship_months / 12.0) * config.internship_credit_factor),
        1,
    )
    # Relevant years cannot exceed total career years
    relevant_years = min(total_years, relevant_years)

    # Scoring helper
    min_req = jd.min_experience_years
    max_req = jd.max_experience_years

    def score_years(y: float) -> float:
        if min_req is None or min_req == 0.0:
            return 100.0
        if y >= min_req:
            # Check over-qualification (> 50% above max)
            if max_req and y > (1.5 * max_req):
                return config.exp_over_qualification_floor
            return 100.0
        # Proportional if below
        return min(100.0, (y / min_req) * 100.0)

    score_rel = score_years(relevant_years)
    score_tot = score_years(total_years)

    exp_score = config.exp_blend_relevant * score_rel + config.exp_blend_total * score_tot
    exp_score = round(max(0.0, min(100.0, exp_score)), 1)

    # Verdict
    gap_years = 0.0
    if min_req is not None:
        if relevant_years >= min_req:
            if max_req and relevant_years > max_req:
                verdict = "above requirement range"
            else:
                verdict = "meets requirement"
        else:
            gap_years = round(min_req - relevant_years, 1)
            verdict = "below requirement"
    else:
        verdict = "meets requirement (no minimum specified)"

    return exp_score, round(total_years, 1), relevant_years, verdict, gap_years


# ------------------------------------------------------------------
# Component 4: Qualification & Degree Matching
# ------------------------------------------------------------------

def compute_qualification_score(
    jd: ParsedJD,
    candidate: ParsedResume,
    config: ScoringWeights = SCORING,
) -> tuple[float, str | None, str | None, str | None, bool]:
    """
    Calculate qualification score (0–100) comparing candidate highest education level
    against the JD's minimum required and preferred degree levels.

    Returns:
        (qualification_score, cand_highest, jd_min_required, jd_preferred, meets_preferred)
    """
    jd_min_level = jd.min_required_level
    jd_pref_level = jd.preferred_level

    # Determine highest candidate level
    cand_levels = [e.level.lower() for e in candidate.education if e.level]
    highest_cand_level = None
    highest_cand_rank = 0

    for lvl in cand_levels:
        rank = config.qual_ranks.get(lvl, 0)
        if rank > highest_cand_rank:
            highest_cand_rank = rank
            highest_cand_level = lvl

    meets_preferred = False
    if jd_pref_level:
        pref_rank = config.qual_ranks.get(jd_pref_level.lower(), 0)
        meets_preferred = highest_cand_rank >= pref_rank

    # No requirement in JD
    if not jd_min_level:
        return config.qual_score_no_requirement, highest_cand_level, None, jd_pref_level, meets_preferred

    # Requirement exists but no degree detected in candidate resume
    if not highest_cand_level or highest_cand_rank == 0:
        return config.qual_score_none_detected, None, jd_min_level, jd_pref_level, False

    req_rank = config.qual_ranks.get(jd_min_level.lower(), 2)

    if highest_cand_rank >= req_rank:
        qual_score = config.qual_score_meets
    elif highest_cand_rank == req_rank - 1:
        qual_score = config.qual_score_one_below
    else:
        qual_score = config.qual_score_two_below

    return qual_score, highest_cand_level, jd_min_level, jd_pref_level, meets_preferred


# ------------------------------------------------------------------
# Component 5: Title Relevance Matching
# ------------------------------------------------------------------

def normalize_title(title: str, seniority_tokens: frozenset[str] | set[str] | None = None) -> str:
    """
    Normalize job title by removing seniority prefixes/suffixes and punctuation (Fix A3).
    Allows true domain semantic comparison (e.g. 'Frontend Developer' vs 'Backend Developer')
    without artificial score inflation from shared generic seniority tokens ('Senior', 'Lead').
    """
    if not title:
        return ""
    # Lowercase and replace non-alphanumeric chars with space
    t = re.sub(r"[^\w\s]", " ", title.lower())
    tokens = seniority_tokens or SCORING.seniority_tokens
    words = [w for w in t.split() if w not in tokens]
    return " ".join(words).strip() or title.strip()


def compute_title_relevance_score(
    jd: ParsedJD,
    candidate: ParsedResume,
    embed_service: EmbeddingService,
    config: ScoringWeights = SCORING,
) -> tuple[float, str | None, float, bool]:
    """
    Calculate past title relevance score (0–100) against the JD role title.
    Normalizes seniority prefixes/suffixes and punctuation before embedding (Fix A3).
    Falls back to summary / projects similarity if candidate has no past job titles.

    Returns:
        (title_score, best_matching_title, raw_similarity, used_summary_fallback)
    """
    jd_raw_title = jd.title or "Software Professional"
    jd_norm_title = normalize_title(jd_raw_title, config.seniority_tokens)
    jd_emb = embed_service.embed_single(jd_norm_title)

    if candidate.job_titles:
        cand_norm_titles = [
            normalize_title(t, config.seniority_tokens) for t in candidate.job_titles
        ]
        title_embs = embed_service.embed(cand_norm_titles)
        sims = [embed_service.cosine_similarity(jd_emb, t) for t in title_embs]
        best_idx = int(np.argmax(sims))
        best_title = candidate.job_titles[best_idx]
        best_sim = float(sims[best_idx])
        used_summary = False
    else:
        # Fallback to candidate summary or projects
        fallback_text = candidate.summary or "Computer Science Graduate"
        fallback_norm = normalize_title(fallback_text, config.seniority_tokens)
        fallback_emb = embed_service.embed_single(fallback_norm)
        best_sim = embed_service.cosine_similarity(jd_emb, fallback_emb)
        best_title = "Inferred from summary"
        used_summary = True

    title_score = calibrate_cosine(
        best_sim, config.title_raw_cos_low, config.title_raw_cos_high
    )
    title_score = round(max(0.0, min(100.0, title_score)), 1)

    return title_score, best_title, round(best_sim, 2), used_summary


# ------------------------------------------------------------------
# Component 6 & 7: Explanations & Narrative Synthesis
# ------------------------------------------------------------------

def generate_reasons_and_narrative(
    skill_score: float,
    semantic_score: float,
    experience_score: float,
    qualification_score: float,
    title_score: float,
    matched_required: list[MatchedSkillItem],
    missing_required: list[str],
    core_req_coverage: float,
    total_years: float,
    relevant_years: float,
    jd: ParsedJD,
    cand_level: str | None,
    best_title: str | None,
    top_evidence: list[ResponsibilityEvidence],
    config: ScoringWeights = SCORING,
    taxonomy: SkillsTaxonomy | None = None,
) -> tuple[list[FactorReason], str, list[str], list[str]]:
    """
    Generate deterministic, specific, plain-English explanations for every factor (Fix A1, A5).
    Zero LLM dependencies.
    """
    tax = taxonomy or get_taxonomy()
    reasons: list[FactorReason] = []
    strengths: list[str] = []
    gaps: list[str] = []

    # 1. Skill Reason (counts REQUIRED skills only; Fix A1)
    req_skills_collapsed = collapse_jd_skill_families(jd.required_skills, tax)
    req_total = len(req_skills_collapsed)
    cov_pct = int(round(core_req_coverage * 100))

    # Top matched required skills
    top_matched_names = [m.jd_skill for m in matched_required[:4]]

    # Gaps: order by core tier first, then supporting/soft (Fix A5)
    missing_core = [
        s for s in missing_required
        if (tax.get_entry(s).tier if tax.get_entry(s) else "core") == "core"
    ]
    missing_other = [s for s in missing_required if s not in missing_core]
    ordered_missing = missing_core + missing_other
    top_missing_names = ordered_missing[:3]

    skill_verdict = "strong" if skill_score >= 70 else ("ok" if skill_score >= 45 else "weak")

    matched_count = len(matched_required)
    if matched_count > 0 and top_matched_names:
        matched_txt = f", including {', '.join(top_matched_names)}"
    else:
        matched_txt = ""

    missing_txt = (
        f"Missing: {', '.join(top_missing_names)}."
        if top_missing_names
        else "All required skills met."
    )

    if matched_count == 0:
        skill_text = f"0 of {req_total} required skills verified (0%). {missing_txt}"
    else:
        skill_text = (
            f"Covers {matched_count} of {req_total} required skills ({cov_pct}%)"
            f"{matched_txt}. {missing_txt}"
        )

    reasons.append(
        FactorReason(
            factor="skill",
            score=skill_score,
            weight=config.w_skill,
            contribution=round(skill_score * config.w_skill, 1),
            verdict=skill_verdict,
            text=skill_text,
        )
    )

    if skill_score >= 70:
        strengths.append(f"Strong required skill coverage ({cov_pct}% of core skills verified)")
    elif ordered_missing:
        gaps.append(f"Lacks key required skills: {', '.join(ordered_missing[:3])}")

    # 2. Semantic Reason
    sem_verdict = "strong" if semantic_score >= 70 else ("ok" if semantic_score >= 45 else "weak")
    if top_evidence:
        top_e = top_evidence[0]
        sem_text = (
            f"Strongest semantic alignment ({int(top_e.similarity*100)}%): "
            f"JD duty '{top_e.jd_duty[:45]}...' aligns with resume experience."
        )
    else:
        sem_text = f"Overall semantic alignment across resume sections scored {semantic_score:.1f}%."

    reasons.append(
        FactorReason(
            factor="semantic",
            score=semantic_score,
            weight=config.w_semantic,
            contribution=round(semantic_score * config.w_semantic, 1),
            verdict=sem_verdict,
            text=sem_text,
        )
    )

    if semantic_score >= 75:
        strengths.append("High contextual and responsibility similarity to the job role")
    elif semantic_score < 45:
        gaps.append("Low contextual alignment between past projects and target responsibilities")

    # 3. Experience Reason
    exp_verdict = "strong" if experience_score >= 80 else ("ok" if experience_score >= 50 else "weak")
    min_exp = jd.min_experience_years or 0
    max_exp_str = f"-{jd.max_experience_years}" if jd.max_experience_years else "+"
    if relevant_years >= min_exp:
        exp_text = (
            f"{total_years:.1f} years total ({relevant_years:.1f} relevant) vs "
            f"{min_exp}{max_exp_str} years required: meets role experience criteria."
        )
    else:
        gap = round(min_exp - relevant_years, 1)
        exp_text = (
            f"{total_years:.1f} years total, but only {relevant_years:.1f} directly relevant "
            f"(needs {min_exp:.1f}+ years, gap of {gap:.1f} years)."
        )

    reasons.append(
        FactorReason(
            factor="experience",
            score=experience_score,
            weight=config.w_experience,
            contribution=round(experience_score * config.w_experience, 1),
            verdict=exp_verdict,
            text=exp_text,
        )
    )

    if experience_score >= 85:
        strengths.append(f"Substantial relevant experience ({relevant_years:.1f} yrs)")
    elif relevant_years < min_exp:
        gaps.append(f"Experience shortfall of {round(min_exp - relevant_years, 1):.1f} years")

    # 4. Qualification Reason
    qual_verdict = "strong" if qualification_score >= 80 else ("ok" if qualification_score >= 50 else "weak")
    jd_req_lvl = jd.min_required_level or "any"
    cand_lvl_str = cand_level or "none detected"
    if qualification_score >= 100:
        qual_text = f"Degree ({cand_lvl_str}) meets or exceeds the required level ({jd_req_lvl})."
    elif qualification_score >= 50:
        qual_text = f"Degree ({cand_lvl_str}) is one level below the preferred requirement ({jd_req_lvl})."
    else:
        qual_text = f"Degree level ({cand_lvl_str}) falls significantly short of required {jd_req_lvl}."

    reasons.append(
        FactorReason(
            factor="qualification",
            score=qualification_score,
            weight=config.w_qualification,
            contribution=round(qualification_score * config.w_qualification, 1),
            verdict=qual_verdict,
            text=qual_text,
        )
    )

    # 5. Title Reason
    title_verdict = "strong" if title_score >= 70 else ("ok" if title_score >= 45 else "weak")
    title_text = f"Past role '{best_title or 'N/A'}' evaluates to a {title_score:.0f}% relevance match with '{jd.title}'."

    reasons.append(
        FactorReason(
            factor="title",
            score=title_score,
            weight=config.w_title,
            contribution=round(title_score * config.w_title, 1),
            verdict=title_verdict,
            text=title_text,
        )
    )

    # Synthesis summary
    summary = (
        f"Candidate demonstrated {skill_verdict} technical alignment with {cov_pct}% core skill coverage. "
        f"{exp_text} Overall profile presents a {sem_verdict} semantic foundation."
    )

    return reasons, summary, strengths[:4], gaps[:4]


# ------------------------------------------------------------------
# Main Orchestrator: match() and rank()
# ------------------------------------------------------------------

def match(
    jd: ParsedJD,
    candidate: ParsedResume,
    taxonomy: SkillsTaxonomy | None = None,
    embed_service: EmbeddingService | None = None,
    config: ScoringWeights = SCORING,
) -> MatchResult:
    """
    Orchestrate full candidate-to-JD matching and return complete explainable MatchResult.
    Pure functional evaluation: zero database or external side-effects.
    """
    tax = taxonomy or get_taxonomy()
    emb = embed_service or get_embedding_service()

    # 1. Compute component scores
    (
        skill_score,
        matched_skills,
        partially_matched,
        missing_req,
        missing_pref,
        extra_relevant,
        core_req_coverage,
    ) = compute_skill_score(jd, candidate, tax, emb, config)

    # Separate required vs preferred matched/partial lists (Fix A1)
    matched_required = [m for m in matched_skills if m.is_required]
    matched_preferred = [m for m in matched_skills if not m.is_required]
    partially_matched_required = [m for m in partially_matched if m.is_required]
    partially_matched_preferred = [m for m in partially_matched if not m.is_required]
    matched_top = matched_skills[:6]

    (
        sem_score,
        req_cov_score,
        whole_doc_score,
        top_evidence,
    ) = compute_semantic_score(jd, candidate, emb, config)

    (
        exp_score,
        tot_years,
        rel_years,
        exp_verdict,
        gap_years,
    ) = compute_experience_score(jd, candidate, emb, config, taxonomy=tax)

    (
        qual_score,
        cand_level,
        jd_req_lvl,
        jd_pref_lvl,
        meets_preferred,
    ) = compute_qualification_score(jd, candidate, config)

    (
        title_score,
        best_title,
        title_sim,
        used_summary_title,
    ) = compute_title_relevance_score(jd, candidate, emb, config)

    # 2. Compute final weighted score
    contributions = {
        "skill": round(skill_score * config.w_skill, 1),
        "semantic": round(sem_score * config.w_semantic, 1),
        "experience": round(exp_score * config.w_experience, 1),
        "qualification": round(qual_score * config.w_qualification, 1),
        "title": round(title_score * config.w_title, 1),
    }
    weights = {
        "skill": config.w_skill,
        "semantic": config.w_semantic,
        "experience": config.w_experience,
        "qualification": config.w_qualification,
        "title": config.w_title,
    }

    uncapped_score = round(sum(contributions.values()), 1)

    # 3. Knockout safeguard check
    is_knockout = False
    knockout_reason = None
    final_score = uncapped_score

    if core_req_coverage < config.knockout_core_coverage_threshold:
        if final_score > config.knockout_score_cap:
            is_knockout = True
            knockout_reason = (
                f"Core required skill coverage is only {round(core_req_coverage*100, 1)}% "
                f"(< {int(config.knockout_core_coverage_threshold*100)}%); "
                f"final score capped at {int(config.knockout_score_cap)} to prevent domain mismatch."
            )
            final_score = config.knockout_score_cap

    # 4. Recommendation Band
    if final_score >= config.band_strong:
        band = "Strong match"
    elif final_score >= config.band_good:
        band = "Good match"
    elif final_score >= config.band_partial:
        band = "Partial match"
    else:
        band = "Weak match"

    # 5. Narrative explanations (uses strictly matched_required; Fix A1)
    reasons, narrative_summary, strengths, gaps = generate_reasons_and_narrative(
        skill_score=skill_score,
        semantic_score=sem_score,
        experience_score=exp_score,
        qualification_score=qual_score,
        title_score=title_score,
        matched_required=matched_required,
        missing_required=missing_req,
        core_req_coverage=core_req_coverage,
        total_years=tot_years,
        relevant_years=rel_years,
        jd=jd,
        cand_level=cand_level,
        best_title=best_title,
        top_evidence=top_evidence,
        config=config,
        taxonomy=tax,
    )

    if is_knockout and knockout_reason:
        gaps.insert(0, knockout_reason)

    return MatchResult(
        final_score=final_score,
        uncapped_score=uncapped_score,
        is_knockout_applied=is_knockout,
        knockout_reason=knockout_reason,
        recommendation_band=band,
        skill_score=skill_score,
        semantic_score=sem_score,
        experience_score=exp_score,
        qualification_score=qual_score,
        title_relevance_score=title_score,
        contributions=contributions,
        weights=weights,
        matched_skills=matched_skills,
        partially_matched=partially_matched,
        missing_required_skills=missing_req,
        missing_preferred_skills=missing_pref,
        extra_relevant_skills=extra_relevant,
        core_required_coverage=core_req_coverage,
        matched_required=matched_required,
        matched_preferred=matched_preferred,
        partially_matched_required=partially_matched_required,
        partially_matched_preferred=partially_matched_preferred,
        matched_top=matched_top,
        requirement_coverage_score=req_cov_score,
        whole_doc_similarity_score=whole_doc_score,
        responsibility_evidence=top_evidence,
        total_experience_years=tot_years,
        relevant_experience_years=rel_years,
        required_min_years=jd.min_experience_years,
        required_max_years=jd.max_experience_years,
        experience_verdict=exp_verdict,
        experience_gap_years=gap_years,
        candidate_highest_level=cand_level,
        jd_min_required_level=jd_req_lvl,
        jd_preferred_level=jd_pref_lvl,
        meets_preferred_qualification=meets_preferred,
        best_matching_title=best_title,
        title_similarity=title_sim,
        used_summary_for_title=used_summary_title,
        summary=narrative_summary,
        strengths=strengths,
        gaps=gaps,
        reasons=reasons,
    )


def rank(
    jd: ParsedJD,
    candidates: list[ParsedResume],
    taxonomy: SkillsTaxonomy | None = None,
    embed_service: EmbeddingService | None = None,
    config: ScoringWeights = SCORING,
) -> list[tuple[ParsedResume, MatchResult]]:
    """
    Score and rank a collection of candidates against a job description.
    Sorts descending by final_score, tie-breaking by core required skill coverage,
    then relevant experience years.
    """
    tax = taxonomy or get_taxonomy()
    emb = embed_service or get_embedding_service()

    results: list[tuple[ParsedResume, MatchResult]] = []
    for cand in candidates:
        match_res = match(jd, cand, taxonomy=tax, embed_service=emb, config=config)
        results.append((cand, match_res))

    # Deterministic tie-breaking sort
    results.sort(
        key=lambda pair: (
            pair[1].final_score,
            pair[1].core_required_coverage,
            pair[1].relevant_experience_years,
        ),
        reverse=True,
    )
    return results
