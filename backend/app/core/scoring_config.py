"""
core/scoring_config.py — Scoring-weight configuration.

All weights that control the final match score live here in a single,
frozen dataclass.  This makes them:
  • easy to find and explain in an interview,
  • importable from any module (`from app.core.scoring_config import SCORING`),
  • safe from accidental mutation at runtime.

Formula:
    final_score = w_skill      * skill_score
                + w_semantic   * semantic_score
                + w_experience * experience_score
                + w_qualification * qualification_score
                + w_title      * title_relevance_score

Each component score is 0–100.  The final score is therefore also 0–100.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class ScoringWeights:
    """Frozen container for all scoring weights and thresholds."""

    # ── Component weights (must sum to 1.0) ──
    w_skill: float = 0.40
    w_semantic: float = 0.25
    w_experience: float = 0.20
    w_qualification: float = 0.10
    w_title: float = 0.05

    # ── Skill matching ──
    # Cosine-similarity threshold for embedding-based soft skill matching.
    skill_soft_match_threshold: float = 0.75
    # Weight multiplier for required vs preferred skills.
    required_skill_weight: float = 1.0
    preferred_skill_weight: float = 0.5

    # ── Experience ──
    # Maximum bonus (percentage points) for over-qualified candidates.
    experience_overqualification_cap: float = 5.0

    # ── Semantic ──
    # Embedding model identifier (Hugging Face hub).
    embedding_model: str = "all-MiniLM-L6-v2"

    def validate(self) -> None:
        """Raise ValueError if weights do not sum to 1.0 (within tolerance)."""
        total = (
            self.w_skill
            + self.w_semantic
            + self.w_experience
            + self.w_qualification
            + self.w_title
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(
                f"Scoring weights must sum to 1.0, got {total:.6f}"
            )


# ── Singleton ──
SCORING = ScoringWeights()
SCORING.validate()   # Fail fast if weights are misconfigured
