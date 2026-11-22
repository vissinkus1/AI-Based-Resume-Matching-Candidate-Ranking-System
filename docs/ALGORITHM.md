# Candidate Ranking & Match Scoring Algorithm

> **Document Version:** 1.0 (Phase 3 Engine)  
> **Target Audience:** Technical interviewers, engineering evaluation, system architects.

---

## 1. Executive Summary & Core Principles

The **AI-Based Resume Matching & Candidate Ranking System** computes an explainable, deterministic **0–100 match score** evaluating candidate fit against a target Job Description (JD).

### Architectural Principles
1. **Explainability First:** Every component score is backed by deterministic evidence (matched skill tokens, concrete resume sentences, and mathematical equations). No black-box or non-reproducible LLM calls are used during scoring.
2. **Hybrid Semantic + Lexical Match:** Pure keyword matching fails when candidates write synonyms or related tools; pure embedding matching hallucinates high similarity on well-written but completely irrelevant resumes. Combining normalized taxonomy matching with calibrated sentence-transformer embeddings eliminates both failure modes.
3. **No Magic Numbers:** Every threshold, weight, penalty, and calibration bound lives in a single frozen configuration (`backend/app/core/scoring_config.py`).
4. **Domain Knockout Safeguard:** Off-domain candidates (e.g., digital marketers applying to backend roles) can achieve moderate cosine similarity due to generic resume jargon. If core required technical skill coverage is $< 25\%$, the final score is strictly capped at $35.0$.

---

## 2. Overall Scoring Formula

The final match score is a weighted linear combination of five normalized component scores ($0 \le S_i \le 100$):

$$\text{Final Score} = w_{\text{skill}} S_{\text{skill}} + w_{\text{sem}} S_{\text{sem}} + w_{\text{exp}} S_{\text{exp}} + w_{\text{qual}} S_{\text{qual}} + w_{\text{title}} S_{\text{title}}$$

### Component Weights ($\sum w_i = 1.0$)

| Component | Weight | Key Question Answered |
|---|:---:|---|
| **$S_{\text{skill}}$ (Skill Match)** | **0.40** | Does the candidate possess the concrete tools, frameworks, and languages required? |
| **$S_{\text{sem}}$ (Semantic Similarity)** | **0.25** | Do their day-to-day responsibilities and projects contextually align with the JD? |
| **$S_{\text{exp}}$ (Experience Evaluation)** | **0.20** | Do they meet the required seniority in **directly relevant** domains? |
| **$S_{\text{qual}}$ (Education/Qualification)** | **0.10** | Does their academic degree level meet or exceed the prerequisite? |
| **$S_{\text{title}}$ (Title Relevance)** | **0.05** | Have they held titles demonstrating domain progression? |

---

## 3. Detailed Component Algorithms

### 3.1. Skill Matching Score ($S_{\text{skill}}$)

#### A. Family Collapse
If a JD lists both a parent skill and its children (e.g., `AWS` alongside `AWS EC2`, `AWS S3`, `AWS Lambda`, or `Git` alongside `GitHub`), the children are dropped from the denominator so one technology family is not counted 4–5 times.

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
| **Exact / Alias** | **1.00** | Canonical or curated alias match (e.g. `PostgreSQL` $\leftrightarrow$ `postgres`, `JavaScript` $\leftrightarrow$ `js`). |
| **Child of Parent** | **0.90** | JD wants parent (`AWS`), candidate has child (`AWS S3`). |
| **Parent of Child** | **0.60** | JD wants child (`AWS S3`), candidate only has parent (`AWS`). |
| **Semantic Soft Match** | **$\le 0.70$** | Skill embedding cosine similarity $\ge 0.62$ (e.g., `FastAPI` $\leftrightarrow$ `Flask`). Credit = $\min(0.70, \cos)$. |
| **No Match** | **0.00** | No related skill found ($\cos < 0.62$). |

#### E. Weighted Combination
Let $C_{\text{req}}$ be the weighted coverage over required skills and $C_{\text{pref}}$ over preferred skills:

$$C_{\text{req}} = \frac{\sum_{s \in \text{req}} \text{Credit}_s \times \text{TierWeight}_s}{\sum_{s \in \text{req}} \text{TierWeight}_s}$$

$$S_{\text{skill}} = 0.80 \times (C_{\text{req}} \times 100) + 0.20 \times (C_{\text{pref}} \times 100)$$

*(If the JD specifies no preferred skills, $S_{\text{skill}} = C_{\text{req}} \times 100$.)*

---

### 3.2. Semantic Similarity Score ($S_{\text{sem}}$)

Semantic similarity is evaluated across two complementary dimensions using `all-MiniLM-L6-v2` (384-dimensional dense vectors with $L_2$ normalization):

