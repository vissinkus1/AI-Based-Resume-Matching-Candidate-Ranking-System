"""
core/scoring_config.py — Central Scoring Weights & Thresholds Configuration.

All weights, thresholds, calibration bounds, and credit tables that control
the candidate ranking and matching engine live here in a single frozen dataclass.
Zero magic numbers in matching code.

Formula:
    final_score = w_skill         * skill_score
                + w_semantic      * semantic_score
                + w_experience    * experience_score
                + w_qualification * qualification_score
                + w_title         * title_relevance_score
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ScoringWeights:
    """Frozen container for all candidate ranking weights, thresholds, and parameters."""

    # ------------------------------------------------------------------
    # 1. Component Weights (must sum to 1.0)
    # ------------------------------------------------------------------
    w_skill: float = 0.40
    w_semantic: float = 0.25
    w_experience: float = 0.20
    w_qualification: float = 0.10
    w_title: float = 0.05

    # ------------------------------------------------------------------
    # 2. Skill Component Parameters
    # ------------------------------------------------------------------
    # Split between required and preferred skills
    skill_required_weight: float = 0.80
    skill_preferred_weight: float = 0.20

    # Skill tier weights
    tier_weight_core: float = 1.0
    tier_weight_supporting: float = 0.6
    tier_weight_soft: float = 0.3

    # Section confidence multipliers
    confidence_mult_strong: float = 1.0     # Explicit skills / experience section
    confidence_mult_medium: float = 0.85    # Projects section
    confidence_mult_basic: float = 0.70     # Other sections / mentions

    # Credit table for skill match types
    credit_exact_or_alias: float = 1.0              # Exact name or curated alias match
    credit_child_of_required_parent: float = 0.9    # JD wants AWS, candidate has AWS S3
    credit_parent_of_required_child: float = 0.6    # JD wants AWS S3, candidate only has AWS
    credit_semantic_soft_match_max: float = 0.70    # Max credit for embedding soft-match

    # Cosine similarity threshold for embedding soft-matching of skill names
    skill_soft_match_threshold: float = 0.62

    # Maximum number of extra relevant candidate skills to report
    max_extra_skills: int = 8

    # ------------------------------------------------------------------
    # 3. Semantic Similarity Parameters
    # ------------------------------------------------------------------
    # Embedding model identifier
    embedding_model: str = "all-MiniLM-L6-v2"

    # Calibration bounds for raw cosine similarity to 0-100 rescale
    semantic_raw_cos_low: float = 0.15
    semantic_raw_cos_high: float = 0.65

    # Blend between requirement-unit coverage and whole-document similarity
    semantic_blend_req_coverage: float = 0.60
    semantic_blend_whole_doc: float = 0.40

    # Number of top responsibility evidence pairs to highlight
    top_responsibility_evidence_count: int = 3

    # ------------------------------------------------------------------
    # 4. Experience Parameters
    # ------------------------------------------------------------------
    # Cosine similarity threshold for an experience entry to be deemed relevant to JD
    exp_relevance_threshold: float = 0.35

    # Minimum number of JD core skills in an entry to automatically mark it relevant
    exp_min_core_skills_for_relevance: int = 2

    # Blend between relevant experience score and total experience score
    exp_blend_relevant: float = 0.70
    exp_blend_total: float = 0.30

    # Floor score for over-qualified candidates (>50% above max requirement)
    exp_over_qualification_floor: float = 90.0

    # Credit factor for internships toward experience
    internship_credit_factor: float = 0.50

    # ------------------------------------------------------------------
    # 5. Qualification Parameters
    # ------------------------------------------------------------------
    qual_ranks: dict[str, int] = field(
        default_factory=lambda: {
            "diploma": 1,
            "bachelor": 2,
            "master": 3,
            "phd": 4,
        }
    )
    qual_score_meets: float = 100.0          # Meets or exceeds required level
    qual_score_one_below: float = 50.0       # One level below required
    qual_score_two_below: float = 20.0       # Two or more levels below required
    qual_score_none_detected: float = 30.0   # Degree required but none detected
    qual_score_no_requirement: float = 100.0 # No degree required by JD

    # ------------------------------------------------------------------
    # 6. Title Relevance Parameters
    # ------------------------------------------------------------------
    title_raw_cos_low: float = 0.15
    title_raw_cos_high: float = 0.65

    # ------------------------------------------------------------------
    # 7. Knockout & Safeguards
    # ------------------------------------------------------------------
    # If core required skill coverage is below this threshold, score is capped
    knockout_core_coverage_threshold: float = 0.25
    knockout_score_cap: float = 35.0

    # ------------------------------------------------------------------
    # 8. Recommendation Bands
    # ------------------------------------------------------------------
    band_strong: float = 75.0     # >= 75: "Strong match"
    band_good: float = 60.0       # 60 - 74: "Good match"
    band_partial: float = 40.0    # 40 - 59: "Partial match"
                                  # < 40: "Weak match"

    def __post_init__(self) -> None:
        """Validate mathematical integrity of all weight distributions."""
        total_weights = (
            self.w_skill
            + self.w_semantic
            + self.w_experience
            + self.w_qualification
            + self.w_title
        )
        if abs(total_weights - 1.0) > 1e-6:
            raise ValueError(
                f"Component weights must sum to 1.0, got {total_weights:.4f}"
            )

        skill_split = self.skill_required_weight + self.skill_preferred_weight
        if abs(skill_split - 1.0) > 1e-6:
            raise ValueError(
                f"Skill split weights must sum to 1.0, got {skill_split:.4f}"
            )

        sem_split = self.semantic_blend_req_coverage + self.semantic_blend_whole_doc
        if abs(sem_split - 1.0) > 1e-6:
            raise ValueError(
                f"Semantic blend weights must sum to 1.0, got {sem_split:.4f}"
            )

        exp_split = self.exp_blend_relevant + self.exp_blend_total
        if abs(exp_split - 1.0) > 1e-6:
            raise ValueError(
                f"Experience blend weights must sum to 1.0, got {exp_split:.4f}"
            )

    def validate(self) -> None:
        """Explicit validation method (backward compatible)."""
        self.__post_init__()


# Global singleton instance
SCORING = ScoringWeights()
