/*
 * pages/Home.jsx — Upload & Intake Page (JD + Resumes).
 *
 * Step 1: Job Description input
 *   - Tabs: "Paste Text" / "Upload File"
 *   - Analyze JD button → calls POST /api/jd/parse
 *   - Results panel: title, skills (editable chips), experience,
 *     qualifications, responsibilities, keywords
 *   - Save Changes → PUT /api/jd/{id}
 *
 * Step 2: Batch Resume Upload & Parsed Candidates Table
 *   - Multi-file drag-and-drop (PDF/DOCX, up to 50 files)
 *   - Batch upload progress bar & per-file status badges
 *   - Parsed candidates table: Name, Email, Experience, Top Skills, Warnings, Delete
 *   - "Run AI Matching" callout (ready for Phase 3)
 */

import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { parseJDText, parseJDFile, updateJD } from "../api/jd";
import {
  uploadResumes,
  listCandidates,
  deleteCandidate,
  clearAllCandidates,
} from "../api/resumes";
import { runMatch } from "../api/match";
import { useJD } from "../context/JDContext";
import SkillChips from "../components/SkillChips";
import API from "../api/client";

function Home() {
  const navigate = useNavigate();

  // Backend health status
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // Matching trigger state
  const [matching, setMatching] = useState(false);
  const [matchError, setMatchError] = useState(null);

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
      setResumeFiles([]); // Clear selection upon batch complete
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

  return (
    <div className="space-y-8 pb-12">
      {/* ── System Health Bar ── */}
      <div className="flex items-center justify-between bg-white px-4 py-2.5 rounded-lg shadow-sm text-xs text-gray-500">
        <div className="flex items-center space-x-2">
          <span className="font-semibold text-gray-700">System Status:</span>
          {healthLoading ? (
            <span className="text-gray-400">checking backend...</span>
          ) : healthStatus?.api && healthStatus?.database ? (
            <span className="inline-flex items-center text-emerald-600 font-medium">
              <span className="h-2 w-2 rounded-full bg-emerald-500 mr-1.5 animate-pulse" />
              Backend &amp; DB Connected
            </span>
          ) : (
            <span className="inline-flex items-center text-rose-600 font-medium">
              <span className="h-2 w-2 rounded-full bg-rose-500 mr-1.5" />
              Backend Offline
            </span>
          )}
        </div>
        {activeJD && (
          <div className="inline-flex items-center bg-indigo-50 text-indigo-700 px-2.5 py-1 rounded-md font-medium">
            <span className="mr-1.5">🎯</span> Active JD:{" "}
            <span className="font-bold ml-1">{activeJD.title || "Untitled Role"}</span>
          </div>
        )}
      </div>

      {/* ════════════════════════════════════════════════════════
          STEP 1: JOB DESCRIPTION
         ════════════════════════════════════════════════════════ */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
              Module 1
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-0.5">
              Step 1: Job Description
            </h2>
          </div>
          {parsedResult && (
            <span className="bg-emerald-100 text-emerald-800 text-xs px-2.5 py-1 rounded-full font-semibold">
              ✓ JD Parsed &amp; Active
            </span>
          )}
        </div>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-5">
          <TabButton
            active={activeTab === "paste"}
            onClick={() => setActiveTab("paste")}
            label="📝 Paste Text"
          />
          <TabButton
            active={activeTab === "upload"}
            onClick={() => setActiveTab("upload")}
            label="📁 Upload File (PDF / DOCX / TXT)"
          />
        </div>

        {/* Tab 1: Paste Text */}
        {activeTab === "paste" && (
          <div>
            <textarea
              value={jdText}
              onChange={(e) => setJdText(e.target.value)}
              placeholder="Paste the full job description here (title, requirements, nice-to-haves, qualifications, responsibilities)..."
              rows={8}
              className="w-full p-3.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm font-mono text-gray-800 leading-relaxed"
            />
            <div className="flex justify-between items-center text-xs text-gray-400 mt-1.5">
              <span>Supports any formatted or unformatted JD text</span>
              <span>{jdText.length} characters</span>
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
              className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
                dragActive
                  ? "border-indigo-500 bg-indigo-50"
                  : selectedFile
                  ? "border-emerald-400 bg-emerald-50/40"
                  : "border-gray-300 hover:border-gray-400 bg-gray-50/50"
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
                <div>
                  <div className="text-3xl mb-2">📄</div>
                  <p className="font-semibold text-gray-800">{selectedFile.name}</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(selectedFile.size / 1024).toFixed(1)} KB — Click or drag to replace
                  </p>
                </div>
              ) : (
                <div>
                  <div className="text-3xl text-gray-400 mb-2">📥</div>
                  <p className="text-sm font-medium text-gray-700">
                    Drop your Job Description file here, or{" "}
                    <span className="text-indigo-600 font-semibold underline">browse</span>
                  </p>
                  <p className="text-xs text-gray-400 mt-1">
                    Accepts PDF, DOCX, or TXT (Max 5 MB)
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Parse Error Alert */}
        {parseError && (
          <div className="mt-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-lg flex items-start space-x-2">
            <span className="text-rose-500 font-bold">⚠️</span>
            <span>{parseError}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="mt-5 flex items-center space-x-4">
          <button
            onClick={handleAnalyze}
            disabled={parsing}
            className={`px-5 py-2.5 rounded-lg text-white font-medium text-sm flex items-center space-x-2 transition-all ${
              parsing
                ? "bg-indigo-400 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-700 shadow-sm hover:shadow"
            }`}
          >
            {parsing ? (
              <>
                <Spinner />
                <span>Analyzing JD via NLP...</span>
              </>
            ) : (
              <>
                <span>✨ Analyze Job Description</span>
              </>
            )}
          </button>
        </div>
      </section>

      {/* ── Parsed JD Results Card ── */}
      {parsedResult && (
        <section className="bg-white rounded-xl shadow-sm border border-emerald-100 p-6 space-y-6">
          <div className="flex items-center justify-between border-b border-gray-100 pb-4">
            <div>
              <span className="text-xs font-bold uppercase tracking-wider text-emerald-600">
                Extraction Results
              </span>
              <h3 className="text-xl font-bold text-gray-900 mt-0.5">
                {parsedResult.title || "Job Title Not Specified"}
              </h3>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${
                  saving
                    ? "bg-gray-200 text-gray-500"
                    : "bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm"
                }`}
              >
                {saving ? "Saving..." : "💾 Save Changes"}
              </button>
            </div>
          </div>

          {saveMessage && (
            <div className="p-3 bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm rounded-lg">
              {saveMessage}
            </div>
          )}

          {/* Quick Stats Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
              <div className="text-xs text-gray-500 uppercase font-semibold">Experience Required</div>
              <div className="text-lg font-bold text-slate-800 mt-1">
                {parsedResult.min_experience_years !== null
                  ? `${parsedResult.min_experience_years}${
                      parsedResult.max_experience_years
                        ? ` – ${parsedResult.max_experience_years}`
                        : "+"
                    } years`
                  : "Not specified"}
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
              <div className="text-xs text-gray-500 uppercase font-semibold">Degree Requirement</div>
              <div className="text-lg font-bold text-slate-800 mt-1 capitalize">
                {parsedResult.min_required_level
                  ? `${parsedResult.min_required_level} degree`
                  : "Any degree"}
                {parsedResult.preferred_level && (
                  <span className="text-xs text-gray-500 font-normal block">
                    Preferred: {parsedResult.preferred_level}
                  </span>
                )}
              </div>
            </div>

            <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
              <div className="text-xs text-gray-500 uppercase font-semibold">Skill Breakdown</div>
              <div className="text-lg font-bold text-slate-800 mt-1">
                <span className="text-indigo-600">{editRequired.length}</span> required ·{" "}
                <span className="text-purple-600">{editPreferred.length}</span> preferred
              </div>
            </div>
          </div>

          {/* Skills Management */}
          <div className="space-y-4 pt-2">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-bold text-gray-800">
                  Required Skills{" "}
                  <span className="text-xs font-normal text-gray-500">
                    (Click to move to preferred, × to remove)
                  </span>
                </h4>
                <span className="text-xs text-indigo-600 font-medium">
                  {editRequired.length} skills
                </span>
              </div>
              <SkillChips
                skills={editRequired}
                badgeColor="indigo"
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

            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-bold text-gray-800">
                  Preferred / Nice-to-Have Skills{" "}
                  <span className="text-xs font-normal text-gray-500">
                    (Click to move to required, × to remove)
                  </span>
                </h4>
                <span className="text-xs text-purple-600 font-medium">
                  {editPreferred.length} skills
                </span>
              </div>
              <SkillChips
                skills={editPreferred}
                badgeColor="purple"
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
            <div className="pt-2">
              <h4 className="text-sm font-bold text-gray-800 mb-2">
                Key Responsibilities ({parsedResult.responsibilities.length})
              </h4>
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700 bg-gray-50 p-3.5 rounded-lg border border-gray-100">
                {parsedResult.responsibilities.slice(0, 5).map((resp, i) => (
                  <li key={i} className="line-clamp-2">
                    {resp}
                  </li>
                ))}
                {parsedResult.responsibilities.length > 5 && (
                  <li className="text-xs text-gray-500 font-semibold list-none mt-1">
                    + {parsedResult.responsibilities.length - 5} more responsibilities
                  </li>
                )}
              </ul>
            </div>
          )}
        </section>
      )}

      {/* ════════════════════════════════════════════════════════
          STEP 2: BATCH RESUME UPLOAD & CANDIDATE INTAKE
         ════════════════════════════════════════════════════════ */}
      <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-6">
        <div className="flex items-center justify-between">
          <div>
            <span className="text-xs font-bold uppercase tracking-wider text-indigo-600">
              Module 2
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-0.5">
              Step 2: Upload Resumes (Batch Intake)
            </h2>
            <p className="text-xs text-gray-500 mt-1">
              Upload batches of candidate resumes (PDF or DOCX). Extract contact info,
              experience, skills, and education history.
            </p>
          </div>
          {candidates.length > 0 && (
            <div className="flex items-center space-x-2">
              <span className="bg-blue-100 text-blue-800 text-xs px-2.5 py-1 rounded-full font-semibold">
                {candidates.length} candidates in database
              </span>
              <button
                onClick={handleClearAllCandidates}
                className="text-xs text-rose-600 hover:text-rose-800 font-medium px-2 py-1 rounded hover:bg-rose-50 transition-colors"
                title="Delete all parsed candidates"
              >
                Clear All
              </button>
            </div>
          )}
        </div>

        {/* Multi-file Dropzone */}
        <div
          onDragEnter={handleResumeDrag}
          onDragLeave={handleResumeDrag}
          onDragOver={handleResumeDrag}
          onDrop={handleResumeDrop}
          onClick={() => resumeInputRef.current?.click()}
          className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all ${
            resumeDragActive
              ? "border-indigo-500 bg-indigo-50"
              : resumeFiles.length > 0
              ? "border-blue-400 bg-blue-50/30"
              : "border-gray-300 hover:border-gray-400 bg-gray-50/50"
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
          <div className="text-3xl text-indigo-500 mb-2">📁</div>
          <p className="text-sm font-semibold text-gray-800">
            Drag &amp; drop multiple resumes here, or{" "}
            <span className="text-indigo-600 underline">browse files</span>
          </p>
          <p className="text-xs text-gray-400 mt-1">
            Accepts PDF and DOCX · Batch of 10+ recommended · Up to 50 files (max 5 MB each)
          </p>
        </div>

        {/* Selected Files Staging List */}
        {resumeFiles.length > 0 && (
          <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-semibold text-gray-800">
                Selected Files ({resumeFiles.length})
                {resumeFiles.length < 10 && (
                  <span className="text-amber-600 font-normal text-xs ml-2">
                    (Tip: 10+ resumes recommended for comprehensive ranking)
                  </span>
                )}
              </span>
              <button
                onClick={() => setResumeFiles([])}
                className="text-xs text-gray-500 hover:text-gray-700"
              >
                Clear selection
              </button>
            </div>

            <div className="max-h-40 overflow-y-auto space-y-1.5 pr-2">
              {resumeFiles.map((f, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between bg-white px-3 py-1.5 rounded border border-gray-200 text-xs"
                >
                  <div className="flex items-center space-x-2 truncate">
                    <span>📄</span>
                    <span className="font-medium text-gray-800 truncate">{f.name}</span>
                    <span className="text-gray-400">({(f.size / 1024).toFixed(0)} KB)</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      removeSelectedFile(idx);
                    }}
                    className="text-gray-400 hover:text-rose-500 text-sm font-bold ml-2 px-1"
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>

            {/* Upload Progress Bar */}
            {uploading && (
              <div className="mt-4 space-y-1.5">
                <div className="flex justify-between text-xs text-indigo-700 font-medium">
                  <span>Uploading &amp; Parsing Resumes...</span>
                  <span>{uploadProgress}%</span>
                </div>
                <div className="w-full bg-indigo-100 rounded-full h-2.5 overflow-hidden">
                  <div
                    className="bg-indigo-600 h-2.5 rounded-full transition-all duration-300"
                    style={{ width: `${uploadProgress}%` }}
                  />
                </div>
              </div>
            )}

            {/* Upload Button */}
            <div className="mt-4 flex items-center justify-end space-x-3">
              <button
                onClick={handleUploadResumes}
                disabled={uploading}
                className={`px-5 py-2 rounded-lg text-white font-medium text-sm flex items-center space-x-2 transition-all ${
                  uploading
                    ? "bg-indigo-400 cursor-not-allowed"
                    : "bg-indigo-600 hover:bg-indigo-700 shadow-sm"
                }`}
              >
                {uploading ? (
                  <>
                    <Spinner />
                    <span>Processing Batch...</span>
                  </>
                ) : (
                  <>
                    <span>🚀 Parse &amp; Ingest {resumeFiles.length} Resumes</span>
                  </>
                )}
              </button>
            </div>
          </div>
        )}

        {/* Batch Upload Summary Results */}
        {batchResults && (
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-sm font-bold text-gray-800">
                Batch Upload Summary:{" "}
                <span className="text-emerald-600">{batchResults.successful} succeeded</span>
                {batchResults.failed > 0 && (
                  <span className="text-rose-600 ml-2">
                    ({batchResults.failed} failed)
                  </span>
                )}
              </h4>
              <button
                onClick={() => setBatchResults(null)}
                className="text-xs text-gray-400 hover:text-gray-600"
              >
                Dismiss
              </button>
            </div>
            <div className="max-h-48 overflow-y-auto space-y-1.5 pr-2">
              {batchResults.results.map((res, i) => (
                <div
                  key={i}
                  className={`flex items-center justify-between px-3 py-1.5 rounded text-xs border ${
                    res.status === "parsed"
                      ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                      : "bg-rose-50 border-rose-200 text-rose-800"
                  }`}
                >
                  <span className="font-medium truncate max-w-xs">{res.filename}</span>
                  <div className="flex items-center space-x-2">
                    {res.name && <span className="text-gray-600">({res.name})</span>}
                    <span
                      className={`font-semibold uppercase text-[10px] px-1.5 py-0.5 rounded ${
                        res.status === "parsed"
                          ? "bg-emerald-200 text-emerald-900"
                          : "bg-rose-200 text-rose-900"
                      }`}
                    >
                      {res.status}
                    </span>
                    {res.error && (
                      <span className="text-rose-600 italic truncate max-w-sm" title={res.error}>
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
        <div className="pt-2">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-bold text-gray-800">
              Parsed Candidates ({candidates.length})
            </h3>
            <button
              onClick={loadCandidates}
              className="text-xs text-indigo-600 hover:text-indigo-800 font-medium"
            >
              🔄 Refresh List
            </button>
          </div>

          {candidatesError && (
            <div className="p-3 bg-rose-50 text-rose-700 text-xs rounded-lg mb-3">
              {candidatesError}
            </div>
          )}

          {candidatesLoading ? (
            <div className="p-8 text-center text-sm text-gray-500">
              <Spinner />
              <span className="ml-2">Loading candidate database...</span>
            </div>
          ) : candidates.length === 0 ? (
            <div className="p-8 text-center border-2 border-dashed border-gray-200 rounded-xl">
              <div className="text-2xl text-gray-300 mb-1">👥</div>
              <p className="text-sm font-medium text-gray-600">No resumes parsed yet</p>
              <p className="text-xs text-gray-400 mt-1">
                Upload resumes above or use sample resumes to begin.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto border border-gray-200 rounded-xl shadow-sm">
              <table className="w-full text-left text-xs text-gray-600">
                <thead className="bg-gray-50 text-gray-700 uppercase font-semibold text-[11px] border-b border-gray-200">
                  <tr>
                    <th className="py-3 px-4">Candidate</th>
                    <th className="py-3 px-4">Contact</th>
                    <th className="py-3 px-4">Experience</th>
                    <th className="py-3 px-4">Skills Extracted</th>
                    <th className="py-3 px-4">Warnings</th>
                    <th className="py-3 px-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100 bg-white">
                  {candidates.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                      <td className="py-3 px-4 font-medium text-gray-900">
                        <div className="font-semibold text-gray-900">
                          {c.name || "Unknown Candidate"}
                        </div>
                        <div className="text-[11px] text-gray-400 truncate max-w-xs">
                          {c.filename}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div>{c.email || <span className="text-gray-400">—</span>}</div>
                        <div className="text-[11px] text-gray-400">{c.phone || ""}</div>
                      </td>
                      <td className="py-3 px-4">
                        <span className="inline-flex items-center px-2 py-0.5 rounded-full font-medium bg-blue-50 text-blue-700">
                          {c.total_experience_years > 0
                            ? `${c.total_experience_years.toFixed(1)} yrs`
                            : "Fresher / 0 yrs"}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex flex-wrap gap-1 max-w-md">
                          {c.top_skills && c.top_skills.length > 0 ? (
                            <>
                              {c.top_skills.map((skill, si) => (
                                <span
                                  key={si}
                                  className="bg-gray-100 text-gray-700 px-1.5 py-0.5 rounded text-[10px]"
                                >
                                  {skill}
                                </span>
                              ))}
                              {c.skills_count > c.top_skills.length && (
                                <span className="bg-indigo-50 text-indigo-700 font-medium px-1.5 py-0.5 rounded text-[10px]">
                                  +{c.skills_count - c.top_skills.length}
                                </span>
                              )}
                            </>
                          ) : (
                            <span className="text-gray-400 italic">None detected</span>
                          )}
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        {c.warnings_count > 0 ? (
                          <span
                            className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-100 text-amber-800"
                            title={`${c.warnings_count} parsing warning(s)`}
                          >
                            ⚠️ {c.warnings_count}
                          </span>
                        ) : (
                          <span className="text-emerald-600 font-semibold text-[11px]">✓ Clean</span>
                        )}
                      </td>
                      <td className="py-3 px-4 text-right">
                        <button
                          onClick={() => handleDeleteCandidate(c.id)}
                          disabled={deletingId === c.id}
                          className="text-rose-500 hover:text-rose-700 font-medium p-1 hover:bg-rose-50 rounded transition-colors"
                          title="Delete candidate"
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

        {/* ── Callout for AI Matching Execution ── */}
        <div className="mt-6 p-4 rounded-xl bg-gradient-to-r from-indigo-50 via-purple-50 to-pink-50 border border-indigo-100 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h4 className="text-sm font-bold text-gray-900">
              Ready for AI Matching &amp; Candidate Ranking?
            </h4>
            <p className="text-xs text-gray-600 mt-0.5">
              {!(jdId || activeJD?.id)
                ? "Step 1: Please analyze or select an active Job Description above."
                : candidates.length === 0
                ? "Step 2: Please upload at least one candidate resume."
                : `Ready to evaluate ${candidates.length} candidate${candidates.length > 1 ? "s" : ""} against the active JD.`}
            </p>
            {matchError && (
              <p className="text-xs text-red-600 font-medium mt-1">
                ⚠️ {matchError}
              </p>
            )}
          </div>
          <button
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
            className={`px-5 py-2.5 rounded-lg font-semibold text-xs flex items-center justify-center gap-2 transition-all shadow-sm ${
              !(jdId || activeJD?.id) || candidates.length === 0 || matching
                ? "bg-gray-300 text-gray-500 cursor-not-allowed shadow-none"
                : "bg-indigo-600 hover:bg-indigo-700 text-white cursor-pointer shadow-indigo-200"
            }`}
          >
            {matching ? (
              <>
                <Spinner />
                <span>Running Multi-Factor Ranking...</span>
              </>
            ) : (
              <span>Run AI Matching &amp; Ranking 🚀</span>
            )}
          </button>
        </div>
      </section>
    </div>
  );
}

/* ── Helper components ── */

function TabButton({ active, onClick, label }) {
  return (
    <button
      onClick={onClick}
      className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
        active
          ? "border-indigo-600 text-indigo-600"
          : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
      }`}
    >
      {label}
    </button>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
  );
}

export default Home;
