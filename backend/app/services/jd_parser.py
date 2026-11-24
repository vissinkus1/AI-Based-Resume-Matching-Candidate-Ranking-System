"""
services/jd_parser.py — Job Description parsing service.

Takes raw JD text and extracts structured information:
  - title, required_skills, preferred_skills
  - min/max experience years
  - qualifications (degree level + raw phrase)
  - responsibilities (bullet list)
  - keywords (domain noun phrases)

Uses spaCy for NLP and the skills taxonomy for skill matching.

Public API:
    parse_jd(text: str) -> ParsedJD
"""

import re
from dataclasses import dataclass, field

import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Span
from spacy.util import filter_spans

from app.services.skills_taxonomy import get_taxonomy


# ------------------------------------------------------------------
# Data classes for structured output
# ------------------------------------------------------------------

@dataclass
class QualificationInfo:
    """A single extracted qualification."""
    level: str         # "bachelor" | "master" | "phd" | "diploma" | "any"
    raw_phrase: str    # Original text, e.g. "B.Tech in Computer Science"


@dataclass
class ParsedJD:
    """Complete structured output of JD parsing."""
    title: str | None = None
    required_skills: list[str] = field(default_factory=list)
    preferred_skills: list[str] = field(default_factory=list)
    min_experience_years: float | None = None
    max_experience_years: float | None = None
    qualifications: list[QualificationInfo] = field(default_factory=list)
    min_required_level: str | None = None
    preferred_level: str | None = None
    responsibilities: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    skill_evidence: dict[str, dict[str, str]] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialise to a plain dict (for JSON / Pydantic)."""
        return {
            "title": self.title,
            "required_skills": self.required_skills,
            "preferred_skills": self.preferred_skills,
            "min_experience_years": self.min_experience_years,
            "max_experience_years": self.max_experience_years,
            "qualifications": [
                {"level": q.level, "raw_phrase": q.raw_phrase}
                for q in self.qualifications
            ],
            "min_required_level": self.min_required_level,
            "preferred_level": self.preferred_level,
            "responsibilities": self.responsibilities,
            "keywords": self.keywords,
            "skill_evidence": self.skill_evidence,
            "warnings": self.warnings,
        }


# ------------------------------------------------------------------
# spaCy model loading (cached)
# ------------------------------------------------------------------

_nlp = None


def _get_nlp():
    """Load en_core_web_sm once and cache it. Auto-downloads if missing."""
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            import sys
            logger.info("spaCy model 'en_core_web_sm' not found. Auto-downloading...")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ------------------------------------------------------------------
# Section detection
# ------------------------------------------------------------------

# Regex patterns for common JD section headings
_SECTION_PATTERNS = {
    "title": re.compile(
        r"(?:job\s*title|role|position|designation)\s*[:\-–—]",
        re.IGNORECASE,
    ),
    "required": re.compile(
        r"(?:required?\s*skills?|must\s*have|requirements?|"
        r"mandatory|essential\s*skills?|key\s*skills?|"
        r"what\s*(?:you|we)\s*(?:need|require|are\s*looking\s*for)|"
        r"qualifications?\s*(?:and|&)?\s*(?:requirements?|skills?))\s*[:\-–—]?",
        re.IGNORECASE,
    ),
    "preferred": re.compile(
        r"(?:nice\s*to\s*have|preferred|bonus|good\s*to\s*have|"
        r"desired|additional|plus|optional\s*skills?)\s*[:\-–—]?",
        re.IGNORECASE,
    ),
    "responsibilities": re.compile(
        r"(?:responsibilities|what\s*you\s*(?:will|'ll)\s*do|"
        r"key\s*responsibilities|role\s*(?:overview|description)|"
        r"duties|job\s*(?:description|duties)|"
        r"about\s*the\s*(?:role|position))\s*[:\-–—]?",
        re.IGNORECASE,
    ),
    "qualifications": re.compile(
        r"(?:education|qualifications?|academic|eligibility|"
        r"educational\s*(?:requirements?|qualifications?))\s*[:\-–—]?",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"(?:experience|years?\s*of\s*experience)\s*[:\-–—]?",
        re.IGNORECASE,
    ),
}


def _split_into_sections(text: str) -> dict[str, str]:
    """
    Split JD text into labelled sections by detecting headings.

    Returns a dict of section_name → section_text.
    If no headings are detected, the entire text goes into "body".
    """
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"body": []}
    current_section = "body"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            sections.setdefault(current_section, []).append("")
            continue

        # Check if this line is a section heading
        matched = False
        for section_name, pattern in _SECTION_PATTERNS.items():
            if pattern.match(stripped):
                current_section = section_name
                matched = True
                # Include content after the colon on the same line
                after_heading = pattern.sub("", stripped).strip()
                sections.setdefault(current_section, [])
                if after_heading:
                    sections[current_section].append(after_heading)
                break

        if not matched:
            sections.setdefault(current_section, []).append(stripped)

    # Join each section's lines into a single string
    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


# ------------------------------------------------------------------
# Title extraction
# ------------------------------------------------------------------

def _extract_title(text: str, sections: dict[str, str]) -> str | None:
    """
    Extract the job title from the JD.

    Strategy:
      1. Check explicit "Job Title:" / "Role:" lines (must start at beginning of line).
      2. Fall back to the first non-empty line of the document if it looks like a title
         (short, not a metadata prefix like "Company:", "Location:", etc.).
    """
    # 1. Check explicit title indicators on their own line
    # Must be at the start of a line (or preceded only by whitespace), not "About the Role:"
    match = re.search(
        r"^[ \t]*(?:job\s*title|role|position|designation)\s*[:\-–—]\s*([^\n\r]+)",
        text,
        re.IGNORECASE | re.MULTILINE,
    )
    if match:
        title = match.group(1).strip()
        if title and len(title) < 100:
            return title

    # 2. Fall back to first non-empty line that isn't a metadata prefix
    _METADATA_PREFIXES = re.compile(
        r"^(?:company|location|date|department|posted|employment\s*type)\s*[:\-–—]",
        re.IGNORECASE,
    )
    for line in text.splitlines():
        line = line.strip()
        if line and len(line) < 100 and not _METADATA_PREFIXES.match(line):
            return line

    return None


# ------------------------------------------------------------------
# Skills extraction
# ------------------------------------------------------------------

def _build_phrase_matcher(nlp) -> tuple[PhraseMatcher, dict[str, str]]:
    """
    Build a spaCy PhraseMatcher loaded with all taxonomy phrases.

    Returns:
        (matcher, span_to_canonical): The matcher and a mapping from
        lowercased phrase text → canonical skill name.
    """
    taxonomy = get_taxonomy()
    matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
    span_to_canonical: dict[str, str] = {}

    for skill_entry in taxonomy._skills:
        # Collect all phrases for this skill: canonical + aliases
        all_phrases = [skill_entry.canonical] + skill_entry.aliases
        patterns = []
        for phrase in all_phrases:
            span_to_canonical[phrase.lower()] = skill_entry.canonical
            doc = nlp.make_doc(phrase)
            patterns.append(doc)
        # Use canonical name as the matcher rule ID
        matcher.add(skill_entry.canonical, patterns)

    return matcher, span_to_canonical


def _is_whole_word_match(doc, start: int, end: int) -> bool:
    """
    Verify that the matched span is a whole-word match, not a partial
    word overlap.

    Example: Reject "Java" matching inside "JavaScript".
    We check that the character immediately before/after the span
    is not an alphanumeric character (i.e. not part of a larger word).
    """
    span_text = doc[start:end].text
    full_text = doc.text

    # Find the character positions of the span in the full text
    span_start_char = doc[start].idx
    span_end_char = doc[end - 1].idx + len(doc[end - 1].text)

    # Check character before the span
    if span_start_char > 0:
        char_before = full_text[span_start_char - 1]
        if char_before.isalnum() or char_before == '-':
            return False

    # Check character after the span
    if span_end_char < len(full_text):
        char_after = full_text[span_end_char]
        if char_after.isalnum():
            # Special case: allow if the next char is a space or punctuation
            # But reject "Java" inside "JavaScript"
            return False

    return True


def _extract_skills(
    text: str, sections: dict[str, str], nlp
) -> tuple[list[str], list[str], dict[str, dict[str, str]]]:
    """
    Extract required and preferred skills from JD text with evidence.

    Uses spaCy PhraseMatcher with the skills taxonomy for case-insensitive
    matching, resolves overlapping spans via longest-match-wins (spacy filter_spans),
    and classifies each skill as required or preferred based on section context.

    Returns:
        (required_skills, preferred_skills, skill_evidence):
        - required_skills: sorted list of canonical skill names
        - preferred_skills: sorted list of canonical skill names
        - skill_evidence: dict mapping canonical name -> {section, sentence, classification}
    """
    matcher, span_to_canonical = _build_phrase_matcher(nlp)

    # Section categories
    preferred_section_names = {"preferred"}
    required_section_names = {"required", "qualifications"}
    has_explicit_required_section = any(s in sections for s in required_section_names)

    # Inline cue phrases for preferred/nice-to-have in sentences
    _preferred_cues = re.compile(
        r"nice\s*to\s*have|preferred|bonus|good\s*to\s*have|"
        r"desirable|advantageous|a\s*plus|not\s*required|optional",
        re.IGNORECASE,
    )

    required_skills: set[str] = set()
    preferred_skills: set[str] = set()
    evidence: dict[str, dict[str, str]] = {}

    for section_name, section_text in sections.items():
        if not section_text.strip():
            continue

        doc = nlp(section_text)
        matches = matcher(doc)

        # Build candidate Spans and enforce whole-word boundaries
        raw_spans = []
        for match_id, start, end in matches:
            if _is_whole_word_match(doc, start, end):
                raw_spans.append(Span(doc, start, end, label=match_id))

        # A1: Longest-match-wins: filter_spans removes overlaps, keeping longest
        filtered_spans = filter_spans(raw_spans)

        for span in filtered_spans:
            matched_text = span.text.lower()
            canonical = span_to_canonical.get(matched_text)
            if not canonical:
                canonical = doc.vocab.strings[span.label]

            sent_text = _get_sentence_text(doc, span.start, span.end).strip()

            # Classification logic
            if section_name in preferred_section_names:
                classification = "preferred"
            elif section_name in required_section_names:
                if _preferred_cues.search(sent_text):
                    classification = "preferred"
                else:
                    classification = "required"
            elif section_name in {"responsibilities", "body", "title"}:
                # If the JD has an explicit requirements section, duties in
                # responsibilities are daily tasks, not mandatory prerequisites.
                if has_explicit_required_section:
                    classification = "preferred"
                else:
                    if _preferred_cues.search(sent_text):
                        classification = "preferred"
                    else:
                        classification = "required"
            else:
                classification = "required"

            # Register skill and evidence
            if classification == "required":
                required_skills.add(canonical)
                # If previously recorded as preferred, upgrade evidence to required
                evidence[canonical] = {
                    "section": section_name,
                    "sentence": sent_text,
                    "classification": "required",
                }
            else:
                preferred_skills.add(canonical)
                if canonical not in evidence or evidence[canonical]["classification"] != "required":
                    evidence[canonical] = {
                        "section": section_name,
                        "sentence": sent_text,
                        "classification": "preferred",
                    }

    # Skills present in required take precedence over preferred
    preferred_skills -= required_skills
    for skill in required_skills:
        if skill in evidence:
            evidence[skill]["classification"] = "required"

    return sorted(required_skills), sorted(preferred_skills), evidence


def _get_sentence_text(doc, start: int, end: int) -> str:
    """Get the specific line or bullet containing the matched span."""
    text = doc.text
    span_start = doc[start].idx
    span_end = doc[end - 1].idx + len(doc[end - 1].text)
    line_start = text.rfind("\n", 0, span_start)
    line_start = 0 if line_start == -1 else line_start + 1
    line_end = text.find("\n", span_end)
    line_end = len(text) if line_end == -1 else line_end
    line_text = text[line_start:line_end].strip()
    # Strip leading bullet dashes or asterisks
    cleaned_line = re.sub(r"^[\d.\-–•*]+\s*", "", line_text).strip()
    if cleaned_line:
        return cleaned_line

    token = doc[start]
    if token.sent is not None:
        return token.sent.text.strip()
    return doc[max(0, start - 10):min(len(doc), end + 10)].text.strip()


# ------------------------------------------------------------------
# Experience extraction
# ------------------------------------------------------------------

# Map English words to numbers (for "five years of experience")
_WORD_TO_NUM = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20,
}

# Range patterns (evaluated first to capture both min and max if present)
_EXPERIENCE_RANGE_PATTERNS = [
    # "3-5 years" / "3 to 5 years" / "3–5 years"
    re.compile(
        r"(\d+\.?\d*)\s*[-–—to]+\s*(\d+\.?\d*)\s*(?:\+\s*)?years?",
        re.IGNORECASE,
    ),
    # "three to five years" / "three-five years" (word numbers)
    re.compile(
        r"(" + "|".join(_WORD_TO_NUM.keys()) +
        r")\s*[-–—to]+\s*(" + "|".join(_WORD_TO_NUM.keys()) +
        r")\s*years?",
        re.IGNORECASE,
    ),
]

# Single value patterns (evaluated if no range is found)
_EXPERIENCE_SINGLE_PATTERNS = [
    # "minimum 3 years" / "at least 4 years" / "min 2 years" / "minimum of 3 years"
    re.compile(
        r"(?:minimum|at\s*least|min\.?)\s*(?:of\s+)?(\d+\.?\d*)\s*(?:\+\s*)?(?:plus\s+)?years?",
        re.IGNORECASE,
    ),
    # "3+ years" / "3 plus years"
    re.compile(
        r"(\d+\.?\d*)\s*(?:\+|plus)\s*years?",
        re.IGNORECASE,
    ),
    # "minimum of three years" / "at least five years" (word numbers)
    re.compile(
        r"(?:minimum|at\s*least|min\.?)\s*(?:of\s+)?(" +
        "|".join(_WORD_TO_NUM.keys()) +
        r")\s*(?:\+\s*)?years?",
        re.IGNORECASE,
    ),
    # Standalone word-number: "five years of experience" / "three years"
    re.compile(
        r"(" + "|".join(_WORD_TO_NUM.keys()) +
        r")\s*(?:\+\s*)?years?\s*(?:of\s+)?(?:experience|exp\.?)?",
        re.IGNORECASE,
    ),
    # Generic digit years: "3 years"
    re.compile(
        r"(\d+\.?\d*)\s*years?",
        re.IGNORECASE,
    ),
]

# All patterns ordered: ranges first, then single values
_EXPERIENCE_PATTERNS = _EXPERIENCE_RANGE_PATTERNS + _EXPERIENCE_SINGLE_PATTERNS

# "Fresher" / "entry level" / "0 years"
_FRESHER_PATTERN = re.compile(
    r"(?:fresher|entry\s*level|entry-level|0\s*years?|no\s*experience\s*required|"
    r"new\s*grad(?:uate)?|recent\s*grad(?:uate)?|graduate\s*trainee)",
    re.IGNORECASE,
)


def _parse_num(value: str) -> float:
    """Convert a string to a number — handles both digits and English words."""
    value = value.strip().lower()
    if value in _WORD_TO_NUM:
        return float(_WORD_TO_NUM[value])
    try:
        return float(value)
    except ValueError:
        return 0.0


def _extract_experience(
    text: str, sections: dict[str, str]
) -> tuple[float | None, float | None]:
    """
    Extract minimum and maximum experience years from JD text.

    Handles:
      - "3-5 years"      → (3, 5)
      - "3+ years"       → (3, None)
      - "minimum 2 years"→ (2, None)
      - "at least 4 years"→ (4, None)
      - "five years"     → (5, None)
      - "fresher"        → (0, 0)
      - "entry level"    → (0, 0)

    Returns:
        (min_years, max_years) — either may be None if not detected.
    """
    # 1. If an explicit experience section exists, try matching against it first
    exp_section = sections.get("experience", "").strip()
    if exp_section:
        for pattern in _EXPERIENCE_PATTERNS:
            match = pattern.search(exp_section)
            if match:
                groups = match.groups()
                if len(groups) == 2 and groups[1] is not None:
                    return _parse_num(groups[0]), _parse_num(groups[1])
                elif len(groups) >= 1:
                    return _parse_num(groups[0]), None

    # 2. Search full text (range patterns first, then single values)
    min_years: float | None = None
    max_years: float | None = None

    for pattern in _EXPERIENCE_PATTERNS:
        match = pattern.search(text)
        if match:
            groups = match.groups()
            if len(groups) == 2 and groups[1] is not None:
                min_years = _parse_num(groups[0])
                max_years = _parse_num(groups[1])
            elif len(groups) >= 1:
                min_years = _parse_num(groups[0])
            break

    # 3. Check for fresher / entry-level if nothing found yet
    if min_years is None and _FRESHER_PATTERN.search(text):
        min_years = 0.0
        max_years = 0.0

    return min_years, max_years


# ------------------------------------------------------------------
# Qualification extraction
# ------------------------------------------------------------------

# Maps degree patterns to standardised levels
_DEGREE_PATTERNS: list[tuple[re.Pattern, str]] = [
    # PhD / Doctorate
    (re.compile(
        r"\b(?:ph\.?d|doctorate|doctor\s*of\s*philosophy)\b",
        re.IGNORECASE,
    ), "phd"),
    # Master's
    (re.compile(
        r"\b(?:master'?s?\s*(?:degree)?|m\.?s\.?c?\.?|m\.?tech|m\.?e\.?|"
        r"mca|m\.?b\.?a\.?|m\.?c\.?a\.?|post\s*graduat(?:e|ion))\b",
        re.IGNORECASE,
    ), "master"),
    # Bachelor's
    (re.compile(
        r"\b(?:bachelor'?s?\s*(?:degree)?|b\.?s\.?c?\.?|b\.?tech|b\.?e\.?|"
        r"bca|b\.?c\.?a\.?|b\.?b\.?a\.?|under\s*graduat(?:e|ion)|"
        r"(?:4|four)\s*year\s*degree)\b",
        re.IGNORECASE,
    ), "bachelor"),
    # Diploma
    (re.compile(
        r"\b(?:diploma|associate'?s?\s*degree|polytechnic)\b",
        re.IGNORECASE,
    ), "diploma"),
    # Any degree / generic
    (re.compile(
        r"\b(?:degree\s+in|any\s+degree|relevant\s+degree|"
        r"equivalent\s+degree|graduation)\b",
        re.IGNORECASE,
    ), "any"),
]

# Subject area patterns (CS, IT, etc.)
_SUBJECT_PATTERN = re.compile(
    r"(?:in|of)\s+(computer\s*science|information\s*technology|"
    r"software\s*engineering|data\s*science|mathematics|statistics|"
    r"electrical\s*engineering|electronics|it|cs|ece|eee|"
    r"computer\s*engineering|computer\s*applications|"
    r"related\s*field|relevant\s*(?:field|discipline)|stem|"
    r"engineering|science)",
    re.IGNORECASE,
)


def _extract_qualifications(
    text: str, sections: dict[str, str]
) -> list[QualificationInfo]:
    """
    Extract educational qualifications from JD text.

    Returns a list of QualificationInfo with normalised level and raw phrase.
    """
    # Prioritize the qualifications/education section
    search_areas = []
    if "qualifications" in sections:
        search_areas.append(sections["qualifications"])
    if "required" in sections:
        search_areas.append(sections["required"])
    search_areas.append(text)  # Also search full text as fallback

    found: list[QualificationInfo] = []
    seen_levels: set[str] = set()

    for area in search_areas:
        for line in area.split("\n"):
            for pattern, level in _DEGREE_PATTERNS:
                match = pattern.search(line)
                if match and level not in seen_levels:
                    # Extract the full phrase (up to end of line or punctuation)
                    raw = line.strip()
                    # Try to get a more focused phrase
                    start = max(0, match.start() - 5)
                    end = min(len(line), match.end() + 80)
                    focused = line[start:end].strip()
                    # Clean up leading bullets/numbers
                    focused = re.sub(r"^[\d.\-–•*]+\s*", "", focused)
                    if focused:
                        raw = focused

                    found.append(QualificationInfo(level=level, raw_phrase=raw))
                    seen_levels.add(level)

    return found


_LEVEL_RANKS = {"diploma": 1, "bachelor": 2, "master": 3, "phd": 4}


def _determine_qualification_levels(
    qualifications: list[QualificationInfo],
    sections: dict[str, str],
) -> tuple[str | None, str | None]:
    """
    Determine min_required_level and preferred_level (A4).

    - min_required_level is the LOWEST level when the text uses 'or'/'equivalent'
      (e.g. 'Bachelor's or Master's' -> bachelor, 'Master's or Ph.D.' -> master).
    - preferred_level is a higher level when marked preferred/plus, or the higher
      alternative option in a qualification requirement.
    """
    if not qualifications:
        return None, None

    preferred_sec = sections.get("preferred", "").lower()
    required_sec = sections.get("required", "").lower() + " " + sections.get("qualifications", "").lower()

    required_levels: list[str] = []
    preferred_levels: list[str] = []

    for q in qualifications:
        if q.level not in _LEVEL_RANKS:
            continue

        raw_lower = q.raw_phrase.lower()

        # Check if raw phrase is in preferred section or contains preferred cue
        is_pref = (
            raw_lower in preferred_sec
            or "preferred" in raw_lower
            or "plus" in raw_lower
            or "bonus" in raw_lower
            or "nice to have" in raw_lower
        )

        if is_pref:
            preferred_levels.append(q.level)
        else:
            required_levels.append(q.level)

    min_required_level = None
    preferred_level = None

    if required_levels:
        # Lowest level in required is the minimum requirement
        sorted_req = sorted(required_levels, key=lambda l: _LEVEL_RANKS[l])
        min_required_level = sorted_req[0]
        # If multiple levels in required (e.g. "Master's or Ph.D." or "Bachelor's or Master's")
        if len(sorted_req) > 1 and not preferred_levels:
            preferred_level = sorted_req[-1]

    if preferred_levels:
        sorted_pref = sorted(preferred_levels, key=lambda l: _LEVEL_RANKS[l])
        preferred_level = sorted_pref[-1]

    return min_required_level, preferred_level


# ------------------------------------------------------------------
# Responsibilities extraction
# ------------------------------------------------------------------

def _extract_responsibilities(
    text: str, sections: dict[str, str]
) -> list[str]:
    """
    Extract the responsibilities/duties list from the JD.

    Looks for bullet points or numbered items in the responsibilities section.
    If no section is detected, tries to find bullet-list blocks in the full text.
    """
    source = sections.get("responsibilities", "")

    if not source.strip():
        # Fallback: look in body
        source = sections.get("body", "")

    if not source.strip():
        return []

    responsibilities: list[str] = []

    for line in source.split("\n"):
        line = line.strip()
        if not line:
            continue
        # Clean leading bullets, dashes, numbers
        cleaned = re.sub(r"^[\d.\-–•*]+\s*", "", line).strip()
        # Only include substantial lines (not section headings)
        if cleaned and len(cleaned) > 10:
            responsibilities.append(cleaned)

    return responsibilities


# ------------------------------------------------------------------
# Keyword extraction
# ------------------------------------------------------------------

def _extract_keywords(text: str, nlp, existing_skills: set[str]) -> list[str]:
    """
    Extract top domain keywords / noun phrases from the JD.

    Uses spaCy noun chunks, filtered to remove:
      - Very short or very long phrases
      - Pronouns and determiners
      - Skills already extracted (avoid duplication)
      - Generic/stop phrases

    Returns up to 20 keywords, deduplicated.
    """
    doc = nlp(text)

    _STOP_PHRASES = {
        "experience", "years", "requirements", "qualifications",
        "responsibilities", "skills", "candidate", "candidates",
        "team", "work", "ability", "knowledge", "understanding",
        "role", "position", "job", "company", "opportunity",
        "environment", "you", "we", "they", "us", "our", "your",
    }

    keywords: list[str] = []
    seen: set[str] = set()

    for chunk in doc.noun_chunks:
        # Clean the chunk text
        text_clean = chunk.text.strip()
        lower = text_clean.lower()

        # Skip if already seen
        if lower in seen:
            continue

        # Skip very short (< 3 chars) or very long (> 50 chars)
        if len(text_clean) < 3 or len(text_clean) > 50:
            continue

        # Skip if it's just a pronoun/determiner/stop word
        if lower in _STOP_PHRASES:
            continue

        # Skip if the root is a stop word
        if chunk.root.text.lower() in _STOP_PHRASES:
            continue

        # Skip if it matches an already-extracted skill
        if lower in {s.lower() for s in existing_skills}:
            continue

        # Skip purely numeric chunks
        if text_clean.replace(" ", "").isdigit():
            continue

        seen.add(lower)
        keywords.append(text_clean)

    # Return top 20
    return keywords[:20]


# ------------------------------------------------------------------
# Main entry point
# ------------------------------------------------------------------

def parse_jd(text: str) -> ParsedJD:
    """
    Parse a Job Description text into structured fields.

    Args:
        text: Raw JD text (already extracted from file, or pasted).

    Returns:
        ParsedJD with all extracted fields populated.
    """
    nlp = _get_nlp()

    # 1. Split the text into sections by detecting headings
    sections = _split_into_sections(text)

    # 2. Extract each field
    title = _extract_title(text, sections)

    required_skills, preferred_skills, skill_evidence = _extract_skills(text, sections, nlp)

    min_exp, max_exp = _extract_experience(text, sections)

    qualifications = _extract_qualifications(text, sections)
    min_qual_level, pref_qual_level = _determine_qualification_levels(qualifications, sections)

    responsibilities = _extract_responsibilities(text, sections)

    all_skills = set(required_skills) | set(preferred_skills)
    keywords = _extract_keywords(text, nlp, all_skills)

    warnings = []
    word_count = len(text.split())
    if word_count < 30:
        warnings.append(
            "Job description appears unusually brief. Matching accuracy improves with detailed requirements, duties, and skills."
        )

    return ParsedJD(
        title=title,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        min_experience_years=min_exp,
        max_experience_years=max_exp,
        qualifications=qualifications,
        min_required_level=min_qual_level,
        preferred_level=pref_qual_level,
        responsibilities=responsibilities,
        keywords=keywords,
        skill_evidence=skill_evidence,
        warnings=warnings,
    )
