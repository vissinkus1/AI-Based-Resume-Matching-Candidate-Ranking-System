"""
tests/test_resume_parser.py — Unit tests for Resume Parsing Service.

Covers:
  - Date range parsing across 6 distinct date formats
  - Injected `today` handling for "Present" / "Current"
  - Non-overlapping date interval merger (parallel jobs)
  - Internship separation
  - Career break / sabbatical exclusion
  - Email & phone extraction across international patterns
  - Name extraction heuristics and filename fallback
  - Education degree level normalization (bachelor, master, phd, diploma)
  - Whole-pipeline integration test on sample resume
"""

import pytest
from app.services.resume_parser import (
    parse_resume,
    _extract_dates_from_line,
    _merge_date_intervals,
    _parse_experience_section,
    _extract_contact_info,
    _parse_education_section,
    _extract_name,
    _clean_job_title_and_company,
    _get_nlp,
)


# ------------------------------------------------------------------
# Date Range Parsing Across Formats
# ------------------------------------------------------------------

def test_date_range_month_year_to_month_year():
    """Format 1: 'Jan 2020 - Mar 2022'"""
    res = _extract_dates_from_line("Jan 2020 - Mar 2022", today=(2026, 11))
    assert res is not None
    start, end, is_current = res
    assert start == (2020, 1)
    assert end == (2022, 3)
    assert not is_current


def test_date_range_apostrophe_year():
    """Format 2: 'Jun'19 - Aug'21'"""
    res = _extract_dates_from_line("Jun'19 - Aug'21", today=(2026, 11))
    assert res is not None
    start, end, is_current = res
    assert start == (2019, 6)
    assert end == (2021, 8)
    assert not is_current


def test_date_range_year_to_year():
    """Format 3: '2019 - 2022'"""
    res = _extract_dates_from_line("2019 - 2022", today=(2026, 11))
    assert res is not None
    start, end, is_current = res
    assert start == (2019, 1)
    assert end == (2022, 12)
    assert not is_current


def test_date_range_month_year_to_present_injected_today():
    """Format 4: 'Jan 2024 - Present' with injected today (2026, 11)"""
    res = _extract_dates_from_line("Jan 2024 - Present", today=(2026, 11))
    assert res is not None
    start, end, is_current = res
    assert start == (2024, 1)
    assert end == (2026, 11)
    assert is_current is True


def test_date_range_since_year_format():
    """Format 5: 'Since Jan 2022'"""
    res = _extract_dates_from_line("Since Jan 2022", today=(2026, 11))
    assert res is not None
    start, end, is_current = res
    assert start == (2022, 1)
    assert end == (2026, 11)
    assert is_current is True


def test_date_range_slash_numeric_format():
    """Format 6: '06/2020 - 08/2023'"""
    res = _extract_dates_from_line("06/2020 - 08/2023", today=(2026, 11))
    assert res is not None
    start, end, is_current = res
    assert start == (2020, 6)
    assert end == (2023, 8)
    assert not is_current


# ------------------------------------------------------------------
# Overlapping Intervals & Experience Merging
# ------------------------------------------------------------------

def test_merge_intervals_disjoint():
    """Two disjoint 12-month periods should sum to 24 months."""
    # 2020-01 to 2020-12 (12 mos)
    # 2022-01 to 2022-12 (12 mos)
    p1 = (2020 * 12 + 1, 2020 * 12 + 12)
    p2 = (2022 * 12 + 1, 2022 * 12 + 12)
    total_months = _merge_date_intervals([p1, p2])
    assert total_months == 24


def test_merge_intervals_complete_subsumption():
    """Job B completely inside Job A: total months equals Job A only."""
    # Job A: Jan 2020 to Dec 2023 (48 mos)
    # Job B: Jun 2021 to Dec 2022 (19 mos concurrent)
    job_a = (2020 * 12 + 1, 2023 * 12 + 12)
    job_b = (2021 * 12 + 6, 2022 * 12 + 12)
    total_months = _merge_date_intervals([job_a, job_b])
    assert total_months == 48


def test_merge_intervals_partial_overlap():
    """Job A: Jan 2020 to Dec 2021 (24 mos). Job B: Jun 2021 to Dec 2022 (19 mos).
    Merged span: Jan 2020 to Dec 2022 (36 mos)."""
    job_a = (2020 * 12 + 1, 2021 * 12 + 12)
    job_b = (2021 * 12 + 6, 2022 * 12 + 12)
    total_months = _merge_date_intervals([job_a, job_b])
    assert total_months == 36


