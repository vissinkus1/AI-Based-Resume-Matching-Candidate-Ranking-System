/*
 * pages/Dashboard.jsx — AI Matching & Candidate Ranking Dashboard.
 *
 * Displays ranking verification results for a specific MatchRun (via ?run=<id>),
 * or lists recent match runs to inspect.
 */

import { useState, useEffect } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { getRun, getResults, listRuns, getExportCsvUrl } from "../api/match";

function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const runId = searchParams.get("run");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Active run state
  const [runDetail, setRunDetail] = useState(null);
  const [results, setResults] = useState([]);
  const [totalResults, setTotalResults] = useState(0);

  // Past runs list (if no run selected)
  const [pastRuns, setPastRuns] = useState([]);
  const [pastRunsLoading, setPastRunsLoading] = useState(false);

  useEffect(() => {
    if (runId) {
      loadRunData(runId);
    } else {
      loadPastRuns();
    }
  }, [runId]);

  const loadRunData = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const [detail, resultsPage] = await Promise.all([
        getRun(id),
        getResults(id, { page: 1, page_size: 100, sort_by: "rank", order: "asc" }),
      ]);
      setRunDetail(detail);
      setResults(resultsPage.items || []);
      setTotalResults(resultsPage.total || 0);
    } catch (err) {
      setError(
        err.response?.data?.detail || "Failed to load ranking results for this run."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadPastRuns = async () => {
    setPastRunsLoading(true);
    try {
      const runs = await listRuns(null, 20);
      setPastRuns(runs);
    } catch (err) {
      console.error("Failed to load past runs:", err);
    } finally {
      setPastRunsLoading(false);
    }
  };

  const getBandBadgeClass = (band) => {
    switch (band) {
      case "Strong match":
        return "bg-emerald-100 text-emerald-800 border-emerald-200";
      case "Good match":
        return "bg-blue-100 text-blue-800 border-blue-200";
      case "Partial match":
        return "bg-amber-100 text-amber-800 border-amber-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-emerald-600";
    if (score >= 65) return "text-blue-600";
    if (score >= 50) return "text-amber-600";
    return "text-rose-600";
  };

  return (
    <div className="space-y-6">
      {/* ── Top Header ── */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Candidate Ranking Dashboard
          </h1>
          <p className="text-sm text-gray-500 mt-1">
            Explainable AI evaluation, multi-factor scoring, and deterministic ranking.
          </p>
        </div>

        {runId && (
          <div className="flex items-center gap-3">
            <a
              href={getExportCsvUrl(runId)}
              target="_blank"
              rel="noreferrer"
              className="px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 text-xs font-semibold rounded-lg shadow-sm flex items-center gap-2 transition"
            >
              <span>📥 Export CSV</span>
            </a>
            <Link
              to="/"
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-lg shadow-sm transition"
            >
              + New Matching Run
            </Link>
          </div>
        )}
      </div>

      {/* ── Error Banner ── */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-xl text-sm text-red-700 flex items-center justify-between">
          <span>⚠️ {error}</span>
          <button
            onClick={() => loadRunData(runId)}
            className="underline font-semibold hover:text-red-900 ml-4"
          >
            Retry
          </button>
        </div>
      )}

      {/* ── Staleness Warning Banner ── */}
      {runDetail?.is_stale && (
        <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl text-sm text-amber-800 flex items-start gap-3">
          <span className="text-lg">⚠️</span>
          <div>
            <div className="font-bold">Job Description Modified Since This Run</div>
            <div className="text-xs text-amber-700 mt-0.5">
              The underlying Job Description or its required skills were updated after this matching run was executed.
              Scores shown here reflect the JD state at run time. Re-run matching on the Home page for fresh results.
            </div>
          </div>
        </div>
      )}

      {/* ── Run Overview Statistics ── */}
      {runDetail && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-medium">Job Target</span>
            <div className="text-sm font-bold text-gray-900 truncate mt-1" title={runDetail.jd_title || "Job Description"}>
              {runDetail.jd_title || `JD #${runDetail.jd_id}`}
            </div>
            <div className="text-[11px] text-gray-400 mt-0.5">
              Run #{runDetail.id} • {new Date(runDetail.created_at).toLocaleDateString()}
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-medium">Cohort Evaluated</span>
            <div className="text-lg font-bold text-gray-900 mt-1">
              {runDetail.candidate_count} Candidates
            </div>
            <div className="text-[11px] text-gray-400 mt-0.5">
              Computed in {runDetail.duration_ms} ms
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-medium">Average Score</span>
            <div className="text-lg font-bold text-indigo-600 mt-1">
              {runDetail.average_score}%
            </div>
            <div className="text-[11px] text-gray-400 mt-0.5">
              Across all candidates
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm">
            <span className="text-xs text-gray-500 font-medium">Top Candidate</span>
            <div className="text-sm font-bold text-gray-900 truncate mt-1">
              {runDetail.top_candidate_name || "None"}
            </div>
            <div className="text-[11px] text-emerald-600 font-semibold mt-0.5">
              Score: {runDetail.top_candidate_score}%
            </div>
          </div>

          <div className="bg-white p-4 rounded-xl border border-gray-200 shadow-sm col-span-2 md:col-span-1">
            <span className="text-xs text-gray-500 font-medium">Bands</span>
            <div className="flex items-center gap-1.5 mt-2 flex-wrap">
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-emerald-100 text-emerald-800 font-semibold">
                S: {runDetail.band_distribution["Strong match"] || 0}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-800 font-semibold">
                G: {runDetail.band_distribution["Good match"] || 0}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-semibold">
                P: {runDetail.band_distribution["Partial match"] || 0}
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-gray-100 text-gray-700 font-semibold">
                W: {runDetail.band_distribution["Weak match"] || 0}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── If No Run Selected: Past Runs Selector ── */}
      {!runId && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6 text-center">
          <div className="max-w-md mx-auto space-y-3">
            <div className="text-4xl">📊</div>
            <h3 className="text-lg font-bold text-gray-900">
              No Active Matching Run Selected
            </h3>
            <p className="text-xs text-gray-500">
              Go to the Home page to analyze a Job Description and run AI matching, or select a previous run below.
            </p>
            <div className="pt-2">
              <Link
                to="/"
                className="inline-block px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-xs rounded-lg transition"
              >
                Go to Upload &amp; Match
              </Link>
            </div>
          </div>

          {pastRuns.length > 0 && (
            <div className="mt-8 text-left border-t border-gray-100 pt-6">
              <h4 className="text-xs font-bold uppercase text-gray-400 tracking-wider mb-3">
                Recent Matching Runs
              </h4>
              <div className="divide-y divide-gray-100 border border-gray-200 rounded-lg overflow-hidden">
                {pastRuns.map((r) => (
                  <div
                    key={r.id}
                    onClick={() => setSearchParams({ run: r.id })}
                    className="p-3.5 flex items-center justify-between hover:bg-gray-50 cursor-pointer transition text-xs"
                  >
                    <div>
                      <span className="font-bold text-gray-900">
                        {r.jd_title || `Job Description #${r.jd_id}`}
                      </span>
                      <span className="text-gray-400 ml-2">
                        Run #{r.id} • {new Date(r.created_at).toLocaleString()}
                      </span>
                      {r.is_stale && (
                        <span className="ml-2 text-[10px] px-1.5 py-0.5 bg-amber-100 text-amber-800 rounded font-semibold">
                          Stale JD
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-gray-600 font-medium">
                        {r.candidate_count} candidates
                      </span>
                      <span className="text-indigo-600 font-semibold">
                        View Results →
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* ── Candidate Results Table ── */}
      {runId && (
        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <div>
              <h2 className="text-sm font-bold text-gray-900">
                Ranked Candidates ({totalResults})
              </h2>
              <span className="text-xs text-gray-500">
                Ordered by composite match score descending with tie-break criteria.
              </span>
            </div>
          </div>

          {loading ? (
            <div className="p-12 text-center text-sm text-gray-400 italic">
              Loading ranked candidate cohort...
            </div>
          ) : results.length === 0 ? (
            <div className="p-12 text-center text-sm text-gray-400 italic">
              No candidate results found for this run.
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200 text-left text-xs">
                <thead className="bg-gray-50 text-gray-500 font-semibold uppercase tracking-wider">
                  <tr>
                    <th className="px-4 py-3 w-12 text-center">Rank</th>
                    <th className="px-4 py-3">Candidate</th>
                    <th className="px-4 py-3">Experience</th>
                    <th className="px-4 py-3 text-center">Factor Scores</th>
                    <th className="px-4 py-3 text-center">Match Score</th>
                    <th className="px-4 py-3 text-center">Band</th>
                    <th className="px-4 py-3">Top Matched Skills</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {results.map((c) => (
                    <tr
                      key={c.id}
                      className="hover:bg-indigo-50/30 transition-colors"
                    >
                      {/* Rank */}
                      <td className="px-4 py-3.5 text-center font-bold text-gray-700">
                        #{c.rank}
                      </td>

                      {/* Candidate info */}
                      <td className="px-4 py-3.5">
                        <div className="font-bold text-gray-900">
                          {c.candidate_name || "Unknown Candidate"}
                        </div>
                        {c.candidate_email && (
                          <div className="text-[11px] text-gray-400">
                            {c.candidate_email}
                          </div>
                        )}
                        {c.is_knockout && (
                          <span className="inline-block mt-1 text-[10px] px-1.5 py-0.5 rounded bg-rose-100 text-rose-700 font-bold border border-rose-200">
                            🛡️ Knockout Capped
                          </span>
                        )}
                      </td>

                      {/* Experience */}
                      <td className="px-4 py-3.5">
                        <div className="font-semibold text-gray-800">
                          {c.relevant_experience_years.toFixed(1)} / {c.total_experience_years.toFixed(1)} yrs
                        </div>
                        <div className="text-[11px] text-gray-400">
                          domain / total
                        </div>
                      </td>

                      {/* Factor Scores breakdown pill */}
                      <td className="px-4 py-3.5 text-center">
                        <div className="inline-flex items-center gap-1 text-[10px] font-mono text-gray-600 bg-gray-50 px-2 py-1 rounded border border-gray-100">
                          <span title="Skill Score">Sk:{Math.round(c.skill_score)}</span>
                          <span>•</span>
                          <span title="Semantic Score">Se:{Math.round(c.semantic_score)}</span>
                          <span>•</span>
                          <span title="Experience Score">Ex:{Math.round(c.experience_score)}</span>
                          <span>•</span>
                          <span title="Qualification Score">Qu:{Math.round(c.qualification_score)}</span>
                          <span>•</span>
                          <span title="Title Score">Ti:{Math.round(c.title_score)}</span>
                        </div>
                      </td>

                      {/* Final Score */}
                      <td className="px-4 py-3.5 text-center">
                        <span
                          className={`text-base font-extrabold ${getScoreColor(
                            c.final_score
                          )}`}
                        >
                          {c.final_score.toFixed(1)}%
                        </span>
                      </td>

                      {/* Band */}
                      <td className="px-4 py-3.5 text-center">
                        <span
                          className={`inline-block px-2.5 py-1 text-[11px] font-bold rounded-full border ${getBandBadgeClass(
                            c.band
                          )}`}
                        >
                          {c.band}
                        </span>
                      </td>

                      {/* Top Skills */}
                      <td className="px-4 py-3.5">
                        <div className="flex flex-wrap gap-1 max-w-xs">
                          {c.top_skills && c.top_skills.length > 0 ? (
                            c.top_skills.map((skill, sIdx) => (
                              <span
                                key={sIdx}
                                className="text-[10px] px-1.5 py-0.5 rounded bg-indigo-50 text-indigo-700 font-medium border border-indigo-100"
                              >
                                {skill}
                              </span>
                            ))
                          ) : (
                            <span className="text-gray-400 italic text-[11px]">
                              No direct core matches
                            </span>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
