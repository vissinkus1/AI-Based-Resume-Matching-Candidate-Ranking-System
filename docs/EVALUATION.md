# System Evaluation, Benchmark & Accuracy Report

> Comprehensive evaluation report verifying ranking accuracy, domain integrity, wild resume parsing resilience, keyword stuffing defenses, and latency benchmarks for the **AI-Based Resume Matching & Candidate Ranking System**.

---

## 1. Executive Summary & Verification Highlights

All evaluation metrics and scores documented in this report are generated directly from the live reconciled pipeline ([scripts/part0_ranking_sanity.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/scripts/part0_ranking_sanity.py), [scripts/evaluate_wild_parsing.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/scripts/evaluate_wild_parsing.py), [scripts/benchmark_50_candidates.py](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/scripts/benchmark_50_candidates.py)).

| Benchmark Dimension | Measured Result | Production Target | Status |
| :--- | :--- | :--- | :--- |
| **Parsing: Candidate Name Accuracy** | **100.0% (9/9)** | $\ge 80.0\%$ | **PASS** |
| **Parsing: Email Contact Accuracy** | **100.0% (9/9)** | $\ge 95.0\%$ | **PASS** |
| **Parsing: Phone Contact Accuracy** | **100.0% (9/9)** | $\ge 90.0\%$ | **PASS** |
| **Parsing: Degree Classification** | **100.0% (9/9)** | $\ge 85.0\%$ | **PASS** |
| **Parsing: Experience Tenure (within 1.0 yr)** | **100.0% (9/9)** | $\ge 70.0\%$ | **PASS** |
| **Parsing: Scanned PDF Exception Handling** | **100.0% (1/1)** | $100.0\%$ | **PASS** |
| **Parsing: Duplicate Candidate Detection** | **100.0% (1/1)** | $100.0\%$ | **PASS** |
| **Domain Integrity: Tech vs Marketer (Java JD)**| **Priya +11.5% over Pooja** | Priya strictly > Pooja | **PASS** |
| **Domain Integrity: Tech vs Marketer (React JD)**| **Priya +65.8% over Pooja** | Priya strictly > Pooja | **PASS** |
| **Keyword Stuffing Defense (Jordan Miller)** | **37.9% (Rank 7, Weak match)** | Cannot achieve Strong/Good | **PASS** |
| **Warm Execution Latency (12 candidates)** | **12.55 ms** | $< 1000.0\text{ ms}$ | **PASS** |
| **50-Candidate Batch Matching Latency** | **1,203.73 ms (24.07 ms/candidate)**| $< 5000.0\text{ ms}$ | **PASS** |

---

## 2. Reconciled Leaderboards Across All 3 Job Descriptions

The tables below display the complete 12-row evaluation tables generated live across all three industry benchmark specifications.

### 2.1 Java Backend Engineer JD (`java_backend_jd.txt`)
- **Required Skills:** Java, Spring Boot, Microservices, REST API, SQL/PostgreSQL, Git, Docker, Unit Testing.
- **Preferred Skills:** Kafka, Kubernetes, AWS, Redis, CI/CD, Agile.
- **Experience Required:** 5.0 years | **Min Qualification:** Bachelor's Degree.

| Rank | Candidate | Exp (Rel/Tot) | Match % | Band | Skill | Semantic | Experience | Qual | Title |
| :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | Siddharth Reddy | 9.6 / 9.6y | **79.1%** | Strong match | 77.3% | 63.8% | 100.0% | 100.0% | 46.2% |
| **2** | ARAVIND SHARMA | 6.1 / 6.1y | **75.3%** | Strong match | 71.0% | 58.5% | 100.0% | 100.0% | 46.2% |
| **3** | Vikram Singh | 5.9 / 5.9y | **60.9%** | Good match | 47.2% | 47.9% | 100.0% | 100.0% | 0.0% |
| **4** | Ananya Iyer | 7.5 / 7.5y | **60.2%** | Good match | 43.8% | 49.4% | 100.0% | 100.0% | 7.2% |
| **5** | RAHUL KAPOOR | 3.9 / 3.9y | **48.6%** | Partial match | 29.6% | 41.8% | 78.0% | 100.0% | 15.2% |
| **6** | SNEHA BANERJEE | 3.5 / 3.5y | **48.4%** | Partial match | 32.9% | 42.3% | 70.0% | 100.0% | 12.1% |
| **7** | MEERA DESHMUKH | 0.0 / 5.5y | **29.6%** | Weak match | 9.4% | 32.7% | 30.0% | 100.0% | 32.5% |
| **8** | Candidate 02 Priya Patel React | 0.0 / 6.1y | **29.1%** | Weak match | 10.9% | 25.7% | 30.0% | 100.0% | 46.3% |
| **9** | ROHIT VERMA | 0.0 / 3.5y | **23.3%** | Weak match | 11.9% | 17.4% | 21.0% | 100.0% | 0.0% |
| **10**| DEEPAK NAIR | 0.0 / 0.0y | **23.0%** | Weak match | 10.4% | 34.4% | 0.8% | 100.0% | 0.0% |
| **11**| DR. KAVITA KRISHNAN | 0.0 / 6.9y | **20.8%** | Weak match | 9.4% | 4.1% | 30.0% | 100.0% | 0.0% |
| **12**| Pooja Hegde (Marketer) | 0.0 / 7.5y | **17.6%** | Weak match | 0.0% | 6.5% | 30.0% | 100.0% | 0.0% |

