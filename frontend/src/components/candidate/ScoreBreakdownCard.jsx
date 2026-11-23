import React, { useState } from "react";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import ScoreBar from "../ui/ScoreBar";

export default function ScoreBreakdownCard({
  scores = {},
  contributions = {},
  weights = {},
  finalScore = 0,
}) {
  const [expandedFactor, setExpandedFactor] = useState(null);

  const factorDefs = [
    {
      key: "skill",
      label: "Skill Match",
      weight: (weights.skill || 0.4) * 100,
      score: scores.skill || 0,
      contribution: contributions.skill || 0,
      maxPts: (weights.skill || 0.4) * 100,
      color: "bg-band-strong",
      description:
        "Evaluates exact taxonomy matches, synonyms, parent/child relationships (e.g. AWS S3 to AWS), and semantic soft matches with 80% weight on required skills and 20% on preferred skills.",
    },
    {
      key: "semantic",
      label: "Semantic Relevance",
      weight: (weights.semantic || 0.25) * 100,
      score: scores.semantic || 0,
      contribution: contributions.semantic || 0,
      maxPts: (weights.semantic || 0.25) * 100,
      color: "bg-brand-sage",
      description:
        "Dense vector embedding comparison using all-MiniLM-L6-v2 combining 60% requirement-coverage and 40% whole-document semantic similarity calibrated against empirical bounds.",
    },
    {
      key: "experience",
      label: "Experience Alignment",
      weight: (weights.experience || 0.2) * 100,
      score: scores.experience || 0,
      contribution: contributions.experience || 0,
      maxPts: (weights.experience || 0.2) * 100,
      color: "bg-brand-forest",
      description:
        "Evaluates both relevant domain experience years (70%) and total career duration (30%) against the JD's minimum and maximum target thresholds.",
    },
    {
      key: "qualification",
      label: "Education & Degree",
      weight: (weights.qualification || 0.1) * 100,
      score: scores.qualification || 0,
      contribution: contributions.qualification || 0,
      maxPts: (weights.qualification || 0.1) * 100,
      color: "bg-band-good",
      description:
        "Evaluates candidate highest degree against the minimum required educational level (Bachelor, Master, Ph.D.) with bonus points for exceeding qualifications.",
    },
    {
      key: "title",
      label: "Job Title Alignment",
      weight: (weights.title || 0.05) * 100,
      score: scores.title || 0,
      contribution: contributions.title || 0,
      maxPts: (weights.title || 0.05) * 100,
      color: "bg-band-partial",
      description:
        "Compares normalized candidate resume job titles against the target position title after stripping seniority modifiers (Senior, Lead, Principal).",
    },
  ];

  const totalCalculated = factorDefs.reduce((acc, f) => acc + f.contribution, 0);

  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      <SectionHeader
        eyebrow="SCORE FORMULA"
        title="Score Composition & Weight Breakdown"
        subtitle="Deterministic formula: Match % = Σ (Factor Score × Weight). Click any row for algorithmic details."
        actions={
          <span className="text-xs font-mono px-3 py-1 rounded-full bg-brand-sage-soft/30 text-brand-ink border border-brand-line">
            5 Factors
          </span>
        }
      />

      {/* 5 Horizontal Progress Bars */}
      <div className="space-y-3.5">
        {factorDefs.map((factor) => {
          const isExpanded = expandedFactor === factor.key;
          return (
            <div
              key={factor.key}
              onClick={() => setExpandedFactor(isExpanded ? null : factor.key)}
              className="bg-brand-ivory/50 border border-brand-line rounded-2xl p-4 hover:border-brand-forest/50 transition cursor-pointer space-y-2"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="font-serif font-bold text-sm text-brand-ink">{factor.label}</span>
                  <span className="text-xs font-mono text-brand-muted">
                    ({factor.weight.toFixed(0)}% weight)
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-brand-muted">Raw:</span>
                  <span className="font-mono font-bold tabular-nums text-brand-ink">
                    {factor.score.toFixed(1)}%
                  </span>
                  <span className="text-brand-line">→</span>
                  <span className="text-brand-muted">Points:</span>
                  <span className="font-mono font-bold tabular-nums text-brand-forest text-sm">
                    {factor.contribution.toFixed(1)} / {factor.maxPts.toFixed(0)}
                  </span>
                </div>
              </div>

              {/* Bar */}
              <div className="w-full bg-brand-sage-soft/40 rounded-full h-2 overflow-hidden border border-brand-line/40">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${factor.color}`}
                  style={{ width: `${Math.min(100, Math.max(0, factor.score))}%` }}
                />
              </div>

              {/* Explanatory Dropdown */}
              {isExpanded && (
                <div className="pt-2 text-xs text-brand-muted leading-relaxed border-t border-brand-line/60 mt-2">
                  <strong className="text-brand-ink">Methodology:</strong> {factor.description}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summation Row */}
      <div className="mt-6 pt-4 border-t border-brand-line flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 bg-brand-ivory/60 p-4 rounded-2xl">
        <div>
          <span className="text-xs font-sans font-semibold uppercase tracking-wider text-brand-muted">
            Formula Verification:
          </span>
          <p className="text-xs font-mono text-brand-ink mt-0.5">
            {factorDefs.map((f) => f.contribution.toFixed(1)).join(" + ")} ={" "}
            <strong className="text-brand-forest font-bold">{totalCalculated.toFixed(1)}%</strong>
          </p>
        </div>
        <div className="text-left sm:text-right">
          <span className="text-xs font-sans font-semibold uppercase tracking-wider text-brand-muted">
            Final Match Score:
          </span>
          <p className="font-display text-3xl text-brand-ink">
            {finalScore.toFixed(1)}%
          </p>
        </div>
      </div>
    </Card>
  );
}
