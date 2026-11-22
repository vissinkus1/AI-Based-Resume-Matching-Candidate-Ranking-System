import React from "react";

export default function NarrativeExplanationCard({
  narrativeSummary = "",
  strengths = [],
  gaps = [],
  reasons = [],
}) {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      <div className="mb-4">
        <h3 className="text-lg font-bold text-white flex items-center gap-2">
          <span>📝</span> Executive Narrative & Hiring Recommendation
        </h3>
        <p className="text-xs text-slate-400 mt-0.5">
          Auditable, human-readable rationale generated from quantitative factor evaluations.
        </p>
      </div>

      {/* Narrative Summary Paragraph */}
      {narrativeSummary && (
        <div className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 mb-6">
          <p className="text-sm text-slate-200 leading-relaxed font-normal">
            {narrativeSummary}
          </p>
        </div>
      )}

      {/* Strengths & Gaps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Strengths */}
        <div className="bg-emerald-950/20 border border-emerald-900/40 rounded-xl p-4">
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span>✓</span> Key Candidate Strengths ({strengths.length})
          </h4>
          {strengths.length > 0 ? (
            <ul className="space-y-2">
              {strengths.map((str, idx) => (
                <li key={idx} className="text-xs text-slate-200 flex items-start gap-2">
                  <span className="text-emerald-400 mt-0.5 font-bold">✓</span>
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-slate-500 italic">No standout strengths detected.</p>
          )}
        </div>

        {/* Gaps */}
        <div className="bg-rose-950/20 border border-rose-900/40 rounded-xl p-4">
          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-3 flex items-center gap-1.5">
            <span>⚠️</span> Missing Requirements & Gaps ({gaps.length})
          </h4>
          {gaps.length > 0 ? (
            <ul className="space-y-2">
              {gaps.map((gap, idx) => (
                <li key={idx} className="text-xs text-slate-200 flex items-start gap-2">
                  <span className="text-rose-400 mt-0.5 font-bold">✗</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-emerald-400 font-medium">
              ✓ No critical gaps found against required criteria!
            </p>
          )}
        </div>
      </div>

      {/* Factor Reasons Breakdown */}
      {reasons && reasons.length > 0 && (
        <div>
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
            Factor-by-Factor Evaluation Rationale
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {reasons.map((r, idx) => {
              const factorName = r.factor || "Factor";
              const verdict = r.verdict || "Evaluated";
              const isPositive =
                verdict.toLowerCase().includes("exceeds") ||
                verdict.toLowerCase().includes("strong") ||
                verdict.toLowerCase().includes("full") ||
                verdict.toLowerCase().includes("pass") ||
                verdict.toLowerCase().includes("high");
              const isWarning =
                verdict.toLowerCase().includes("gap") ||
                verdict.toLowerCase().includes("low") ||
                verdict.toLowerCase().includes("fail") ||
                verdict.toLowerCase().includes("missing");

              return (
                <div
                  key={idx}
                  className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex flex-col justify-between"
                >
                  <div className="flex items-center justify-between gap-2 mb-1.5">
                    <span className="font-semibold text-xs text-slate-300 capitalize">
                      {factorName}
                    </span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        isPositive
                          ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                          : isWarning
                          ? "bg-rose-500/15 text-rose-400 border border-rose-500/30"
                          : "bg-amber-500/15 text-amber-400 border border-amber-500/30"
                      }`}
                    >
                      {verdict}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-snug">
                    {r.detail || r.reason || "Evaluated against position benchmarks."}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
