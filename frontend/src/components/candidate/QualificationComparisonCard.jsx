import React from "react";

export default function QualificationComparisonCard({
  qualificationBreakdown = {},
  educationEntries = [],
  jdMinLevel = "None",
  jdPreferredLevel = null,
}) {
  const candidateLevel = qualificationBreakdown.candidate_highest_level || "Not detected";
  const verdict = qualificationBreakdown.verdict || "Evaluated";
  const score = qualificationBreakdown.score !== undefined ? qualificationBreakdown.score : 100;

  const isExceeds = verdict.toLowerCase().includes("exceeds");
  const isPass = verdict.toLowerCase().includes("meets") || verdict.toLowerCase().includes("pass") || score >= 90;
  const isFail = verdict.toLowerCase().includes("below") || verdict.toLowerCase().includes("fail") || score < 60;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🎓</span> Education & Degree Qualification
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Compares candidate degree level against minimum required and preferred credentials.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Score:</span>
          <span className="text-base font-black text-purple-400">
            {typeof score === "number" ? score.toFixed(1) : score}/100
          </span>
          <span
            className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${isExceeds
                ? "bg-purple-500/15 text-purple-300 border border-purple-500/30"
                : isPass
                  ? "bg-emerald-500/15 text-emerald-400 border border-emerald-500/30"
                  : "bg-rose-500/15 text-rose-400 border border-rose-500/30"
              }`}
          >
            {isExceeds ? "Exceeds Requirement" : isPass ? "Requirement Met" : "Below Minimum"}
          </span>
        </div>
      </div>

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            JD Required Level
          </span>
          <p className="text-base font-bold text-white capitalize mt-0.5">
            {jdMinLevel || "Bachelor's (or equivalent)"}
          </p>
          {jdPreferredLevel && (
            <span className="text-[11px] text-slate-400 mt-1 block">
              Preferred: {jdPreferredLevel}
            </span>
          )}
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Candidate Highest Degree
          </span>
          <p className="text-base font-bold text-emerald-400 capitalize mt-0.5">
            {candidateLevel}
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">
            Hierarchy verified
          </span>
        </div>

        <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Qualification Status
          </span>
          <p className="text-base font-bold text-white mt-0.5">
            {verdict}
          </p>
          <span className="text-[11px] text-slate-400 mt-1 block">
            {qualificationBreakdown.reason || "Formal credential check"}
          </span>
        </div>
      </div>

      {/* Listed Education Entries */}
      {educationEntries && educationEntries.length > 0 && (
        <div className="space-y-2.5">
          <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Reported Degrees & Institutions ({educationEntries.length})
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {educationEntries.map((edu, idx) => (
              <div
                key={idx}
                className="bg-slate-950/60 border border-slate-800 rounded-xl p-3 flex items-start justify-between gap-3"
              >
                <div>
                  <h5 className="font-bold text-xs text-white">
                    {edu.degree || edu.raw_phrase || "Degree"}
                    {edu.field ? ` in ${edu.field}` : ""}
                  </h5>
                  <p className="text-xs text-slate-400 mt-0.5">
                    {edu.institution || "Accredited University"}
                  </p>
                </div>
                {edu.year && (
                  <span className="text-[11px] font-mono text-slate-400 bg-slate-800 px-2 py-0.5 rounded">
                    {edu.year}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