def test_internship_exclusion_from_total_experience():
    """Internships should be tracked in internship_months, not in full-time total years."""
    text = """
    Software Engineer | Acme Corp
    Jan 2023 - Present
    Software Engineering Intern | Beta Labs
    May 2022 - Aug 2022
    """
    entries, total_years, intern_months, _ = _parse_experience_section(
        text, today=(2026, 11)
    )
    # Jan 2023 to Nov 2026 = 47 months = 3.9 years
    assert total_years == 3.9
    # May 2022 to Aug 2022 = 4 months
    assert intern_months == 4


def test_career_break_sabbatical_exclusion():
    """Career break / sabbatical should not be counted toward work experience."""
    text = """
    Frontend Developer | Acme
    Jun 2024 - Present
    Career Break / Sabbatical
    Jan 2022 - May 2024
    Junior Developer | Beta
    Jan 2019 - Dec 2021
    """
    entries, total_years, _, _ = _parse_experience_section(
        text, today=(2026, 11)
    )
    # Jun 2024 to Nov 2026 (30 mos = 2.5y) + Jan 2019 to Dec 2021 (36 mos = 3.0y) = 5.5y
    # Sabbatical (29 mos) must NOT be included (which would yield 7.9y)
    assert total_years <= 5.7


# ------------------------------------------------------------------
# Contact Information Extraction
# ------------------------------------------------------------------

def test_email_extraction_variants():
    """Test standard and complex email patterns."""
    text = "Contact me at john.doe_123@sub.domain.co.uk or call tomorrow."
    info = _extract_contact_info(text)
    assert info["email"] == "john.doe_123@sub.domain.co.uk"


def test_phone_extraction_indian_and_us():
    """Test Indian +91 and US formatted phone numbers."""
    info1 = _extract_contact_info("Phone: +91 98765 43210")
    assert info1["phone"] == "+91 98765 43210"

    info2 = _extract_contact_info("Tel: +1 (415) 555-2671")
    assert info2["phone"] == "+1 415 555 2671"

    info3 = _extract_contact_info("Mobile: 9876543210")
    assert info3["phone"] == "9876543210"


def test_social_links_extraction():
    """Test LinkedIn and GitHub profile link extraction."""
    text = "Profiles: linkedin.com/in/jane-doe-dev and github.com/janedoe"
    info = _extract_contact_info(text)
    assert "linkedin.com/in/jane-doe-dev" in (info["linkedin_url"] or "")
    assert "github.com/janedoe" in (info["github_url"] or "")


# ------------------------------------------------------------------
# Name Extraction & Fallback
# ------------------------------------------------------------------

def test_name_extraction_from_header_line():
    nlp = _get_nlp()
    text = "ARAVIND SHARMA\naravind@email.com | +91 98765 43210\nSenior Engineer"
    name, warnings = _extract_name(text, "resume.pdf", nlp)
    assert name == "ARAVIND SHARMA"


def test_name_fallback_to_filename_when_unclear():
    nlp = _get_nlp()
    text = "1234567890\ninfo@email.com\nSome summary paragraph without clear name"
    name, warnings = _extract_name(text, "candidate_john_smith.pdf", nlp)
    assert "John Smith" in name or name == "Candidate John Smith"


# ------------------------------------------------------------------
# Education Parsing & Normalization
# ------------------------------------------------------------------

def test_education_level_mapping():
    """Ensure degrees map to normalized levels (bachelor, master, phd, diploma)."""
    text = """
    Bachelor of Technology in Computer Science | IIT Delhi | 2016 - 2020
    Master of Science in Artificial Intelligence | Stanford | 2020 - 2022
    Doctor of Philosophy (Ph.D.) in Machine Learning | MIT | 2022 - 2025
    Diploma in Web Development | Polytech | 2015
    """
    entries = _parse_education_section(text)
    levels = [e.level for e in entries]
    assert "bachelor" in levels
    assert "master" in levels
    assert "phd" in levels
    assert "diploma" in levels


# ------------------------------------------------------------------
# Full Pipeline Test
# ------------------------------------------------------------------