1. **Requirement-Unit Coverage ($S_{\text{req}}$):**
   - The JD is partitioned into requirement units: each duty in `responsibilities` plus each sentence in `skill_evidence`.
   - The resume is partitioned into contextual chunks: `summary`, each work experience `entry.description`, `projects` text, and key skills.
   - For each JD unit $u_i$, we compute its maximum cosine similarity against all resume chunks $c_j$:
     $$\text{sim}(u_i) = \max_j (u_i \cdot c_j)$$
   - The mean of $\text{sim}(u_i)$ is rescaled via linear calibration.

2. **Whole-Document Similarity ($S_{\text{doc}}$):**
   - Mean-pooled JD unit embeddings vs mean-pooled resume chunk embeddings:
     $$\text{sim}_{\text{doc}} = \left(\frac{\sum u_i}{\|\sum u_i\|}\right) \cdot \left(\frac{\sum c_j}{\|\sum c_j\|}\right)$$
   - Rescaled via linear calibration.

3. **Linear Cosine Calibration:**
   Raw cosine similarities for sentence embeddings typically fall between $0.15$ (unrelated noise) and $0.65$ (strong topical alignment). We map $[\text{low}=0.15, \text{high}=0.65]$ into $[0, 100]$:
   $$\text{Calibrate}(\cos) = \min\left(100, \max\left(0, \frac{\cos - 0.15}{0.65 - 0.15} \times 100\right)\right)$$

4. **Blend:**
   $$S_{\text{sem}} = 0.60 \times S_{\text{req}} + 0.40 \times S_{\text{doc}}$$

---

### 3.3. Experience Score ($S_{\text{exp}}$)

Experience is scored on **relevant experience** ($Y_{\text{rel}}$) alongside total career experience ($Y_{\text{tot}}$):

#### A. Relevance Criterion
An experience entry is deemed relevant to the target JD if:
1. $\text{CosineSimilarity}(\text{title} + \text{description}, \text{JD text}) \ge 0.35$, **OR**
2. The entry description contains $\ge 2$ JD core required skills.

#### B. Interval Merging
Overlapping date intervals for relevant entries are merged into a continuous timeline: concurrent jobs and consulting contracts are never double-counted. Career breaks and sabbaticals are excluded. Internships are credited at $50\%$.

#### C. Scoring Function
Let $Y_{\min}$ and $Y_{\max}$ be the JD requirements:
- If $Y \ge Y_{\min}$:
  - If $Y_{\max}$ is specified and $Y > 1.5 \times Y_{\max}$ (e.g. 9.5 yrs for a 3–5 yr role):
    $$\text{score}(Y) = 90.0 \quad (\text{over-qualification floor})$$
  - Else: $\text{score}(Y) = 100.0$.
- If $Y < Y_{\min}$:
  $$\text{score}(Y) = \frac{Y}{Y_{\min}} \times 100.0$$

#### D. Blend
$$S_{\text{exp}} = 0.70 \times \text{score}(Y_{\text{rel}}) + 0.30 \times \text{score}(Y_{\text{tot}})$$

---

### 3.4. Qualification Score ($S_{\text{qual}}$)

Academic levels are ranked ordinally:
$$\text{Diploma} (1) < \text{Bachelor} (2) < \text{Master} (3) < \text{Ph.D.} (4)$$

Comparing the candidate's highest level against the JD's `min_required_level`:
- **Meets or Exceeds:** $S_{\text{qual}} = 100.0$
- **One Level Below:** $S_{\text{qual}} = 50.0$
- **Two or More Levels Below:** $S_{\text{qual}} = 20.0$
- **No Degree Detected (when required):** $S_{\text{qual}} = 30.0$
- **No Requirement in JD:** $S_{\text{qual}} = 100.0$

---

### 3.5. Title Relevance Score ($S_{\text{title}}$)

1. For candidates with past work history, we compute the maximum raw cosine between `jd.title` and each title in `candidate.job_titles`.
2. For freshers with no past titles, we compute similarity between `jd.title` and the candidate's executive summary / project headings.
3. The raw cosine is rescaled via linear calibration ($[0.15, 0.65] \to [0, 100]$):
   $$S_{\text{title}} = \text{Calibrate}(\max \cos)$$

---

### 3.6. Knockout Safeguard

To prevent keyword-stuffed or generic off-domain resumes from ranking high due to dense semantic text, a hard knockout is evaluated:
$$\text{If } \text{Coverage}_{\text{core\_required}} < 25\% \implies \text{Final Score} = \min(\text{Final Score}, 35.0)$$

---

## 4. Worked Numerical Example

### Scenario
- **Job Description:** Senior Java Backend Developer (`java_backend_jd.txt`)
  - Experience: 5.0 – 8.0 years
  - Degree: Bachelor's required, Master's preferred
  - Title: "Senior Java/Spring Boot Backend Developer"
  - Key Skills: Java, Spring Boot, Microservices, PostgreSQL, Docker, Kubernetes, AWS, REST API, Git, JUnit
- **Candidate:** Aravind Sharma (`candidate_01_aravind_sharma_java.pdf`)
  - Past Experience: Senior Backend Engineer at Infosys (2022–Present, 49 mos) + Software Engineer at Wipro (2020–2022, 24 mos) $\to$ **6.1 years** total.
  - Degree: Bachelor of Technology (IIT Madras, 2020) $\to$ `bachelor`.
  - Past Titles: "Senior Backend Engineer", "Software Engineer".