---

### 2.2 React Frontend Developer JD (`react_frontend_jd.docx`)
- **Required Skills:** React, JavaScript, TypeScript, HTML/CSS, Tailwind CSS, Redux, REST API, Git.
- **Preferred Skills:** Next.js, GraphQL, Webpack, Jest, Responsive Design, Performance Optimization.
- **Experience Required:** 3.0 years | **Min Qualification:** Bachelor's Degree.

| Rank | Candidate | Exp (Rel/Tot) | Match % | Band | Skill | Semantic | Experience | Qual | Title |
| :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | Candidate 02 Priya Patel React | 6.1 / 6.1y | **83.4%** | Strong match | 81.3% | 67.4% | 100.0% | 100.0% | 85.0% |
| **2** | MEERA DESHMUKH | 5.5 / 5.5y | **82.1%** | Strong match | 78.4% | 66.0% | 100.0% | 100.0% | 85.0% |
| **3** | ROHIT VERMA | 3.5 / 3.5y | **56.6%** | Partial match | 45.2% | 48.0% | 100.0% | 100.0% | 0.0% |
| **4** | Ananya Iyer | 0.0 / 7.5y | **46.8%** | Partial match | 25.4% | 42.1% | 30.0% | 100.0% | 100.0% |
| **5** | RAHUL KAPOOR | 0.0 / 3.9y | **45.0%** | Partial match | 25.8% | 35.8% | 30.0% | 100.0% | 100.0% |
| **6** | ARAVIND SHARMA | 0.0 / 6.1y | **43.7%** | Partial match | 22.8% | 34.8% | 30.0% | 100.0% | 100.0% |
| **7** | DEEPAK NAIR | 0.0 / 0.0y | **33.3%** | Weak match | 38.6% | 36.3% | 0.8% | 100.0% | 0.0% |
| **8** | SNEHA BANERJEE | 0.0 / 3.5y | **30.2%** | Weak match | 21.0% | 32.7% | 30.0% | 100.0% | 0.0% |
| **9** | Siddharth Reddy | 0.0 / 9.6y | **29.7%** | Weak match | 19.5% | 33.1% | 30.0% | 100.0% | 0.0% |
| **10**| Vikram Singh | 0.0 / 5.9y | **28.3%** | Weak match | 17.5% | 31.6% | 30.0% | 100.0% | 0.0% |
| **11**| DR. KAVITA KRISHNAN | 0.0 / 6.9y | **21.1%** | Weak match | 9.4% | 5.3% | 30.0% | 100.0% | 0.0% |
| **12**| Pooja Hegde (Marketer) | 0.0 / 7.5y | **17.6%** | Weak match | 0.0% | 6.5% | 30.0% | 100.0% | 0.0% |

---

### 2.3 AI/ML Engineer JD (`aiml_engineer_jd.pdf`)
- **Required Skills:** Python, PyTorch/TensorFlow, Machine Learning, Deep Learning, NLP, Scikit-Learn, Git.
- **Preferred Skills:** Hugging Face, Transformers, MLflow, Docker, Kubernetes, AWS.
- **Experience Required:** 4.0 years | **Min Qualification:** Master's or Ph.D. Degree.

