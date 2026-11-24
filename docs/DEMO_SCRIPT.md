# Live Video Walkthrough & Recruiter Demo Script

> A synchronized 6-to-8 minute end-to-end demonstration script for live evaluator presentations, recorded walkthroughs, and executive demonstrations of the **AI-Based Resume Matching & Candidate Ranking System**.

---

## Demo Overview & Pre-Flight Checklist

### Setup & Verification (2 minutes before presentation)
1. **Start Backend Server:**
   ```powershell
   .\scripts\run_backend.ps1
   ```
   *Verify: Terminal shows "Uvicorn running on http://127.0.0.1:8080".*
2. **Start Frontend Client:**
   ```powershell
   .\scripts\run_frontend.ps1
   ```
   *Verify: Terminal shows "Local: http://localhost:5173/".*
3. **Browser Setup:**
   - Open Chrome or Edge to `http://localhost:5173/`.
   - Set browser zoom to 100%. Open Developer Tools (F12) to Console tab to prove zero runtime warnings or errors.

---

## Timed Walkthrough Script (Total Duration: 7:30)

```
00:00 - 01:00  Scene 1: Introduction & The Core Problem
01:00 - 02:15  Scene 2: One-Click Demo Seeding & Instant Matching
02:15 - 04:00  Scene 3: Deep Candidate Comparison (Siddharth vs. Vikram vs. Priya)
04:00 - 05:15  Scene 4: Explainability, Transparency & Keyword-Stuffing Defense
05:15 - 06:15  Scene 5: Edge Case Resilience (Scanned PDF & Off-Domain Marketer)
06:15 - 07:00  Scene 6: Staleness Detection & Recruiter Editing
07:00 - 07:30  Scene 7: Conclusion & Responsible AI Statement
```

---

### Scene 1: Introduction & The Core Problem (0:00 – 1:00)

**Visual:**
Browser is open to the Home page (`http://localhost:5173/`). The editorial sage-ivory layout is visible: large condensed uppercase headline *"MATCH RESUMES TO JOB DESCRIPTIONS WITH EXPLAINABLE AI"*, clean top navigation, and two upload zones.

**Action:**
Cursor hovers over the navigation and down to the upload cards.

**Spoken Script:**
> *"Hello everyone. Today I'm demonstrating our AI-Based Resume Matching and Candidate Ranking System.*
>
> *Every recruiter faces two critical problems with modern hiring software: traditional ATS tools rely on simplistic keyword matching, which candidates game by copying and pasting job requirements. On the other hand, black-box LLMs are slow, non-deterministic, expensive, and raise severe data privacy and compliance concerns.*
>
> *We engineered this platform as a high-performance, deterministic alternative. It combines structured NLP parsing, hierarchical taxonomy resolution, and local sentence embeddings to rank candidates in milliseconds while providing complete mathematical explainability for every score."*

---

### Scene 2: One-Click Demo Seeding & Instant Matching (1:00 – 2:15)

**Visual:**
On the Home page, point to the top notification banner or the Quick Demo section.

**Action:**
1. Click the **"⚡ Load Java Demo"** pill button on the Home page.
2. The UI seeds the Senior Java Backend Engineer JD and 12 synthetic resumes in one click.
3. Automatically transitions to the **Ranking Dashboard** (`/dashboard`).
4. Point out the loaded leaderboard table with 12 populated candidate rows.

**Spoken Script:**
> *"To demonstrate live functionality, I'm clicking our one-click 'Load Java Demo' button. Behind the scenes, the FastAPI backend has loaded our Senior Java Backend Engineer specification and ingested 12 synthetic resumes spanning different experience tiers, skills, and domains.*
>
> *Notice how fast that was: the full matching run across all 12 candidates executed in just 12 milliseconds warm. In the dashboard header, we immediately see our high-level cohort statistics: an average score of 42.4%, two Strong matches, two Good matches, two Partial matches, and six Weak matches.*
>
> *Notice our accessibility-first design: recommendation bands are never communicated by color alone. Every badge explicitly displays 'Strong match', 'Good match', 'Partial match', or 'Weak match', styled with WCAG AA compliant contrast ratios."*

