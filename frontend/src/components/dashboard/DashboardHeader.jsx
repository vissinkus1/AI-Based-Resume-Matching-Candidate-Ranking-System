import React from "react";
import { Link } from "react-router-dom";
import { getExportCsvUrl } from "../../api/match";

export default function DashboardHeader({
  run,
  onReRun,
  reRunning = false,
}) {
  if (!run) return null;

  const runDate = run.created_at
    ? new Date(run.created_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Recently";

  const exportUrl = getExportCsvUrl(run.id);

  return (
    <div className="space-y-4 mb-6">
      {/* Top Banner if Stale */}
      {run.is_stale && (
        <div className="bg-amber-500/15 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-amber-200">
          <div className="flex items-center gap-3">
            <span className="text-xl">⚠️</span>
            <div>
              <p className="font-semibold text-amber-300">
                Stale Results Warning: {run.stale_reason || "Data has changed"}
              </p>
              <p className="text-xs text-amber-300/80">
                The job description or candidate pool was modified since this run was calculated. Re-run matching to update scores.
              </p>
            </div>
          </div>
          <button
            onClick={onReRun}
            disabled={reRunning}
            className="px-4 py-2 bg-amber-500 hover:bg-amber-600 active:bg-amber-700 text-slate-950 font-semibold text-xs rounded-lg transition-all flex items-center gap-1.5 whitespace-nowrap shadow-sm disabled:opacity-50"
          >
            {reRunning ? "Re-running..." : "⚡ Re-run Now"}
          </button>
        </div>
      )}

      {/* Main Header Card */}
      <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl flex flex-col lg:flex-row lg:items-center justify-between gap-6">
        <div>
          <div className="flex items-center gap-2.5 flex-wrap mb-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Run #{run.id}
            </span>
            <span className="text-xs text-slate-400">
              Generated: {runDate}
            </span>
            <span className="text-xs text-slate-500">•</span>
            <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-slate-800 text-slate-300 border border-slate-700">
              v1.0 • all-MiniLM-L6-v2
            </span>
            {run.duration_ms && (
              <span className="text-xs text-slate-400 font-mono">
                ({run.duration_ms} ms)
              </span>
            )}
          </div>

          <h1 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight flex items-center gap-3">
            {run.jd_title || "Job Description Match"}
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Evaluated {run.candidate_count} {run.candidate_count === 1 ? "candidate" : "candidates"} across 5 explainable matching dimensions.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-3 flex-wrap">
          <a
            href={exportUrl}
            download={`match_run_${run.id}_ranking.csv`}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-200 text-sm font-medium rounded-xl border border-slate-700 transition flex items-center gap-2 shadow-sm"
          >
            <svg className="w-4 h-4 text-emerald-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Export CSV
          </a>

          <button
            onClick={onReRun}
            disabled={reRunning}
            className="px-5 py-2.5 bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white text-sm font-semibold rounded-xl transition shadow-lg shadow-indigo-500/25 flex items-center gap-2 disabled:opacity-50"
          >
            <svg
              className={`w-4 h-4 ${reRunning ? "animate-spin" : ""}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            {reRunning ? "Running..." : "Run Again"}
          </button>
        </div>
      </div>
    </div>
  );
}
