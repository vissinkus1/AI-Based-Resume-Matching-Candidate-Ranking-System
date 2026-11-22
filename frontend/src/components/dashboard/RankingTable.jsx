import React from "react";
import { useNavigate } from "react-router-dom";

export default function RankingTable({
  results = [],
  runId,
  loading = false,
  sortBy = "rank",
  order = "asc",
  onSortChange,
  onResetFilters,
}) {
  const navigate = useNavigate();

  const handleRowClick = (candidateId) => {
    navigate(`/candidate/${candidateId}?run=${runId}`);
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) {
      return (
        <span className="text-slate-600 ml-1 text-[10px]">▲▼</span>
      );
    }
    return order === "asc" ? (
      <span className="text-indigo-400 ml-1 text-[11px]">▲</span>
    ) : (
      <span className="text-indigo-400 ml-1 text-[11px]">▼</span>
    );
  };

  const handleHeaderSort = (field) => {
    if (sortBy === field) {
      onSortChange(field, order === "asc" ? "desc" : "asc");
    } else {
      onSortChange(field, field === "score" || field === "experience" ? "desc" : "asc");
    }
  };

  const getBandBadge = (band) => {
    const b = (band || "").toLowerCase();
    switch (b) {
      case "strong":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/15 text-emerald-400 border border-emerald-500/30 whitespace-nowrap">
            Strong
          </span>
        );
      case "good":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-teal-500/15 text-teal-400 border border-teal-500/30 whitespace-nowrap">
            Good
          </span>
        );
      case "partial":
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30 whitespace-nowrap">
            Partial
          </span>
        );
      case "weak":
      default:
        return (
          <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/15 text-rose-400 border border-rose-500/30 whitespace-nowrap">
            Weak
          </span>
        );
    }
  };

  const getProgressBarColor = (band) => {
    const b = (band || "").toLowerCase();
    switch (b) {
      case "strong":
        return "bg-emerald-500";
      case "good":
        return "bg-teal-500";
      case "partial":
        return "bg-amber-500";
      case "weak":
      default:
        return "bg-rose-500";
    }
  };

  // Loading Skeletons
  if (loading) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl p-6 space-y-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="animate-pulse flex items-center justify-between gap-4 py-3 border-b border-slate-800/60 last:border-0">
            <div className="flex items-center gap-3 w-1/4">
              <div className="w-8 h-8 rounded-full bg-slate-800" />
              <div className="space-y-1.5 flex-1">
                <div className="h-4 bg-slate-800 rounded w-3/4" />
                <div className="h-3 bg-slate-800/60 rounded w-1/2" />
              </div>
            </div>
            <div className="h-4 bg-slate-800 rounded w-20" />
            <div className="h-3 bg-slate-800 rounded w-32" />
            <div className="h-6 bg-slate-800 rounded w-48" />
            <div className="h-5 bg-slate-800 rounded w-16" />
          </div>
        ))}
      </div>
    );
  }

  // Empty State
  if (!results || results.length === 0) {
    return (
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-12 text-center shadow-xl">
        <div className="w-14 h-14 mx-auto rounded-full bg-slate-800 flex items-center justify-center text-2xl text-slate-400 mb-3">
          🔍
        </div>
        <h3 className="text-lg font-bold text-white mb-1">No Matching Candidates Found</h3>
        <p className="text-sm text-slate-400 max-w-md mx-auto mb-5">
          No candidates matched your search criteria or filter constraints. Try adjusting the score threshold, experience, or band.
        </p>
        {onResetFilters && (
          <button
            onClick={onResetFilters}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition shadow"
          >
            Reset All Filters
          </button>
        )}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* ── Desktop & Tablet View (Wide Table) ── */}
      <div className="hidden md:block bg-slate-900 border border-slate-800 rounded-2xl overflow-hidden shadow-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-950/80 text-slate-400 text-xs uppercase tracking-wider border-b border-slate-800 select-none">
              <tr>
                {/* 1. Candidate */}
                <th
                  onClick={() => handleHeaderSort("name")}
                  className="py-3.5 px-4 font-semibold cursor-pointer hover:text-white transition"
                >
                  Candidate {getSortIcon("name")}
                </th>

                {/* 2. Experience */}
                <th
                  onClick={() => handleHeaderSort("experience")}
                  className="py-3.5 px-4 font-semibold cursor-pointer hover:text-white transition"
                >
                  Experience {getSortIcon("experience")}
                </th>

                {/* 3. Match % */}
                <th
                  onClick={() => handleHeaderSort("score")}
                  className="py-3.5 px-4 font-semibold cursor-pointer hover:text-white transition min-w-[150px]"
                >
                  Match % {getSortIcon("score")}
                </th>

                {/* 4. Matched Skills */}
                <th className="py-3.5 px-4 font-semibold">
                  Matched Skills
                </th>

                {/* 5. Rank */}
                <th
                  onClick={() => handleHeaderSort("rank")}
                  className="py-3.5 px-3 font-semibold cursor-pointer hover:text-white transition text-center"
                >
                  Rank {getSortIcon("rank")}
                </th>

                {/* 6. Band */}
                <th className="py-3.5 px-3 font-semibold text-center">
                  Band
                </th>

                {/* 7. Missing Required */}
                <th className="py-3.5 px-3 font-semibold text-center">
                  Missing Req.
                </th>

                {/* 8. Knockout */}
                <th className="py-3.5 px-3 font-semibold text-center">
                  Knockout
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-slate-800/80">
              {results.map((row) => {
                const totalExp = row.total_experience_years || 0;
                const relExp = row.relevant_experience_years !== undefined ? row.relevant_experience_years : totalExp;
                const topSkills = row.matched_top_skills || [];
                const missingCount = row.missing_required_count || 0;
                const missingSkills = row.missing_required_skills || [];

                return (
                  <tr
                    key={row.candidate_id}
                    onClick={() => handleRowClick(row.candidate_id)}
                    className="hover:bg-slate-800/50 cursor-pointer transition-colors group"
                  >
                    {/* 1. Candidate: Name + email */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-slate-800 text-indigo-400 font-bold text-xs flex items-center justify-center border border-slate-700 group-hover:border-indigo-500/50 transition">
                          {(row.name || "?").charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="font-bold text-white text-sm group-hover:text-indigo-400 transition truncate">
                            {row.name || "Unknown Candidate"}
                          </p>
                          <p className="text-xs text-slate-400 truncate">
                            {row.email || "No email"}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* 2. Experience */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="font-semibold text-white">
                        {totalExp.toFixed(1)} yrs
                      </span>{" "}
                      <span className="text-xs text-indigo-400 font-medium">
                        ({relExp.toFixed(1)} rel)
                      </span>
                    </td>

                    {/* 3. Match % Progress Bar */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-2.5">
                        <span className="font-black text-sm text-white min-w-[42px]">
                          {row.final_score.toFixed(1)}%
                        </span>
                        <div className="w-24 bg-slate-800 rounded-full h-2 overflow-hidden flex-1">
                          <div
                            className={`h-full rounded-full ${getProgressBarColor(row.band)}`}
                            style={{ width: `${Math.min(100, Math.max(0, row.final_score))}%` }}
                          />
                        </div>
                      </div>
                    </td>

                    {/* 4. Matched Skills (up to 5 chips + +N more badge) */}
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap items-center gap-1 max-w-[280px]">
                        {topSkills.slice(0, 5).map((sk) => (
                          <span
                            key={sk}
                            className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                          >
                            {sk}
                          </span>
                        ))}
                        {topSkills.length > 5 && (
                          <span
                            className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700 cursor-help"
                            title={topSkills.slice(5).join(", ")}
                          >
                            +{topSkills.length - 5} more
                          </span>
                        )}
                        {topSkills.length === 0 && (
                          <span className="text-xs text-slate-500 italic">None matched</span>
                        )}
                      </div>
                    </td>

                    {/* 5. Rank */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      <span className="font-black text-sm text-slate-300">
                        #{row.original_rank || row.rank}
                      </span>
                    </td>

                    {/* 6. Band badge */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      {getBandBadge(row.band)}
                    </td>

                    {/* 7. Missing Required */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      {missingCount > 0 ? (
                        <span
                          className="px-2 py-0.5 rounded text-xs font-semibold bg-rose-500/10 text-rose-400 border border-rose-500/20 cursor-help"
                          title={missingSkills.length > 0 ? `Missing: ${missingSkills.join(", ")}` : "Missing required skills"}
                        >
                          {missingCount} missing
                        </span>
                      ) : (
                        <span className="text-xs text-emerald-400 font-bold">✓ All met</span>
                      )}
                    </td>

                    {/* 8. Knockout */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      {row.is_knockout ? (
                        <span
                          className="px-2 py-0.5 rounded text-xs font-bold bg-red-950 text-red-400 border border-red-700 cursor-help animate-pulse"
                          title={row.knockout_reason || "Candidate disqualified by safety rules"}
                        >
                          ⚠️ Knockout
                        </span>
                      ) : (
                        <span className="text-slate-600 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Mobile View (< md breakpoint cards) ── */}
      <div className="md:hidden space-y-3">
        {results.map((row) => {
          const totalExp = row.total_experience_years || 0;
          const relExp = row.relevant_experience_years !== undefined ? row.relevant_experience_years : totalExp;
          const topSkills = row.matched_top_skills || [];

          return (
            <div
              key={row.candidate_id}
              onClick={() => handleRowClick(row.candidate_id)}
              className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg hover:border-indigo-500/50 transition cursor-pointer space-y-3"
            >
              {/* Header: Rank + Name + Band */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-black text-sm text-slate-400">
                    #{row.original_rank || row.rank}
                  </span>
                  <div>
                    <h4 className="font-bold text-white text-base leading-tight">
                      {row.name || "Unknown Candidate"}
                    </h4>
                    <p className="text-xs text-slate-400">{row.email}</p>
                  </div>
                </div>
                {getBandBadge(row.band)}
              </div>

              {/* Score & Experience Bar */}
              <div className="bg-slate-950 p-3 rounded-xl border border-slate-800/80 space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-400">Overall Match:</span>
                  <span className="font-black text-base text-white">
                    {row.final_score.toFixed(1)}%
                  </span>
                </div>
                <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div
                    className={`h-full rounded-full ${getProgressBarColor(row.band)}`}
                    style={{ width: `${Math.min(100, Math.max(0, row.final_score))}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-slate-300 pt-1">
                  <span>Experience:</span>
                  <span className="font-semibold">
                    {totalExp.toFixed(1)} yrs <span className="text-indigo-400">({relExp.toFixed(1)} rel)</span>
                  </span>
                </div>
              </div>

              {/* Matched Skills */}
              {topSkills.length > 0 && (
                <div>
                  <p className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">
                    Top Matched Skills:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {topSkills.slice(0, 5).map((sk) => (
                      <span
                        key={sk}
                        className="px-2 py-0.5 rounded text-[11px] font-medium bg-emerald-500/10 text-emerald-300 border border-emerald-500/20"
                      >
                        {sk}
                      </span>
                    ))}
                    {topSkills.length > 5 && (
                      <span className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-slate-800 text-slate-300 border border-slate-700">
                        +{topSkills.length - 5}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Knockout banner if any */}
              {row.is_knockout && (
                <div className="bg-red-950/60 border border-red-700/60 rounded-lg p-2 text-xs text-red-300 flex items-center gap-1.5">
                  <span>⚠️</span>
                  <span>Knockout: {row.knockout_reason || "Disqualified"}</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
