import React, { useState } from "react";

export default function ExtractedResumeDataCard({
  rawResumeText = "",
  parseWarnings = [],
  extractedSkills = [],
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("raw"); // "raw" | "skills"

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl shadow-xl overflow-hidden mb-6">
      {/* Header toggle button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-5 flex items-center justify-between text-left hover:bg-slate-800/40 transition"
      >
        <div className="flex items-center gap-3">
          <span className="text-xl">🗂️</span>
          <div>
            <h3 className="text-sm font-bold text-white">
              Raw Extracted Resume Data & Parser Audit
            </h3>
            <p className="text-xs text-slate-400 mt-0.5">
              Inspect the exact plain-text parsed representation and parser warnings.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {parseWarnings && parseWarnings.length > 0 && (
            <span className="px-2 py-0.5 rounded text-[11px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30">
              {parseWarnings.length} Warnings
            </span>
          )}
          <span className="text-slate-400 text-sm font-mono">
            {isOpen ? "▲ Hide" : "▼ Show"}
          </span>
        </div>
      </button>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-6 border-t border-slate-800 space-y-4">
          {/* Parser Warnings Banner if any */}
          {parseWarnings && parseWarnings.length > 0 && (
            <div className="bg-amber-950/40 border border-amber-800/60 rounded-xl p-4 text-xs text-amber-200 space-y-1">
              <h4 className="font-bold text-amber-300">Parser Diagnostics:</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-300">
                {parseWarnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Sub-tabs */}
          <div className="flex items-center gap-2 border-b border-slate-800 pb-2">
            <button
              onClick={() => setActiveTab("raw")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "raw"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Raw Document Text
            </button>
            <button
              onClick={() => setActiveTab("skills")}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition ${
                activeTab === "skills"
                  ? "bg-indigo-600 text-white"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              Extracted Taxonomy Skills ({extractedSkills.length})
            </button>
          </div>

          {activeTab === "raw" && (
            <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 max-h-96 overflow-y-auto font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed select-text">
              {rawResumeText || "No raw text available."}
            </div>
          )}

          {activeTab === "skills" && (
            <div className="bg-slate-950 rounded-xl p-4 border border-slate-800 max-h-96 overflow-y-auto space-y-2">
              {extractedSkills && extractedSkills.length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {extractedSkills.map((sk, idx) => {
                    const name = typeof sk === "string" ? sk : sk.name || sk.skill;
                    const tier = typeof sk === "object" ? sk.tier : null;
                    const conf = typeof sk === "object" ? sk.confidence : null;

                    return (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg text-xs bg-slate-900 text-slate-300 border border-slate-700 flex items-center gap-1.5"
                      >
                        <strong className="text-white">{name}</strong>
                        {tier && <span className="text-[10px] text-slate-500">[{tier}]</span>}
                        {conf && <span className="text-[10px] text-indigo-400">{conf}</span>}
                      </span>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-slate-500 italic">No extracted skills.</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
