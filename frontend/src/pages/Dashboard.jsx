/*
 * pages/Dashboard.jsx — AI Matching & Candidate Ranking Dashboard.
 *
 * Implements Module 4:
 * - DashboardHeader with stale notification, re-run, CSV export.
 * - SummaryCards with 4 clickable match band cards, pool size, avg score.
 * - ControlsBar with debounced search, band, min score slider, experience, skill, reset.
 * - RankingTable with strictly required column order, colored bars, rank, knockout.
 * - URL query string synchronization for all filters and sorting.
 */

import React, { useState, useEffect, useCallback, useMemo } from "react";
import { useSearchParams, Link, useNavigate } from "react-router-dom";
import { getRun, getResults, listRuns, runMatch, getLatestRun } from "../api/match";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import SummaryCards from "../components/dashboard/SummaryCards";
import ControlsBar from "../components/dashboard/ControlsBar";
import RankingTable from "../components/dashboard/RankingTable";

export default function Dashboard() {
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();

  const runId = searchParams.get("run");
  const sortBy = searchParams.get("sort") || "rank";
  const order = searchParams.get("order") || "asc";
  const band = searchParams.get("band") || "";
  const minScore = parseInt(searchParams.get("min_score") || "0", 10);
  const minExperience = parseFloat(searchParams.get("min_exp") || "0");
  const skill = searchParams.get("skill") || "";
  const search = searchParams.get("search") || "";

  // Data states
  const [loading, setLoading] = useState(false);
  const [reRunning, setReRunning] = useState(false);
  const [error, setError] = useState(null);
  const [runDetail, setRunDetail] = useState(null);
  const [resultsData, setResultsData] = useState({
    items: [],
    total: 0,
    filtered_count: 0,
    band_counts: {},
  });

  // Past runs state (if no run selected)
  const [pastRuns, setPastRuns] = useState([]);
  const [pastRunsLoading, setPastRunsLoading] = useState(false);

  // Helper to update query params cleanly
  const updateQueryParam = useCallback(
    (key, value) => {
      setSearchParams(
        (prev) => {
          const next = new URLSearchParams(prev);
          if (value === null || value === undefined || value === "" || value === 0) {
            next.delete(key);
          } else {
            next.set(key, String(value));
          }
          return next;
        },
        { replace: true }
      );
    },
    [setSearchParams]
  );

  // Load run metadata and results
  const loadRun = useCallback(
    async (id) => {
      setLoading(true);
      setError(null);
      try {
        const params = {
          limit: 100,
          offset: 0,
          sort_by: sortBy,
          order: order,
        };
        if (band) params.band = band;
        if (minScore > 0) params.min_score = minScore;
        if (minExperience > 0) params.min_experience = minExperience;
        if (skill) params.skill = skill;
        if (search) params.search = search;

        const [detail, resultsPage] = await Promise.all([
          getRun(id),
          getResults(id, params),
        ]);

        setRunDetail(detail);
        setResultsData(resultsPage);
      } catch (err) {
        console.error("Failed to load run:", err);
        setError(
          err.response?.data?.detail || "Failed to load matching run results."
        );
      } finally {
        setLoading(false);
      }
    },
    [sortBy, order, band, minScore, minExperience, skill, search]
  );

  // Load past runs if no run ID in URL
  const loadPastRuns = useCallback(async () => {
    setPastRunsLoading(true);
    try {
      const runs = await listRuns(null, 30);
      setPastRuns(runs || []);
      // If runs exist and no run selected, automatically load the latest
      if (runs && runs.length > 0 && !runId) {
        navigate(`/dashboard?run=${runs[0].id}`, { replace: true });
      }
    } catch (err) {
      console.error("Failed to list past runs:", err);
    } finally {
      setPastRunsLoading(false);
    }
  }, [runId, navigate]);

  useEffect(() => {
    if (runId) {
      loadRun(runId);
    } else {
      loadPastRuns();
    }
  }, [runId, loadRun, loadPastRuns]);

  // Handle re-running match
  const handleReRun = async () => {
    if (!runDetail?.jd_id) return;
    setReRunning(true);
    try {
      const newRun = await runMatch(runDetail.jd_id);
      navigate(`/dashboard?run=${newRun.id}`);
    } catch (err) {
      alert("Failed to re-run match: " + (err.response?.data?.detail || err.message));
    } finally {
      setReRunning(false);
    }
  };

  // Filter change handlers
  const handleSelectBand = (selectedBand) => {
    updateQueryParam("band", selectedBand);
  };

  const handleSearchChange = (val) => {
    updateQueryParam("search", val);
  };

  const handleMinScoreChange = (val) => {
    updateQueryParam("min_score", val);
  };

  const handleMinExperienceChange = (val) => {
    updateQueryParam("min_exp", val);
  };

  const handleSkillChange = (val) => {
    updateQueryParam("skill", val);
  };

  const handleSortChange = (newSort, newOrder) => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("sort", newSort);
        next.set("order", newOrder);
        return next;
      },
      { replace: true }
    );
  };

  const handleResetFilters = () => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams();
        if (runId) next.set("run", runId);
        return next;
      },
      { replace: true }
    );
  };

  const hasActiveFilters = Boolean(
    band || minScore > 0 || minExperience > 0 || skill || search
  );

  // Available skills from JD
  const availableSkills = useMemo(() => {
    if (!runDetail?.jd_parsed) return [];
    const req = runDetail.jd_parsed.required_skills || [];
    const pref = runDetail.jd_parsed.preferred_skills || [];
    return Array.from(new Set([...req, ...pref]));
  }, [runDetail]);

  // Cohort statistics
  const averageScore = useMemo(() => {
    if (!resultsData.items || resultsData.items.length === 0) return null;
    const sum = resultsData.items.reduce((acc, curr) => acc + curr.final_score, 0);
    return sum / resultsData.items.length;
  }, [resultsData.items]);

  const topCandidate = useMemo(() => {
    if (!resultsData.items || resultsData.items.length === 0) return null;
    // Top candidate by score
    return [...resultsData.items].sort((a, b) => b.final_score - a.final_score)[0];
  }, [resultsData.items]);

  // If no run selected and no past runs found
  if (!runId && !pastRunsLoading && pastRuns.length === 0) {
    return (
      <div className="max-w-4xl mx-auto py-16 px-4 text-center">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 flex items-center justify-center text-3xl mb-4">
          📊
        </div>
        <h2 className="text-2xl font-black text-white mb-2">No Matching Runs Found</h2>
        <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
          You haven't run any candidate evaluations yet. Start by parsing a Job Description and matching candidate resumes, or try the instant sample data demo.
        </p>
        <Link
          to="/"
          className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm rounded-xl transition shadow-lg shadow-indigo-500/25 inline-flex items-center gap-2"
        >
          <span>🚀</span> Go to Home & Match Resumes
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span>⚠️</span>
            <span>{error}</span>
          </div>
          <button
            onClick={() => loadRun(runId)}
            className="text-xs font-bold underline hover:text-white"
          >
            Retry
          </button>
        </div>
      )}

      {/* Header */}
      {runDetail && (
        <DashboardHeader
          run={runDetail}
          onReRun={handleReRun}
          reRunning={reRunning}
        />
      )}

      {/* Summary Cards */}
      <SummaryCards
        bandCounts={resultsData.band_counts}
        totalCount={resultsData.total}
        averageScore={averageScore}
        topCandidate={topCandidate}
        selectedBand={band}
        onSelectBand={handleSelectBand}
      />

      {/* Controls Bar */}
      <ControlsBar
        search={search}
        onSearchChange={handleSearchChange}
        band={band}
        onBandChange={handleSelectBand}
        minScore={minScore}
        onMinScoreChange={handleMinScoreChange}
        minExperience={minExperience}
        onMinExperienceChange={handleMinExperienceChange}
        skill={skill}
        onSkillChange={handleSkillChange}
        availableSkills={availableSkills}
        onResetFilters={handleResetFilters}
        hasActiveFilters={hasActiveFilters}
        filteredCount={resultsData.filtered_count}
        totalCount={resultsData.total}
      />

      {/* Ranking Table */}
      <RankingTable
        results={resultsData.items}
        runId={runId}
        loading={loading}
        sortBy={sortBy}
        order={order}
        onSortChange={handleSortChange}
        onResetFilters={handleResetFilters}
      />
    </div>
  );
}