def test_parse_resume_full_pipeline():
    """Integration test parsing complete resume text."""
    sample_text = """
    Jane Doe
    jane.dev@example.com | +1 555 123 4567 | San Francisco, CA
    github.com/janedev

    PROFESSIONAL SUMMARY
    Full stack software engineer with 4 years of experience building web apps with React, Python, and PostgreSQL.

    TECHNICAL SKILLS
    React, JavaScript, Python, PostgreSQL, Docker, Git, REST API

    PROFESSIONAL EXPERIENCE
    Software Engineer | Tech Inc
    Jan 2023 - Present
    • Developed responsive React frontends and integrated with Python REST APIs.
    • Deployed microservices using Docker on AWS cloud.

    Junior Developer | Startup LLC
    Jan 2021 - Dec 2022
    • Wrote PostgreSQL queries and built backend services.

    EDUCATION
    Bachelor of Science in Computer Science | UC Berkeley | 2017 - 2021
    """
    parsed = parse_resume(
        file_bytes=sample_text.encode("utf-8"),
        filename="jane_doe_resume.txt",
        today=(2026, 11),
    )

    assert parsed.name == "Jane Doe"
    assert parsed.email == "jane.dev@example.com"
    assert parsed.phone == "+1 555 123 4567"
    assert parsed.total_experience_years >= 5.5
    assert len(parsed.skills) >= 5
    skill_names = [s.name for s in parsed.skills]
    assert "React" in skill_names
    assert "Python" in skill_names
    assert "PostgreSQL" in skill_names
    assert len(parsed.education) >= 1
    assert parsed.education[0].level == "bachelor"


# ------------------------------------------------------------------
# Part A1 & A2 Tests: Title Cleaning and Description Skills
# ------------------------------------------------------------------

def test_clean_job_titles_separators():
    """Verify title cleaning across pipe, dash, at, @, and comma separators."""
    # 1. Pipe
    t1, c1 = _clean_job_title_and_company("Senior Backend Engineer | Infosys Ltd, Bangalore")
    assert t1 == "Senior Backend Engineer"
    assert c1 == "Infosys Ltd"

    # 2. 'at'
    t2, c2 = _clean_job_title_and_company("Frontend Developer at Acme Corp")
    assert t2 == "Frontend Developer"
    assert c2 == "Acme Corp"

    # 3. '@'
    t3, c3 = _clean_job_title_and_company("Staff Research Scientist @ AI Labs")
    assert t3 == "Staff Research Scientist"
    assert c3 == "AI Labs"

    # 4. Dash
    t4, c4 = _clean_job_title_and_company("Lead Cloud Infrastructure Engineer - Apex Systems")
    assert t4 == "Lead Cloud Infrastructure Engineer"
    assert c4 == "Apex Systems"

    # 5. Comma
    t5, c5 = _clean_job_title_and_company("Senior Developer, TechCorp India")
    assert t5 == "Senior Developer"
    assert c5 == "TechCorp India"


def test_experience_entry_description_and_skills():
    """Verify description text collection and embedded skills detection per entry."""
    sample_text = """
    Software Engineer | CloudScale Inc
    Jan 2023 - Present
    • Built distributed event-driven microservices using Spring Boot and Apache Kafka.
    • Provisioned PostgreSQL databases and deployed containers with Docker onto Kubernetes.
    • Implemented automated CI/CD pipelines with Jenkins.
    """
    entries, total_years, _, _ = _parse_experience_section(
        sample_text, today=(2026, 11)
    )
    assert len(entries) == 1
    entry = entries[0]
    assert entry.title == "Software Engineer"
    assert entry.company == "CloudScale Inc"
    assert "Spring Boot" in entry.description
    assert "Apache Kafka" in entry.description
    assert len(entry.skills_in_entry) >= 4
    assert "Spring Boot" in entry.skills_in_entry
    assert "Docker" in entry.skills_in_entry
    assert "Kubernetes" in entry.skills_in_entry
    assert "PostgreSQL" in entry.skills_in_entry


def test_job_titles_clean_in_parsed_resume():
    """Verify ParsedResume.job_titles contains ONLY clean titles (no company/location)."""
    sample_text = """
    Alice Johnson
    alice@example.com | +1 555 987 6543
    PROFESSIONAL EXPERIENCE
    Senior Backend Engineer | Infosys Ltd, Bangalore
    Nov 2022 - Present
    • Developed Spring Boot applications.
    Software Engineer at Wipro Technologies
    Nov 2020 - Oct 2022
    • Wrote Java code and REST APIs.
    """
    parsed = parse_resume(
        file_bytes=sample_text.encode("utf-8"),
        filename="alice.txt",
        today=(2026, 11),
    )
    assert "Senior Backend Engineer" in parsed.job_titles
    assert "Software Engineer" in parsed.job_titles
    # Must NOT have pipe or company name in job_titles list
    for t in parsed.job_titles:
        assert "|" not in t
        assert "Infosys" not in t
        assert "Wipro" not in t