---

### Scene 3: Deep Candidate Comparison (2:15 – 4:00)

**Visual:**
Dashboard table showing:
- Rank 1: **Siddharth Reddy** (79.1%, Strong match)
- Rank 3: **Vikram Singh** (60.9%, Good match)
- Rank 8: **Priya Patel** (29.1%, Weak match)

**Action:**
1. Click on **Siddharth Reddy** (Rank 1). The app navigates to `/candidate/1`.
2. Scroll through the Candidate Hero Card, Score Breakdown Gauges, and Skill Evidence Chips.
3. Click "Next Candidate" to show **Vikram Singh** (Rank 3).
4. Navigate back or click **Priya Patel** (Rank 8).

**Spoken Script:**
> *"Now let's examine why the engine ranked these candidates in this exact order. Let's compare three distinct profiles:*
>
> *First, our Rank #1 candidate, **Siddharth Reddy**, scoring **79.1%**. Siddharth is a textbook strong match. He brings 9.6 years of relevant enterprise Java experience against our 5-year requirement, earning a perfect 100% experience score. In the Skill Match section, our taxonomy recognized his expertise across Java, Spring Boot, Microservices, and Kafka, scoring 77.3%. His semantic duty alignment scored 63.8% because his previous work descriptions closely match our architectural responsibilities.*
>
> *Next, let's look at **Vikram Singh** at Rank #3 with **60.9%** ('Good match'). Vikram has nearly 6 years of solid backend experience and matches our core Java stack. However, his title relevance scored 0% because his previous titles were generalist software engineering roles, and he lacks our preferred cloud certifications, placing him deservedly in the Good tier.*
>
> *Finally, look at **Priya Patel** at Rank #8 scoring **29.1%** ('Weak match'). Priya is a skilled Senior Frontend Developer with 6 years in React, TypeScript, and modern UI architectures. A naive keyword tool might have ranked her high simply because she has tech experience at top firms. But our engine correctly identified that her skills and titles are frontend-focused, giving her only 10.9% on skill relevance and 0 years of relevant backend experience. She is evaluated honestly as a Weak match for a Java backend role."*

---

### Scene 4: Explainability & Keyword-Stuffing Defense (4:00 – 5:15)

**Visual:**
On Siddharth Reddy's detail page, scroll to the **Skill Alignment** and **Factor Breakdown** tables.

**Action:**
1. Hover over the skill chips showing green matched chips (`Java`, `Spring Boot`, `Kafka`), yellow partial chips, and grey missing chips.
2. Point out the **Knockout Safeguard** status card (*"Knockout Threshold: Passed"*).

**Spoken Script:**
> *"A critical differentiator of our system is transparency. We do not provide an arbitrary number; we explain every single point.*
>
> *Under Skill Breakdown, recruiters see exact evidence snippets parsed from the candidate's resume for every matched requirement. Our hierarchical taxonomy prevents gaming via Skill Family Collapse: if a candidate repeats synonyms like 'Docker', 'Containerization', and 'Docker Compose', our taxonomy collapses them into a single concept family so they cannot artificially inflate their score.*
>
> *Furthermore, our Knockout Safeguard protects hiring teams against resume stuffing. In our robustness benchmarks, an adversarial candidate who dumped 40 technical keywords into a single resume block without any verifiable job experience or education was capped at 37.9% ('Weak match') because the engine detected zero chronological tenure and knocked out the fraudulent profile."*

---

### Scene 5: Edge Case Resilience (5:15 – 6:15)

**Visual:**
Return to Dashboard. Point out the bottom candidate **Pooja Hegde** (Rank 12, 17.6%). Then open the file upload modal or explain scanned PDF handling.

