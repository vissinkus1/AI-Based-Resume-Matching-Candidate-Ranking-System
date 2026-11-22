import React from "react";
import { useNavigate } from "react-router-dom";

export default function CandidateTopBar({
  rank = 1,
  totalCandidates = 1,
  prevCandidateId = null,
  nextCandidateId = null,
  runId = null,
}) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (runId) {
      navigate(`/dashboard?run=${runId}`);
    } else {
      navigate("/dashboard");
    }
  };

  const handleNav = (targetId) => {
    if (targetId) {
      navigate(`/candidate/${targetId}${runId ? `?run=${runId}` : ""}`);
    }
  };

  return (
    <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4 mb-6 bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg">
      {/* Back Button */}
      <button
        onClick={handleBack}
        className="flex items-center gap-2 text-sm font-semibold text-slate-300 hover:text-white transition group cursor-pointer"
      >
        <span className="w-8 h-8 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400 group-hover:bg-indigo-600 group-hover:text-white transition">
          ←
        </span>
        <span>Back to Ranking Dashboard</span>
      </button>

      {/* Center / Right: Rank badge & Prev/Next navigation */}
      <div className="flex items-center justify-between sm:justify-end gap-3">
        <span className="px-3 py-1 rounded-full text-xs font-bold bg-indigo-500/15 text-indigo-400 border border-indigo-500/30">
          Rank #{rank} of {totalCandidates} Candidates
        </span>

        <div className="flex items-center gap-1.5">
          <button
            onClick={() => handleNav(prevCandidateId)}
            disabled={!prevCandidateId}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-200 border border-slate-700 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
            title={prevCandidateId ? "Previous candidate" : "First candidate in ranking"}
          >
            <span>‹</span> Prev
          </button>
          <button
            onClick={() => handleNav(nextCandidateId)}
            disabled={!nextCandidateId}
            className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-800 hover:bg-slate-700 active:bg-slate-600 text-slate-200 border border-slate-700 transition disabled:opacity-40 disabled:cursor-not-allowed flex items-center gap-1"
            title={nextCandidateId ? "Next candidate" : "Last candidate in ranking"}
          >
            Next <span>›</span>
          </button>
        </div>
      </div>
    </div>
  );
}