| Rank | Candidate | Exp (Rel/Tot) | Match % | Band | Skill | Semantic | Experience | Qual | Title |
| :---: | :--- | :---: | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| **1** | DR. KAVITA KRISHNAN | 6.9 / 6.9y | **87.8%** | Strong match | 84.5% | 76.2% | 100.0% | 100.0% | 85.0% |
| **2** | Ananya Iyer | 0.0 / 7.5y | **40.4%** | Partial match | 18.2% | 40.8% | 30.0% | 100.0% | 35.8% |
| **3** | Siddharth Reddy | 0.0 / 9.6y | **39.0%** | Weak match | 18.8% | 40.8% | 30.0% | 100.0% | 23.4% |
| **4** | RAHUL KAPOOR | 0.0 / 3.9y | **38.9%** | Weak match | 18.2% | 39.4% | 30.0% | 100.0% | 23.4% |
| **5** | ARAVIND SHARMA | 0.0 / 6.1y | **38.3%** | Weak match | 16.4% | 39.5% | 30.0% | 100.0% | 23.4% |
| **6** | SNEHA BANERJEE | 0.0 / 3.5y | **37.7%** | Weak match | 18.2% | 34.6% | 30.0% | 100.0% | 23.4% |
| **7** | Vikram Singh | 0.0 / 5.9y | **36.9%** | Weak match | 14.8% | 39.4% | 30.0% | 100.0% | 23.4% |
| **8** | DEEPAK NAIR | 0.0 / 0.0y | **29.7%** | Weak match | 27.6% | 33.7% | 0.8% | 100.0% | 0.0% |
| **9** | MEERA DESHMUKH | 0.0 / 5.5y | **29.2%** | Weak match | 9.4% | 31.0% | 30.0% | 100.0% | 23.4% |
| **10**| Candidate 02 Priya Patel React | 0.0 / 6.1y | **28.6%** | Weak match | 9.4% | 28.5% | 30.0% | 100.0% | 23.4% |
| **11**| ROHIT VERMA | 0.0 / 3.5y | **22.5%** | Weak match | 9.4% | 22.0% | 21.0% | 100.0% | 0.0% |
| **12**| Pooja Hegde (Marketer) | 0.0 / 7.5y | **17.6%** | Weak match | 0.0% | 6.5% | 30.0% | 100.0% | 0.0% |

---

## 3. Domain Integrity Audit: Priya Patel vs. Pooja Hegde

A fundamental test of ranking integrity is verifying that a candidate with software engineering skills is never outranked by an off-domain professional (marketing) when applying for software engineering roles.

### 3.1 Java Backend Engineer JD
- **Priya Patel (Senior Frontend Developer):**
  - Score: **29.1%** (Rank 8)
  - Skills: 10.9% (matches Git, REST API, Agile)
  - Title Relevance: 46.3% (technical engineering title)
- **Pooja Hegde (Growth Marketing Lead):**
  - Score: **17.6%** (Rank 12)
  - Skills: 0.0%
  - Title Relevance: 0.0%
- **Margin:** Priya ranks **4 positions and +11.5 percentage points** above Pooja.

### 3.2 React Frontend Developer JD
- **Priya Patel (Senior Frontend Developer):**
  - Score: **83.4%** (Rank 1, Strong match)
  - Skills: 81.3% | Title Relevance: 85.0%
- **Pooja Hegde (Growth Marketing Lead):**
  - Score: **17.6%** (Rank 12, Weak match)
  - Skills: 0.0% | Title Relevance: 0.0%
- **Margin:** Priya ranks **11 positions and +65.8 percentage points** above Pooja.

---

## 4. Wild Resume Ingestion & Accuracy Evaluation

We generated 10 adversarial synthetic resumes ([sample_data/resumes_wild/](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/sample_data/resumes_wild/)) reflecting messy formatting anomalies encountered in production:
1. `wild_01_no_headings.txt`: Free-flowing narrative text with zero section headers.
2. `wild_02_table_skills.docx`: Technical skills embedded in table cells.
3. `wild_03_header_contact.docx`: Contact information placed exclusively in the DOCX header container.
4. `wild_04_twocolumn_sidebar.pdf`: Asymmetric two-column PDF with left-hand sidebar.
5. `wild_05_varied_dates.pdf`: Irregular date ranges (*"since 2018"*, *"2023 – Present"*, *"Sept '21 – Mar '23"*).
6. `wild_06_experience_stated_only.txt`: Experience stated exclusively in narrative prose (*"over 5 years of professional experience"*).
7. `wild_07_indian_education.pdf`: Indian academic grading (*"Dr. R. K. Mehta"*, B.Tech CSE, CGPA 8.2/10).
8. `wild_08_senior_4page.pdf`: 4-page senior CV with 6 historical roles, ligatures, and unicode bullets.
9. `wild_09_scanned_image.pdf`: Scanned/image-only PDF with zero selectable text characters.
10. `wild_10_duplicate.pdf`: Duplicate submission of `wild_01`.

### 4.1 Field Accuracy Scorecard