---

### Component Calculations

#### 1. Skill Score ($S_{\text{skill}}$)
- Required skills in JD (after family collapse): 18 skills.
- Exact matches: Java (1.0), Spring Boot (1.0), Microservices (1.0), PostgreSQL (1.0), Docker (1.0), Kubernetes (1.0), REST API (1.0), Git (1.0), JUnit (1.0), Redis (1.0), Algorithms (1.0), Data Structures (1.0), OOP (1.0), CI/CD (1.0).
- Child match: AWS (JD preferred) matched by candidate AWS EC2, S3, RDS.
- Coverage calculation:
  - Required skills weighted coverage: $84.2\%$
  - Preferred skills weighted coverage: $88.5\%$
  - Split: $0.80 \times 84.2 + 0.20 \times 88.5 = 85.1$
  $$\mathbf{S_{\text{skill}} = 85.1}$$
  $$\text{Contribution} = 0.40 \times 85.1 = \mathbf{34.0}$$

#### 2. Semantic Score ($S_{\text{sem}}$)
- Mean requirement-unit max cosine: $0.578$
  - Rescaled: $\frac{0.578 - 0.15}{0.50} \times 100 = 85.6$
- Whole-document cosine: $0.521$
  - Rescaled: $\frac{0.521 - 0.15}{0.50} \times 100 = 74.2$
- Blend: $0.60 \times 85.6 + 0.40 \times 74.2 = 81.0$
  $$\mathbf{S_{\text{sem}} = 81.0}$$
  $$\text{Contribution} = 0.25 \times 81.0 = \mathbf{20.3}$$

#### 3. Experience Score ($S_{\text{exp}}$)
- Total Career Years: $6.1$ yrs.
- Relevant Experience: Both Infosys and Wipro entries meet the $\ge 2$ core skills criterion $\to$ Merged relevant duration = $6.1$ yrs.
- Required Range: $5.0 - 8.0$ yrs.
- Candidate has $6.1 \ge 5.0$ and $< 1.5 \times 8.0 = 12.0 \implies \text{score}(6.1) = 100.0$.
- Blend: $0.70 \times 100.0 + 0.30 \times 100.0 = 100.0$.
  $$\mathbf{S_{\text{exp}} = 100.0}$$
  $$\text{Contribution} = 0.20 \times 100.0 = \mathbf{20.0}$$

#### 4. Qualification Score ($S_{\text{qual}}$)
- Candidate degree: `bachelor` (rank 2).
- JD minimum requirement: `bachelor` (rank 2).
- Candidate meets requirement $\implies \mathbf{S_{\text{qual}} = 100.0}$.
  $$\text{Contribution} = 0.10 \times 100.0 = \mathbf{10.0}$$

#### 5. Title Relevance Score ($S_{\text{title}}$)
- Candidate titles: "Senior Backend Engineer", "Software Engineer".
- Max cosine against "Senior Java/Spring Boot Backend Developer": $0.612$.
- Rescaled: $\frac{0.612 - 0.15}{0.50} \times 100 = 92.4$.
  $$\mathbf{S_{\text{title}} = 92.4}$$
  $$\text{Contribution} = 0.05 \times 92.4 = \mathbf{4.6}$$

---

### Final Score Synthesis
$$\text{Final Score} = 34.0 + 20.3 + 20.0 + 10.0 + 4.6 = \mathbf{88.9\%}$$

- **Knockout check:** Core required coverage is $85\% > 25\% \implies$ No knockout applied.
- **Recommendation Band:** $88.9 \ge 75 \implies$ **"Strong match"**.

---

## 5. Parameter Reference (`scoring_config.py`)

| Parameter | Default Value | Purpose |
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
| `skill_soft_match_threshold` | 0.62 | Minimum cosine between skill names for soft match |
| `semantic_raw_cos_low` | 0.15 | Lower calibration bound for cosine rescaling |
| `semantic_raw_cos_high` | 0.65 | Upper calibration bound for cosine rescaling |
| `semantic_blend_req_coverage` | 0.60 | Share of semantic score from requirement units |
| `semantic_blend_whole_doc` | 0.40 | Share of semantic score from mean document embeddings |
| `exp_relevance_threshold` | 0.35 | Cosine threshold to classify an experience entry as relevant |
| `exp_over_qualification_floor` | 90.0 | Minimum score floor for senior/overqualified profiles |
| `internship_credit_factor` | 0.50 | Duration multiplier for student internships |
| `knockout_core_coverage_threshold`| 0.25 | Minimum required core skill coverage to avoid score cap |
| `knockout_score_cap` | 35.0 | Score cap applied when knockout is triggered |
| `band_strong` | 75.0 | Score threshold for "Strong match" |
| `band_good` | 60.0 | Score threshold for "Good match" |
| `band_partial` | 40.0 | Score threshold for "Partial match" |
