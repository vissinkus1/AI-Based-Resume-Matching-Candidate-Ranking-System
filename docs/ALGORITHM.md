# Candidate Ranking & Match Scoring Algorithm

> **Document Version:** 2.0 (Phase 6 Reconciled Engine)  
> **Target Audience:** Technical interviewers, evaluators, system architects.

---

## 1. Executive Summary & Core Principles

The **AI-Based Resume Matching & Candidate Ranking System** computes an explainable, deterministic **0–100 match score** evaluating candidate fit against a target Job Description (JD).

### Architectural Principles
1. **Explainability First:** Every component score is backed by deterministic evidence (matched skill tokens, concrete resume sentences, and mathematical equations). No black-box or non-reproducible LLM calls are used during scoring.
2. **Hybrid Semantic + Lexical Match:** Pure keyword matching fails when candidates write synonyms or related tools; pure embedding matching hallucinates high similarity on well-written but completely irrelevant resumes. Combining normalized taxonomy matching with calibrated sentence-transformer embeddings eliminates both failure modes.
3. **No Magic Numbers:** Every threshold, weight, penalty, and calibration bound lives in a single frozen configuration (`backend/app/core/scoring_config.py`).
4. **Domain Knockout Safeguard:** Off-domain candidates (e.g., digital marketers applying to backend roles) can achieve moderate cosine similarity due to generic resume jargon. If core required technical skill coverage is < 25%, the final score is strictly capped at 35.0.

---

## 2. Overall Scoring Formula

The final match score is a weighted linear combination of five normalized component scores (0 <= S_i <= 100):

```
Final Score = 0.40 * S_skill + 0.25 * S_sem + 0.20 * S_exp + 0.10 * S_qual + 0.05 * S_title
```

### Component Weights (Sum = 1.0)

| Component | Weight | Key Question Answered |
|---|:---:|---|
| **S_skill (Skill Match)** | **0.40** | Does the candidate possess the concrete tools, frameworks, and languages required? |
| **S_sem (Semantic Similarity)** | **0.25** | Do their day-to-day responsibilities and projects contextually align with the JD? |
| **S_exp (Experience Evaluation)** | **0.20** | Do they meet the required seniority in **directly relevant** domains? |
| **S_qual (Education/Qualification)** | **0.10** | Does their academic degree level meet or exceed the prerequisite? |
| **S_title (Title Relevance)** | **0.05** | Have they held titles demonstrating domain progression? |

---

## 3. Detailed Component Algorithms

### 3.1. Skill Matching Score (S_skill)

#### A. Family Collapse
If a JD lists both a parent skill and its children (e.g., `AWS` alongside `AWS EC2`, `AWS S3`, `AWS Lambda`, or `Git` alongside `GitHub`), the children are dropped from the denominator so one technology family is not counted 4-5 times. Language frameworks (e.g. `Spring Boot` vs `Java`, `React` vs `JavaScript`) are explicitly preserved as distinct competencies (Decision D36).

#### B. Skill Weight Tiers
Every skill in `skills_taxonomy.json` is assigned a tier:
- **Core (Weight = 1.0):** Languages, frameworks, primary databases, cloud platforms.
- **Supporting (Weight = 0.6):** Methodologies, CI/CD tools, architecture concepts, secondary tools.
- **Soft (Weight = 0.3):** Leadership, Communication, Mentorship.

#### C. Candidate Skill Confidence Filter
Only candidate skills extracted with `strong` (explicit skill / experience sections) or `medium` (projects section) confidence are admitted. Unstructured `basic` mentions are ignored.

#### D. Credit Table
For each JD skill, candidate skills are evaluated for the highest available credit:

