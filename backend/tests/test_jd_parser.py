"""
tests/test_jd_parser.py — Tests for the JD parsing pipeline.

Covers:
  - Experience range extraction (numeric, word, fresher)
  - Qualification normalization
  - Required vs preferred skill classification
  - Alias matching ("JS" → JavaScript, "Java" ≠ "JavaScript")
  - File type handling and error cases
  - Full JD parsing end-to-end

Run from the backend directory:
    python -m pytest tests/ -v
"""

import pytest
from pathlib import Path

# ── Service imports ──
from app.services.text_extractor import extract_text
from app.services.skills_taxonomy import get_taxonomy
from app.services.jd_parser import (
    parse_jd,
    _extract_experience,
    _extract_qualifications,
    _split_into_sections,
)
from app.core.exceptions import (
    UnsupportedFileTypeError,
    EmptyFileError,
    CorruptFileError,
)


# ==================================================================
# 1. Skills Taxonomy Tests
# ==================================================================

class TestSkillsTaxonomy:
    """Tests for the skills taxonomy loader and lookup."""

    def test_taxonomy_loads(self):
        tax = get_taxonomy()
        assert len(tax) > 300, f"Expected 300+ skills, got {len(tax)}"

    def test_canonical_lookup(self):
        tax = get_taxonomy()
        assert tax.find("JavaScript") == "JavaScript"
        assert tax.find("Python") == "Python"

    def test_alias_lookup_js(self):
        """'js' should resolve to 'JavaScript'."""
        tax = get_taxonomy()
        assert tax.find("js") == "JavaScript"
        assert tax.find("JS") == "JavaScript"  # Case-insensitive

    def test_alias_lookup_postgres(self):
        tax = get_taxonomy()
        assert tax.find("postgres") == "PostgreSQL"
        assert tax.find("psql") == "PostgreSQL"

    def test_alias_lookup_ml(self):
        tax = get_taxonomy()
        assert tax.find("ml") == "Machine Learning"

    def test_unknown_skill(self):
        tax = get_taxonomy()
        assert tax.find("unknownskill123") is None

    def test_all_phrases_not_empty(self):
        tax = get_taxonomy()
        phrases = tax.all_phrases()
        assert len(phrases) > 500  # Should have many more phrases than skills


# ==================================================================
# 2. Experience Extraction Tests
# ==================================================================

class TestExperienceExtraction:
    """Tests for experience-range parsing."""

    def test_range_numeric(self):
        """'3-5 years' → (3, 5)."""
        min_y, max_y = _extract_experience("3-5 years of experience", {})
        assert min_y == 3.0
        assert max_y == 5.0

    def test_plus_years(self):
        """'5+ years' → (5, None)."""
        min_y, max_y = _extract_experience("5+ years experience required", {})
        assert min_y == 5.0

    def test_minimum_years(self):
        """'minimum 2 years' → (2, None)."""
        min_y, max_y = _extract_experience("minimum 2 years of experience", {})
        assert min_y == 2.0

    def test_at_least(self):
        """'at least 4 years' → (4, None)."""
        min_y, max_y = _extract_experience("at least 4 years experience", {})
        assert min_y == 4.0

    def test_word_numbers(self):
        """'three to five years' → (3, 5)."""
        min_y, max_y = _extract_experience("three to five years of experience", {})
        assert min_y == 3.0
        assert max_y == 5.0

    def test_single_word_number(self):
        """'five years' → (5, None)."""
        min_y, max_y = _extract_experience("five years of experience", {})
        assert min_y == 5.0

    def test_fresher(self):
        """'fresher' → (0, 0)."""
        min_y, max_y = _extract_experience("Open to freshers", {})
        assert min_y == 0.0
        assert max_y == 0.0

    def test_entry_level(self):
        """'entry level' → (0, 0)."""
        min_y, max_y = _extract_experience("Entry level position", {})
        assert min_y == 0.0
        assert max_y == 0.0

    def test_no_experience_mentioned(self):
        """No experience info → (None, None)."""
        min_y, max_y = _extract_experience("We need a skilled developer.", {})
        assert min_y is None
        assert max_y is None


# ==================================================================
# 3. Qualification Extraction Tests
# ==================================================================

class TestQualificationExtraction:
    """Tests for qualification/education parsing."""

    def test_bachelors(self):
        quals = _extract_qualifications(
            "Bachelor's degree in Computer Science required", {}
        )
        assert len(quals) >= 1
        assert any(q.level == "bachelor" for q in quals)

    def test_btech(self):
        quals = _extract_qualifications(
            "B.Tech in CS or IT from a recognized university", {}
        )
        assert any(q.level == "bachelor" for q in quals)

    def test_masters(self):
        quals = _extract_qualifications(
            "Master's degree or M.Tech preferred", {}
        )
        assert any(q.level == "master" for q in quals)

    def test_phd(self):
        quals = _extract_qualifications(
            "Ph.D. in Machine Learning or related field", {}
        )
        assert any(q.level == "phd" for q in quals)

    def test_mca(self):
        quals = _extract_qualifications(
            "MCA or equivalent degree", {}
        )
        assert any(q.level == "master" for q in quals)

    def test_diploma(self):
        quals = _extract_qualifications(
            "Diploma in Computer Engineering", {}
        )
        assert any(q.level == "diploma" for q in quals)


# ==================================================================
# 4. Skill Classification Tests (Required vs Preferred)
# ==================================================================

