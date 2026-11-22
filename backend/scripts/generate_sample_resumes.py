"""
scripts/generate_sample_resumes.py — Generate 12 synthetic test resumes and ground truth.

Generates 12 resumes (7 PDF, 5 DOCX) in sample_data/resumes/:
  1. candidate_01_aravind_sharma_java.pdf      (PDF standard single-column, Java Sr backend)
  2. candidate_02_priya_patel_react.docx        (DOCX table contact header, React frontend)
  3. candidate_03_rohit_verma_aiml.pdf          (PDF two-column layout, AI/ML NLP engineer)
  4. candidate_04_ananya_iyer_fullstack.docx    (DOCX "Jun'19 - Aug'21" date format, Fullstack)
  5. candidate_05_deepak_nair_fresher.pdf       (PDF Fresher, 0 yrs exp, projects + internship)
  6. candidate_06_vikram_singh_overlap.docx     (DOCX Overlapping jobs, Cloud/DevOps)
  7. candidate_07_meera_deshmukh_gap.pdf        (PDF Career gap sabbatical, React/Web)
  8. candidate_08_siddharth_reddy_senior.docx   (DOCX Senior 9.5 yrs, Lead Architect)
  9. candidate_09_kavita_krishnan_data_nlp.pdf  (PDF "Since 2022" format, PhD NLP Researcher)
  10. candidate_10_pooja_hegde_marketer.docx    (DOCX Negative example: Digital Marketer)
  11. candidate_11_rahul_kapoor_devops.pdf      (PDF DevOps/Cloud infrastructure)
  12. candidate_12_sneha_banerjee_react_java.pdf(PDF Comma-separated skills, Fullstack junior)

Also writes sample_data/resumes/ground_truth.json with exact ground-truth values.
"""

import json
from pathlib import Path
import docx
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
import fitz  # PyMuPDF

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
RESUMES_DIR = ROOT_DIR / "sample_data" / "resumes"
GROUND_TRUTH_FILE = RESUMES_DIR / "ground_truth.json"


# ------------------------------------------------------------------
# PDF Generation Helpers
# ------------------------------------------------------------------

def create_single_column_pdf(filepath: Path, text: str) -> None:
    """Generate a clean single-column PDF using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)  # Letter size
    rect = fitz.Rect(54, 45, 558, 747)  # 0.75 in margin

    # Draw header line or insert text
    page.insert_textbox(rect, text, fontsize=10, fontname="helv", lineheight=1.25)
    doc.save(str(filepath))
    doc.close()
    print(f"  [PDF] Created {filepath.name}")


def create_two_column_pdf(filepath: Path, left_text: str, right_text: str) -> None:
    """Generate a two-column PDF (sidebar + main column) using PyMuPDF."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)

    # Left sidebar: width 170 pt
    rect_left = fitz.Rect(45, 45, 215, 747)
    # Right main body: width 340 pt
    rect_right = fitz.Rect(230, 45, 567, 747)

    # Draw a subtle vertical divider
    shape = page.new_shape()
    shape.draw_line(fitz.Point(222, 45), fitz.Point(222, 747))
    shape.finish(color=(0.85, 0.85, 0.85), width=1)
    shape.commit()

    page.insert_textbox(rect_left, left_text, fontsize=9.5, fontname="helv", lineheight=1.25)
    page.insert_textbox(rect_right, right_text, fontsize=10, fontname="helv", lineheight=1.25)

    doc.save(str(filepath))
    doc.close()
    print(f"  [PDF 2-Col] Created {filepath.name}")


# ------------------------------------------------------------------
# DOCX Generation Helpers
# ------------------------------------------------------------------

def create_standard_docx(filepath: Path, sections: list[tuple[str, list[str]]], title_block: dict) -> None:
    """Generate a clean DOCX resume."""
    doc = docx.Document()
    # Set standard margins (0.75 inch)
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Name Header
    name_para = doc.add_paragraph()
    run = name_para.add_run(title_block["name"])
    run.font.size = Pt(18)
    run.font.bold = True
    run.font.color.rgb = RGBColor(30, 41, 59)

    # Contact line
    contact_parts = [
        title_block.get("email"),
        title_block.get("phone"),
        title_block.get("location"),
        title_block.get("linkedin"),
    ]
    contact_para = doc.add_paragraph(" | ".join([p for p in contact_parts if p]))
    contact_para.runs[0].font.size = Pt(9.5)
    contact_para.runs[0].font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    for heading, lines in sections:
        h = doc.add_paragraph()
        hrun = h.add_run(heading.upper())
        hrun.font.bold = True
        hrun.font.size = Pt(12)
        hrun.font.color.rgb = RGBColor(37, 99, 235)  # Indigo/Blue accent
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(3)

        for line in lines:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            if line.startswith("•") or line.startswith("-"):
                p.paragraph_format.left_indent = Inches(0.2)
            p_run = p.add_run(line)
            p_run.font.size = Pt(10)

    doc.save(str(filepath))
    print(f"  [DOCX] Created {filepath.name}")


