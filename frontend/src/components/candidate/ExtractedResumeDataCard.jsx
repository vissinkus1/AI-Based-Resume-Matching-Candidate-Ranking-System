import React, { useState } from "react";
import Card from "../ui/Card";
import Chip from "../ui/Chip";
import Badge from "../ui/Badge";
import Eyebrow from "../ui/Eyebrow";

export default function ExtractedResumeDataCard({
  rawResumeText = "",
  parseWarnings = [],
  extractedSkills = [],
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState("raw"); // "raw" | "skills"

  return (
    <Card padding="p-0" className="bg-brand-paper overflow-hidden mb-6">
      {/* Header toggle button */}
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-6 sm:p-8 flex items-center justify-between text-left hover:bg-brand-sage-soft/10 transition cursor-pointer"
      >
        <div className="flex items-center gap-3.5">
          <span className="text-2xl shrink-0">🗂️</span>
          <div>
            <Eyebrow>AUDIT TRAIL</Eyebrow>
            <h3 className="font-serif text-lg sm:text-xl font-bold text-brand-ink">
              Raw Extracted Resume Data &amp; Parser Diagnostics
            </h3>
            <p className="text-xs text-brand-muted mt-0.5">
              Inspect the exact plain-text parsed representation, extraction confidence, and warnings.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {parseWarnings && parseWarnings.length > 0 && (
            <Badge variant="partial" size="sm" dot={false}>
              {parseWarnings.length} Warnings
            </Badge>
          )}
          <span className="text-brand-forest text-xs font-mono font-semibold">
            {isOpen ? "▲ Hide" : "▼ Show"}
          </span>
        </div>
      </button>

      {/* Expanded Content */}
      {isOpen && (
        <div className="p-6 sm:p-8 border-t border-brand-line space-y-4 bg-brand-ivory/30">
          {/* Parser Warnings Banner if any */}
          {parseWarnings && parseWarnings.length > 0 && (
            <div className="bg-band-partial/15 border border-band-partial/40 rounded-2xl p-4 text-xs text-brand-ink space-y-1">
              <h4 className="font-serif font-bold text-sm text-brand-ink">Parser Diagnostics:</h4>
              <ul className="list-disc list-inside space-y-1 text-brand-muted">
                {parseWarnings.map((w, idx) => (
                  <li key={idx}>{w}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Sub-tabs */}
          <div className="flex items-center gap-2 border-b border-brand-line pb-3">
            <button
              type="button"
              onClick={() => setActiveTab("raw")}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition ${
                activeTab === "raw"
                  ? "bg-brand-forest text-brand-ivory"
                  : "bg-brand-sage-soft/30 text-brand-muted hover:text-brand-ink"
              }`}
            >
              Raw Document Text
            </button>
            <button
              type="button"
              onClick={() => setActiveTab("skills")}
              className={`px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition ${
                activeTab === "skills"
                  ? "bg-brand-forest text-brand-ivory"
                  : "bg-brand-sage-soft/30 text-brand-muted hover:text-brand-ink"
              }`}
            >
              Extracted Taxonomy Skills ({extractedSkills.length})
            </button>
          </div>

          {activeTab === "raw" && (
            <div className="bg-brand-paper rounded-2xl p-5 border border-brand-line max-h-96 overflow-y-auto font-mono text-xs text-brand-ink whitespace-pre-wrap leading-relaxed select-text shadow-inner">
              {rawResumeText || "No raw text available."}
            </div>
          )}

          {activeTab === "skills" && (
            <div className="bg-brand-paper rounded-2xl p-5 border border-brand-line max-h-96 overflow-y-auto space-y-2">
              {extractedSkills && extractedSkills.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {extractedSkills.map((sk, idx) => {
                    const name = typeof sk === "string" ? sk : sk.name || sk.skill;
                    const tier = typeof sk === "object" ? sk.tier : null;
                    const conf = typeof sk === "object" ? sk.confidence : null;

                    return (
                      <Chip key={idx} variant="extra">
                        <span>{name}</span>
                        {(tier || conf) && (
                          <span className="text-[10px] font-mono text-brand-muted">
                            ({tier ? tier : ""}{tier && conf ? " · " : ""}{conf ? conf : ""})
                          </span>
                        )}
                      </Chip>
                    );
                  })}
                </div>
              ) : (
                <p className="text-xs text-brand-muted italic">No taxonomy skills extracted.</p>
              )}
            </div>
          )}
        </div>
      )}
    </Card>
  );
}
