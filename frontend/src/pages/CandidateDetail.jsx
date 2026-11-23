/*
 * pages/CandidateDetail.jsx — Comprehensive Explainable Candidate Match Detail.
 *
 * Implements Module 5 (Phase 6A Editorial Sage Design):
 * - CandidateTopBar (back link preserving state, rank badge, prev/next buttons)
 * - CandidateHeroCard (identity, contact, circular SVG gauge with Anton font, knockout banner)
 * - ScoreBreakdownCard (5 weighted progress bars, summation line, factor explanations)
 * - NarrativeExplanationCard (plain-English summary, strengths, gaps, factor verdicts)
 * - SkillsSection (matched, partial/child credit, missing required, missing preferred, extra)
 * - ExperienceComparisonCard (target range bar, relevant vs total, chronological jobs)
 * - QualificationComparisonCard (degree hierarchy level comparison, education history)
 * - SemanticEvidenceCard (side-by-side JD duties vs resume snippets with cosine scores)
 * - ExtractedResumeDataCard (collapsible audit of raw extracted text & parse warnings)
 */

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
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
import EmptyState from "../components/ui/EmptyState";
import Card from "../components/ui/Card";
import Skeleton from "../components/ui/Skeleton";

export default function CandidateDetail() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
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
      <div className="max-w-5xl mx-auto space-y-6 py-4">
        <Card padding="p-6" className="h-20 flex items-center justify-between">
          <Skeleton variant="rectangular" width="160px" height="36px" />
          <Skeleton variant="rectangular" width="200px" height="36px" />
        </Card>
        <Card padding="p-8" className="h-64 flex flex-col justify-between">
          <div className="space-y-3">
            <Skeleton variant="text" width="40%" />
            <Skeleton variant="text" width="60%" />
          </div>
          <Skeleton variant="rectangular" width="100%" height="40px" />
        </Card>
        <Card padding="p-6" className="h-72">
          <Skeleton variant="rectangular" width="100%" height="100%" />
        </Card>
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div className="py-16">
        <EmptyState
          title="Could Not Load Candidate Detail"
          description={error || "Candidate evaluation record was not found for this match run."}
          actionLabel="← Back to Ranking Dashboard"
          onAction={() => navigate(activeRunId ? `/dashboard?run=${activeRunId}` : "/dashboard")}
        />
      </div>
    );
  }

  const expBreakdown = data.experience_breakdown || data.experience || {};
  const qualBreakdown = data.qualification_breakdown || data.qualification || {};
  const skillsBreakdown = data.skills_breakdown || data.skills || {};
  const semanticBreakdown = data.semantic_breakdown || data.semantic || {};

  const totalExp =
    expBreakdown.total_years !== undefined
      ? expBreakdown.total_years
      : expBreakdown.total_experience_years || 0;
  const relExp =
    expBreakdown.relevant_years !== undefined
      ? expBreakdown.relevant_years
      : expBreakdown.relevant_experience_years !== undefined
      ? expBreakdown.relevant_experience_years
      : totalExp;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
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
        score={data.scores?.experience}
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
        score={data.scores?.semantic}
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
