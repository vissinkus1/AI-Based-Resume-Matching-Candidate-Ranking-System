import React from "react";

export default function ExperienceComparisonCard({
  experienceBreakdown = {},
  experienceEntries = [],
  jdMinExp = null,
  jdMaxExp = null,
  totalExp = 0,
  relevantExp = 0,
}) {
  const verdict = experienceBreakdown.verdict || (relevantExp >= (jdMinExp || 0) ? "Meets Requirement" : "Below Minimum");
  const score = experienceBreakdown.score !== undefined ? experienceBreakdown.score : 0;

  // Max scale for visual comparison bar (e.g. 15 yrs or max of all + 2)
  const maxScale = Math.max(12, totalExp + 2, (jdMaxExp || jdMinExp || 5) + 3);

  const jdMinPct = jdMinExp ? (jdMinExp / maxScale) * 100 : 0;
  const jdMaxPct = jdMaxExp ? (jdMaxExp / maxScale) * 100 : jdMinPct + 15;
  const totalPct = Math.min(100, (totalExp / maxScale) * 100);
  const relPct = Math.min(100, (relevantExp / maxScale) * 100);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>💼</span> Experience Alignment & Work History
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Evaluated by relevant domain duration (70%) and total career tenure (30%).
          </p>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-slate-400">Score:</span>
          <span className="text-base font-black text-indigo-400">
            {typeof score === "number" ? score.toFixed(1) : score}/100
          </span>
          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-800 text-slate-200 border border-slate-700">
            {verdict}
          </span>
        </div>
      </div>

      {/* Visual Comparison Bar */}
      <div className="bg-slate-950 p-4 rounded-xl border border-slate-800/80 mb-6 space-y-3">
        <div className="flex items-center justify-between text-xs text-slate-400">
          <span>0 yrs</span>
          <span>Target Range vs Candidate Tenure</span>
          <span>{maxScale.toFixed(0)} yrs</span>
        </div>

        {/* Bar container */}
        <div className="relative h-6 bg-slate-900 rounded-lg overflow-hidden border border-slate-800">
          {/* JD Required Target Range Zone */}
          {jdMinExp && (
            <div
              className="absolute top-0 bottom-0 bg-indigo-500/20 border-x border-indigo-500/40 z-0"
              style={{
                left: `${jdMinPct}%`,
                width: `${Math.max(5, jdMaxPct - jdMinPct)}%`,
              }}
              title={`JD Target: ${jdMinExp}${jdMaxExp ? `–${jdMaxExp}` : "+"} years`}
            />
          )}

          {/* Candidate Total Experience */}
          <div
            className="absolute top-1 bottom-1 bg-slate-700/80 rounded opacity-60 z-10 transition-all duration-700"
            style={{ left: 0, width: `${totalPct}%` }}
            title={`Total Experience: ${totalExp.toFixed(1)} years`}
          />

          {/* Candidate Relevant Experience */}
          <div
            className="absolute top-1 bottom-1 bg-emerald-500 rounded z-20 transition-all duration-700"
            style={{ left: 0, width: `${relPct}%` }}
            title={`Relevant Experience: ${relevantExp.toFixed(1)} years`}
          />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-emerald-500 inline-block" />
              <strong className="text-white">{relevantExp.toFixed(1)} yrs</strong>{" "}
              <span className="text-slate-400">Relevant Experience</span>
            </span>

            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-slate-700 inline-block" />
              <strong className="text-white">{totalExp.toFixed(1)} yrs</strong>{" "}
              <span className="text-slate-400">Total Career</span>
            </span>

            {jdMinExp && (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-indigo-500/40 border border-indigo-400 inline-block" />
                <span className="text-indigo-300 font-medium">
                  JD Target: {jdMinExp}{jdMaxExp ? `–${jdMaxExp}` : "+"} yrs
                </span>
              </span>
            )}
          </div>

          <div className="text-xs text-slate-400 italic">
            {experienceBreakdown.rule_used || "Domain core skills & semantic relevance"}
          </div>
        </div>
      </div>

      {/* Work History Timeline */}
      <div>
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3">
          Chronological Work History ({experienceEntries.length} positions)
        </h4>

        {experienceEntries && experienceEntries.length > 0 ? (
          <div className="space-y-3">
            {experienceEntries.map((job, idx) => {
              const isRelevant = Boolean(
                job.is_relevant !== undefined ? job.is_relevant : (job.months && job.months > 0)
              );
              const skillsInJob = job.skills_in_entry || [];
              const durationYrs = job.months ? (job.months / 12).toFixed(1) : null;

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border transition-all ${
                    isRelevant
                      ? "bg-slate-950/80 border-slate-700/80"
                      : "bg-slate-950/40 border-slate-800/60 opacity-80"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h5 className="font-bold text-sm text-white">{job.title || "Position"}</h5>
                        {job.company && (
                          <span className="text-xs font-semibold text-slate-400">
                            at {job.company}
                          </span>
                        )}
                        {isRelevant ? (
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                            ✓ Relevant to this JD
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-400">
                            General Background
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="text-xs text-slate-400 whitespace-nowrap">
                      {durationYrs ? `${durationYrs} yrs` : ""}
                      {job.start_date ? ` (${job.start_date} – ${job.end_date || "Present"})` : ""}
                    </div>
                  </div>

                  {/* Bullet points / description */}
                  {job.description && (
                    <p className="text-xs text-slate-300 leading-relaxed mb-2.5 whitespace-pre-line line-clamp-3">
                      {job.description}
                    </p>
                  )}

                  {/* Skills detected in this position */}
                  {skillsInJob.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1.5 pt-1">
                      <span className="text-[10px] text-slate-500 uppercase font-bold">Skills:</span>
                      {skillsInJob.map((sk, sIdx) => (
                        <span
                          key={sIdx}
                          className="px-2 py-0.5 rounded text-[10px] font-medium bg-slate-800 text-slate-300 border border-slate-700"
                        >
                          {sk}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">No structured work entries extracted.</p>
        )}
      </div>
    </div>
  );
}