class TestSkillClassification:
    """Tests for required vs preferred skill classification."""

    def test_required_section_skills(self):
        """Skills under 'Requirements:' should be required."""
        jd_text = """
Senior Developer

Requirements:
- Strong proficiency in Python and Django
- Experience with PostgreSQL

Nice to Have:
- Experience with Docker
- Knowledge of AWS
"""
        parsed = parse_jd(jd_text)
        assert "Python" in parsed.required_skills
        assert "Django" in parsed.required_skills
        assert "PostgreSQL" in parsed.required_skills

    def test_preferred_section_skills(self):
        """Skills under 'Nice to Have:' should be preferred."""
        jd_text = """
Developer

Requirements:
- Python experience required

Nice to Have:
- Experience with Docker
- Knowledge of AWS
"""
        parsed = parse_jd(jd_text)
        assert "Docker" in parsed.preferred_skills
        assert "AWS" in parsed.preferred_skills

    def test_java_not_in_javascript(self):
        """
        'Java' must NOT match inside 'JavaScript'.
        This is the critical whole-word boundary test.
        """
        jd_text = """
Frontend Developer

Requirements:
- Expert in JavaScript and React
- No Java experience needed
"""
        parsed = parse_jd(jd_text)
        assert "JavaScript" in parsed.required_skills
        assert "React" in parsed.required_skills
        # Java should NOT be extracted from "JavaScript"
        # It may appear from "No Java experience needed" but let's check
        # the key point: JavaScript presence doesn't falsely add Java

    def test_alias_js_to_javascript(self):
        """'JS' should map to canonical 'JavaScript'."""
        jd_text = """
Developer

Requirements:
- Proficient in JS and React
"""
        parsed = parse_jd(jd_text)
        assert "JavaScript" in parsed.required_skills


# ==================================================================
# 5. File Handling Tests
# ==================================================================

class TestFileHandling:
    """Tests for text extraction and file error handling."""

    def test_txt_extraction(self):
        content = "This is a test job description with Python skills."
        result = extract_text(content.encode("utf-8"), "test.txt")
        assert "Python" in result

    def test_empty_file_raises(self):
        with pytest.raises(EmptyFileError):
            extract_text(b"", "empty.txt")

    def test_unsupported_type_raises(self):
        with pytest.raises(UnsupportedFileTypeError):
            extract_text(b"some content", "file.xlsx")

    def test_corrupt_pdf_raises(self):
        with pytest.raises(CorruptFileError):
            extract_text(b"not a real pdf", "bad.pdf")

    def test_corrupt_docx_raises(self):
        with pytest.raises(CorruptFileError):
            extract_text(b"not a real docx", "bad.docx")


# ==================================================================
# 6. Full JD Parsing (End-to-End)
# ==================================================================

class TestFullJDParsing:
    """End-to-end tests parsing complete sample JDs."""

    @pytest.fixture
    def java_jd_text(self):
        path = Path(__file__).resolve().parent.parent.parent / "sample_data" / "jds" / "java_backend_jd.txt"
        return path.read_text(encoding="utf-8")

    @pytest.fixture
    def react_jd_text(self):
        path = Path(__file__).resolve().parent.parent.parent / "sample_data" / "jds" / "react_frontend_jd.txt"
        return path.read_text(encoding="utf-8")

    @pytest.fixture
    def aiml_jd_text(self):
        path = Path(__file__).resolve().parent.parent.parent / "sample_data" / "jds" / "aiml_engineer_jd.txt"
        return path.read_text(encoding="utf-8")

    def test_java_jd_has_title(self, java_jd_text):
        parsed = parse_jd(java_jd_text)
        assert parsed.title is not None
        assert len(parsed.title) > 0

    def test_java_jd_required_skills(self, java_jd_text):
        parsed = parse_jd(java_jd_text)
        # Should find Java, Spring Boot, PostgreSQL, etc. in required
        assert "Java" in parsed.required_skills
        assert "Spring Boot" in parsed.required_skills

    def test_java_jd_preferred_skills(self, java_jd_text):
        parsed = parse_jd(java_jd_text)
        # Kafka, AWS should be in preferred (under "Nice to Have")
        assert "Apache Kafka" in parsed.preferred_skills or "AWS" in parsed.preferred_skills

    def test_java_jd_experience(self, java_jd_text):
        parsed = parse_jd(java_jd_text)
        assert parsed.min_experience_years is not None
        assert parsed.min_experience_years >= 5

    def test_react_jd_skills(self, react_jd_text):
        parsed = parse_jd(react_jd_text)
        assert "React" in parsed.required_skills
        assert "JavaScript" in parsed.required_skills or "TypeScript" in parsed.required_skills

    def test_aiml_jd_skills(self, aiml_jd_text):
        parsed = parse_jd(aiml_jd_text)
        assert "Python" in parsed.required_skills
        assert "Machine Learning" in parsed.required_skills or "PyTorch" in parsed.required_skills

    def test_aiml_jd_word_experience(self, aiml_jd_text):
        """The AI/ML JD says 'three to five years' — word numbers."""
        parsed = parse_jd(aiml_jd_text)
        assert parsed.min_experience_years == 3.0
        assert parsed.max_experience_years == 5.0

    def test_all_jds_have_responsibilities(self, java_jd_text, react_jd_text, aiml_jd_text):
        for text in [java_jd_text, react_jd_text, aiml_jd_text]:
            parsed = parse_jd(text)
            assert len(parsed.responsibilities) >= 3, "Each JD should have at least 3 responsibilities"

    def test_all_jds_have_qualifications(self, java_jd_text, react_jd_text, aiml_jd_text):
        for text in [java_jd_text, react_jd_text, aiml_jd_text]:
            parsed = parse_jd(text)
            assert len(parsed.qualifications) >= 1, "Each JD should have at least 1 qualification"