| Evaluated Field | Correct / Total | Measured Accuracy | Threshold | Outcome |
| :--- | :---: | :---: | :---: | :---: |
| **Candidate Name** | 9 / 9 | **100.0%** | $\ge 80.0\%$ | **PASS** |
| **Email Address** | 9 / 9 | **100.0%** | $\ge 95.0\%$ | **PASS** |
| **Phone Number** | 9 / 9 | **100.0%** | $\ge 90.0\%$ | **PASS** |
| **Degree Classification** | 9 / 9 | **100.0%** | $\ge 85.0\%$ | **PASS** |
| **Experience Tenure (within 1.0 yr)** | 9 / 9 | **100.0%** | $\ge 70.0\%$ | **PASS** |
| **Scanned PDF Handling** | 1 / 1 | **100.0%** | $100.0\%$ | **PASS** |
| **Duplicate Candidate Flag** | 1 / 1 | **100.0%** | $100.0\%$ | **PASS** |

---

## 5. Keyword Stuffing Defense Experiment

To evaluate vulnerability to adversarial keyword stuffing, we tested `wild_keyword_stuffing.txt` (candidate: *Jordan Miller*). The resume contains an unsorted list of 40 technical keywords, 0 job entries, 0 degrees, and 0 job titles.

### 5.1 Experiment Results (Java Backend Engineer JD)

| Rank | Candidate | Match Score | Band | Skill Score | Semantic | Exp Score | Qual Score | Title Score |
| :---: | :--- | :---: | :--- | :---: | :---: | :---: | :---: | :---: |
| 1 | Siddharth Reddy | 79.1% | Strong match | 77.3% | 63.8% | 100.0% | 100.0% | 46.2% |
| 2 | ARAVIND SHARMA | 75.3% | Strong match | 71.0% | 58.5% | 100.0% | 100.0% | 46.2% |
| 3 | Vikram Singh | 60.9% | Good match | 47.2% | 47.9% | 100.0% | 100.0% | 0.0% |
| 4 | Ananya Iyer | 60.2% | Good match | 43.8% | 49.4% | 100.0% | 100.0% | 7.2% |
| 5 | RAHUL KAPOOR | 48.6% | Partial match | 29.6% | 41.8% | 78.0% | 100.0% | 15.2% |
| 6 | SNEHA BANERJEE | 48.4% | Partial match | 32.9% | 42.3% | 70.0% | 100.0% | 12.1% |
| **7**| **Jordan Miller (Keyword Stuffed)**| **37.9%** | **Weak match** | **72.4%** | **23.6%** | **0.0%** | **30.0%** | **0.0%** |
| 8 | MEERA DESHMUKH | 29.6% | Weak match | 9.4% | 32.7% | 30.0% | 100.0% | 32.5% |
| 9 | Candidate 02 Priya Patel React | 29.1% | Weak match | 10.9% | 25.7% | 30.0% | 100.0% | 46.3% |
| 10| ROHIT VERMA | 23.3% | Weak match | 11.9% | 17.4% | 21.0% | 100.0% | 0.0% |
| 11| DEEPAK NAIR | 23.0% | Weak match | 10.4% | 34.4% | 0.8% | 100.0% | 0.0% |
| 12| DR. KAVITA KRISHNAN | 20.8% | Weak match | 9.4% | 4.1% | 30.0% | 100.0% | 0.0% |
| 13| Pooja Hegde | 17.6% | Weak match | 0.0% | 6.5% | 30.0% | 100.0% | 0.0% |

### 5.2 Analysis & System Safeguards
- **Why Naive ATS Fails:** A conventional ATS ranking solely on skill count would place Jordan Miller at Rank #1 with 15 matched skills.
- **Why Our Engine Neutralizes It:** 
  1. **Zero Experience (0.0%):** Jordan Miller has zero verified dates, receiving zero experience credit.
  2. **Low Semantic Context (23.6%):** A list of keywords lacks contextual duty sentences, suppressing the semantic duty score.
  3. **Zero Title Match (0.0%):** No professional title was found.
  4. **Composite Result:** Despite scoring 72.4% on raw skills, the composite weighted score is strictly bounded to **37.9% ('Weak match')**, trailing behind every legitimate Java backend engineer.

---

## 6. Performance & Execution Latency Benchmarks

Benchmarks were recorded on a standard Windows developer workstation without GPU acceleration.

### 6.1 12-Resume Execution Profile
- **Cold Execution (first start, loading weights):** 1,472 ms
- **Warm Execution (in-memory cached vectors):** **12.55 ms** (79.7x speedup)
- **API Response Overhead (FastAPI + JSON serialization):** 8.2 ms

### 6.2 50-Candidate Large Cohort Benchmark
- **Cohort Size:** 50 parsed synthetic candidates
- **Total Execution Time:** **1,203.73 ms** (1.204 seconds)
- **Average Latency per Candidate:** **24.07 ms**
- **Top Candidate:** Siddharth Reddy (79.1%) | **Lowest Candidate:** Pooja Hegde (17.6%)
- **Target Threshold:** $< 5,000$ ms (**PASSED** with 75.9% margin).
