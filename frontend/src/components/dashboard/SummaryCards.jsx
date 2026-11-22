import React from "react";

export default function SummaryCards({
  bandCounts = {},
  totalCount = 0,
  averageScore = null,
  topCandidate = null,
  selectedBand = null,
  onSelectBand,
}) {
  const bands = [
    {
      id: "strong",
      label: "Strong Match",
      sublabel: "Score ≥ 80%",
      count: bandCounts.strong || 0,
      bgColor: "bg-emerald-950/30 hover:bg-emerald-950/50",
      activeBorder: "border-emerald-500 ring-2 ring-emerald-500/30",
      defaultBorder: "border-emerald-900/40",
      textColor: "text-emerald-400",
      accentBg: "bg-emerald-500/20 text-emerald-300",
    },
    {
      id: "good",
      label: "Good Match",
      sublabel: "Score 65–79%",
      count: bandCounts.good || 0,
      bgColor: "bg-teal-950/30 hover:bg-teal-950/50",
      activeBorder: "border-teal-500 ring-2 ring-teal-500/30",
      defaultBorder: "border-teal-900/40",
      textColor: "text-teal-400",
      accentBg: "bg-teal-500/20 text-teal-300",
    },
    {
      id: "partial",
      label: "Partial Match",
      sublabel: "Score 50–64%",
      count: bandCounts.partial || 0,
      bgColor: "bg-amber-950/30 hover:bg-amber-950/50",
      activeBorder: "border-amber-500 ring-2 ring-amber-500/30",
      defaultBorder: "border-amber-900/40",
      textColor: "text-amber-400",
      accentBg: "bg-amber-500/20 text-amber-300",
    },
    {
      id: "weak",
      label: "Weak Match",
      sublabel: "Score < 50%",
      count: bandCounts.weak || 0,
      bgColor: "bg-rose-950/30 hover:bg-rose-950/50",
      activeBorder: "border-rose-500 ring-2 ring-rose-500/30",
      defaultBorder: "border-rose-900/40",
      textColor: "text-rose-400",
      accentBg: "bg-rose-500/20 text-rose-300",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 mb-6">
      {/* 4 Interactive Band Cards */}
      {bands.map((b) => {
        const isSelected = selectedBand === b.id;
        return (
          <button
            key={b.id}
            onClick={() => onSelectBand(isSelected ? null : b.id)}
            className={`text-left p-4 rounded-xl border transition-all cursor-pointer relative ${b.bgColor} ${
              isSelected ? b.activeBorder : b.defaultBorder
            }`}
          >
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-300">{b.label}</span>
              {isSelected && (
                <span className="text-[10px] uppercase font-bold px-1.5 py-0.5 rounded bg-white text-slate-900">
                  Active
                </span>
              )}
            </div>
            <div className="flex items-baseline gap-2">
              <span className={`text-2xl font-black ${b.textColor}`}>{b.count}</span>
              <span className="text-[11px] text-slate-400">
                ({totalCount > 0 ? Math.round((b.count / totalCount) * 100) : 0}%)
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-1">{b.sublabel}</p>
          </button>
        );
      })}

      {/* Total Candidates */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
        <span className="text-xs font-semibold text-slate-400">Total Pool</span>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl font-black text-white">{totalCount}</span>
          <span className="text-xs text-slate-400">resumes</span>
        </div>
        <p className="text-[10px] text-slate-400 mt-1">All parsed applicants</p>
      </div>

      {/* Average Score */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60">
        <span className="text-xs font-semibold text-slate-400">Avg Score</span>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-2xl font-black text-indigo-400">
            {averageScore !== null ? `${averageScore.toFixed(1)}%` : "—"}
          </span>
        </div>
        <p className="text-[10px] text-slate-400 mt-1">Weighted cohort mean</p>
      </div>

      {/* Top Candidate */}
      <div className="p-4 rounded-xl border border-slate-800 bg-slate-900/60 col-span-2 md:col-span-2 lg:col-span-1">
        <span className="text-xs font-semibold text-slate-400">Top Candidate</span>
        <div className="mt-1 truncate">
          <p className="text-sm font-bold text-white truncate" title={topCandidate?.name || "None"}>
            {topCandidate?.name || "—"}
          </p>
          <p className="text-xs text-emerald-400 font-semibold mt-0.5">
            {topCandidate?.final_score ? `${topCandidate.final_score.toFixed(1)}% match` : "—"}
          </p>
        </div>
      </div>
    </div>
  );
}
