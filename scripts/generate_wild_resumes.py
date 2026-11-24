"""
scripts/generate_wild_resumes.py — Generate 10 synthetic "wild" resumes and ground truth.
"""

import json
from pathlib import Path
import docx
import fitz  # PyMuPDF

ROOT_DIR = Path(__file__).resolve().parent.parent
WILD_DIR = ROOT_DIR / "sample_data" / "resumes_wild"
WILD_DIR.mkdir(parents=True, exist_ok=True)
GROUND_TRUTH_FILE = WILD_DIR / "ground_truth_wild.json"


def generate_all():
    print("Generating 10 wild synthetic resumes in sample_data/resumes_wild/...")

    # -------------------------------------------------------------
    # 1. wild_01_no_headings.txt
    # Free-flowing text, no section headers
    # -------------------------------------------------------------
    text_01 = (
        "Alex Taylor is an experienced software engineer with 4.5 years of experience building Python and FastAPI microservices. "
        "He can be reached at alex.taylor.dev@example.com or by telephone at +1-555-019-2834. "
        "Alex graduated from Boston University with a Bachelor of Science in Computer Science in May 2020. "
        "From June 2022 to November 2026 he has worked as a Senior Software Engineer at CloudNet Systems where he architected REST APIs, PostgreSQL databases, Docker containers, and automated CI/CD pipelines. "
        "Prior to that, from June 2020 to May 2022 he worked as a Junior Developer at DataFlow Corp developing Python backend scripts and SQL queries. "
        "His core technical competencies include Python, FastAPI, Docker, PostgreSQL, REST API, Git, Redis, and Linux."
    )
    (WILD_DIR / "wild_01_no_headings.txt").write_text(text_01, encoding="utf-8")
    print("  [TXT] Created wild_01_no_headings.txt")

    # -------------------------------------------------------------
    # 2. wild_02_table_skills.docx
    # Skills laid out in a table grid in DOCX
    # -------------------------------------------------------------
    doc_02 = docx.Document()
    doc_02.add_heading("Priyesh Sen", 0)
    doc_02.add_paragraph("Email: priyesh.sen@example.com | Phone: +91-9876543210 | Location: Bengaluru, India")
    doc_02.add_heading("Technical Skills Overview", level=1)

    table_02 = doc_02.add_table(rows=4, cols=2)
    skills_grid = [
        ("Languages", "Java, Python, SQL"),
        ("Frameworks", "Spring Boot, Hibernate, Django"),
        ("Databases", "PostgreSQL, MySQL, Redis"),
        ("DevOps & Cloud", "AWS, Docker, Git, CI/CD, Linux"),
    ]
    for row_idx, (cat, val) in enumerate(skills_grid):
        table_02.cell(row_idx, 0).text = cat
        table_02.cell(row_idx, 1).text = val

    doc_02.add_heading("Work Experience", level=1)
    p_exp = doc_02.add_paragraph()
    p_exp.add_run("Java Backend Developer | FinTech Solutions (June 2021 – November 2024)\n").bold = True
    p_exp.add_run(
        "Developed scalable banking microservices using Java and Spring Boot. "
        "Managed PostgreSQL databases and deployed Dockerized services to AWS EC2. "
        "Built automated CI/CD pipelines with Git."
    )

    doc_02.add_heading("Education", level=1)
    doc_02.add_paragraph("B.Tech in Information Technology | Anna University (2017 – 2021)")
    doc_02.save(str(WILD_DIR / "wild_02_table_skills.docx"))
    print("  [DOCX] Created wild_02_table_skills.docx")

    # -------------------------------------------------------------
    # 3. wild_03_header_contact.docx
    # Contact details only in DOCX header
    # -------------------------------------------------------------
    doc_03 = docx.Document()
    section_03 = doc_03.sections[0]
    header_03 = section_03.header
    header_p = header_03.paragraphs[0]
    header_p.text = "Natasha Romanoff | Email: natasha.code@example.com | Phone: +1-555-014-9988 | Austin, TX"

    doc_03.add_heading("Natasha Romanoff", 0)
    doc_03.add_paragraph("Full Stack Software Engineer specializing in modern cloud architectures.")

    doc_03.add_heading("Skills", level=1)
    doc_03.add_paragraph("JavaScript, TypeScript, React, Node.js, Express, MongoDB, Docker, Git, REST API")

    doc_03.add_heading("Professional Experience", level=1)
    p3 = doc_03.add_paragraph()
    p3.add_run("Senior Full Stack Developer | WebScale Inc (January 2021 – Present)\n").bold = True
    p3.add_run(
        "Designed and implemented high-volume web applications using React, TypeScript, and Node.js. "
        "Containerized services with Docker and integrated MongoDB clusters."
    )

    doc_03.add_heading("Education", level=1)
    doc_03.add_paragraph("Bachelor of Science in Computer Science | University of Texas (2016 – 2020)")
    doc_03.save(str(WILD_DIR / "wild_03_header_contact.docx"))
    print("  [DOCX] Created wild_03_header_contact.docx")

    # -------------------------------------------------------------
    # 4. wild_04_twocolumn_sidebar.pdf
    # Two-column PDF: left sidebar holding skills and contact, right column holding experience
    # -------------------------------------------------------------
    doc_04 = fitz.open()
    page_04 = doc_04.new_page(width=612, height=792)

    left_text_04 = (
        "CARLOS MENDEZ\n"
        "Frontend Engineer\n\n"
        "CONTACT\n"
        "Email:\n"
        "carlos.mendez@example.com\n\n"
        "Phone:\n"
        "+1-555-012-7744\n\n"
        "Location:\n"
        "Chicago, IL\n\n"
        "TECHNICAL SKILLS\n"
        "- React\n"
        "- Next.js\n"
        "- JavaScript\n"
        "- TypeScript\n"
        "- HTML5 & CSS3\n"
        "- Tailwind CSS\n"
        "- Redux Toolkit\n"
        "- Git & GitHub\n"
        "- REST API\n\n"
        "EDUCATION\n"
        "B.S. Software Engineering\n"
        "Illinois Tech (2016-2020)"
    )

    right_text_04 = (
        "PROFESSIONAL SUMMARY\n"
        "Creative Frontend Engineer with 4 years of hands-on experience building performant, accessible web apps in React.\n\n"
        "PROFESSIONAL EXPERIENCE\n\n"
        "Senior Frontend Developer | Apex Interactive\n"
        "August 2020 – Present (4 years 3 months)\n"
        "- Spearheaded frontend architecture migration from legacy code to React 18 and Next.js.\n"
        "- Developed responsive, reusable design component libraries with Tailwind CSS and TypeScript.\n"
        "- Optimized Core Web Vitals, achieving a 45% reduction in first contentful paint (FCP).\n"
        "- Collaborated with UI/UX designers and backend teams via REST API integration.\n\n"
        "Frontend Intern | Digital Wave Agency\n"
        "January 2020 – June 2020\n"
        "- Built interactive landing pages using JavaScript, HTML, and CSS."
    )

    rect_left_04 = fitz.Rect(45, 45, 210, 747)
    rect_right_04 = fitz.Rect(225, 45, 567, 747)

    # Draw vertical divider
    shape_04 = page_04.new_shape()
    shape_04.draw_line(fitz.Point(217, 45), fitz.Point(217, 747))
    shape_04.finish(color=(0.8, 0.85, 0.8), width=1)
    shape_04.commit()

    page_04.insert_textbox(rect_left_04, left_text_04, fontsize=9, fontname="helv", lineheight=1.2)
    page_04.insert_textbox(rect_right_04, right_text_04, fontsize=10, fontname="helv", lineheight=1.25)
    doc_04.save(str(WILD_DIR / "wild_04_twocolumn_sidebar.pdf"))
    doc_04.close()
    print("  [PDF] Created wild_04_twocolumn_sidebar.pdf")

    # -------------------------------------------------------------
    # 5. wild_05_varied_dates.pdf
    # Dates in varied, irregular formats
    # -------------------------------------------------------------
    doc_05 = fitz.open()
    page_05 = doc_05.new_page(width=612, height=792)
    rect_05 = fitz.Rect(54, 45, 558, 747)

    text_05 = (
        "HARUTO TAKAHASHI\n"
        "Email: haruto.t@example.com | Phone: +81-90-1234-5678 | Tokyo, Japan\n\n"
        "SUMMARY\n"
        "Senior Cloud Infrastructure and Backend Engineer since 2018 with a track record across diverse startups.\n\n"
        "EXPERIENCE\n\n"
        "Principal Platform Architect | Sakura Cloud Systems\n"
        "2023 – Present\n"
        "Lead enterprise Kubernetes clusters and multi-region AWS cloud deployments with Terraform.\n\n"
        "Senior Backend Developer | Tokyo Tech Labs\n"
        "Jan-2020 to Dec-2022\n"
        "Developed high-throughput Go and Python microservices. Maintained PostgreSQL and Redis datastores.\n\n"
        "DevOps Engineer | Nihon Web Services\n"
        "Sept '21 – Mar '23 (Concurrent Part-time Consulting)\n"
        "Automated CI/CD delivery pipelines using Docker and GitHub Actions.\n\n"
        "Software Engineer | StartUp Zero\n"
        "since 2018\n"
        "Engineered foundational REST APIs in Python and configured Linux servers.\n\n"
        "SKILLS\n"
        "Go, Python, AWS, Docker, Kubernetes, Terraform, PostgreSQL, Redis, Linux, CI/CD, Git\n\n"
        "EDUCATION\n"
        "B.S. in Computer Science | University of Tokyo (graduated 2018)"
    )
    page_05.insert_textbox(rect_05, text_05, fontsize=10, fontname="helv", lineheight=1.25)
    doc_05.save(str(WILD_DIR / "wild_05_varied_dates.pdf"))
    doc_05.close()
    print("  [PDF] Created wild_05_varied_dates.pdf")

    # -------------------------------------------------------------
    # 6. wild_06_experience_stated_only.txt
    # Experience stated only in prose without job date ranges
    # -------------------------------------------------------------
    text_06 = (
        "Samuel O'Connor\n"
        "samuel.oconnor@example.com | +44-7700-900123 | London, UK\n\n"
        "Professional Summary:\n"
        "I have over 5 years of professional experience in enterprise Java and microservices architecture. "
        "Throughout my career as a Senior Software Engineer, I have architected distributed systems using Spring Boot, Hibernate, and Apache Kafka. "
        "I possess deep expertise in PostgreSQL database tuning, Docker container orchestration, and continuous integration with Git and Jenkins. "
        "I hold a Bachelor of Science (Honours) degree in Computer Systems Engineering from the University of Manchester.\n\n"
        "Core Skills:\n"
        "Java, Spring Boot, Microservices, PostgreSQL, Kafka, Docker, Kubernetes, AWS, Git, JUnit, Agile, Linux."
    )
    (WILD_DIR / "wild_06_experience_stated_only.txt").write_text(text_06, encoding="utf-8")
    print("  [TXT] Created wild_06_experience_stated_only.txt")

    # -------------------------------------------------------------
    # 7. wild_07_indian_education.pdf
    # Indian education credentials and honorific Dr. R. K. Mehta
    # -------------------------------------------------------------
    doc_07 = fitz.open()
    page_07 = doc_07.new_page(width=612, height=792)
    rect_07 = fitz.Rect(54, 45, 558, 747)

    text_07 = (
        "DR. R. K. MEHTA\n"
        "Email: dr.rkmehta@example.com | Mobile: +91-9123456789 | Hyderabad, Telangana\n\n"
        "EXECUTIVE SUMMARY\n"
        "AI/ML Research Scientist with 6 years of expertise in NLP, Large Language Models, and deep learning.\n\n"
        "PROFESSIONAL EXPERIENCE\n\n"
        "Lead AI Scientist | Bharat AI Research Labs (July 2021 – Present)\n"
        "Trained domain-specific PyTorch transformers, fine-tuned BERT and LLM models, and deployed models via FastAPI.\n\n"
        "Machine Learning Engineer | DataCore India (August 2018 – June 2021)\n"
        "Engineered predictive algorithms in Python using Scikit-Learn, TensorFlow, and Pandas on AWS.\n\n"
        "EDUCATION & ACADEMICS\n\n"
        "- Ph.D. in Computer Science (NLP Specialization) | IIT Hyderabad (2018)\n"
        "- B.Tech (CSE) | XYZ Institute of Technology | CGPA 8.2 / 10 (2014)\n"
        "- Intermediate (12th Standard) | State Board of Intermediate Education | 91.4% (2010)\n\n"
        "TECHNICAL SKILLS\n"
        "Python, PyTorch, TensorFlow, NLP, Transformers, Scikit-Learn, FastAPI, Docker, AWS, Git"
    )
    page_07.insert_textbox(rect_07, text_07, fontsize=10, fontname="helv", lineheight=1.25)
    doc_07.save(str(WILD_DIR / "wild_07_indian_education.pdf"))
    doc_07.close()
    print("  [PDF] Created wild_07_indian_education.pdf")

    # -------------------------------------------------------------
    # 8. wild_08_senior_4page.pdf
    # 4-page senior CV with 6 roles, ligatures ("fi", "fl"), unicode bullets
    # -------------------------------------------------------------
    doc_08 = fitz.open()

    p1_text = (
        "ELIZABETH MONTGOMERY, Ph.D.\n"
        "Email: elizabeth.montgomery@example.com | Phone: +1-555-019-8877 | New York, NY\n\n"
        "EXECUTIVE PROFILE\n"
        "Distinguished enterprise architect with 15+ years of software leadership, system optimization, and technical strategy.\n\n"
        "CORE COMPETENCIES\n"
        "• Enterprise Java & Spring Ecosystem\n"
        "• Cloud Infrastructure (AWS & Azure)\n"
        "• High-throughput Distributed Systems\n"
        "• Relational & NoSQL Data Architecture\n"
        "• Team Mentorship & Agile Leadership\n\n"
        "CHRONOLOGICAL CAREER HISTORY\n\n"
        "Chief Technical Architect | Global FinTech Capital (2020 – Present)\n"
        "▪ Defined technological roadmap for multi-currency trade execution platform processing $20B daily volume.\n"
        "▪ Architected distributed microservices utilizing Java 21, Spring Boot 3, Apache Kafka, and PostgreSQL.\n"
        "▪ Supervised 42 principal engineers across 5 global timezones."
    )
    p2_text = (
        "ELIZABETH MONTGOMERY, Ph.D. — Page 2\n\n"
        "Principal Software Architect | Morgan Wealth Systems (2016 – 2020)\n"
        "▪ Spearheaded the cloud migration of 120+ legacy monolithic services into containerized Docker pods on Kubernetes.\n"
        "▪ Optimized database queries and connection pools, yielding a 4x throughput efficiency boost.\n"
        "▪ Implemented secure OAuth2 and mTLS authentication layers across external APIs.\n\n"
        "Senior Backend Lead | Enterprise Data Corp (2012 – 2016)\n"
        "▪ Designed robust RESTful microservices with Spring Framework and Hibernate ORM.\n"
        "▪ Directed automated CI/CD pipeline adoption with Git, Jenkins, and Ansible."
    )
    p3_text = (
        "ELIZABETH MONTGOMERY, Ph.D. — Page 3\n\n"
        "Senior Software Engineer | Vanguard Solutions (2009 – 2012)\n"
        "▪ Developed core algorithmic trading modules using Java and C++.\n"
        "▪ Managed Oracle database schemas and optimized index access paths.\n\n"
        "Software Engineer | Horizon Tech (2007 – 2009)\n"
        "▪ Built J2EE web applications with Struts and Servlets.\n"
        "▪ Collaborated in early Agile Scrum pilot teams."
    )
    p4_text = (
        "ELIZABETH MONTGOMERY, Ph.D. — Page 4\n\n"
        "Associate Developer | NextGen Software (2005 – 2007)\n"
        "▪ Maintained legacy Java backend scripts and JUnit test suites.\n\n"
        "ACADEMIC CREDENTIALS\n"
        "► Ph.D. in Computer Engineering | Columbia University (2005)\n"
        "► Master of Science in Computer Science | Cornell University (2001)\n"
        "► Bachelor of Science in Electrical Engineering | MIT (1999)\n\n"
        "PUBLICATIONS & PATENTS\n"
        "Published 8 peer-reviewed IEEE papers on distributed consensus and transaction isolation."
    )

    for p_content in [p1_text, p2_text, p3_text, p4_text]:
        p = doc_08.new_page(width=612, height=792)
        p.insert_textbox(fitz.Rect(54, 45, 558, 747), p_content, fontsize=10, fontname="helv", lineheight=1.25)

    doc_08.save(str(WILD_DIR / "wild_08_senior_4page.pdf"))
    doc_08.close()
    print("  [PDF] Created wild_08_senior_4page.pdf (4 pages)")

    # -------------------------------------------------------------
    # 9. wild_09_scanned_image.pdf
    # Scanned / image-only PDF with zero selectable text layer
    # -------------------------------------------------------------
    doc_09 = fitz.open()
    page_09 = doc_09.new_page(width=612, height=792)
    # Draw vector rectangle and graphics without ANY text
    shape_09 = page_09.new_shape()
    shape_09.draw_rect(fitz.Rect(100, 100, 500, 700))
    shape_09.finish(color=(0.3, 0.3, 0.3), fill=(0.95, 0.95, 0.95))
    shape_09.commit()
    doc_09.save(str(WILD_DIR / "wild_09_scanned_image.pdf"))
    doc_09.close()
    print("  [PDF] Created wild_09_scanned_image.pdf (zero text layer)")

    # -------------------------------------------------------------
    # 10. wild_10_duplicate.pdf
    # Identical content to wild_01_no_headings.txt in PDF format
    # -------------------------------------------------------------
    doc_10 = fitz.open()
    page_10 = doc_10.new_page(width=612, height=792)
    page_10.insert_textbox(fitz.Rect(54, 45, 558, 747), text_01, fontsize=10, fontname="helv", lineheight=1.25)
    doc_10.save(str(WILD_DIR / "wild_10_duplicate.pdf"))
    doc_10.close()
    print("  [PDF] Created wild_10_duplicate.pdf (duplicate of wild_01)")

    # -------------------------------------------------------------
    # 11. wild_keyword_stuffing.txt
    # 40 JD skills in raw block, 0 experience, 0 projects
    # -------------------------------------------------------------
    text_stuffing = (
        "Jordan Miller\n"
        "jordan.stuffing@example.com | +1-555-010-4433\n\n"
        "TECHNICAL SKILLS:\n"
        "Java, Spring Boot, Microservices, PostgreSQL, MySQL, Docker, Kubernetes, AWS, REST API, Git, "
        "JUnit, CI/CD, Redis, Linux, Apache Kafka, Elasticsearch, Hibernate, React, TypeScript, JavaScript, "
        "HTML, CSS, Tailwind CSS, Python, PyTorch, TensorFlow, Machine Learning, Deep Learning, NLP, Scikit-Learn, "
        "SQL, MongoDB, GraphQL, Node.js, Next.js, Redux, C++, Go, Terraform, Agile."
    )
    (WILD_DIR / "wild_keyword_stuffing.txt").write_text(text_stuffing, encoding="utf-8")
    print("  [TXT] Created wild_keyword_stuffing.txt")

    # -------------------------------------------------------------
    # Write Ground Truth JSON BEFORE evaluating
    # -------------------------------------------------------------
    ground_truth = {
        "wild_01_no_headings.txt": {
            "name": "Alex Taylor",
            "email": "alex.taylor.dev@example.com",
            "phone": "+1-555-019-2834",
            "degree_level": "bachelor",
            "experience_years": 4.5,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "REST API", "Git", "Redis", "Linux", "CI/CD"],
        },
        "wild_02_table_skills.docx": {
            "name": "Priyesh Sen",
            "email": "priyesh.sen@example.com",
            "phone": "+91-9876543210",
            "degree_level": "bachelor",
            "experience_years": 3.4,
            "skills": ["Java", "Spring Boot", "PostgreSQL", "AWS", "Docker", "Git", "CI/CD", "Linux", "MySQL", "Redis", "Python"],
        },
        "wild_03_header_contact.docx": {
            "name": "Natasha Romanoff",
            "email": "natasha.code@example.com",
            "phone": "+1-555-014-9988",
            "degree_level": "bachelor",
            "experience_years": 3.8,
            "skills": ["JavaScript", "TypeScript", "React", "Node.js", "Express", "MongoDB", "Docker", "Git", "REST API"],
        },
        "wild_04_twocolumn_sidebar.pdf": {
            "name": "Carlos Mendez",
            "email": "carlos.mendez@example.com",
            "phone": "+1-555-012-7744",
            "degree_level": "bachelor",
            "experience_years": 4.25,
            "skills": ["React", "Next.js", "JavaScript", "TypeScript", "HTML", "CSS", "Tailwind CSS", "Redux", "Git", "REST API"],
        },
        "wild_05_varied_dates.pdf": {
            "name": "Haruto Takahashi",
            "email": "haruto.t@example.com",
            "phone": "+81-90-1234-5678",
            "degree_level": "bachelor",
            "experience_years": 6.0,
            "skills": ["Go", "Python", "AWS", "Docker", "Kubernetes", "Terraform", "PostgreSQL", "Redis", "Linux", "CI/CD", "Git"],
        },
        "wild_06_experience_stated_only.txt": {
            "name": "Samuel O'Connor",
            "email": "samuel.oconnor@example.com",
            "phone": "+44-7700-900123",
            "degree_level": "bachelor",
            "experience_years": 5.0,
            "skills": ["Java", "Spring Boot", "Microservices", "PostgreSQL", "Kafka", "Docker", "Kubernetes", "AWS", "Git", "JUnit", "Agile", "Linux"],
        },
        "wild_07_indian_education.pdf": {
            "name": "Dr. R. K. Mehta",
            "email": "dr.rkmehta@example.com",
            "phone": "+91-9123456789",
            "degree_level": "phd",
            "experience_years": 6.25,
            "skills": ["Python", "PyTorch", "TensorFlow", "NLP", "Transformers", "Scikit-Learn", "FastAPI", "Docker", "AWS", "Git"],
        },
        "wild_08_senior_4page.pdf": {
            "name": "Elizabeth Montgomery",
            "email": "elizabeth.montgomery@example.com",
            "phone": "+1-555-019-8877",
            "degree_level": "phd",
            "experience_years": 15.0,
            "skills": ["Java", "Spring Boot", "Kafka", "PostgreSQL", "Docker", "Kubernetes", "AWS", "Azure", "Git", "Jenkins", "Ansible", "JUnit", "OAuth", "Microservices"],
        },
        "wild_09_scanned_image.pdf": {
            "name": None,
            "email": None,
            "phone": None,
            "degree_level": None,
            "experience_years": 0.0,
            "skills": [],
            "is_scanned": True,
        },
        "wild_10_duplicate.pdf": {
            "name": "Alex Taylor",
            "email": "alex.taylor.dev@example.com",
            "phone": "+1-555-019-2834",
            "degree_level": "bachelor",
            "experience_years": 4.5,
            "skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "REST API", "Git", "Redis", "Linux", "CI/CD"],
            "is_duplicate_of": "alex.taylor.dev@example.com",
        },
    }

    GROUND_TRUTH_FILE.write_text(json.dumps(ground_truth, indent=2), encoding="utf-8")
    print(f"\nSaved Ground Truth metadata to {GROUND_TRUTH_FILE.name}")


if __name__ == "__main__":
    generate_all()