| Match Type | Credit | Description & Example |
|---|:---:|---|
| **Exact / Alias** | **1.00** | Canonical or curated alias match (e.g. `PostgreSQL` <-> `postgres`, `JavaScript` <-> `js`). |
| **Child of Parent** | **0.90** | JD wants parent (`AWS`), candidate has child (`AWS S3`). |
| **Parent of Child** | **0.60** | JD wants child (`AWS S3`), candidate only has parent (`AWS`). |
| **Semantic Soft Match** | **<= 0.70** | Skill embedding cosine similarity >= 0.62 (e.g., `FastAPI` <-> `Flask`). Credit = min(0.70, cos). |
| **Inferred Concept** | **<= 0.70** | Missing supporting/soft skills (e.g. `Clean Architecture`, `Agile`) inferred from experience snippet cosine >= 0.60. Core skills are strictly exempt from inference. |
| **No Match** | **0.00** | No related skill found (cos < 0.62). |

#### E. Weighted Combination
Let `C_req` be the weighted coverage over required skills and `C_pref` over preferred skills:

```
C_req  = sum(Credit_s * TierWeight_s) / sum(TierWeight_s)   [for s in required]
C_pref = sum(Credit_s * TierWeight_s) / sum(TierWeight_s)   [for s in preferred]

S_skill = 0.80 * (C_req * 100) + 0.20 * (C_pref * 100)
```
*(If the JD specifies no preferred skills, S_skill = C_req * 100).*

---

### 3.2. Semantic Similarity Score (S_sem)

Semantic similarity is evaluated across two complementary dimensions using `all-MiniLM-L6-v2` (384-dimensional dense vectors with L2 normalization):

1. **Requirement-Unit Coverage (S_req):**
   - The JD is partitioned into requirement units: each duty in `responsibilities` (filtered to genuine duty sentences, dropping boilerplate < 6 words or lacking verbs) plus each sentence in `skill_evidence`.
   - The resume is partitioned into contextual chunks: `summary`, each work experience `entry.description`, `projects` text, and key skills.
   - For each JD unit `u_i`, we compute its maximum cosine similarity against all resume chunks `c_j`:
     `sim(u_i) = max_j (u_i . c_j)`
   - The mean of `sim(u_i)` is rescaled via linear calibration.

2. **Whole-Document Similarity (S_doc):**
   - Mean-pooled JD unit embeddings vs mean-pooled resume chunk embeddings:
     `sim_doc = (mean(u_i) / ||mean(u_i)||) . (mean(c_j) / ||mean(c_j)||)`
   - Rescaled via linear calibration.

3. **Linear Cosine Calibration:**
   Raw cosine similarities for sentence embeddings typically fall between 0.15 (unrelated noise) and 0.70 (strong topical alignment). We map [low=0.15, high=0.70] into [0, 100]:
   `Calibrate(cos) = min(100, max(0, (cos - 0.15) / (0.70 - 0.15) * 100))`

4. **Blend:**
   `S_sem = 0.60 * S_req + 0.40 * S_doc`

---

### 3.3. Experience Score (S_exp)

Experience is scored on **relevant experience** (`Y_rel`) alongside total career experience (`Y_tot`):

#### A. Relevance Criterion
An experience entry is deemed relevant to the target JD if:
1. `CosineSimilarity(title + description, JD text) >= 0.35`, **OR**
2. The entry description contains >= 2 JD core required skills. (Generic tools like Git, Docker, Linux, SQL do not confer domain experience on their own).

#### B. Interval Merging
Overlapping date intervals for relevant entries are merged into a continuous timeline: concurrent jobs and consulting contracts are never double-counted. Career breaks and sabbaticals are excluded. Internships are credited at 50%.

#### C. Scoring Function
Let `Y_min` and `Y_max` be the JD requirements:
- If `Y >= Y_min`:
  - If `Y_max` is specified and `Y > 1.5 * Y_max` (e.g. 9.5 yrs for a 3-5 yr role):
    `score(Y) = 90.0` (over-qualification floor).
  - Else: `score(Y) = 100.0`.
- If `Y < Y_min`:
  `score(Y) = (Y / Y_min) * 100.0`