def create_table_contact_docx(filepath: Path, sections: list[tuple[str, list[str]]], contact_data: dict) -> None:
    """Generate DOCX with contact header structured inside a table."""
    doc = docx.Document()
    for section in doc.sections:
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

    # Contact Table: 1 row, 2 cells (Name left, Contact right)
    table = doc.add_table(rows=1, cols=2)
    table.autofit = True
    c0 = table.cell(0, 0)
    c1 = table.cell(0, 1)

    p0 = c0.paragraphs[0]
    r0 = p0.add_run(contact_data["name"])
    r0.font.bold = True
    r0.font.size = Pt(18)
    r0.font.color.rgb = RGBColor(30, 41, 59)

    sub0 = p0.add_run(f"\n{contact_data.get('title', '')}")
    sub0.font.size = Pt(11)
    sub0.font.color.rgb = RGBColor(71, 85, 105)

    p1 = c1.paragraphs[0]
    p1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r1 = p1.add_run(
        f"Email: {contact_data['email']}\n"
        f"Phone: {contact_data['phone']}\n"
        f"Location: {contact_data.get('location', '')}\n"
        f"{contact_data.get('linkedin', '')}"
    )
    r1.font.size = Pt(9.5)
    r1.font.color.rgb = RGBColor(100, 116, 139)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)

    for heading, lines in sections:
        h = doc.add_paragraph()
        hrun = h.add_run(heading.upper())
        hrun.font.bold = True
        hrun.font.size = Pt(12)
        hrun.font.color.rgb = RGBColor(37, 99, 235)
        h.paragraph_format.space_before = Pt(8)
        h.paragraph_format.space_after = Pt(3)

        for line in lines:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(2)
            if line.startswith("•") or line.startswith("-"):
                p.paragraph_format.left_indent = Inches(0.2)
            p_run = p.add_run(line)
            p_run.font.size = Pt(10)

    doc.save(str(filepath))
    print(f"  [DOCX Table] Created {filepath.name}")


# ------------------------------------------------------------------
# Resume Definitions
# ------------------------------------------------------------------

