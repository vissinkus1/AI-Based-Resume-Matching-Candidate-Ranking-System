import React from "react";

export default function SkillsSection({
  skillsBreakdown = {},
}) {
  const matchedRequired = skillsBreakdown.matched_required || [];
  const matchedPreferred = skillsBreakdown.matched_preferred || [];
  const partial = skillsBreakdown.partial || [];
  const missingRequired = skillsBreakdown.missing_required || [];
  const missingPreferred = skillsBreakdown.missing_preferred || [];
  const extraSkills = skillsBreakdown.extra_skills || [];

  const requiredCount = skillsBreakdown.required_count || (matchedRequired.length + missingRequired.length);
  const matchedReqCount = skillsBreakdown.matched_required_count || matchedRequired.length;
  const coveragePct = requiredCount > 0 ? Math.round((matchedReqCount / requiredCount) * 100) : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      {/* Section Header with Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🎯</span> Skill Coverage & Match Matrix
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Detailed breakdown of matched, partial, missing, and extra domain skills.
          </p>
        </div>

        {/* Coverage summary badges */}
        <div className="flex items-center gap-3">
          <div className="bg-slate-950 px-3.5 py-1.5 rounded-xl border border-slate-800 text-center">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Required Met
            </span>
            <span className="text-base font-black text-emerald-400">
              {matchedReqCount} of {requiredCount}
            </span>
          </div>

          <div className="bg-slate-950 px-3.5 py-1.5 rounded-xl border border-slate-800 text-center">
            <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
              Coverage %
            </span>
            <span className="text-base font-black text-indigo-400">
              {coveragePct}%
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* 1. Matched Required Skills (Green) */}
        <div>
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
            <span>✓</span> Matched Required Skills ({matchedRequired.length})
          </h4>
          {matchedRequired.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {matchedRequired.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                const matchType = typeof item === "object" ? item.match_type || item.type || "exact" : "exact";
                const evidence = typeof item === "object" ? item.evidence : null;

                return (
                  <div
                    key={idx}
                    className="group relative inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/25 hover:border-emerald-400 transition cursor-help shadow-sm"
                  >
                    <span>{name}</span>
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.2 rounded bg-emerald-500/20 text-emerald-200">
                      {matchType}
                    </span>

                    {/* Tooltip on hover */}
                    {evidence && (
                      <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 w-64 p-2 bg-slate-950 text-slate-200 text-[11px] rounded-lg border border-slate-700 shadow-xl opacity-0 group-hover:opacity-100 transition pointer-events-none z-20">
                        <p className="font-semibold text-emerald-400 mb-0.5">Resume Evidence:</p>
                        <p className="italic leading-snug">"{evidence}"</p>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-rose-400 italic">No required skills were matched.</p>
          )}
        </div>

        {/* 2. Partial / Inferred Skills (Amber) */}
        {partial.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
              <span>≈</span> Partial / Parent-Child Credits ({partial.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {partial.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                const reason = typeof item === "object" ? item.reason || item.matched_via : "partial";
                const credit = typeof item === "object" && item.credit !== undefined ? `${Math.round(item.credit * 100)}%` : "Partial";

                return (
                  <div
                    key={idx}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-amber-500/10 text-amber-300 border border-amber-500/25 shadow-sm"
                    title={reason ? `Matched via: ${reason}` : undefined}
                  >
                    <span>{name}</span>
                    <span className="text-[10px] uppercase font-bold px-1.5 py-0.2 rounded bg-amber-500/20 text-amber-200">
                      {credit}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* 3. Missing Required Skills (Red) */}
        <div>
          <h4 className="text-xs font-bold text-rose-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
            <span>✗</span> Missing Required Skills ({missingRequired.length})
          </h4>
          {missingRequired.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {missingRequired.map((name, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-rose-500/10 text-rose-300 border border-rose-500/25"
                >
                  {name}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-emerald-400 font-medium">✓ All required skills matched!</p>
          )}
        </div>

        {/* 4. Matched Preferred Skills (Light Green) */}
        {matchedPreferred.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-teal-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
              <span>★</span> Matched Preferred / Bonus Skills ({matchedPreferred.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {matchedPreferred.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                return (
                  <span
                    key={idx}
                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-teal-500/10 text-teal-300 border border-teal-500/25"
                  >
                    {name}
                  </span>
                );
              })}
            </div>
          </div>
        )}

        {/* 5. Missing Preferred Skills (Gray) */}
        {missingPreferred.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
              <span>○</span> Missing Preferred Skills ({missingPreferred.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {missingPreferred.map((name, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1.5 rounded-xl text-xs font-medium bg-slate-800 text-slate-400 border border-slate-700"
                >
                  {name}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 6. Extra Relevant Domain Skills (Blue) */}
        {extraSkills.length > 0 && (
          <div>
            <h4 className="text-xs font-bold text-blue-400 uppercase tracking-wider mb-2.5 flex items-center gap-2">
              <span>✦</span> Additional Domain Skills Found ({extraSkills.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {extraSkills.map((sk, idx) => {
                const name = typeof sk === "string" ? sk : sk.name || sk.skill;
                return (
                  <span
                    key={idx}
                    className="px-3 py-1 rounded-xl text-xs font-medium bg-blue-500/10 text-blue-300 border border-blue-500/25"
                  >
                    {name}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
