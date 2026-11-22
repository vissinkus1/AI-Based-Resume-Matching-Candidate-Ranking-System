  """
update_taxonomy_a1_a3.py — Updates skills taxonomy with:
- Rename 'Apache' to 'Apache HTTP Server' with explicit aliases (no bare 'Apache')
- Add 'tier' ('core', 'supporting', 'soft')
- Add 'parent' for parent/child skills (AWS services -> AWS, GitHub Actions -> CI/CD, etc.)
"""
import json
from pathlib import Path

TAX_PATH = Path(__file__).resolve().parent.parent / "app" / "data" / "skills_taxonomy.json"

CATEGORY_TIER_DEFAULT = {
    "programming_languages": "core",
    "frontend": "core",
    "backend": "core",
    "databases": "core",
    "cloud_devops": "core",
    "ai_ml": "core",
    "data": "core",
    "security": "core",
    "concepts": "supporting",
    "testing": "supporting",
    "tools": "supporting",
    "soft_skills": "soft",
}

# Specific tier overrides
TIER_OVERRIDES = {
    # Methodologies under soft_skills are "supporting" as per prompt (e.g. Agile, Scrum)
    "Agile": "supporting",
    "Scrum": "supporting",
    "Kanban": "supporting",
    "Code Review": "supporting",
    "Clean Architecture": "supporting",
    "Technical Writing": "soft",
}

# Parent mappings: child canonical -> parent canonical
PARENT_MAPPINGS = {
    # AWS services -> AWS
    "AWS EC2": "AWS",
    "AWS S3": "AWS",
    "AWS Lambda": "AWS",
    "AWS RDS": "AWS",
    "AWS ECS": "AWS",
    "AWS EKS": "AWS",
    "AWS CloudFormation": "AWS",

    # CI/CD & Git
    "GitHub Actions": "CI/CD",
    "GitLab CI/CD": "CI/CD",
    "CircleCI": "CI/CD",
    "Jenkins": "CI/CD",
    "ArgoCD": "CI/CD",
    "GitHub": "Git",
    "GitLab": "Git",
    "Bitbucket": "Git",

    # Frontend
    "Redux": "React",
    "Next.js": "React",
    "React Native": "React",
    "Nuxt.js": "Vue.js",

    # Backend frameworks -> Language/Runtime
    "Spring Boot": "Java",
    "Hibernate": "Java",
    "Django": "Python",
    "Flask": "Python",
    "FastAPI": "Python",
    "Celery": "Python",
    "SQLAlchemy": "Python",
    "Express.js": "Node.js",
    "NestJS": "Node.js",
    "ASP.NET": "C#",
    "Ruby on Rails": "Ruby",
    "Sinatra": "Ruby",
    "Laravel": "PHP",
    "Symfony": "PHP",
    "CodeIgniter": "PHP",
    "Gin": "Go",
    "Fiber": "Go",
    "Actix": "Rust",
    "Axum": "Rust",

    # AI / ML / NLP
    "PyTorch": "Deep Learning",
    "TensorFlow": "Deep Learning",
    "Keras": "Deep Learning",
    "spaCy": "Natural Language Processing",
    "NLTK": "Natural Language Processing",
    "Hugging Face": "Natural Language Processing",
    "LangChain": "Natural Language Processing",
    "LlamaIndex": "Natural Language Processing",
    "Whisper": "Natural Language Processing",
    "Large Language Models": "Natural Language Processing",
    "GPT": "Natural Language Processing",
    "Retrieval-Augmented Generation": "Natural Language Processing",
    "OpenCV": "Computer Vision",
    "XGBoost": "Machine Learning",
    "LightGBM": "Machine Learning",
    "CatBoost": "Machine Learning",
    "scikit-learn": "Machine Learning",

    # Python Data Science ecosystem
    "Pandas": "Python",
    "NumPy": "Python",
    "SciPy": "Python",
    "Matplotlib": "Python",
    "Seaborn": "Python",

    # Big Data
    "PySpark": "Apache Spark",

    # Testing -> Language
    "pytest": "Python",
    "JUnit": "Java",
    "Mockito": "Java",
    "Jest": "JavaScript",
    "Cypress": "JavaScript",
    "Playwright": "JavaScript",
    "Vitest": "JavaScript",
}


def main():
    with open(TAX_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    updated_skills = []
    for skill in data["skills"]:
        canonical = skill["canonical"]

        # A1: Fix Apache entry
        if canonical == "Apache":
            canonical = "Apache HTTP Server"
            skill["canonical"] = "Apache HTTP Server"
            skill["aliases"] = ["apache http", "apache http server", "apache server", "httpd"]

        # A3: Set tier
        category = skill.get("category", "")
        tier = TIER_OVERRIDES.get(canonical, CATEGORY_TIER_DEFAULT.get(category, "core"))
        skill["tier"] = tier

        # A2: Set parent if mapped
        if canonical in PARENT_MAPPINGS:
            skill["parent"] = PARENT_MAPPINGS[canonical]
        else:
            skill["parent"] = None

        updated_skills.append(skill)

    data["skills"] = updated_skills

    with open(TAX_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"Updated {len(updated_skills)} skills with tier and parent.")
    print("Sample updated entry (AWS EC2):", [s for s in updated_skills if s["canonical"] == "AWS EC2"][0])
    print("Sample updated entry (Apache HTTP Server):", [s for s in updated_skills if s["canonical"] == "Apache HTTP Server"][0])
    print("Sample updated entry (Agile):", [s for s in updated_skills if s["canonical"] == "Agile"][0])


if __name__ == "__main__":
    main()