def generate_all_resumes():
    RESUMES_DIR.mkdir(parents=True, exist_ok=True)

    ground_truth = {}

    # ==============================================================
    # 1. Aravind Sharma — Senior Java Backend Engineer (PDF)
    # ==============================================================
    f1 = "candidate_01_aravind_sharma_java.pdf"
    t1 = """ARAVIND SHARMA
aravind.sharma@email.com | +91 98765 43210 | Bangalore, India | linkedin.com/in/aravind-sharma

PROFESSIONAL SUMMARY
Senior Java Backend Engineer with 6 years of experience architecting and developing high-throughput microservices using Spring Boot, PostgreSQL, Apache Kafka, and Docker on AWS cloud.

TECHNICAL SKILLS
• Programming Languages: Java, Python, SQL
• Frameworks & Libraries: Spring Boot, Spring Data JPA, Hibernate, JUnit, Mockito
• Distributed Systems & Databases: Microservices, Apache Kafka, PostgreSQL, Redis, REST API
• Cloud & DevOps: Docker, Kubernetes, AWS (EC2, S3, RDS), Git, Maven, CI/CD

PROFESSIONAL EXPERIENCE
Senior Backend Engineer | Infosys Ltd, Bangalore
Nov 2022 - Present
• Designed and maintained 15+ Spring Boot microservices handling over 50,000 requests per second.
• Integrated Apache Kafka event streams for asynchronous order processing, reducing latency by 35%.
• Optimized PostgreSQL queries and introduced Redis caching, cutting database response times in half.
• Mentored 4 junior engineers on clean architecture, unit testing with JUnit, and code reviews.

Software Engineer | Wipro Technologies, Bangalore
Nov 2020 - Oct 2022
• Developed REST APIs using Java and Spring Boot for financial ledger services.
• Containerized backend applications using Docker and orchestrated deployments on Kubernetes clusters.
• Implemented automated CI/CD deployment pipelines using Jenkins and Git.

EDUCATION
Bachelor of Technology in Computer Science and Engineering | IIT Madras
2016 - 2020
"""
    create_single_column_pdf(RESUMES_DIR / f1, t1)
    ground_truth[f1] = {
        "name": "Aravind Sharma",
        "email": "aravind.sharma@email.com",
        "phone": "+91 98765 43210",
        "total_experience_years": 6.0,
        "education_level": "bachelor",
        "skills": ["Java", "Python", "SQL", "Spring Boot", "Hibernate", "JUnit", "Microservices", "Apache Kafka", "PostgreSQL", "Redis", "REST API", "Docker", "Kubernetes", "AWS", "Git", "CI/CD"],
    }

    # ==============================================================
    # 2. Priya Patel — React Frontend Developer (DOCX with table header)
    # ==============================================================
    f2 = "candidate_02_priya_patel_react.docx"
    c2 = {
        "name": "Priya Patel",
        "title": "Senior Frontend Developer",
        "email": "priya.patel@devmail.com",
        "phone": "+91 91234 56789",
        "location": "Pune, India",
        "linkedin": "linkedin.com/in/priya-patel-frontend",
    }
    s2 = [
        ("Summary", [
            "Passionate Frontend Developer with 6 years of experience building modern, responsive, and high-performance single page web applications using React, TypeScript, Redux, and Tailwind CSS."
        ]),
        ("Technical Skills", [
            "• Frontend: React, JavaScript, TypeScript, Next.js, Redux, HTML5, CSS3, Tailwind CSS",
            "• Testing & Tools: Jest, React Testing Library, Webpack, Vite, Git, npm, Figma",
            "• Concepts: Responsive Design, Single Page Application, REST API, Web Accessibility (WCAG)"
        ]),
        ("Work Experience", [
            "Senior Frontend Developer | TechCorp India, Pune",
            "Jan 2023 - Present",
            "• Lead development of the customer analytics web dashboard using React 18, TypeScript, and Tailwind CSS.",
            "• Migrated legacy jQuery frontends to Next.js with server-side rendering, improving First Contentful Paint by 40%.",
            "• Wrote comprehensive unit and integration tests using Jest and React Testing Library maintaining 88% test coverage.",
            "",
            "Frontend Web Developer | AppStudio Solutions, Pune",
            "Nov 2020 - Dec 2022",
            "• Built modular React components with Redux Toolkit for state management across an e-commerce platform.",
            "• Integrated REST APIs and optimized client-side bundle size using Webpack code splitting.",
            "• Collaborated with UX designers using Figma to deliver accessible WCAG-compliant responsive interfaces."
        ]),
        ("Education", [
            "Bachelor of Engineering in Information Technology",
            "Pune University | 2016 - 2020"
        ])
    ]
    create_table_contact_docx(RESUMES_DIR / f2, s2, c2)
    ground_truth[f2] = {
        "name": "Priya Patel",
        "email": "priya.patel@devmail.com",
        "phone": "+91 91234 56789",
        "total_experience_years": 6.0,
        "education_level": "bachelor",
        "skills": ["React", "JavaScript", "TypeScript", "Next.js", "Redux", "HTML5", "CSS3", "Tailwind CSS", "Jest", "Webpack", "Vite", "Git", "Figma", "REST API"],
    }

    # ==============================================================
    # 3. Rohit Verma — AI/ML NLP Engineer (PDF Two-Column)
    # ==============================================================
    f3 = "candidate_03_rohit_verma_aiml.pdf"
    left_t3 = """ROHIT VERMA
AI/ML Engineer

CONTACT
rohit.verma@aiml-labs.org
+1 415 555 2671
San Francisco, CA
linkedin.com/in/rohit-verma-ml
github.com/rohitverma-ai

EDUCATION
Master of Science in
Artificial Intelligence
Carnegie Mellon University
2021 - 2023

Bachelor of Technology in
Computer Science
NIT Surat
2017 - 2021

SKILLS
• Languages:
  Python, C++, SQL
• Frameworks:
  PyTorch, TensorFlow,
  Hugging Face, Scikit-Learn
• NLP & GenAI:
  Transformers, BERT,
  LLM, LangChain, Spacy
• Tools & Platforms:
  Docker, MLflow,
  AWS, Git, Linux
"""
    right_t3 = """PROFESSIONAL SUMMARY
Machine Learning Engineer with 3.4 years of industry experience developing and deploying deep learning and natural language processing models into enterprise production.

PROFESSIONAL EXPERIENCE
Machine Learning Engineer | DeepVision AI, San Francisco, CA
Jun 2023 - Present
• Fine-tuned transformer models (BERT, RoBERTa, and open-source LLMs) using PyTorch and Hugging Face for automated document classification and named entity extraction.
• Engineered scalable inference pipelines serving over 2 million daily predictions with Docker and FastAPI.
• Conducted model evaluation using precision, recall, and F1-score; tracked hyperparameter experiments with MLflow.
• Collaborated with data engineering teams to build automated feature extraction pipelines in Python and SQL.

PROJECTS
• Question Answering System: Implemented extractive QA using Hugging Face Transformers and FAISS vector indexing with 91% top-3 retrieval accuracy.
• Biomedical Named Entity Recognizer: Trained custom spaCy and PyTorch NER architectures on clinical medical abstracts.
"""
    create_two_column_pdf(RESUMES_DIR / f3, left_t3, right_t3)
    ground_truth[f3] = {
        "name": "Rohit Verma",
        "email": "rohit.verma@aiml-labs.org",
        "phone": "+1 415 555 2671",
        "total_experience_years": 3.4,
        "education_level": "master",
        "skills": ["Python", "C++", "SQL", "PyTorch", "TensorFlow", "Hugging Face", "Scikit-Learn", "Transformers", "BERT", "LLM", "LangChain", "Docker", "MLflow", "AWS", "Git", "Linux", "FastAPI"],
    }

    # ==============================================================
    # 4. Ananya Iyer — Fullstack Developer ("Jun'19 - Aug'21" date format, DOCX)
    # ==============================================================
    f4 = "candidate_04_ananya_iyer_fullstack.docx"
    t4_block = {
        "name": "Ananya Iyer",
        "email": "ananya.iyer@cloudtech.io",
        "phone": "+91 88877 66554",
        "location": "Hyderabad, India",
        "linkedin": "linkedin.com/in/ananya-iyer",
    }
    s4 = [
        ("Professional Summary", [
            "Full Stack Software Engineer with 7.4 years of progressive experience delivering scalable cloud solutions across frontend and backend tiers using React, Node.js, TypeScript, PostgreSQL, and Docker."
        ]),
        ("Technical Expertise", [
            "• Languages & Core: JavaScript, TypeScript, Python, HTML5, CSS3",
            "• Frontend: React, Redux, Next.js, Tailwind CSS",
            "• Backend & Storage: Node.js, Express, PostgreSQL, MongoDB, GraphQL, REST API",
            "• Cloud & DevOps: AWS, Docker, Git, CI/CD"
        ]),
        ("Experience", [
            "Senior Full Stack Engineer | CloudWave Solutions, Hyderabad",
            "Sep'21 - Present",
            "• Architected and shipped customer web portals using React and Node.js with GraphQL and PostgreSQL backends.",
            "• Containerized core microservices using Docker and orchestrated cloud deployments onto AWS ECS.",
            "• Enforced rigorous automated code quality, CI/CD pipelines, and pull request reviews across 8 developers.",
            "",
            "Software Developer | StartupHub Technologies, Bangalore",
            "Jun'19 - Aug'21",
            "• Developed full stack web applications using React, Express, MongoDB, and Tailwind CSS.",
            "• Implemented secure JWT authentication and role-based access control across internal REST API endpoints.",
            "• Managed database schemas and optimized MongoDB aggregate queries."
        ]),
        ("Education", [
            "B.Tech in Computer Science and Engineering",
            "NIT Trichy | 2015 - 2019"
        ])
    ]
    create_standard_docx(RESUMES_DIR / f4, s4, t4_block)
    ground_truth[f4] = {
        "name": "Ananya Iyer",
        "email": "ananya.iyer@cloudtech.io",
        "phone": "+91 88877 66554",
        "total_experience_years": 7.4,  # Sep 2021 to Nov 2026 (62 mos) + Jun 2019 to Aug 2021 (26 mos) = 88 mos = 7.33 yrs
        "education_level": "bachelor",
        "skills": ["JavaScript", "TypeScript", "Python", "HTML5", "CSS3", "React", "Redux", "Next.js", "Tailwind CSS", "Node.js", "Express", "PostgreSQL", "MongoDB", "GraphQL", "REST API", "AWS", "Docker", "Git", "CI/CD"],
    }

    # ==============================================================
    # 5. Deepak Nair — Fresher (PDF, 0 yrs exp, projects + internship)
    # ==============================================================
    f5 = "candidate_05_deepak_nair_fresher.pdf"
    t5 = """DEEPAK NAIR
deepak.nair2024@gmail.com | +91 94455 11223 | Kochi, India | github.com/deepaknair-dev

OBJECTIVE
Motivated 2024 Computer Science graduate seeking an entry-level software engineer role. Strong foundation in Python, React, JavaScript, SQL, and web application development through academic projects and internship.

EDUCATION
Bachelor of Science in Computer Science
Kerala University, Trivandrum | Graduated May 2024 | CGPA: 8.6/10

TECHNICAL SKILLS
• Programming: Python, JavaScript, SQL, C
• Web Technologies: React, HTML5, CSS3, Flask, REST API
• Developer Tools: Git, GitHub, VS Code, Linux

ACADEMIC PROJECTS
Online Bookstore Web Application
• Built a full-stack responsive web application using React frontend and Flask REST API backend with SQLite database.
• Designed user authentication, product catalog search, and shopping cart persistence using React hooks and Context API.

Automated Resume Keyword Extractor
• Developed a Python tool using regular expressions and basic NLP to extract programming skills from student resumes.

INTERNSHIP EXPERIENCE
Software Development Intern | WebCraft Technologies, Kochi
May 2024 - Jul 2024
• Supported senior developers by building reusable React UI components and fixing responsive CSS layout bugs.
• Wrote unit tests and assisted in API integration using Git for version control.
"""
    create_single_column_pdf(RESUMES_DIR / f5, t5)
    ground_truth[f5] = {
        "name": "Deepak Nair",
        "email": "deepak.nair2024@gmail.com",
        "phone": "+91 94455 11223",
        "total_experience_years": 0.0,
        "education_level": "bachelor",
        "skills": ["Python", "JavaScript", "SQL", "C", "React", "HTML5", "CSS3", "Flask", "REST API", "Git", "GitHub", "Linux"],
    }

    # ==============================================================
    # 6. Vikram Singh — Overlapping Jobs (DOCX)
    # ==============================================================
    f6 = "candidate_06_vikram_singh_overlap.docx"
    t6_block = {
        "name": "Vikram Singh",
        "email": "vikram.singh@enterprise.net",
        "phone": "+91 98111 22334",
        "location": "Noida, India",
        "linkedin": "linkedin.com/in/vikram-singh-cloud",
    }
    s6 = [
        ("Summary", [
            "DevOps and Cloud Engineer with 5.8 years of hands-on experience designing cloud infrastructure on AWS, implementing Kubernetes container orchestration, and automating CI/CD pipelines."
        ]),
        ("Technical Skills", [
            "• Cloud & DevOps: AWS, Kubernetes, Docker, Terraform, CI/CD, Linux, Bash, Jenkins",
            "• Development & DB: Java, Spring Boot, Python, PostgreSQL, Microservices, Git"
        ]),
        ("Experience", [
            "Lead Cloud Infrastructure Engineer | Apex Systems, Noida",
            "Jan 2021 - Present",
            "• Managed multi-region AWS cloud deployments hosting 40+ microservices on Amazon EKS Kubernetes clusters.",
            "• Automated infrastructure provisioning using Terraform and standardized CI/CD pipelines.",
            "• Reduced cloud infrastructure costs by 28% through reserved instance planning and automated container scaling.",
            "",
            "Cloud Consultant (Concurrent Part-time) | DataFlow Analytics, Gurgaon",
            "Jun 2022 - Dec 2023",
            "• Advised client engineering teams on Docker containerization best practices and PostgreSQL database backups.",
            "• Set up automated alerting and metric dashboards for microservices monitoring."
        ]),
        ("Education", [
            "Bachelor of Engineering in Information Science",
            "Bangalore University | 2016 - 2020"
        ])
    ]
    create_standard_docx(RESUMES_DIR / f6, s6, t6_block)
    ground_truth[f6] = {
        "name": "Vikram Singh",
        "email": "vikram.singh@enterprise.net",
        "phone": "+91 98111 22334",
        "total_experience_years": 5.8,  # Jan 2021 to Nov 2026 = 70 months = 5.83 yrs (concurrent job Jun 2022 - Dec 2023 ignored by merger)
        "education_level": "bachelor",
        "skills": ["AWS", "Kubernetes", "Docker", "Terraform", "CI/CD", "Linux", "Bash", "Jenkins", "Java", "Spring Boot", "Python", "PostgreSQL", "Microservices", "Git"],
    }

    # ==============================================================
    # 7. Meera Deshmukh — Career Gap (PDF)
    # ==============================================================
    f7 = "candidate_07_meera_deshmukh_gap.pdf"
    t7 = """MEERA DESHMUKH
meera.deshmukh@webdev.org | +91 97666 54321 | Mumbai, India | linkedin.com/in/meera-deshmukh

PROFILE
Frontend Engineer with 5.4 years of professional web development experience specializing in React, TypeScript, Redux, and modern CSS architecture. Re-entered the workforce with refreshed skills after a planned sabbatical.

SKILLS
• Languages: JavaScript, TypeScript, HTML5, CSS3
• Frameworks & Libraries: React, Redux, Next.js, Tailwind CSS
• Design & Tools: Figma, Git, Webpack, REST API

PROFESSIONAL EXPERIENCE
Frontend Engineer | Zenith Digital, Mumbai
Jun 2024 - Present
• Developing customer-facing React and Next.js applications using TypeScript and Tailwind CSS.
• Implemented reusable UI components adhering strictly to design system tokens exported from Figma.
• Integrated REST API endpoints with optimistic caching and state management via Redux Toolkit.

Career Break / Sabbatical (Family & Upskilling)
Jan 2022 - May 2024
• Completed advanced certifications in TypeScript, Next.js, and Modern Web Accessibility.

Junior Web Developer | PixelCrafters, Mumbai
Jan 2019 - Dec 2021
• Built responsive landing pages and Single Page Applications using React and JavaScript.
• Wrote cross-browser CSS and collaborated with backend engineers on REST API integrations.

EDUCATION
Master of Computer Applications (MCA) | Mumbai University
2016 - 2019
"""
    create_single_column_pdf(RESUMES_DIR / f7, t7)
    ground_truth[f7] = {
        "name": "Meera Deshmukh",
        "email": "meera.deshmukh@webdev.org",
        "phone": "+91 97666 54321",
        "total_experience_years": 5.4,  # Jun 2024 to Nov 2026 (29 mos) + Jan 2019 to Dec 2021 (36 mos) = 65 mos = 5.42 yrs
        "education_level": "master",
        "skills": ["JavaScript", "TypeScript", "HTML5", "CSS3", "React", "Redux", "Next.js", "Tailwind CSS", "Figma", "Git", "Webpack", "REST API"],
    }

    # ==============================================================
    # 8. Siddharth Reddy — Senior Architect 9.5 yrs (DOCX)
    # ==============================================================
    f8 = "candidate_08_siddharth_reddy_senior.docx"
    t8_block = {
        "name": "Siddharth Reddy",
        "email": "siddharth.reddy@fintech-core.com",
        "phone": "+91 99000 88776",
        "location": "Bangalore, India",
        "linkedin": "linkedin.com/in/siddharth-reddy-architect",
    }
    s8 = [
        ("Executive Summary", [
            "Seasoned Principal Software Architect with 9.5 years of industry experience designing and deploying high-scale distributed financial systems, resilient microservices architectures, and event-driven backends using Java, Spring Boot, Kafka, and Kubernetes."
        ]),
        ("Technical Mastery", [
            "• Languages & Core: Java, Python, SQL, Distributed Systems, System Design",
            "• Frameworks: Spring Boot, Spring Cloud, Hibernate, JUnit",
            "• Messaging & Data: Apache Kafka, PostgreSQL, Redis, Elasticsearch, MongoDB",
            "• Cloud & Infrastructure: AWS, Docker, Kubernetes, CI/CD, Terraform, Git"
        ]),
        ("Work History", [
            "Principal Architect | FinTech Core Systems, Bangalore",
            "Jan 2022 - Present",
            "• Defined technical vision and architecture for core banking ledger handling $2B+ in annual transaction volume.",
            "• Championed event-driven architecture utilizing Apache Kafka clusters, achieving sub-100ms end-to-end latency.",
            "• Spearheaded migration from monolithic services to 30+ Kubernetes microservices on AWS.",
            "",
            "Lead Backend Engineer | GlobalPay Solutions, Bangalore",
            "Jan 2018 - Dec 2021",
            "• Led team of 10 engineers building payment gateway integration microservices in Java and Spring Boot.",
            "• Architected distributed caching with Redis and optimized high-volume PostgreSQL transaction throughput.",
            "",
            "Software Engineer | CyberSolutions India, Hyderabad",
            "May 2017 - Dec 2017",
            "• Implemented RESTful web services in Java and created unit tests with JUnit and Mockito."
        ]),
        ("Education", [
            "Bachelor of Technology in Computer Science",
            "NIT Warangal | 2013 - 2017"
        ])
    ]
    create_standard_docx(RESUMES_DIR / f8, s8, t8_block)
    ground_truth[f8] = {
        "name": "Siddharth Reddy",
        "email": "siddharth.reddy@fintech-core.com",
        "phone": "+91 99000 88776",
        "total_experience_years": 9.5,  # Jan 2022 to Nov 2026 (58 mos) + Jan 2018 to Dec 2021 (48 mos) + May 2017 to Dec 2017 (8 mos) = 114 mos = 9.5 yrs
        "education_level": "bachelor",
        "skills": ["Java", "Python", "SQL", "Spring Boot", "Hibernate", "JUnit", "Apache Kafka", "PostgreSQL", "Redis", "Elasticsearch", "MongoDB", "AWS", "Docker", "Kubernetes", "CI/CD", "Terraform", "Git", "REST API", "Microservices"],
    }

    # ==============================================================
    # 9. Kavita Krishnan — PhD NLP Researcher ("Since 2022" dates, PDF)
    # ==============================================================
    f9 = "candidate_09_kavita_krishnan_data_nlp.pdf"
    t9 = """DR. KAVITA KRISHNAN
kavita.krishnan@data-intelligence.ai | +1 650 444 3322 | Palo Alto, CA | github.com/kavitak-nlp

PROFESSIONAL SUMMARY
Senior Research Scientist and NLP Specialist with 6.8 years of post-graduate experience pioneering Transformer models, Large Language Models (LLM), and generative AI solutions in Python and PyTorch.

CORE TECHNICAL SKILLS
• Machine Learning & NLP: PyTorch, Natural Language Processing, Machine Learning, Deep Learning, Transformers, BERT, LLM, Hugging Face, Scikit-Learn
• Data & Programming: Python, Pandas, NumPy, SQL
• Tools: Docker, Git, Linux, Jupyter

RESEARCH & PROFESSIONAL EXPERIENCE
Staff Research Scientist | AI Research Labs, Palo Alto, CA
Since Jan 2022
• Directing NLP research on parameter-efficient fine-tuning (LoRA, QLoRA) for open-weight Large Language Models.
• Published 4 papers at ACL and EMNLP on multilingual representation learning with BERT and Transformer architectures.
• Mentored research interns and deployed Hugging Face models using PyTorch into cloud inference services.

Postdoctoral Researcher | Stanford NLP Group, Stanford, CA
Jan 2020 - Dec 2021
• Investigated semantic similarity metrics and embedding representations for cross-lingual transfer learning.
• Built automated text summarization pipelines using PyTorch and Scikit-Learn.

EDUCATION
Ph.D. in Computer Science (Natural Language Processing) | Stanford University | 2015 - 2020
Bachelor of Science in Computer Science | UC Berkeley | 2011 - 2015
"""
    create_single_column_pdf(RESUMES_DIR / f9, t9)
    ground_truth[f9] = {
        "name": "Kavita Krishnan",
        "email": "kavita.krishnan@data-intelligence.ai",
        "phone": "+1 650 444 3322",
        "total_experience_years": 6.8,  # Jan 2022 to Nov 2026 (58 mos) + Jan 2020 to Dec 2021 (24 mos) = 82 mos = 6.83 yrs
        "education_level": "phd",
        "skills": ["PyTorch", "Natural Language Processing", "Machine Learning", "Deep Learning", "Transformers", "BERT", "LLM", "Hugging Face", "Scikit-Learn", "Python", "Pandas", "NumPy", "SQL", "Docker", "Git", "Linux"],
    }

    # ==============================================================
    # 10. Pooja Hegde — Digital Marketer (Negative example, DOCX)
    # ==============================================================
    f10 = "candidate_10_pooja_hegde_marketer.docx"
    t10_block = {
        "name": "Pooja Hegde",
        "email": "pooja.hegde@growthmarketing.co",
        "phone": "+91 98450 12345",
        "location": "Mumbai, India",
        "linkedin": "linkedin.com/in/pooja-hegde-marketing",
    }
    s10 = [
        ("Professional Summary", [
            "Results-driven Digital Marketing and Brand Growth Lead with 7.3 years of experience driving inbound user acquisition, search engine optimization, content strategy, and multi-channel campaign execution."
        ]),
        ("Core Competencies", [
            "• Digital Marketing: Search Engine Optimization, Content Marketing, Social Media Marketing, Email Campaigns",
            "• Tools: Google Analytics, Google Ads, HubSpot, Mailchimp, Hootsuite, Canva",
            "• Skills: Market Research, Copywriting, Brand Strategy, Lead Generation"
        ]),
        ("Experience", [
            "Senior Growth Marketing Lead | BrightScale Media, Mumbai",
            "Jan 2022 - Present",
            "• Spearheaded brand campaigns delivering 140% organic web traffic growth across search channels.",
            "• Managed an annual advertising budget of $500K across paid search and social media channels.",
            "",
            "Digital Marketing Specialist | AdVenture Media, Pune",
            "Jun 2019 - Dec 2021",
            "• Executed search engine marketing and email newsletter automation for B2B enterprise clients.",
            "• Analyzed conversion funnels and user retention metrics using analytics dashboards."
        ]),
        ("Education", [
            "Master of Business Administration in Marketing",
            "Symbiosis Institute, Pune | 2017 - 2019"
        ])
    ]
    create_standard_docx(RESUMES_DIR / f10, s10, t10_block)
    ground_truth[f10] = {
        "name": "Pooja Hegde",
        "email": "pooja.hegde@growthmarketing.co",
        "phone": "+91 98450 12345",
        "total_experience_years": 7.3,  # Jan 2022 to Nov 2026 (58 mos) + Jun 2019 to Dec 2021 (30 mos) = 88 mos = 7.33 yrs
        "education_level": "master",
        "skills": [],  # Negative domain example: no software engineering skills in taxonomy
    }

    # ==============================================================
    # 11. Rahul Kapoor — DevOps & Cloud Engineer (PDF)
    # ==============================================================
    f11 = "candidate_11_rahul_kapoor_devops.pdf"
    t11 = """RAHUL KAPOOR
rahul.kapoor@cloudops.io | +91 99887 76655 | Gurgaon, India | linkedin.com/in/rahul-kapoor-devops

SUMMARY
DevOps and Site Reliability Engineer with 3.8 years of experience building scalable CI/CD pipelines, containerizing applications with Docker and Kubernetes, and managing AWS cloud infrastructure with Terraform.

TECHNICAL SKILLS
• Cloud & Containers: AWS, Docker, Kubernetes, Terraform
• Automation & OS: CI/CD, Jenkins, Linux, Bash, Ansible, Git
• Monitoring & Scripting: Prometheus, Grafana, Python

EXPERIENCE
DevOps Engineer | CloudOps Infrastructure, Gurgaon
Jan 2023 - Present
• Provisioned scalable cloud infrastructure on AWS utilizing modular Terraform blueprints.
• Managed Kubernetes clusters, wrote Helm charts, and containerized microservices using Docker.
• Automated deployment workflows using Jenkins CI/CD pipelines and monitored infrastructure health with Prometheus and Grafana.
• Scripted maintenance tasks in Python and Bash across Linux servers.

EDUCATION
Bachelor of Engineering in Electronics and Communication | Delhi Technological University
2018 - 2022
"""
    create_single_column_pdf(RESUMES_DIR / f11, t11)
    ground_truth[f11] = {
        "name": "Rahul Kapoor",
        "email": "rahul.kapoor@cloudops.io",
        "phone": "+91 99887 76655",
        "total_experience_years": 3.8,  # Jan 2023 to Nov 2026 = 46 months = 3.83 yrs
        "education_level": "bachelor",
        "skills": ["AWS", "Docker", "Kubernetes", "Terraform", "CI/CD", "Jenkins", "Linux", "Bash", "Ansible", "Git", "Prometheus", "Grafana", "Python"],
    }

    # ==============================================================
    # 12. Sneha Banerjee — Comma-Separated Skills Fullstack (PDF)
    # ==============================================================
    f12 = "candidate_12_sneha_banerjee_react_java.pdf"
    t12 = """SNEHA BANERJEE
sneha.banerjee@codeworks.in | +91 98300 11223 | Kolkata, India | github.com/snehabanerjee

CAREER OBJECTIVE
Full Stack Developer with 3.4 years of professional experience building web applications using React on the frontend and Java Spring Boot on the backend.

TECHNICAL SKILLS
React, JavaScript, Java, Spring Boot, HTML5, CSS3, MySQL, REST API, Git, Docker

EXPERIENCE
Full Stack Developer | CodeWorks Solutions, Kolkata
Jun 2023 - Present
• Built responsive web user interfaces using React, JavaScript, HTML5, and CSS3.
• Developed REST APIs and microservice endpoints with Java and Spring Boot.
• Designed database tables and optimized SQL queries in MySQL.
• Maintained code repositories using Git and deployed development environments with Docker.

EDUCATION
Bachelor of Technology in Information Technology | Jadavpur University
2019 - 2023
"""
    create_single_column_pdf(RESUMES_DIR / f12, t12)
    ground_truth[f12] = {
        "name": "Sneha Banerjee",
        "email": "sneha.banerjee@codeworks.in",
        "phone": "+91 98300 11223",
        "total_experience_years": 3.4,  # Jun 2023 to Nov 2026 = 41 months = 3.42 yrs
        "education_level": "bachelor",
        "skills": ["React", "JavaScript", "Java", "Spring Boot", "HTML5", "CSS3", "MySQL", "REST API", "Git", "Docker"],
    }

    # Write ground truth JSON
    with open(GROUND_TRUTH_FILE, "w", encoding="utf-8") as f:
        json.dump(ground_truth, f, indent=2)

    print(f"\nGround truth successfully written to {GROUND_TRUTH_FILE}")
    print(f"Total synthetic resumes generated: {len(ground_truth)}")


if __name__ == "__main__":
    generate_all_resumes()
