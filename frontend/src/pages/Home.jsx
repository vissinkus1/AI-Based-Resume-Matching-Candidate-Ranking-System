/*
 * pages/Home.jsx — Upload page (JD + Resumes).
 *
 * Step 1: Job Description input
 *   - Tabs: "Paste Text" / "Upload File"
 *   - Analyze JD button → calls POST /api/jd/parse
 *   - Results panel: title, skills (editable chips), experience,
 *     qualifications, responsibilities, keywords
 *   - Save Changes → PUT /api/jd/{id}
 *
 * Step 2: Resume upload (placeholder — Phase 2)
 */

import { useState, useEffect, useRef } from "react";
import { parseJDText, parseJDFile, updateJD } from "../api/jd";
import { useJD } from "../context/JDContext";
import SkillChips from "../components/SkillChips";
import API from "../api/client";

function Home() {
  // Backend health status
  const [healthStatus, setHealthStatus] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);

  // JD input state
  const [activeTab, setActiveTab] = useState("paste"); // "paste" | "upload"
  const [jdText, setJdText] = useState("");
  const [selectedFile, setSelectedFile] = useState(null);
  const [dragActive, setDragActive] = useState(false);
  const fileInputRef = useRef(null);

  // Parse state
  const [parsing, setParsing] = useState(false);
  const [parseError, setParseError] = useState(null);
  const [parsedResult, setParsedResult] = useState(null);
  const [jdId, setJdId] = useState(null);

  // Editable parsed fields (local state for editing before save)
  const [editRequired, setEditRequired] = useState([]);
  const [editPreferred, setEditPreferred] = useState([]);
  const [saving, setSaving] = useState(false);
  const [saveMessage, setSaveMessage] = useState(null);

  // Global JD context
  const { setActiveJD } = useJD();

  // ── Health check on mount ──
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
  }, []);

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

      // Set in global context for other pages
      setActiveJD({ id: result.id, title: result.title, parsed: result.parsed });
    } catch (err) {
      const msg =
        err.response?.data?.detail || err.message || "Failed to parse JD.";
      setParseError(msg);
    } finally {
      setParsing(false);
    }
  };

  // ── Save Changes ──
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
      setActiveJD({ id: jdId, title: updated.title, parsed: updated.parsed });
      setSaveMessage("Changes saved successfully!");
    } catch (err) {
      setSaveMessage("Failed to save: " + (err.response?.data?.detail || err.message));
    } finally {
      setSaving(false);
    }
  };

  // ── Skill editing helpers ──
  const removeRequired = (skill) =>
    setEditRequired((prev) => prev.filter((s) => s !== skill));
  const removePreferred = (skill) =>
    setEditPreferred((prev) => prev.filter((s) => s !== skill));
  const addRequired = (skill) =>
    setEditRequired((prev) => [...prev, skill]);
  const addPreferred = (skill) =>
    setEditPreferred((prev) => [...prev, skill]);
  const moveToPreferred = (skill) => {
    removeRequired(skill);
    setEditPreferred((prev) => [...prev, skill]);
  };
  const moveToRequired = (skill) => {
    removePreferred(skill);
    setEditRequired((prev) => [...prev, skill]);
  };

  // ── Drag & drop handlers ──
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") setDragActive(true);
    else if (e.type === "dragleave") setDragActive(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.[0]) {
      setSelectedFile(e.dataTransfer.files[0]);
    }
  };

  // Check if skills were edited
  const skillsEdited =
    parsedResult &&
    (JSON.stringify(editRequired) !== JSON.stringify(parsedResult.required_skills) ||
     JSON.stringify(editPreferred) !== JSON.stringify(parsedResult.preferred_skills));

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold text-gray-800">
        Upload Job Description & Resumes
      </h1>

      {/* ── Backend status (compact) ── */}
      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-500">Backend:</span>
        {healthLoading ? (
          <span className="text-gray-400 animate-pulse">checking…</span>
        ) : healthStatus?.status === "healthy" ? (
          <span className="text-green-600 font-medium">✅ Connected</span>
        ) : (
          <span className="text-red-600 font-medium">❌ Unreachable</span>
        )}
      </div>

      {/* ════════════════════════════════════════════════════════
          STEP 1: JOB DESCRIPTION
         ════════════════════════════════════════════════════════ */}
      <section className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Step 1: Job Description
        </h2>

        {/* Tabs */}
        <div className="flex border-b border-gray-200 mb-4">
          <TabButton
            active={activeTab === "paste"}
            onClick={() => setActiveTab("paste")}
            label="📝 Paste Text"
          />
          <TabButton
            active={activeTab === "upload"}
            onClick={() => setActiveTab("upload")}
            label="📎 Upload File"
          />
        </div>

        {/* Tab content */}
        {activeTab === "paste" ? (
          <textarea
            value={jdText}
            onChange={(e) => setJdText(e.target.value)}
            placeholder="Paste the job description text here…"
            rows={10}
            className="w-full px-4 py-3 border border-gray-300 rounded-md resize-y
                       focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 outline-none
                       text-sm font-mono"
          />
        ) : (
          <div
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`border-2 border-dashed rounded-lg p-10 text-center cursor-pointer
                        transition-colors ${
                          dragActive
                            ? "border-indigo-500 bg-indigo-50"
                            : "border-gray-300 hover:border-indigo-400 hover:bg-gray-50"
                        }`}
          >
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
              className="hidden"
            />
            {selectedFile ? (
              <div>
                <p className="text-indigo-600 font-medium">{selectedFile.name}</p>
                <p className="text-gray-400 text-sm mt-1">
                  {(selectedFile.size / 1024).toFixed(1)} KB — Click or drop to change
                </p>
              </div>
            ) : (
              <div>
                <p className="text-gray-500">
                  Drag & drop a file here, or click to browse
                </p>
                <p className="text-gray-400 text-xs mt-1">
                  Supported: PDF, DOCX, TXT (max 5 MB)
                </p>
              </div>
            )}
          </div>
        )}

        {/* Analyze button */}
        <div className="mt-4 flex items-center gap-4">
          <button
            onClick={handleAnalyze}
            disabled={parsing}
            className="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-md
                       hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed
                       transition-colors"
          >
            {parsing ? (
              <span className="flex items-center gap-2">
                <Spinner /> Analyzing…
              </span>
            ) : (
              "🔍 Analyze JD"
            )}
          </button>
          {parseError && (
            <p className="text-red-600 text-sm">{parseError}</p>
          )}
        </div>
      </section>

      {/* ════════════════════════════════════════════════════════
          PARSED RESULTS
         ════════════════════════════════════════════════════════ */}
      {parsedResult && (
        <section className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-700">
              Parsed Results
            </h2>
            <span className="text-sm text-gray-400">JD #{jdId}</span>
          </div>

          {/* Title */}
          {parsedResult.title && (
            <div className="mb-4">
              <h3 className="text-lg font-bold text-indigo-700">
                {parsedResult.title}
              </h3>
            </div>
          )}

          {/* Two-column layout for skills */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <SkillChips
              skills={editRequired}
              onRemove={removeRequired}
              onAdd={addRequired}
              onToggle={moveToPreferred}
              color="green"
              label="Required Skills"
              toggleLabel="Move to Preferred"
            />
            <SkillChips
              skills={editPreferred}
              onRemove={removePreferred}
              onAdd={addPreferred}
              onToggle={moveToRequired}
              color="yellow"
              label="Preferred Skills"
              toggleLabel="Move to Required"
            />
          </div>

          {/* Save changes button (shows only when skills were edited) */}
          {skillsEdited && (
            <div className="mb-6 flex items-center gap-3">
              <button
                onClick={handleSave}
                disabled={saving}
                className="px-5 py-2 bg-green-600 text-white rounded-md font-medium
                           hover:bg-green-700 disabled:opacity-50"
              >
                {saving ? "Saving…" : "💾 Save Changes"}
              </button>
              {saveMessage && (
                <span className={`text-sm ${
                  saveMessage.includes("success") ? "text-green-600" : "text-red-600"
                }`}>
                  {saveMessage}
                </span>
              )}
            </div>
          )}

          {/* Experience */}
          <InfoRow label="Experience Required">
            {parsedResult.min_experience_years != null ? (
              <span>
                {parsedResult.min_experience_years}
                {parsedResult.max_experience_years != null
                  ? `–${parsedResult.max_experience_years}`
                  : "+"}{" "}
                years
              </span>
            ) : (
              <span className="text-gray-400 italic">Not specified</span>
            )}
          </InfoRow>

          {/* Qualifications */}
          <InfoRow label="Qualifications">
            {parsedResult.qualifications?.length > 0 ? (
              <ul className="list-disc list-inside">
                {parsedResult.qualifications.map((q, i) => (
                  <li key={i}>
                    <span className="font-medium capitalize">{q.level}</span>
                    {" — "}
                    <span className="text-gray-600">{q.raw_phrase}</span>
                  </li>
                ))}
              </ul>
            ) : (
              <span className="text-gray-400 italic">Not detected</span>
            )}
          </InfoRow>

          {/* Responsibilities */}
          <InfoRow label="Responsibilities">
            {parsedResult.responsibilities?.length > 0 ? (
              <ul className="list-disc list-inside space-y-1 text-sm text-gray-700">
                {parsedResult.responsibilities.map((r, i) => (
                  <li key={i}>{r}</li>
                ))}
              </ul>
            ) : (
              <span className="text-gray-400 italic">Not detected</span>
            )}
          </InfoRow>

          {/* Keywords */}
          <InfoRow label="Keywords">
            <div className="flex flex-wrap gap-2">
              {parsedResult.keywords?.length > 0 ? (
                parsedResult.keywords.map((kw, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-blue-50 text-blue-700 rounded text-xs border border-blue-200"
                  >
                    {kw}
                  </span>
                ))
              ) : (
                <span className="text-gray-400 italic">None</span>
              )}
            </div>
          </InfoRow>
        </section>
      )}

      {/* ════════════════════════════════════════════════════════
          STEP 2: RESUME UPLOAD (placeholder — Phase 2)
         ════════════════════════════════════════════════════════ */}
      <section className="bg-white rounded-lg shadow p-6 opacity-60">
        <h2 className="text-xl font-semibold text-gray-700 mb-4">
          Step 2: Upload Resumes
        </h2>
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
          <p className="text-gray-400">
            Upload a batch of candidate resumes (PDF/DOCX).
          </p>
          <p className="text-gray-300 text-xs mt-2 italic">
            Coming in Phase 2
          </p>
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

function InfoRow({ label, children }) {
  return (
    <div className="mb-4">
      <h4 className="text-sm font-semibold text-gray-600 mb-1">{label}</h4>
      <div className="text-gray-800">{children}</div>
    </div>
  );
}

function Spinner() {
  return (
    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
      <circle
        className="opacity-25"
        cx="12" cy="12" r="10"
        stroke="currentColor" strokeWidth="4"
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