#### D. Blend
```
S_exp = 0.70 * score(Y_rel) + 0.30 * score(Y_tot)
```

---

### 3.4. Qualification Score (S_qual)

Academic levels are ranked ordinally:
`Diploma (1) < Bachelor (2) < Master (3) < Ph.D. (4)`

Comparing the candidate's highest level against the JD's `min_required_level`:
- **Meets or Exceeds:** S_qual = 100.0
- **One Level Below:** S_qual = 50.0
- **Two or More Levels Below:** S_qual = 20.0
- **No Degree Detected (when required):** S_qual = 30.0
- **No Requirement in JD:** S_qual = 100.0

---

### 3.5. Title Relevance Score (S_title)

1. For candidates with past work history, we normalize titles (stripping seniority tokens like senior, lead, junior) and compute the maximum cosine similarity between `jd.title` and each title in `candidate.job_titles`.
2. For freshers with no past titles, we compute similarity between `jd.title` and the candidate's executive summary / project headings.
3. The raw cosine is rescaled via domain-calibrated linear bounds ([low=0.30, high=0.75] -> [0, 100]):
   `S_title = min(100, max(0, (cos - 0.30) / (0.75 - 0.30) * 100))`
   *Rationale:* This calibrated window ensures that cross-domain technical roles (e.g. React Developer for Java JD, cos ~0.42) score clearly low (~28%), while direct role matches (Senior Java Developer, cos ~0.73) score high (>95%).

---

### 3.6. Knockout Safeguard

To prevent keyword-stuffed or generic off-domain resumes from ranking high due to dense semantic text, a hard knockout safeguard is evaluated:
```
If Coverage_core_required < 25%:
    Final Score = min(Final Score, 35.0)
```

---

## 4. Worked Numerical Example: Siddharth Reddy

### Target Job Description: Java Backend Engineer
- **Title:** Senior Java/Spring Boot Backend Developer (`java_backend_jd.txt`)
- **Required Experience:** 5.0 - 8.0 years
- **Required Qualification:** Bachelor's degree (Master's preferred)
- **Required Skills:** Java, Spring Boot, Microservices, PostgreSQL, Docker, Kubernetes, AWS, REST API, Git, JUnit

### Candidate Profile: Siddharth Reddy (`candidate_08_siddharth_reddy_senior.docx`)
- **Total Experience:** 9.6 years (all verified relevant in enterprise Java architecture)
- **Education:** B.Tech in Computer Science & Engineering (meets Bachelor prerequisite)
- **Extracted Titles:** "Senior Software Architect", "Lead Java Developer"

---

### Component Calculations (Matching Live API)

#### 1. Skill Score (S_skill)
- **Weighted Required Skill Coverage:** 77.3%
  - Exact matches: Java (1.0), Spring Boot (1.0), Microservices (1.0), PostgreSQL (1.0), Docker (1.0), Kubernetes (1.0), REST API (1.0), Git (1.0), CI/CD (1.0).
  - Child match: AWS S3, RDS, EC2 roll up to AWS with 0.90 credit.
- **Score:** S_skill = **77.3%**
- **Contribution:** `0.40 * 77.3 = 30.92 pts`

#### 2. Semantic Similarity Score (S_sem)
- **Requirement-Unit Coverage:** Mean max cosine = 0.528 -> Rescaled = 68.7%
- **Whole-Document Similarity:** Cosine = 0.460 -> Rescaled = 56.4%
- **Blend:** `0.60 * 68.7 + 0.40 * 56.4 = 63.8%`
- **Score:** S_sem = **63.8%**
- **Contribution:** `0.25 * 63.8 = 15.95 pts`

#### 3. Experience Score (S_exp)
- **Relevant Experience:** 9.6 years >= 5.0 required.
- Candidate has 9.6 yrs, which is <= 1.5 * 8.0 (12.0 yrs max bound), hence receives full 100.0%.
- **Blend:** `0.70 * 100.0 + 0.30 * 100.0 = 100.0%`
- **Score:** S_exp = **100.0%**
- **Contribution:** `0.20 * 100.0 = 20.00 pts`

