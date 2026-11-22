"""
services/skills_taxonomy.py — Skills taxonomy loader and lookup service.

Loads the curated skills taxonomy from JSON and builds fast lookup
structures for skill extraction.  Used by JD parser (Phase 1),
resume parser (Phase 2), and the matching engine (Phase 3).

Public API:
    get_taxonomy()           -> SkillsTaxonomy (singleton)
    taxonomy.find(text)      -> canonical name or None
    taxonomy.all_phrases()   -> list of all matchable phrases
"""

import json
from dataclasses import dataclass, field
from pathlib import Path


# Path to the taxonomy JSON file (relative to this module)
_TAXONOMY_PATH = Path(__file__).resolve().parent.parent / "data" / "skills_taxonomy.json"


@dataclass
class SkillEntry:
    """One skill from the taxonomy."""
    canonical: str           # e.g. "JavaScript"
    category: str            # e.g. "programming_languages"
    aliases: list[str] = field(default_factory=list) # e.g. ["js", "java script", "ecmascript"]
    parent: str | None = None # e.g. "AWS" for "AWS EC2", "CI/CD" for "GitHub Actions"
    tier: str = "core"       # "core" | "supporting" | "soft"


class SkillsTaxonomy:
    """
    In-memory skills taxonomy with O(1) alias-to-canonical lookup.

    Usage:
        tax = get_taxonomy()
        tax.find("js")          # → "JavaScript"
        tax.find("JavaScript")  # → "JavaScript"
        tax.find("unknown")     # → None
    """

    def __init__(self, skills: list[SkillEntry]):
        self._skills = skills

        # Fast direct lookup by canonical name
        self._by_canonical: dict[str, SkillEntry] = {
            s.canonical: s for s in skills
        }

        # Build lookup: lowercased phrase → canonical name
        # Both the canonical name and every alias are indexed.
        self._lookup: dict[str, str] = {}
        for skill in skills:
            key = skill.canonical.lower()
            self._lookup[key] = skill.canonical
            for alias in skill.aliases:
                self._lookup[alias.lower()] = skill.canonical

        # Category index: category → list of canonical names
        self._categories: dict[str, list[str]] = {}
        for skill in skills:
            self._categories.setdefault(skill.category, []).append(
                skill.canonical
            )

    # ── Public methods ──

    def find(self, text: str) -> str | None:
        """
        Look up a phrase and return the canonical skill name, or None.

        The lookup is case-insensitive.
        """
        return self._lookup.get(text.lower().strip())

    def all_phrases(self) -> list[str]:
        """
        Return every matchable phrase (canonical names + aliases),
        in their original casing.  Used to build a spaCy PhraseMatcher.
        """
        phrases: list[str] = []
        for skill in self._skills:
            phrases.append(skill.canonical)
            phrases.extend(skill.aliases)
        return phrases

    def all_canonical(self) -> list[str]:
        """Return all canonical skill names."""
        return [s.canonical for s in self._skills]

    def categories(self) -> dict[str, list[str]]:
        """Return a copy of the category → skills mapping."""
        return dict(self._categories)

    def get_entry(self, canonical: str) -> SkillEntry | None:
        """Return the SkillEntry for a canonical name, or None."""
        return self._by_canonical.get(canonical)

    def __len__(self) -> int:
        return len(self._skills)

    def __repr__(self) -> str:
        return f"SkillsTaxonomy({len(self._skills)} skills, {len(self._lookup)} phrases)"


# ------------------------------------------------------------------
# Loader (singleton pattern)
# ------------------------------------------------------------------

_instance: SkillsTaxonomy | None = None


def get_taxonomy(path: Path | None = None) -> SkillsTaxonomy:
    """
    Load the skills taxonomy from JSON (cached after first call).

    Args:
        path: Override path to the taxonomy JSON file (useful for testing).

    Returns:
        A SkillsTaxonomy instance.
    """
    global _instance

    if _instance is not None and path is None:
        return _instance

    taxonomy_path = path or _TAXONOMY_PATH

    with open(taxonomy_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    entries = [
        SkillEntry(
            canonical=item["canonical"],
            category=item["category"],
            aliases=item.get("aliases", []),
            parent=item.get("parent"),
            tier=item.get("tier", "core"),
        )
        for item in data["skills"]
    ]

    taxonomy = SkillsTaxonomy(entries)

    if path is None:
        _instance = taxonomy

    return taxonomy
