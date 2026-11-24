"""
services/resume_parser.py — Comprehensive Resume Parsing Service.

Extracts structured information from resumes (PDF, DOCX):
  - Contact info: name, email, phone, linkedin_url, github_url, location
  - Section segmentation: summary, experience, education, skills, projects, certifications
  - Skills matching: whole-resume taxonomy matching (alias-aware, longest-match-wins,
    confidence scoring, parent tracking, evidence)
  - Work experience: entries with title, company, start/end dates, months, is_current,
    is_internship, overlap merging, total experience years (with injectable `today`)
  - Education history: degree, normalized level (diploma/bachelor/master/phd), field, institution, year
  - Executive summary and parse warnings

Public API:
    parse_resume(file_bytes: bytes, filename: str, today: tuple[int, int] = (2026, 11)) -> ParsedResume
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import spacy
from spacy.tokens import Span
from spacy.util import filter_spans

from app.services.text_extractor import extract_text
from app.services.skills_taxonomy import get_taxonomy, SkillsTaxonomy


# ------------------------------------------------------------------
# Structured Dataclasses
# ------------------------------------------------------------------

@dataclass
class ExperienceEntry:
    title: str = ""
    company: str = ""
    start_date: str = ""
    end_date: str = ""
    months: int = 0
    is_current: bool = False
    is_internship: bool = False
    description: str = ""
    skills_in_entry: list[str] = field(default_factory=list)


@dataclass
class EducationEntry:
    degree: str = ""
    level: str = ""       # "diploma" | "bachelor" | "master" | "phd"
    field: str = ""
    institution: str = ""
    year: int | None = None


@dataclass
class ResumeSkill:
    name: str             # Canonical skill name
    category: str = ""
    tier: str = "core"    # "core" | "supporting" | "soft"
    parent: str | None = None
    section: str = ""     # e.g. "skills", "experience", "projects"
    confidence: str = "strong"  # "strong" | "medium" | "basic"
    evidence: str = ""


@dataclass
class ParsedResume:
    name: str = ""
    email: str | None = None
    phone: str | None = None
    linkedin_url: str | None = None
    github_url: str | None = None
    location: str | None = None
    total_experience_years: float = 0.0
    internship_months: int = 0
    experience_source: str = "date_ranges"  # "date_ranges" | "stated_in_text"
    job_titles: list[str] = field(default_factory=list)
    skills: list[ResumeSkill] = field(default_factory=list)
    experience_entries: list[ExperienceEntry] = field(default_factory=list)
    education: list[EducationEntry] = field(default_factory=list)
    summary: str = ""
    sections: dict[str, str] = field(default_factory=dict)
    parse_warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "location": self.location,
            "total_experience_years": self.total_experience_years,
            "internship_months": self.internship_months,
            "experience_source": self.experience_source,
            "job_titles": self.job_titles,
            "skills": [
                {
                    "name": s.name,
                    "category": s.category,
                    "tier": s.tier,
                    "parent": s.parent,
                    "section": s.section,
                    "confidence": s.confidence,
                    "evidence": s.evidence,
                }
                for s in self.skills
            ],
            "experience_entries": [
                {
                    "title": e.title,
                    "company": e.company,
                    "start_date": e.start_date,
                    "end_date": e.end_date,
                    "months": e.months,
                    "is_current": e.is_current,
                    "is_internship": e.is_internship,
                    "description": e.description,
                    "skills_in_entry": e.skills_in_entry,
                }
                for e in self.experience_entries
            ],
            "education": [
                {
                    "degree": ed.degree,
                    "level": ed.level,
                    "field": ed.field,
                    "institution": ed.institution,
                    "year": ed.year,
                }
                for ed in self.education
            ],
            "summary": self.summary,
            "sections": self.sections,
            "parse_warnings": self.parse_warnings,
        }


# ------------------------------------------------------------------
# Regex Patterns
# ------------------------------------------------------------------

_EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b"
)

# Indian and international phone patterns
_PHONE_PATTERNS = [
    # Indian with country code: +91 98765 43210, +91-9876543210, 91 9876543210
    re.compile(r"(?:\+91|91)[\s-]?[6-9]\d{4}[\s-]?\d{5}\b"),
    # Indian 10 digits starting with 6-9 (optional leading 0)
    re.compile(r"\b0?[6-9]\d{4}[\s-]?\d{5}\b"),
    re.compile(r"\b0?[6-9]\d{9}\b"),
    # US / International formats: +1 (123) 456-7890, 123-456-7890, (123) 456-7890
    re.compile(r"(?:\+?1[\s-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"),
    # General international with +: +44 20 7946 0919, +49 30 123456
    re.compile(r"\+\d{1,3}[\s-]\d{2,4}[\s-]\d{4,8}\b"),
]

_LINKEDIN_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)/?",
    re.IGNORECASE,
)

_GITHUB_PATTERN = re.compile(
    r"(?:https?://)?(?:www\.)?github\.com/([a-zA-Z0-9_-]+)/?",
    re.IGNORECASE,
)

# Common section headers
_RESUME_SECTION_PATTERNS = {
    "summary": re.compile(
        r"^(?:professional\s+summary|career\s+summary|executive\s+summary|summary|profile|about\s+me|career\s+objective|objective|professional\s+profile)\s*[:\-–—]?$",
        re.IGNORECASE,
    ),
    "experience": re.compile(
        r"^(?:(?:research\s+&?\s*)?(?:work|professional)?\s*experience|employment\s+history|work\s+history|career\s+history|chronological\s+(?:career\s+)?history|work\s+experience|professional\s+background|research\s+experience)\s*[:\-–—]?$",
        re.IGNORECASE,
    ),
    "education": re.compile(
        r"^(?:education|academic\s+background|educational\s+qualifications|academic\s+history|education\s+&\s+qualifications|degrees|academic\s+profile)\s*[:\-–—]?$",
        re.IGNORECASE,
    ),
    "skills": re.compile(
        r"^(?:(?:core\s+)?technical\s+skills|skills\s+&\s+technologies|core\s+competencies|skills\s+&\s+tools|key\s+skills|skills|technologies|tools\s+&\s+technologies|technical\s+expertise|technical\s+mastery|core\s+skills)\s*[:\-–—]?$",
        re.IGNORECASE,
    ),
    "projects": re.compile(
        r"^(?:projects|key\s+projects|academic\s+projects|personal\s+projects|notable\s+projects)\s*[:\-–—]?$",
        re.IGNORECASE,
    ),
    "certifications": re.compile(
        r"^(?:certifications|certificates|licenses|credentials|professional\s+certifications)\s*[:\-–—]?$",
        re.IGNORECASE,
    ),
}

# Month names mapping to integer 1-12
_MONTH_MAP = {
    "jan": 1, "january": 1, "feb": 2, "february": 2,
    "mar": 3, "march": 3, "apr": 4, "april": 4,
    "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
    "aug": 8, "august": 8, "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10, "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}

_PRESENT_WORDS = {"present", "current", "till date", "now", "ongoing", "date"}

# Date range extraction regexes
_DATE_RANGE_REGEXES = [
    # "Jan 2020 - Mar 2022", "January 2020 – Present", "Jun'19 - Aug'20", "06/2020 - 08/2023"
    re.compile(
        r"([a-zA-Z]{3,}|0?[1-9]|1[0-2])[\s'/\.]+(\d{2,4})\s*(?:[-–—~?to\s]+)\s*([a-zA-Z]{3,}|0?[1-9]|1[0-2])[\s'/\.]+(\d{2,4}|present|current|till\s*date|now)",
        re.IGNORECASE,
    ),
    # "Jan 2020 - Present", "Jun'19 - Present"
    re.compile(
        r"([a-zA-Z]{3,}|0?[1-9]|1[0-2])[\s'/\.]+(\d{2,4})\s*(?:[-–—~?to\s]+)\s*(present|current|till\s*date|now)",
        re.IGNORECASE,
    ),
    # "2019 - 2022", "2020 - Present"
    re.compile(
        r"\b(19\d{2}|20\d{2})\s*(?:[-–—~?to\s]+)\s*(19\d{2}|20\d{2}|present|current|till\s*date|now)\b",
        re.IGNORECASE,
    ),
    # "Since Jan 2021", "Since 2021"
    re.compile(
        r"(?:since|from)\s+([a-zA-Z]{3,}|0?[1-9]|1[0-2])?[\s'/\.]*(\d{4})",
        re.IGNORECASE,
    ),
]


# ------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------

_nlp_cache = None


def _get_nlp():
    """Load en_core_web_sm once and cache it. Auto-downloads if missing."""
    global _nlp_cache
    if _nlp_cache is None:
        try:
            _nlp_cache = spacy.load("en_core_web_sm")
        except OSError:
            import subprocess
            import sys
            logger.info("spaCy model 'en_core_web_sm' not found. Auto-downloading...")
            subprocess.run([sys.executable, "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp_cache = spacy.load("en_core_web_sm")
    return _nlp_cache


def _normalize_phone(raw: str) -> str:
    """Normalize extracted phone string."""
    cleaned = re.sub(r"[^\d+]", " ", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def _extract_name(text: str, filename: str, nlp) -> tuple[str, list[str]]:
    """
    Extract candidate name from top lines using heuristics and spaCy PERSON NER.
    Falls back to cleaned filename if heuristics fail.
    """
    warnings = []
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # Forbidden tokens that indicate a line is not a person's name
    _NON_NAME_WORDS = {
        "resume", "curriculum", "vitae", "cv", "profile", "summary",
        "contact", "email", "phone", "mobile", "portfolio", "address",
        "education", "experience", "skills", "projects", "objective",
        "developer", "engineer", "designer", "manager", "analyst",
        "senior", "junior", "lead", "architect", "consultant", "intern",
    }

    # Inspect first 8 lines
    for line in lines[:8]:
        line_clean = line.strip()
        lower = line_clean.lower()

        # Skip lines with contact info or URLs
        if "@" in line_clean or "http" in lower or "linkedin" in lower or "github" in lower:
            continue
        if any(c.isdigit() for c in line_clean):
            # If line has multiple digits, it's likely a phone or address
            num_digits = sum(1 for c in line_clean if c.isdigit())
            if num_digits > 3:
                continue

        # Skip if too long or contains non-name keywords
        words = line_clean.split()
        if len(words) < 1 or len(words) > 5:
            continue
        if len(line_clean) > 40:
            continue
        if any(w.lower() in _NON_NAME_WORDS for w in words):
            continue

        # Test line with spaCy NER
        doc = nlp(line_clean)
        has_person = any(ent.label_ == "PERSON" for ent in doc.ents)

        # Name heuristic: capitalized words with only letters, dots, hyphens
        is_title_case = all(w[0].isupper() for w in words if w and w[0].isalpha())
        all_alpha = all(w.replace(".", "").replace("-", "").isalpha() for w in words)

        if (has_person or (is_title_case and all_alpha)) and len(words) >= 2:
            return line_clean, warnings

    # Second-chance fallback: Check spaCy PERSON entities in the first 500 characters
    doc_intro = nlp(text[:500])
    for ent in doc_intro.ents:
        if ent.label_ == "PERSON":
            ent_words = ent.text.strip().split()
            if 2 <= len(ent_words) <= 4:
                if not any(w.lower() in _NON_NAME_WORDS for w in ent_words):
                    return ent.text.strip(), warnings

    # Fallback to cleaned filename
    clean_stem = Path(filename).stem
    # Remove words like resume, cv, draft, etc.
    clean_stem = re.sub(r"(?i)[-_]?(?:resume|cv|curriculum_vitae|profile)[-_]?", " ", clean_stem)
    clean_stem = re.sub(r"[-_]+", " ", clean_stem).strip()
    clean_stem = " ".join(w.capitalize() for w in clean_stem.split())

    warnings.append("Candidate name inferred from filename")
    return clean_stem or "Unknown Candidate", warnings


def _extract_contact_info(text: str) -> dict[str, str | None]:
    """Extract email, phone, linkedin, github, and location."""
    email = None
    email_match = _EMAIL_PATTERN.search(text)
    if email_match:
        email = email_match.group(0).lower().strip()

    phone = None
    for p_pat in _PHONE_PATTERNS:
        match = p_pat.search(text)
        if match:
            phone = _normalize_phone(match.group(0))
            break

    linkedin_url = None
    li_match = _LINKEDIN_PATTERN.search(text)
    if li_match:
        user = li_match.group(1)
        linkedin_url = f"https://linkedin.com/in/{user}"

    github_url = None
    gh_match = _GITHUB_PATTERN.search(text)
    if gh_match:
        user = gh_match.group(1)
        github_url = f"https://github.com/user/{user}" if "github.com" not in gh_match.group(0) else gh_match.group(0)

    # Location (best effort from first 10 lines)
    location = None
    lines = [l.strip() for l in text.splitlines()[:10] if l.strip()]
    _COMMON_CITIES = [
        "Bangalore", "Bengaluru", "Hyderabad", "Pune", "Mumbai", "Delhi",
        "Noida", "Gurgaon", "Gurugram", "Chennai", "Kolkata", "Ahmedabad",
        "San Francisco", "New York", "Seattle", "Austin", "Boston", "London",
        "Toronto", "Berlin", "Singapore",
    ]
    for line in lines:
        for city in _COMMON_CITIES:
            if re.search(rf"\b{city}\b", line, re.IGNORECASE):
                location = city
                break
        if location:
            break

    return {
        "email": email,
        "phone": phone,
        "linkedin_url": linkedin_url,
        "github_url": github_url,
        "location": location,
    }


def _segment_sections(text: str) -> dict[str, str]:
    """Segment resume text into standard sections based on detected headings."""
    lines = text.split("\n")
    sections: dict[str, list[str]] = {"header": []}
    current_section = "header"

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Check if line matches a known section heading
        matched_sec = None
        for sec_name, pattern in _RESUME_SECTION_PATTERNS.items():
            if pattern.match(stripped):
                matched_sec = sec_name
                break

        if matched_sec:
            current_section = matched_sec
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, []).append(stripped)

    return {k: "\n".join(v).strip() for k, v in sections.items() if v}


# ------------------------------------------------------------------
# Skills Extraction for Resumes
# ------------------------------------------------------------------

def _extract_resume_skills(
    text: str, sections: dict[str, str], nlp, taxonomy: SkillsTaxonomy
) -> list[ResumeSkill]:
    """
    Extract skills across the resume with longest-match-wins and section confidence.
    """
    from app.services.jd_parser import _build_phrase_matcher, _is_whole_word_match

    matcher, span_to_canonical = _build_phrase_matcher(nlp)

    skills_by_canonical: dict[str, ResumeSkill] = {}

    for sec_name, sec_text in sections.items():
        if not sec_text.strip():
            continue

        doc = nlp(sec_text)
        matches = matcher(doc)

        raw_spans = []
        for match_id, start, end in matches:
            if _is_whole_word_match(doc, start, end):
                raw_spans.append(Span(doc, start, end, label=match_id))

        filtered_spans = filter_spans(raw_spans)

        for span in filtered_spans:
            matched_text = span.text.lower()
            canonical = span_to_canonical.get(matched_text)
            if not canonical:
                canonical = doc.vocab.strings[span.label]

            entry = taxonomy.get_entry(canonical)
            category = entry.category if entry else ""
            tier = entry.tier if entry else "core"
            parent = entry.parent if entry else None

            # Determine confidence based on section
            if sec_name in {"skills", "experience"}:
                confidence = "strong"
            elif sec_name == "projects":
                confidence = "medium"
            else:
                confidence = "basic"

            # Sentence evidence
            token = doc[span.start]
            ev = token.sent.text.strip() if token.sent is not None else span.text

            # If already present, keep the higher confidence
            if canonical in skills_by_canonical:
                prev = skills_by_canonical[canonical]
                rank = {"strong": 3, "medium": 2, "basic": 1}
                if rank[confidence] > rank[prev.confidence]:
                    prev.confidence = confidence
                    prev.section = sec_name
                    prev.evidence = ev
            else:
                skills_by_canonical[canonical] = ResumeSkill(
                    name=canonical,
                    category=category,
                    tier=tier,
                    parent=parent,
                    section=sec_name,
                    confidence=confidence,
                    evidence=ev,
                )

    return sorted(skills_by_canonical.values(), key=lambda s: s.name)


# ------------------------------------------------------------------
# Experience Date Parsing & Overlap Merging
# ------------------------------------------------------------------

def _parse_month_year(m_str: str, y_str: str, default_month: int = 1) -> tuple[int, int] | None:
    """Parse month and year strings into (year, month)."""
    try:
        # Handle 2-digit years (e.g. '19 -> 2019)
        year = int(y_str)
        if year < 100:
            year += 2000 if year < 70 else 1900

        month = default_month
        if m_str:
            m_lower = m_str.lower().strip().replace(".", "")
            if m_lower.isdigit():
                month = int(m_lower)
            elif m_lower in _MONTH_MAP:
                month = _MONTH_MAP[m_lower]

        month = max(1, min(12, month))
        return (year, month)
    except Exception:
        return None


def _extract_dates_from_line(
    line: str, today: tuple[int, int]
) -> tuple[tuple[int, int], tuple[int, int], bool] | None:
    """
    Extract (start_date, end_date, is_current) from a text line.
    start_date and end_date are (year, month).
    """
    for regex in _DATE_RANGE_REGEXES:
        match = regex.search(line)
        if not match:
            continue

        groups = match.groups()
        is_current = False

        if len(groups) == 4:
            # (m1, y1, m2, y2)
            m1, y1, m2, y2 = groups
            start = _parse_month_year(m1, y1, default_month=1)
            if y2.lower().strip() in _PRESENT_WORDS:
                end = today
                is_current = True
            else:
                end = _parse_month_year(m2, y2, default_month=12)
            if start and end:
                return (start, end, is_current)

        elif len(groups) == 3:
            # (m1, y1, present_word)
            m1, y1, pres = groups
            start = _parse_month_year(m1, y1, default_month=1)
            end = today
            is_current = True
            if start and end:
                return (start, end, is_current)

        elif len(groups) == 2:
            g1, g2 = groups
            # "Since 2021" or "2019 - 2022"
            if g2.lower().strip() in _PRESENT_WORDS:
                start = _parse_month_year(None, g1, default_month=1)
                end = today
                is_current = True
            elif g1 and g1.isdigit() and g2 and g2.isdigit():
                start = _parse_month_year(None, g1, default_month=1)
                end = _parse_month_year(None, g2, default_month=12)
            elif "since" in line.lower() or "from" in line.lower():
                start = _parse_month_year(g1, g2, default_month=1)
                end = today
                is_current = True
            else:
                start = None
                end = None

            if start and end:
                return (start, end, is_current)

    return None


def _merge_date_intervals(intervals: list[tuple[int, int]]) -> int:
    """
    Merge overlapping (start_month_idx, end_month_idx) intervals.
    Returns total distinct months.
    """
    if not intervals:
        return 0

    # Sort intervals by start
    sorted_intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: list[list[int]] = []

    for start, end in sorted_intervals:
        if not merged:
            merged.append([start, end])
        else:
            prev_start, prev_end = merged[-1]
            if start <= prev_end + 1:  # overlapping or adjacent
                merged[-1][1] = max(prev_end, end)
            else:
                merged.append([start, end])

    total_months = sum((end - start + 1) for start, end in merged)
    return total_months


_COMMON_TITLES_PATTERN = re.compile(
    r"\b(?:software\s+engineer|senior\s+backend\s+engineer|backend\s+engineer|"
    r"frontend\s+developer|frontend\s+web\s+developer|senior\s+frontend\s+developer|"
    r"full\s*stack\s+developer|full\s*stack\s+engineer|senior\s+full\s*stack\s+engineer|"
    r"developer|frontend|backend|full\s*stack|"
    r"data\s+scientist|data\s+engineer|ai\s+engineer|ml\s+engineer|machine\s+learning\s+engineer|"
    r"devops\s+engineer|cloud\s+engineer|cloud\s+consultant|cloud\s+infrastructure\s+engineer|lead\s+cloud\s+infrastructure\s+engineer|"
    r"research\s+scientist|staff\s+research\s+scientist|growth\s+marketing\s+lead|digital\s+marketing\s+specialist|marketing\s+specialist|"
    r"intern|internship|tech\s+lead|team\s+lead|principal\s+architect|manager|analyst|"
    r"consultant|architect|specialist|programmer|trainee)\b",
    re.IGNORECASE,
)


def _clean_job_title_and_company(raw_title: str, existing_company: str = "") -> tuple[str, str]:
    """
    Ensure job title contains ONLY the role title, never "Title | Company, City".
    Handles separators:
      - " | " (pipe)
      - " - " / " – " / " — " (dash/hyphen with spaces)
      - " at "
      - " @ "
      - ", " (comma)
    """
    if not raw_title:
        return "", existing_company

    title = raw_title.strip()
    company = (existing_company or "").strip()

    # 1. Pipe: "Senior Backend Engineer | Infosys Ltd, Bangalore"
    if " | " in title:
        parts = title.split(" | ", 1)
        title = parts[0].strip()
        if not company:
            company = parts[1].strip()

    # 2. " at " or " @ "
    elif re.search(r"(?i)\s+at\s+", title):
        parts = re.split(r"(?i)\s+at\s+", title, maxsplit=1)
        title = parts[0].strip()
        if not company:
            company = parts[1].strip()

    elif " @ " in title:
        parts = title.split(" @ ", 1)
        title = parts[0].strip()
        if not company:
            company = parts[1].strip()

    # 3. Dash: "Software Developer - StartupHub Technologies, Bangalore"
    elif re.search(r"\s+[-–—]\s+", title):
        parts = re.split(r"\s+[-–—]\s+", title, maxsplit=1)
        title = parts[0].strip()
        if not company:
            company = parts[1].strip()

    # 4. Comma: "Senior Developer, TechCorp India"
    elif "," in title:
        parts = [p.strip() for p in title.split(",", 1)]
        if _COMMON_TITLES_PATTERN.search(parts[0]):
            title = parts[0]
            if not company:
                company = parts[1]

    # Clean any trailing punctuation
    title = re.sub(r"^[\s\|\-–—,]+|[\s\|\-–—,]+$", "", title).strip()

    # Clean company if it has trailing location, e.g. "Infosys Ltd, Bangalore"
    if company and "," in company:
        comp_parts = [c.strip() for c in company.split(",")]
        company = comp_parts[0]

    return title, company


def _extract_skills_from_snippet(snippet: str, nlp, taxonomy: SkillsTaxonomy) -> list[str]:
    """Find taxonomy skills mentioned in an experience description snippet."""
    if not snippet or not snippet.strip():
        return []
    from app.services.jd_parser import _build_phrase_matcher, _is_whole_word_match
    matcher, span_to_canonical = _build_phrase_matcher(nlp)
    doc = nlp(snippet)
    matches = matcher(doc)
    raw_spans = []
    for match_id, start, end in matches:
        if _is_whole_word_match(doc, start, end):
            raw_spans.append(Span(doc, start, end, label=match_id))
    filtered = filter_spans(raw_spans)
    found = set()
    for span in filtered:
        canonical = span_to_canonical.get(span.text.lower())
        if not canonical:
            canonical = doc.vocab.strings[span.label]
        found.add(canonical)
    return sorted(list(found))


def _parse_experience_section(
    exp_text: str, today: tuple[int, int], nlp=None, taxonomy=None
) -> tuple[list[ExperienceEntry], float, int, str]:
    """
    Parse experience entries, merge overlapping dates, clean titles,
    extract descriptions and embedded skills, and compute total experience years.
    """
    if nlp is None:
        nlp = _get_nlp()
    if taxonomy is None:
        taxonomy = get_taxonomy()

    lines = [l.strip() for l in exp_text.splitlines() if l.strip()]
    entries: list[ExperienceEntry] = []
    date_intervals: list[tuple[int, int]] = []
    internship_months = 0

    date_line_indices: list[tuple[int, tuple[tuple[int, int], tuple[int, int], bool]]] = []
    for i, line in enumerate(lines):
        date_res = _extract_dates_from_line(line, today)
        if date_res:
            date_line_indices.append((i, date_res))

    for idx, (i, date_res) in enumerate(date_line_indices):
        start_date, end_date, is_current = date_res

        # Calculate months for this entry
        start_idx = start_date[0] * 12 + start_date[1]
        end_idx = end_date[0] * 12 + end_date[1]

        if end_idx >= start_idx:
            months = end_idx - start_idx + 1
        else:
            months = 0

        # Determine title and company from line or preceding lines
        title = ""
        company = ""

        prev_limit = (date_line_indices[idx - 1][0] + 1) if idx > 0 else 0
        surrounding = lines[max(prev_limit, i - 2):i + 1]
        for sline in surrounding:
            if _extract_dates_from_line(sline, today):
                continue
            t_match = _COMMON_TITLES_PATTERN.search(sline)
            if t_match and not title:
                title = sline
            elif not company and sline != title and len(sline) < 50:
                company = sline

        # Clean title & company (A1)
        title, company = _clean_job_title_and_company(title, company)

        is_internship = "intern" in (title + " " + lines[i]).lower()
        surrounding_context = " ".join(surrounding).lower()
        is_break = any(
            term in (title + " " + company + " " + surrounding_context).lower()
            for term in ["career break", "sabbatical", "career gap", "parental leave", "maternity leave"]
        )

        # Collect description lines (A2)
        next_date_i = date_line_indices[idx + 1][0] if idx + 1 < len(date_line_indices) else len(lines)
        desc_lines = []
        for dline in lines[i + 1:next_date_i]:
            # Stop if encountering the next entry's title
            if idx + 1 < len(date_line_indices) and _COMMON_TITLES_PATTERN.search(dline):
                break
            desc_lines.append(dline)

        description = "\n".join(desc_lines).strip()[:1200]
        skills_in_entry = _extract_skills_from_snippet(description, nlp, taxonomy) if (nlp and taxonomy) else []

        entry = ExperienceEntry(
            title=title or ("Career Break" if is_break else "Software Professional"),
            company=company,
            start_date=f"{start_date[0]}-{start_date[1]:02d}",
            end_date="Present" if is_current else f"{end_date[0]}-{end_date[1]:02d}",
            months=months,
            is_current=is_current,
            is_internship=is_internship,
            description=description,
            skills_in_entry=skills_in_entry,
        )
        entries.append(entry)

        if is_internship:
            internship_months += months
        elif not is_break:
            date_intervals.append((start_idx, end_idx))

    if date_intervals:
        total_months = _merge_date_intervals(date_intervals)
        total_years = round(total_months / 12.0, 1)
        source = "date_ranges"
    else:
        stated_match = re.search(
            r"(?:over|more than|approx\.?|nearly)?\s*(\d+\.?\d*)\+?\s*years?\s*(?:of\s+)?(?:professional\s+)?(?:experience|exp)",
            exp_text,
            re.IGNORECASE,
        )
        if stated_match:
            total_years = float(stated_match.group(1))
            source = "stated_in_text"
        else:
            total_years = 0.0
            source = "date_ranges"

    return entries, total_years, internship_months, source


# ------------------------------------------------------------------
# Education Parsing
# ------------------------------------------------------------------

_DEGREE_MAPPING = [
    (re.compile(r"\b(?:ph\.?d|doctorate)\b", re.IGNORECASE), "phd", "Ph.D."),
    (re.compile(r"\b(?:m\.?tech|m\.?e\.?)\b", re.IGNORECASE), "master", "M.Tech"),
    (re.compile(r"\b(?:mca|m\.?c\.?a\.?)\b", re.IGNORECASE), "master", "MCA"),
    (re.compile(r"\b(?:mba|m\.?b\.?a\.?)\b", re.IGNORECASE), "master", "MBA"),
    (re.compile(r"\b(?:master'?s?(?:\s+degree)?|m\.?s\.?c?\.?)\b", re.IGNORECASE), "master", "Master's Degree"),
    (re.compile(r"\b(?:b\.?tech|b\.?e\.?)\b", re.IGNORECASE), "bachelor", "B.Tech"),
    (re.compile(r"\b(?:bca|b\.?c\.?a\.?)\b", re.IGNORECASE), "bachelor", "BCA"),
    (re.compile(r"\b(?:bachelor'?s?(?:\s+degree)?|b\.?s\.?c?\.?)\b", re.IGNORECASE), "bachelor", "Bachelor's Degree"),
    (re.compile(r"\b(?:diploma|polytechnic)\b", re.IGNORECASE), "diploma", "Diploma"),
]


def _parse_education_section(edu_text: str) -> list[EducationEntry]:
    """Parse degrees, institution, field, and year from education section."""
    lines = [l.strip() for l in edu_text.splitlines() if l.strip()]
    entries: list[EducationEntry] = []

    for line in lines:
        for pat, level, deg_name in _DEGREE_MAPPING:
            if pat.search(line):
                # Extract year if present
                y_match = re.search(r"\b(19\d{2}|20\d{2})\b", line)
                year = int(y_match.group(0)) if y_match else None

                # Extract field (e.g. "in Computer Science")
                field = ""
                f_match = re.search(
                    r"(?:in|of)\s+([A-Za-z\s&]+?)(?:,|\||\(|$|\bfrom\b|\bwith\b|\d{4})",
                    line,
                    re.IGNORECASE,
                )
                if f_match:
                    field = f_match.group(1).strip()

                # Extract institution
                institution = ""
                inst_match = re.search(
                    r"(?:from|at)?\s*([A-Za-z\s\.,&]+?(?:University|College|Institute|School|IIT|NIT|BITS)[A-Za-z\s\.,&]*)",
                    line,
                    re.IGNORECASE,
                )
                if inst_match:
                    institution = inst_match.group(1).strip()

                entries.append(
                    EducationEntry(
                        degree=deg_name,
                        level=level,
                        field=field or "Computer Science",
                        institution=institution,
                        year=year,
                    )
                )
                break  # Matched one degree pattern for this line

    return entries


# ------------------------------------------------------------------
# Main Entry Point
# ------------------------------------------------------------------

def parse_resume(
    file_bytes: bytes, filename: str, today: tuple[int, int] = (2026, 11)
) -> ParsedResume:
    """
    Parse a resume from raw file bytes.

    Args:
        file_bytes: bytes of the PDF or DOCX file
        filename: original filename
        today: (year, month) to evaluate 'Present' / 'Current' (default: 2026, 11)

    Returns:
        ParsedResume structured object.
    """
    nlp = _get_nlp()
    taxonomy = get_taxonomy()

    # 1. Extract clean plain text
    raw_text = extract_text(file_bytes, filename)

    # 2. Segment sections
    sections = _segment_sections(raw_text)

    # 3. Extract Name & Contact Info
    name, name_warnings = _extract_name(raw_text, filename, nlp)
    contact = _extract_contact_info(raw_text)

    # 4. Extract Skills across resume
    skills = _extract_resume_skills(raw_text, sections, nlp, taxonomy)

    # 5. Extract Experience & total years
    exp_text = sections.get("experience", "")
    if not exp_text and "projects" in sections:
        # Fresher or project-only
        exp_text = sections.get("projects", "")

    exp_entries, total_years, internship_months, exp_source = _parse_experience_section(
        exp_text, today, nlp, taxonomy
    )

    # If no experience section, check full text
    if not exp_entries and total_years == 0.0:
        stated = re.search(
            r"(?:over|more than|approx\.?|nearly)?\s*(\d+\.?\d*)\+?\s*years?\s*(?:of\s+)?(?:professional\s+)?(?:experience|exp)",
            raw_text,
            re.IGNORECASE,
        )
        if stated:
            total_years = float(stated.group(1))
            exp_source = "stated_in_text"

    # Extract distinct clean job titles
    job_titles = []
    seen_titles = set()
    for e in exp_entries:
        cleaned_t, _ = _clean_job_title_and_company(e.title, e.company)
        lower_t = cleaned_t.lower()
        if (
            cleaned_t
            and lower_t not in seen_titles
            and lower_t not in {"career break", "software professional"}
        ):
            seen_titles.add(lower_t)
            job_titles.append(cleaned_t)

    # 6. Extract Education
    edu_text = sections.get("education", "") + "\n" + raw_text
    education = _parse_education_section(edu_text)

    # 7. Summary
    summary = sections.get("summary", "")
    if not summary:
        # Fallback to first two sentences of non-header lines
        body_lines = [l.strip() for l in raw_text.splitlines()[:6] if l.strip()]
        summary = " ".join(body_lines[:2])

    # 8. Warnings
    warnings = list(name_warnings)
    if not contact["email"]:
        warnings.append("No email address found")
    if not contact["phone"]:
        warnings.append("No phone number found")
    if not exp_entries and total_years == 0.0:
        warnings.append("No work history or dates detected (fresher or unparseable)")

    return ParsedResume(
        name=name,
        email=contact["email"],
        phone=contact["phone"],
        linkedin_url=contact["linkedin_url"],
        github_url=contact["github_url"],
        location=contact["location"],
        total_experience_years=total_years,
        internship_months=internship_months,
        experience_source=exp_source,
        job_titles=job_titles,
        skills=skills,
        experience_entries=exp_entries,
        education=education,
        summary=summary,
        sections=sections,
        parse_warnings=warnings,
    )