#### 4. Qualification Score (S_qual)
- Candidate degree: Bachelor's in CSE.
- JD requirement: Bachelor's degree.
- Candidate meets prerequisite -> S_qual = **100.0%**
- **Contribution:** `0.10 * 100.0 = 10.00 pts`

#### 5. Title Relevance Score (S_title)
- Candidate normalized titles: "software architect", "java developer".
- Max cosine against "Senior Java/Spring Boot Backend Developer" = 0.508.
- Rescaled: `(0.508 - 0.30) / (0.75 - 0.30) * 100 = 46.2%`
- **Score:** S_title = **46.2%**
- **Contribution:** `0.05 * 46.2 = 2.31 pts`

---

### Final Score Synthesis

```
Final Score = 30.92 (Skill) + 15.95 (Semantic) + 20.00 (Experience) + 10.00 (Qualification) + 2.31 (Title)
            = 79.18 -> 79.1%
```

- **Knockout check:** Core required coverage is 77.3% (> 25% threshold) -> No knockout applied.
- **Recommendation Band:** Score 79.1% >= 75.0% -> **"Strong match"** (Rank #1).

---

## 5. Parameter Reference (`backend/app/core/scoring_config.py`)

| Parameter | Value | Purpose |
|---|:---:|---|
| `w_skill` | 0.40 | Final weight for technical skill coverage |
| `w_semantic` | 0.25 | Final weight for contextual responsibility similarity |
| `w_experience` | 0.20 | Final weight for relevant vs required years |
| `w_qualification` | 0.10 | Final weight for academic degree matching |
| `w_title` | 0.05 | Final weight for job title alignment |
| `skill_required_weight` | 0.80 | Share of skill score from required skills |
| `skill_preferred_weight` | 0.20 | Share of skill score from preferred skills |
| `tier_weight_core` | 1.0 | Tier weight for languages, frameworks, DBs |
| `tier_weight_supporting`| 0.6 | Tier weight for tools, CI/CD, testing |
| `tier_weight_soft` | 0.3 | Tier weight for soft skills |
| `credit_child_of_required_parent` | 0.90 | Credit when candidate has specific sub-tool |
| `credit_parent_of_required_child` | 0.60 | Credit when candidate has generic platform |
| `credit_semantic_soft_match_max` | 0.70 | Maximum credit for embedding soft-match |
| `inferred_concept_credit_max` | 0.70 | Credit for inferred concepts from experience |
| `skill_soft_match_threshold` | 0.62 | Minimum cosine between skill names for soft match |
| `semantic_raw_cos_low` | 0.15 | Lower calibration bound for cosine rescaling |
| `semantic_raw_cos_high` | 0.70 | Upper calibration bound for cosine rescaling |
| `semantic_blend_req_coverage` | 0.60 | Share of semantic score from requirement units |
| `semantic_blend_whole_doc` | 0.40 | Share of semantic score from mean document embeddings |
| `exp_relevance_threshold` | 0.35 | Cosine threshold to classify an experience entry as relevant |
| `exp_over_qualification_floor` | 90.0 | Minimum score floor for senior/overqualified profiles |
| `internship_credit_factor` | 0.50 | Duration multiplier for student internships |
| `title_raw_cos_low` | 0.30 | Lower calibration bound for title cosine |
| `title_raw_cos_high` | 0.75 | Upper calibration bound for title cosine |
| `knockout_core_coverage_threshold`| 0.25 | Minimum required core skill coverage to avoid score cap |
| `knockout_score_cap` | 35.0 | Score cap applied when knockout is triggered |
| `band_strong` | 75.0 | Score threshold for "Strong match" |
| `band_good` | 60.0 | Score threshold for "Good match" |
| `band_partial` | 40.0 | Score threshold for "Partial match" |
