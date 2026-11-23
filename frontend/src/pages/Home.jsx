/*
 * pages/Home.jsx — Editorial Intake & Evaluation Page (JD + Resumes).
 *
 * Implements Phase 6A Editorial Sage Design:
 * - Huge Anton display headline, Fraunces serif headings, Inter tabular-nums body.
 * - Paper surfaces, sage & forest green accents, hairline dividers.
 * - Live preview card, 3-pillar feature list, 1-click evaluator demo.
 * - Step 1: Job Description extraction & editing.
 * - Step 2: Batch Resume upload & parsed candidate repository.
 * - Deterministic matching execution callout.
 */

import React, { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { parseJDText, parseJDFile, updateJD } from "../api/jd";
import {
  uploadResumes,
  listCandidates,
  deleteCandidate,
  clearAllCandidates,
} from "../api/resumes";
import { runMatch } from "../api/match";
import { seedDemo } from "../api/demo";
import { useJD } from "../context/JDContext";
import API from "../api/client";

// Shared Editorial UI Primitives
import Button from "../components/ui/Button";
import Card from "../components/ui/Card";
import SectionHeader from "../components/ui/SectionHeader";
import Eyebrow from "../components/ui/Eyebrow";
import Chip from "../components/ui/Chip";
import Badge from "../components/ui/Badge";
import ScoreBar from "../components/ui/ScoreBar";
import Divider from "../components/ui/Divider";
import EmptyState from "../components/ui/EmptyState";
import SkillChips from "../components/SkillChips";

export default function Home() {
  const navigate = useNavigate();

  // Backend health status
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Matching trigger state
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState(null);

  // One-click demo state
  const [demoLoading, setDemoLoading] = useState(false);
  const [demoSelectedJd, setDemoSelectedJd] = useState(null);
  const [demoError, setDemoError] = useState(null);

  // ── Step 1: JD input state ──
  const [activeTab, setActiveTab] = useState("paste"); // "paste" | "upload"
  const [jdText, setJdText] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [parsedResult, setParsedResult] = useState(null);
  const [jdId, setJdId] = useState(null);

  const [editRequired, setEditRequired] = useState([]);
  const [editPreferred, setEditPreferred] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);

  // Global JD context
  const { activeJD, setActiveJD } = useJD();

  // ── Step 2: Resume Batch Upload state ──
  const [resumeFiles, setResumeFiles] = useState([]);
  const [resumeDragActive, setResumeDragActive] = useState(false);
  const resumeInputRef = useRef(null);

  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [batchResults, setBatchResults] = useState(null);
  const [candidates, setCandidates] = useState([]);
  const [candidatesLoading, setCandidatesLoading] = useState(false);
  const [candidatesError, setCandidatesError] = useState(null);
  const [deletingId, setDeletingId] = useState(null);

  // ── Health check and initial load ──
  useEffect(() => {
    API.get("/health")
      .then((res) => {
        setHealthStatus(res.data);
        setHealthLoading(false);
      })
      .catch(() => {
        setHealthStatus({ status: "unreachable", api: false, database: false });
        setHealthLoading(false);
      });

    loadCandidates();
  }, []);

  // Sync activeJD with local state if context already has one
  useEffect(() => {
    if (activeJD && !parsedResult) {
      setParsedResult(activeJD.parsed);
      setJdId(activeJD.id);
      setEditRequired(activeJD.parsed.required_skills || []);
      setEditPreferred(activeJD.parsed.preferred_skills || []);
    }
  }, [activeJD]);

  const loadCandidates = async () => {
    setCandidatesLoading(true);
    setCandidatesError(null);
    try {
      const data = await listCandidates();
      setCandidates(data);
    } catch (err) {
      setCandidatesError("Failed to fetch candidates from server.");
    } finally {
      setCandidatesLoading(false);
    }
  };

  // ── Analyze JD ──
  const handleAnalyze = async () => {
    setParsing(true);
    setParseError(null);
    setParsedResult(null);
    setSaveMessage(null);

    try {
      let result;
      if (activeTab === "paste") {
        if (!jdText.trim() || jdText.trim().length < 10) {
          throw new Error("Please enter at least 10 characters of JD text.");
        }
        result = await parseJDText(jdText);
      } else {
        if (!selectedFile) {
          throw new Error("Please select a file to upload.");
        }
        result = await parseJDFile(selectedFile);
      }

      setParsedResult(result.parsed);
      setJdId(result.id);
      setEditRequired(result.parsed.required_skills || []);
      setEditPreferred(result.parsed.preferred_skills || []);

      setActiveJD({ id: result.id, title: result.title, parsed: result.parsed });
    } catch (err) {
      const msg =
        err.response?.data?.detail || err.message || "Failed to parse JD.";
      setParseError(msg);
    } finally {
      setParsing(false);
    }
  };

  // ── Save JD Changes ──
  const handleSave = async () => {
    if (!jdId) return;
    setSaving(true);
    setSaveMessage(null);

    try {
      const updated = await updateJD(jdId, {
        required_skills: editRequired,
        preferred_skills: editPreferred,
      });

      setParsedResult(updated.parsed);
      setActiveJD({ id: updated.id, title: updated.title, parsed: updated.parsed });
      setSaveMessage("Changes saved successfully!");
      setTimeout(() => setSaveMessage(null), 3000);
    } catch (err) {
      setSaveMessage(
        "Failed to save changes: " +
          (err.response?.data?.detail || err.message)
      );
    } finally {
      setSaving(false);
    }
  };

  // ── JD File drag-and-drop ──
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  // ── Resume Drag-and-drop & File Selection ──
  const handleResumeDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setResumeDragActive(true);
    } else if (e.type === "dragleave") {
      setResumeDragActive(false);
    }
  };

  const handleResumeDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setResumeDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      addResumeFiles(Array.from(e.dataTransfer.files));
    }
  };

  const handleResumeFileSelect = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      addResumeFiles(Array.from(e.target.files));
    }
  };

  const addResumeFiles = (incoming) => {
    const valid = incoming.filter((f) => {
      const ext = f.name.toLowerCase();
      return ext.endsWith(".pdf") || ext.endsWith(".docx");
    });
    setResumeFiles((prev) => {
      const existingNames = new Set(prev.map((f) => f.name));
      const novel = valid.filter((f) => !existingNames.has(f.name));
      return [...prev, ...novel];
    });
  };

  const removeSelectedFile = (index) => {
    setResumeFiles((prev) => prev.filter((_, i) => i !== index));
  };

  // ── Batch Upload Resumes ──
  const handleUploadResumes = async () => {
    if (resumeFiles.length === 0) return;
    setUploading(true);
    setUploadProgress(0);
    setBatchResults(null);

    try {
      const response = await uploadResumes(resumeFiles, (pct) => {
        setUploadProgress(pct);
      });
      setBatchResults(response);
      setResumeFiles([]);
      await loadCandidates();
    } catch (err) {
      setBatchResults({
        total_files: resumeFiles.length,
        successful: 0,
        failed: resumeFiles.length,
        results: [
          {
            filename: "Batch request",
            status: "failed",
            error: err.response?.data?.detail || err.message || "Upload request failed",
          },
        ],
      });
    } finally {
      setUploading(false);
    }
  };

  // ── Delete Candidate ──
  const handleDeleteCandidate = async (candidateId) => {
    if (!window.confirm("Are you sure you want to delete this candidate?")) return;
    setDeletingId(candidateId);
    try {
      await deleteCandidate(candidateId);
      setCandidates((prev) => prev.filter((c) => c.id !== candidateId));
    } catch (err) {
      alert("Failed to delete candidate: " + (err.response?.data?.detail || err.message));
    } finally {
      setDeletingId(null);
    }
  };

  // ── Clear All Candidates ──
  const handleClearAllCandidates = async () => {
    if (!window.confirm("Are you sure you want to clear ALL candidates? This cannot be undone.")) return;
    try {
      await clearAllCandidates();
      setCandidates([]);
      setBatchResults(null);
    } catch (err) {
      alert("Failed to clear candidates: " + (err.response?.data?.detail || err.message));
    }
  };

  // ── One-Click Demo Seeder ──
  const handleSeedDemo = async (jdKey) => {
    setDemoLoading(true);
    setDemoSelectedJd(jdKey);
    setDemoError(null);
    try {
      const resp = await seedDemo(jdKey, true);
      navigate(`/dashboard?run=${resp.run_id}`);
    } catch (err) {
      console.error("Demo seed error:", err);
      setDemoError(err.response?.data?.detail || err.message || "Failed to initialize demo data.");
      setDemoLoading(false);
      setDemoSelectedJd(null);
    }
  };

  return (
    <div className="space-y-12 pb-16">
      {/* ── Editorial Top System Status Bar ── */}
      <div className="flex flex-wrap items-center justify-between gap-3 bg-brand-paper border border-brand-line px-5 py-2.5 rounded-full shadow-soft text-xs text-brand-muted">
        <div className="flex items-center gap-2">
          <span className="font-semibold text-brand-ink uppercase tracking-wider text-[11px]">System Status:</span>
          {healthLoading ? (
            <span className="text-brand-muted">verifying runtime...</span>
          ) : healthStatus?.api && healthStatus?.database ? (
            <span className="inline-flex items-center text-band-strong font-medium">
              <span className="h-2 w-2 rounded-full bg-band-strong mr-1.5 animate-pulse" />
              Backend &amp; SQLite Online
            </span>
          ) : (
            <span className="inline-flex items-center text-band-weak font-medium">
              <span className="h-2 w-2 rounded-full bg-band-weak mr-1.5" />
              Backend Offline
            </span>
          )}
        </div>
        {activeJD && (
          <div className="inline-flex items-center bg-brand-sage-soft/30 text-brand-ink px-3 py-1 rounded-full text-xs font-medium border border-brand-line">
            <span className="mr-1.5 text-brand-forest">🎯</span> Active Role:{" "}
            <span className="font-bold ml-1 text-brand-forest">{activeJD.title || "Untitled Role"}</span>
          </div>
        )}
      </div>

      {/* ── Editorial Hero Section ── */}
      <section className="space-y-8">
        <div className="space-y-3">
          <Eyebrow>AI RESUME MATCHING</Eyebrow>
          <p className="font-serif italic text-xl sm:text-2xl text-brand-muted">
            Smarter shortlists, explained.
          </p>
          <h1 className="font-display uppercase text-5xl sm:text-7xl lg:text-8xl tracking-tight leading-[0.92] text-brand-sage-deep max-w-4xl">
            BETTER HIRING, RANKED
          </h1>
          <p className="text-base sm:text-lg text-brand-muted max-w-2xl font-sans pt-2 leading-relaxed">
            Ingest unstructured resumes, extract core competencies, and evaluate candidates with calibrated semantic embeddings and transparent multi-factor scoring.
          </p>
        </div>

        {/* Hero CTAs */}
        <div className="flex flex-wrap items-center gap-4 pt-2">
          <Button
            variant="primary"
            size="lg"
            onClick={() => {
              const demoSec = document.getElementById("demo-evaluator-section");
              if (demoSec) demoSec.scrollIntoView({ behavior: "smooth" });
            }}
          >
            Try with sample data
          </Button>
          <Button
            variant="outlined"
            size="lg"
            onClick={() => {
              const step1Sec = document.getElementById("step-1-jd-section");
              if (step1Sec) step1Sec.scrollIntoView({ behavior: "smooth" });
            }}
          >
            Upload your own
          </Button>
        </div>

        {/* Live Preview Card (Static Synthetic Sample - Example Only) */}
        <div className="pt-4">
          <Card padding="p-6 sm:p-8" className="bg-brand-paper border-brand-line">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-brand-line gap-2">
              <div>
                <Eyebrow>EXAMPLE PREVIEW · STATIC DEMO</Eyebrow>
                <h3 className="font-serif text-lg sm:text-xl font-bold text-brand-ink">
                  Deterministic Multi-Factor Scoring in Action
                </h3>
              </div>
              <span className="text-[11px] font-sans font-bold uppercase tracking-wider text-brand-forest bg-brand-sage-soft/50 px-3 py-1 rounded-full self-start sm:self-auto border border-brand-line">
                Example Benchmark
              </span>
            </div>

            <div className="mt-4 divide-y divide-brand-line">
              {/* Row 1 */}
              <div className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1 md:w-1/3">
                  <div className="flex items-center gap-2">
                    <span className="font-display text-xl text-brand-forest">#1</span>
                    <span className="font-serif font-bold text-base text-brand-ink">Elena Rostova</span>
                    <span className="text-[10px] font-mono uppercase text-brand-muted bg-brand-ivory px-1.5 py-0.5 rounded border border-brand-line">Example</span>
                    <Badge band="strong">Strong Match</Badge>
                  </div>
                  <p className="text-xs text-brand-muted">Senior AI/ML Research Engineer · 6.5 yrs</p>
                </div>
                <div className="md:w-1/3">
                  <ScoreBar value={94.2} band="strong" label="Composite Score" />
                </div>
                <div className="flex flex-wrap gap-1.5 md:w-1/3 justify-start md:justify-end">
                  <Chip variant="matched">PyTorch</Chip>
                  <Chip variant="matched">Transformers</Chip>
                  <Chip variant="matched">NLP</Chip>
                  <Chip variant="preferred">+4 more</Chip>
                </div>
              </div>

              {/* Row 2 */}
              <div className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1 md:w-1/3">
                  <div className="flex items-center gap-2">
                    <span className="font-display text-xl text-brand-sage-deep">#2</span>
                    <span className="font-serif font-bold text-base text-brand-ink">Marcus Vance</span>
                    <span className="text-[10px] font-mono uppercase text-brand-muted bg-brand-ivory px-1.5 py-0.5 rounded border border-brand-line">Example</span>
                    <Badge band="good">Good Match</Badge>
                  </div>
                  <p className="text-xs text-brand-muted">Lead Systems Architect · 8.0 yrs</p>
                </div>
                <div className="md:w-1/3">
                  <ScoreBar value={68.5} band="good" label="Composite Score" />
                </div>
                <div className="flex flex-wrap gap-1.5 md:w-1/3 justify-start md:justify-end">
                  <Chip variant="matched">FastAPI</Chip>
                  <Chip variant="matched">Docker</Chip>
                  <Chip variant="partial">Python</Chip>
                  <Chip variant="extra">+3 more</Chip>
                </div>
              </div>

              {/* Row 3 */}
              <div className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div className="space-y-1 md:w-1/3">
                  <div className="flex items-center gap-2">
                    <span className="font-display text-xl text-band-partial">#3</span>
                    <span className="font-serif font-bold text-base text-brand-ink">Sofia Chen</span>
                    <span className="text-[10px] font-mono uppercase text-brand-muted bg-brand-ivory px-1.5 py-0.5 rounded border border-brand-line">Example</span>
                    <Badge band="partial">Partial Match</Badge>
                  </div>
                  <p className="text-xs text-brand-muted">Frontend Developer · 2.5 yrs</p>
                </div>
                <div className="md:w-1/3">
                  <ScoreBar value={52.0} band="partial" label="Composite Score" />
                </div>
                <div className="flex flex-wrap gap-1.5 md:w-1/3 justify-start md:justify-end">
                  <Chip variant="matched">TypeScript</Chip>
                  <Chip variant="partial">React</Chip>
                  <Chip variant="missing">PyTorch</Chip>
                </div>
              </div>
            </div>
          </Card>
        </div>

        {/* 3-Pillar Feature List */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
          <Card padding="p-6" className="space-y-3">
            <div className="w-10 h-10 rounded-full bg-brand-forest/10 border border-brand-line flex items-center justify-center text-brand-forest">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <h3 className="font-serif text-base font-bold text-brand-ink">Parse Any Resume</h3>
            <p className="text-xs sm:text-sm text-brand-muted leading-relaxed">
              Standardize PDF and DOCX files automatically into structured contact, experience, skills, and degree entries.
            </p>
          </Card>

          <Card padding="p-6" className="space-y-3">
            <div className="w-10 h-10 rounded-full bg-brand-forest/10 border border-brand-line flex items-center justify-center text-brand-forest">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <h3 className="font-serif text-base font-bold text-brand-ink">Match by Meaning, Not Keywords</h3>
            <p className="text-xs sm:text-sm text-brand-muted leading-relaxed">
              Sentence transformers and taxonomy graph aliases prevent keyword spoofing and reward genuine domain depth.
            </p>
          </Card>

          <Card padding="p-6" className="space-y-3">
            <div className="w-10 h-10 rounded-full bg-brand-forest/10 border border-brand-line flex items-center justify-center text-brand-forest">
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="font-serif text-base font-bold text-brand-ink">Explain Every Score</h3>
            <p className="text-xs sm:text-sm text-brand-muted leading-relaxed">
              Transparent 5-factor breakdown with full text evidence, qualification checks, and knockout protection.
            </p>
          </Card>
        </div>
      </section>

      {/* ── One-Click Instant Evaluator Demo ── */}
      <section id="demo-evaluator-section">
        <Card padding="p-6 sm:p-8" className="bg-brand-paper border-brand-forest/40 relative overflow-hidden">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2 max-w-xl">
              <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-[11px] font-semibold bg-brand-forest text-brand-ivory uppercase tracking-wider">
                <span>⚡</span> ONE-CLICK EVALUATOR DEMO
              </div>
              <h2 className="font-serif text-2xl sm:text-3xl font-bold text-brand-ink tracking-tight">
                Benchmark the AI System in One Click
              </h2>
              <p className="text-xs sm:text-sm text-brand-muted leading-relaxed">
                Skip manual file preparation. Select a calibrated target role to ingest 12 synthetic candidate resumes, compute 5-factor scores, and view the live ranking dashboard.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0" id="try-demo-btn">
              <Button
                variant="secondary"
                size="md"
                disabled={demoLoading}
                onClick={() => handleSeedDemo("java")}
                className="justify-center"
              >
                <span>☕</span>
                <span>{demoLoading && demoSelectedJd === "java" ? "Seeding..." : "Java Backend JD"}</span>
                <span className="text-[10px] font-mono opacity-60">(12 Resumes)</span>
              </Button>

              <Button
                variant="secondary"
                size="md"
                disabled={demoLoading}
                onClick={() => handleSeedDemo("react")}
                className="justify-center"
              >
                <span>⚛️</span>
                <span>{demoLoading && demoSelectedJd === "react" ? "Seeding..." : "React Frontend JD"}</span>
                <span className="text-[10px] font-mono opacity-60">(12 Resumes)</span>
              </Button>

              <Button
                variant="primary"
                size="md"
                disabled={demoLoading}
                onClick={() => handleSeedDemo("aiml")}
                className="justify-center"
              >
                <span>🤖</span>
                <span>{demoLoading && demoSelectedJd === "aiml" ? "Seeding..." : "AI/ML Engineer JD"}</span>
                <span className="text-[10px] font-mono text-brand-ivory/80">(12 Resumes)</span>
              </Button>
            </div>
          </div>

          {demoLoading && (
            <div className="mt-6 pt-6 border-t border-brand-line flex items-center gap-3 text-xs sm:text-sm text-brand-forest">
              <div className="w-4 h-4 border-2 border-brand-forest border-t-transparent rounded-full animate-spin shrink-0" />
              <span>
                Ingesting calibrated specifications and 12 candidate resumes, computing 5-factor matching matrix...
              </span>
            </div>
          )}

          {demoError && (
            <div className="mt-4 p-3.5 rounded-2xl bg-band-weak/10 border border-band-weak/30 text-xs text-band-weak">
              {demoError}
            </div>
          )}
        </Card>
      </section>

      {/* ════════════════════════════════════════════════════════
          STEP 1: JOB DESCRIPTION
         ════════════════════════════════════════════════════════ */}
      <section id="step-1-jd-section">
        <Card padding="p-6 sm:p-8" className="space-y-6">
          <SectionHeader
            eyebrow="MODULE 01"
            title="Step 1: Job Description"
            subtitle="Input target role requirements to extract competencies, experience requirements, and education criteria."
            actions={
              parsedResult && (
                <Badge variant="strong" size="sm">
                  ✓ JD Active
                </Badge>
              )
            }
          />

          {/* Tabs */}
          <div className="flex items-center gap-2 border-b border-brand-line pb-3">
            <button
              type="button"
              onClick={() => setActiveTab("paste")}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "paste"
                  ? "bg-brand-forest text-brand-ivory"
                  : "bg-brand-sage-soft/30 text-brand-muted hover:text-brand-ink"
              }`}
            >
              📝 Paste Text
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("upload")}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all ${
                activeTab === "upload"
                  ? "bg-brand-forest text-brand-ivory"
                  : "bg-brand-sage-soft/30 text-brand-muted hover:text-brand-ink"
              }`}
            >
              📁 Upload File (PDF / DOCX / TXT)
            </button>
          </div>

          {/* Tab 1: Paste Text */}
          {activeTab === "paste" && (
            <div className="space-y-2">
              <textarea
                value={jdText}
                onChange={(e) => setJdText(e.target.value)}
                placeholder="Paste the job description text here (role title, requirements, preferred skills, qualifications, responsibilities)..."
                rows={8}
                className="w-full p-4 border border-brand-line rounded-2xl bg-brand-ivory/50 focus:bg-brand-paper focus:ring-2 focus:ring-brand-forest/20 focus:border-brand-forest text-sm font-mono text-brand-ink placeholder:text-brand-muted/70 transition-all outline-none leading-relaxed"
              />
              <div className="flex justify-between items-center text-xs text-brand-muted px-1">
                <span>Supports unformatted or formatted job description text</span>
                <span className="font-mono tabular-nums">{jdText.length} characters</span>
              </div>
            </div>
          )}

          {/* Tab 2: Upload File */}
          {activeTab === "upload" && (
            <div>
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
                  dragActive
                    ? "border-brand-forest bg-brand-sage-soft/40"
                    : selectedFile
                    ? "border-brand-forest bg-brand-paper"
                    : "border-brand-line hover:border-brand-forest/60 bg-brand-ivory/30"
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.docx,.txt"
                  onChange={(e) => {
                    if (e.target.files?.[0]) setSelectedFile(e.target.files[0]);
                  }}
                  className="hidden"
                />
                {selectedFile ? (
                  <div className="space-y-2">
                    <div className="text-3xl">📄</div>
                    <p className="font-serif font-bold text-brand-ink">{selectedFile.name}</p>
                    <p className="text-xs text-brand-muted">
                      {(selectedFile.size / 1024).toFixed(1)} KB — Click or drag to replace
                    </p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-3xl text-brand-muted">📥</div>
                    <p className="text-sm font-medium text-brand-ink">
                      Drop your Job Description file here, or{" "}
                      <span className="text-brand-forest font-semibold underline">browse</span>
                    </p>
                    <p className="text-xs text-brand-muted">
                      Accepts PDF, DOCX, or TXT (Max 5 MB)
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Parse Error Alert */}
          {parseError && (
            <div className="p-4 bg-band-weak/10 border border-band-weak/30 text-band-weak text-xs rounded-2xl flex items-start gap-2">
              <span className="font-bold">⚠️</span>
              <span>{parseError}</span>
            </div>
          )}

          {/* Action Button */}
          <div className="flex items-center gap-3">
            <Button
              variant="primary"
              size="md"
              onClick={handleAnalyze}
              disabled={parsing}
              loading={parsing}
            >
              <span>✨</span>
              <span>{parsing ? "Extracting Competencies..." : "Analyze Job Description"}</span>
            </Button>
          </div>
        </Card>
      </section>

      {/* ── Parsed JD Results Card ── */}
      {parsedResult && (
        <section>
          <Card padding="p-6 sm:p-8" className="space-y-6">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-brand-line gap-3">
              <div>
                <Eyebrow>SPECIFICATION EXTRACTION</Eyebrow>
                <h3 className="font-serif text-xl sm:text-2xl font-bold text-brand-ink mt-0.5">
                  {parsedResult.title || "Job Title Not Specified"}
                </h3>
              </div>
              <Button
                variant="secondary"
                size="sm"
                onClick={handleSave}
                disabled={saving}
                loading={saving}
              >
                💾 Save Skill Changes
              </Button>
            </div>

            {saveMessage && (
              <div className="p-3.5 bg-band-strong/15 border border-band-strong/30 text-band-strong text-xs rounded-2xl">
                {saveMessage}
              </div>
            )}

            {/* Quick Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-brand-ivory/50 p-4 rounded-2xl border border-brand-line">
                <Eyebrow>Experience Required</Eyebrow>
                <div className="font-serif text-lg font-bold text-brand-ink mt-1">
                  {parsedResult.min_experience_years !== null
                    ? `${parsedResult.min_experience_years}${
                        parsedResult.max_experience_years
                          ? ` – ${parsedResult.max_experience_years}`
                          : "+"
                      } years`
                    : "Not specified"}
                </div>
              </div>

              <div className="bg-brand-ivory/50 p-4 rounded-2xl border border-brand-line">
                <Eyebrow>Degree Requirement</Eyebrow>
                <div className="font-serif text-lg font-bold text-brand-ink mt-1 capitalize">
                  {parsedResult.min_required_level
                    ? `${parsedResult.min_required_level} degree`
                    : "Any degree"}
                  {parsedResult.preferred_level && (
                    <span className="text-xs text-brand-muted font-normal block mt-0.5">
                      Preferred: {parsedResult.preferred_level}
                    </span>
                  )}
                </div>
              </div>

              <div className="bg-brand-ivory/50 p-4 rounded-2xl border border-brand-line">
                <Eyebrow>Skill Breakdown</Eyebrow>
                <div className="font-serif text-lg font-bold text-brand-ink mt-1">
                  <span className="text-brand-forest">{editRequired.length}</span> required ·{" "}
                  <span className="text-brand-sage">{editPreferred.length}</span> preferred
                </div>
              </div>
            </div>

            {/* Skills Management */}
            <div className="space-y-6 pt-2">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-serif text-sm font-bold text-brand-ink">
                    Required Skills{" "}
                    <span className="font-sans text-xs font-normal text-brand-muted">
                      (⇄ moves to preferred, × removes)
                    </span>
                  </h4>
                  <span className="font-mono text-xs font-semibold text-brand-forest">
                    {editRequired.length} skills
                  </span>
                </div>
                <SkillChips
                  skills={editRequired}
                  label="Required"
                  color="green"
                  onRemove={(skill) =>
                    setEditRequired((prev) => prev.filter((s) => s !== skill))
                  }
                  onToggleCategory={(skill) => {
                    setEditRequired((prev) => prev.filter((s) => s !== skill));
                    setEditPreferred((prev) => [...prev, skill]);
                  }}
                  onAdd={(skill) => {
                    if (!editRequired.includes(skill)) {
                      setEditRequired((prev) => [...prev, skill]);
                    }
                  }}
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <h4 className="font-serif text-sm font-bold text-brand-ink">
                    Preferred / Nice-to-Have Skills{" "}
                    <span className="font-sans text-xs font-normal text-brand-muted">
                      (⇄ moves to required, × removes)
                    </span>
                  </h4>
                  <span className="font-mono text-xs font-semibold text-brand-sage">
                    {editPreferred.length} skills
                  </span>
                </div>
                <SkillChips
                  skills={editPreferred}
                  label="Preferred"
                  color="yellow"
                  onRemove={(skill) =>
                    setEditPreferred((prev) => prev.filter((s) => s !== skill))
                  }
                  onToggleCategory={(skill) => {
                    setEditPreferred((prev) => prev.filter((s) => s !== skill));
                    setEditRequired((prev) => [...prev, skill]);
                  }}
                  onAdd={(skill) => {
                    if (!editPreferred.includes(skill)) {
                      setEditPreferred((prev) => [...prev, skill]);
                    }
                  }}
                />
              </div>
            </div>

            {/* Responsibilities */}
            {parsedResult.responsibilities?.length > 0 && (
              <div className="pt-2 space-y-2">
                <h4 className="font-serif text-sm font-bold text-brand-ink">
                  Key Responsibilities ({parsedResult.responsibilities.length})
                </h4>
                <ul className="list-disc list-inside space-y-1.5 text-xs text-brand-muted bg-brand-ivory/50 p-4 rounded-2xl border border-brand-line">
                  {parsedResult.responsibilities.slice(0, 5).map((resp, i) => (
                    <li key={i} className="line-clamp-2">
                      {resp}
                    </li>
                  ))}
                  {parsedResult.responsibilities.length > 5 && (
                    <li className="text-[11px] text-brand-muted font-semibold list-none mt-1">
                      + {parsedResult.responsibilities.length - 5} more responsibilities
                    </li>
                  )}
                </ul>
              </div>
            )}
          </Card>
        </section>
      )}

      {/* ════════════════════════════════════════════════════════
          STEP 2: BATCH RESUME UPLOAD & CANDIDATE INTAKE
         ════════════════════════════════════════════════════════ */}
      <section>
        <Card padding="p-6 sm:p-8" className="space-y-6">
          <SectionHeader
            eyebrow="MODULE 02"
            title="Step 2: Upload Resumes (Batch Intake)"
            subtitle="Ingest batches of candidate resumes (PDF or DOCX) to extract contact details, experience, skills, and education."
            actions={
              candidates.length > 0 && (
                <div className="flex items-center gap-2">
                  <Badge variant="neutral" size="sm">
                    {candidates.length} in database
                  </Badge>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleClearAllCandidates}
                    className="text-band-weak hover:text-band-weak"
                  >
                    Clear All
                  </Button>
                </div>
              )
            }
          />

          {/* Multi-file Dropzone */}
          <div
            onDragEnter={handleResumeDrag}
            onDragLeave={handleResumeDrag}
            onDragOver={handleResumeDrag}
            onDrop={handleResumeDrop}
            onClick={() => resumeInputRef.current?.click()}
            className={`border-2 border-dashed rounded-3xl p-8 sm:p-12 text-center cursor-pointer transition-all ${
              resumeDragActive
                ? "border-brand-forest bg-brand-sage-soft/40"
                : resumeFiles.length > 0
                ? "border-brand-forest bg-brand-paper"
                : "border-brand-line hover:border-brand-forest/60 bg-brand-ivory/30"
            }`}
          >
            <input
              ref={resumeInputRef}
              type="file"
              multiple
              accept=".pdf,.docx"
              onChange={handleResumeFileSelect}
              className="hidden"
            />
            <div className="text-3xl text-brand-sage mb-2">📁</div>
            <p className="font-serif text-sm font-bold text-brand-ink">
              Drag &amp; drop multiple resumes here, or{" "}
              <span className="text-brand-forest underline">browse files</span>
            </p>
            <p className="text-xs text-brand-muted mt-1">
              Accepts PDF and DOCX · Batch of 10+ recommended · Up to 50 files (max 5 MB each)
            </p>
          </div>

          {/* Selected Files Staging List */}
          {resumeFiles.length > 0 && (
            <div className="bg-brand-ivory/60 border border-brand-line rounded-2xl p-5 space-y-3">
              <div className="flex items-center justify-between">
                <span className="font-serif text-sm font-bold text-brand-ink">
                  Selected Files ({resumeFiles.length})
                  {resumeFiles.length < 10 && (
                    <span className="text-band-partial font-normal text-xs ml-2">
                      (10+ resumes recommended for diverse shortlists)
                    </span>
                  )}
                </span>
                <button
                  type="button"
                  onClick={() => setResumeFiles([])}
                  className="text-xs text-brand-muted hover:text-brand-ink"
                >
                  Clear selection
                </button>
              </div>

              <div className="max-h-44 overflow-y-auto space-y-1.5 pr-2">
                {resumeFiles.map((f, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between bg-brand-paper px-3.5 py-2 rounded-xl border border-brand-line text-xs"
                  >
                    <div className="flex items-center gap-2 truncate">
                      <span>📄</span>
                      <span className="font-medium text-brand-ink truncate">{f.name}</span>
                      <span className="text-brand-muted font-mono">({(f.size / 1024).toFixed(0)} KB)</span>
                    </div>
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        removeSelectedFile(idx);
                      }}
                      className="text-brand-muted hover:text-band-weak font-bold text-sm ml-2 px-1"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>

              {/* Upload Progress Bar */}
              {uploading && (
                <div className="pt-2">
                  <ScoreBar
                    value={uploadProgress}
                    label="Uploading &amp; Parsing Resumes..."
                    height="h-2.5"
                  />
                </div>
              )}

              {/* Upload Button */}
              <div className="pt-2 flex justify-end">
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleUploadResumes}
                  disabled={uploading}
                  loading={uploading}
                >
                  🚀 Parse &amp; Ingest {resumeFiles.length} Resumes
                </Button>
              </div>
            </div>
          )}

          {/* Batch Upload Summary Results */}
          {batchResults && (
            <div className="p-5 bg-brand-ivory/70 border border-brand-line rounded-2xl space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-serif text-sm font-bold text-brand-ink">
                  Batch Upload Summary:{" "}
                  <span className="text-band-strong">{batchResults.successful} succeeded</span>
                  {batchResults.failed > 0 && (
                    <span className="text-band-weak ml-2">
                      ({batchResults.failed} failed)
                    </span>
                  )}
                </h4>
                <button
                  type="button"
                  onClick={() => setBatchResults(null)}
                  className="text-xs text-brand-muted hover:text-brand-ink"
                >
                  Dismiss
                </button>
              </div>
              <div className="max-h-48 overflow-y-auto space-y-1.5 pr-2">
                {batchResults.results.map((res, i) => (
                  <div
                    key={i}
                    className={`flex items-center justify-between px-3.5 py-2 rounded-xl text-xs border ${
                      res.status === "parsed"
                        ? "bg-brand-paper border-band-strong/30 text-brand-ink"
                        : "bg-band-weak/10 border-band-weak/30 text-band-weak"
                    }`}
                  >
                    <span className="font-medium truncate max-w-xs">{res.filename}</span>
                    <div className="flex items-center gap-2">
                      {res.name && <span className="text-brand-muted font-medium">({res.name})</span>}
                      <Badge
                        variant={res.status === "parsed" ? "strong" : "weak"}
                        size="sm"
                      >
                        {res.status}
                      </Badge>
                      {res.error && (
                        <span className="text-band-weak italic truncate max-w-sm" title={res.error}>
                          {res.error}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Parsed Candidates Table ── */}
          <div className="pt-2 space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="font-serif text-base font-bold text-brand-ink">
                Parsed Candidates Repository ({candidates.length})
              </h3>
              <Button
                variant="ghost"
                size="sm"
                onClick={loadCandidates}
              >
                🔄 Refresh List
              </Button>
            </div>

            {candidatesError && (
              <div className="p-3.5 bg-band-weak/10 text-band-weak border border-band-weak/30 text-xs rounded-2xl">
                {candidatesError}
              </div>
            )}

            {candidatesLoading ? (
              <div className="p-12 text-center text-sm text-brand-muted">
                <div className="w-6 h-6 border-2 border-brand-forest border-t-transparent rounded-full animate-spin mx-auto mb-2" />
                <span>Loading parsed candidate repository...</span>
              </div>
            ) : candidates.length === 0 ? (
              <EmptyState
                title="No resumes parsed yet"
                description="Upload resumes using the dropzone above or seed the benchmark dataset with the 1-click demo."
              />
            ) : (
              <div className="overflow-x-auto border border-brand-line rounded-2xl bg-brand-paper shadow-soft">
                <table className="w-full text-left text-xs text-brand-ink">
                  <thead className="bg-brand-ivory/60 text-brand-muted uppercase font-sans font-semibold text-[11px] tracking-wider border-b border-brand-line">
                    <tr>
                      <th className="py-3.5 px-4">Candidate</th>
                      <th className="py-3.5 px-4">Contact</th>
                      <th className="py-3.5 px-4">Experience</th>
                      <th className="py-3.5 px-4">Top Skills Detected</th>
                      <th className="py-3.5 px-4">Integrity</th>
                      <th className="py-3.5 px-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-brand-line">
                    {candidates.map((c) => (
                      <tr key={c.id} className="hover:bg-brand-sage-soft/15 transition-colors">
                        <td className="py-3.5 px-4">
                          <div className="font-serif font-bold text-brand-ink">
                            {c.name || "Unknown Candidate"}
                          </div>
                          <div className="text-[11px] text-brand-muted truncate max-w-xs font-mono">
                            {c.filename}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="font-mono text-brand-ink/90">{c.email || <span className="text-brand-muted">—</span>}</div>
                          <div className="text-[11px] text-brand-muted font-mono">{c.phone || ""}</div>
                        </td>
                        <td className="py-3.5 px-4">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-mono tabular-nums font-medium bg-brand-ivory border border-brand-line text-brand-ink">
                            {c.total_experience_years > 0
                              ? `${c.total_experience_years.toFixed(1)} yrs`
                              : "Fresher / 0 yrs"}
                          </span>
                        </td>
                        <td className="py-3.5 px-4">
                          <div className="flex flex-wrap gap-1 max-w-md">
                            {c.top_skills && c.top_skills.length > 0 ? (
                              <>
                                {c.top_skills.map((skill, si) => (
                                  <Chip key={si} variant="extra" size="sm">
                                    {skill}
                                  </Chip>
                                ))}
                                {c.skills_count > c.top_skills.length && (
                                  <span className="text-[10px] font-mono text-brand-muted py-0.5 px-1 font-semibold">
                                    +{c.skills_count - c.top_skills.length}
                                  </span>
                                )}
                              </>
                            ) : (
                              <span className="text-brand-muted italic text-[11px]">None detected</span>
                            )}
                          </div>
                        </td>
                        <td className="py-3.5 px-4">
                          {c.warnings_count > 0 ? (
                            <Badge variant="partial" size="sm" dot={false}>
                              ⚠️ {c.warnings_count} warn
                            </Badge>
                          ) : (
                            <span className="text-band-strong font-semibold text-[11px] uppercase tracking-wide">
                              ✓ Clean
                            </span>
                          )}
                        </td>
                        <td className="py-3.5 px-4 text-right">
                          <button
                            type="button"
                            onClick={() => handleDeleteCandidate(c.id)}
                            disabled={deletingId === c.id}
                            className="text-brand-muted hover:text-band-weak p-1.5 rounded-lg hover:bg-brand-sage-soft/30 transition-colors"
                            title="Delete candidate"
                            aria-label={`Delete ${c.name || 'candidate'}`}
                          >
                            {deletingId === c.id ? "..." : "🗑️"}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* ── Callout for Deterministic AI Matching Execution ── */}
          <div className="mt-8 p-6 rounded-3xl bg-brand-paper border-2 border-brand-forest/30 shadow-soft flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <h4 className="font-serif text-lg font-bold text-brand-ink">
                Ready for Multi-Factor Ranking?
              </h4>
              <p className="text-xs text-brand-muted">
                {!(jdId || activeJD?.id)
                  ? "Step 1: Please analyze or select an active Job Description above."
                  : candidates.length === 0
                  ? "Step 2: Please upload at least one candidate resume."
                  : `Evaluate ${candidates.length} candidate${candidates.length > 1 ? "s" : ""} with skills (40%), semantics (25%), experience (20%), degrees (10%), and titles (5%).`}
              </p>
              {matchError && (
                <p className="text-xs text-band-weak font-medium mt-1">
                  ⚠️ {matchError}
                </p>
              )}
            </div>
            <Button
              variant="primary"
              size="lg"
              onClick={async () => {
                const targetJdId = jdId || activeJD?.id;
                if (!targetJdId) {
                  setMatchError("Please select or parse a Job Description first.");
                  return;
                }
                if (candidates.length === 0) {
                  setMatchError("Please upload at least one candidate resume.");
                  return;
                }
                setMatching(true);
                setMatchError(null);
                try {
                  const runRes = await runMatch(targetJdId);
                  navigate(`/dashboard?run=${runRes.id}`);
                } catch (err) {
                  const msg = err.response?.data?.detail || "Failed to execute AI matching.";
                  setMatchError(msg);
                } finally {
                  setMatching(false);
                }
              }}
              disabled={!(jdId || activeJD?.id) || candidates.length === 0 || matching}
              loading={matching}
            >
              🚀 Run Multi-Factor Match
            </Button>
          </div>
        </Card>
      </section>
    </div>
  );
}
