/*
 * pages/CandidateDetail.jsx — Comprehensive Explainable Candidate Match Detail.
 *
 * Implements Module 5:
 * - CandidateTopBar (back link preserving state, rank badge, prev/next buttons)
 * - CandidateHeroCard (identity, contact, circular SVG gauge, knockout banner)
 * - ScoreBreakdownCard (5 weighted progress bars, summation line, factor explanations)
 * - NarrativeExplanationCard (plain-English summary, strengths, gaps, factor verdicts)
 * - SkillsSection (matched, partial/child credit, missing required, missing preferred, extra)
 * - ExperienceComparisonCard (target range bar, relevant vs total, chronological jobs)
 * - QualificationComparisonCard (degree hierarchy level comparison, education history)
 * - SemanticEvidenceCard (side-by-side JD duties vs resume snippets with cosine scores)
 * - ExtractedResumeDataCard (collapsible audit of raw extracted text & parse warnings)
 */

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useSearchParams, Link } from "react-router-dom";
import { getCandidateResult, getLatestRun } from "../api/match";

import CandidateTopBar from "../components/candidate/CandidateTopBar";
import CandidateHeroCard from "../components/candidate/CandidateHeroCard";
import ScoreBreakdownCard from "../components/candidate/ScoreBreakdownCard";
import NarrativeExplanationCard from "../components/candidate/NarrativeExplanationCard";
import SkillsSection from "../components/candidate/SkillsSection";
import ExperienceComparisonCard from "../components/candidate/ExperienceComparisonCard";
import QualificationComparisonCard from "../components/candidate/QualificationComparisonCard";
import SemanticEvidenceCard from "../components/candidate/SemanticEvidenceCard";
import ExtractedResumeDataCard from "../components/candidate/ExtractedResumeDataCard";

export default function CandidateDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const runIdFromUrl = searchParams.get("run");

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [activeRunId, setActiveRunId] = useState(runIdFromUrl);

  const loadCandidateDetail = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      let rId = runIdFromUrl;
      if (!rId) {
        // Fallback to latest run if run param was omitted
        const latest = await getLatestRun();
        if (!latest?.id) {
          throw new Error("No active matching runs found to display candidate ranking.");
        }
        rId = latest.id;
        setActiveRunId(latest.id);
      }

      const result = await getCandidateResult(rId, id);
      setData(result);
    } catch (err) {
      console.error("Failed to load candidate detail:", err);
      setError(
        err.response?.data?.detail || err.message || "Failed to load candidate match detail."
      );
    } finally {
      setLoading(false);
    }
  }, [id, runIdFromUrl]);

  useEffect(() => {
    loadCandidateDetail();
  }, [loadCandidateDetail]);

  // Loading skeleton
  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        <div className="animate-pulse bg-slate-900 border border-slate-800 rounded-2xl p-6 h-20" />
        <div className="animate-pulse bg-slate-900 border border-slate-800 rounded-2xl p-8 h-64" />
        <div className="animate-pulse bg-slate-900 border border-slate-800 rounded-2xl p-6 h-72" />
        <div className="animate-pulse bg-slate-900 border border-slate-800 rounded-2xl p-6 h-60" />
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div className="max-w-2xl mx-auto py-16 px-4 text-center">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-400 flex items-center justify-center text-3xl mb-4">
          ⚠️
        </div>
        <h2 className="text-2xl font-bold text-white mb-2">Could Not Load Candidate Detail</h2>
        <p className="text-slate-400 text-sm max-w-md mx-auto mb-6">
          {error || "Candidate evaluation record was not found for this match run."}
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link
            to={activeRunId ? `/dashboard?run=${activeRunId}` : "/dashboard"}
            className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition"
          >
            ← Back to Dashboard
          </Link>
          <button
            onClick={loadCandidateDetail}
            className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold rounded-xl transition shadow"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  const expBreakdown = data.experience_breakdown || data.experience || {};
  const qualBreakdown = data.qualification_breakdown || data.qualification || {};
  const skillsBreakdown = data.skills_breakdown || data.skills || {};
  const semanticBreakdown = data.semantic_breakdown || data.semantic || {};

  const totalExp = expBreakdown.total_experience_years || 0;
  const relExp = expBreakdown.relevant_experience_years !== undefined ? expBreakdown.relevant_experience_years : totalExp;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* 1. Top Navigation Bar */}
      <CandidateTopBar
        rank={data.rank}
        totalCandidates={data.total_candidates}
        prevCandidateId={data.prev_candidate_id}
        nextCandidateId={data.next_candidate_id}
        runId={activeRunId}
      />

      {/* 2. Candidate Hero Card */}
      <CandidateHeroCard
        candidate={data}
        finalScore={data.final_score}
        band={data.band}
        isKnockout={data.is_knockout}
        knockoutReason={data.knockout_reason}
        totalExp={totalExp}
        relExp={relExp}
        jdTitle={data.jd_title}
      />

      {/* 3. Score Breakdown & Algorithmic Summation */}
      <ScoreBreakdownCard
        scores={data.scores}
        contributions={data.contributions}
        weights={data.weights}
        finalScore={data.final_score}
      />

      {/* 4. Plain-English Narrative Summary */}
      <NarrativeExplanationCard
        narrativeSummary={data.narrative_summary}
        strengths={data.strengths}
        gaps={data.gaps}
        reasons={data.reasons}
      />

      {/* 5. Deep-Dive Skills Matrix */}
      <SkillsSection
        skillsBreakdown={skillsBreakdown}
      />

      {/* 6. Experience Timeline & Relevance Comparison */}
      <ExperienceComparisonCard
        experienceBreakdown={expBreakdown}
        experienceEntries={data.experience_entries}
        jdMinExp={data.jd_min_experience_years}
        jdMaxExp={data.jd_max_experience_years}
        totalExp={totalExp}
        relevantExp={relExp}
      />

      {/* 7. Degree & Qualification Check */}
      <QualificationComparisonCard
        qualificationBreakdown={qualBreakdown}
        educationEntries={data.education}
        jdMinLevel={data.jd_min_required_qualification}
        jdPreferredLevel={data.jd_preferred_qualification}
      />

      {/* 8. Sentence-Level Semantic Alignment */}
      <SemanticEvidenceCard
        semanticBreakdown={semanticBreakdown}
      />

      {/* 9. Parser Audit & Diagnostics */}
      <ExtractedResumeDataCard
        rawResumeText={data.raw_resume_text}
        parseWarnings={data.parse_warnings}
        extractedSkills={data.candidate_skills || []}
      />
    </div>
  );
}