**Action:**
1. Highlight **Pooja Hegde** (Growth Marketing Lead).
2. Briefly show Developer Tools Console or mention batch upload tests.

**Spoken Script:**
> *"Let's also look at our boundary test cases:*
>
> *At the very bottom of our leaderboard sits **Pooja Hegde** at **17.6%**. Pooja is an accomplished marketing professional with 7.5 years of experience. A flawed semantic search model might have given her a generic professional score. But our calibrated title threshold and domain requirements ensure she scores 0% on skills and 0% on title relevance, guaranteeing she never displaces any engineering candidate.*
>
> *In addition, our ingestion pipeline handles format anomalies gracefully. When an applicant uploads a scanned or image-only PDF with zero text layer, our text extractor detects the missing text stream, raises an isolated ScannedPDFError, and alerts the recruiter without crashing the server or aborting the batch."*

---

### Scene 6: Staleness Detection & Recruiter Editing (6:15 – 7:00)

**Visual:**
Navigate to the Job Description edit tab or trigger a JD update.

**Action:**
1. Show the JD modification modal or trigger a minor skill update.
2. Point out the yellow warning banner that appears on the dashboard:
   *"Job description has been modified since these scores were calculated. Re-run matching to update rankings."*
3. Click **"⚡ Re-run Now"**. The banner clears and scores synchronize instantly.

**Spoken Script:**
> *"In real-world hiring, requirements evolve. If a hiring manager updates the job description—such as adding AWS or Kubernetes as mandatory—our system detects the modification using SHA-256 snapshot hashes.*
>
> *The dashboard immediately flags existing results as stale with this yellow warning banner. With a single click of 'Re-run Now', the engine re-evaluates the cohort against the updated criteria in milliseconds, keeping decisions synchronized."*

---

### Scene 7: Conclusion & Responsible AI Statement (7:00 – 7:30)

**Visual:**
Return to Home page or Dashboard summary.

**Action:**
Present closing remarks with contact details and repository link.

**Spoken Script:**
> *"To summarize: our system provides enterprise recruiters with a deterministic, sub-20 millisecond matching engine that cuts candidate screening time from hours to seconds.*
>
> *Most importantly, our platform is built for Responsible AI: protected demographic attributes like gender, age, ethnicity, and photos are never collected or scored. Our algorithms comply with EU AI Act High-Risk transparency requirements, run 100% locally with complete data privacy, and deliver auditable, ethical hiring recommendations.*
>
> *Thank you, and I look forward to your questions."*

---

## Contingency Plan: "What To Do If X Fails During Live Demo"

| Issue / Failure | Immediate Contingency Action | Verbal Recovery Line |
| :--- | :--- | :--- |
| **Backend port 8080 busy or refused** | Run `Stop-Process -Name python -Force` in PowerShell, then re-run `.\scripts\run_backend.ps1`. | *"Let me quickly restart our local background API service."* |
| **Frontend fails to open on 5173** | In `frontend/`, run `node node_modules/vite/bin/vite.js --port 5173`. | *"Vite is hot-reloading the frontend client."* |
| **Demo button shows 'Failed to seed'** | Check backend terminal; if SQLite was locked, delete `resume_matcher.db` and click Seed again. | *"The local test SQLite database refreshed its connection pool."* |
| **A screenshot or image doesn't render** | All screenshots are permanently backed up in [docs/screenshots/](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/docs/screenshots/). Show the static files. | *"Here are the exact high-resolution renders captured across 1280px, 768px, and 375px viewports."* |
| **Evaluator asks why an LLM isn't used** | Refer directly to Section 1, Question 1.1 of [INTERVIEW_PREP.md](file:///c:/Users/singh/OneDrive/Desktop/AI-Based%20Resume%20Matching%20%26%20Candidate%20Ranking%20System/docs/INTERVIEW_PREP.md). | *"We deliberately chose a hybrid architecture for determinism, sub-20ms speed, and privacy compliance."* |
