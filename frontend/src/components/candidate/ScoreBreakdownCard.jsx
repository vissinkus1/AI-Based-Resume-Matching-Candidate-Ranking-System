import React, { useState } from "react";

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
      color: "bg-emerald-500",
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
      color: "bg-teal-500",
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
      color: "bg-indigo-500",
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
      color: "bg-purple-500",
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
      color: "bg-amber-500",
      description:
        "Compares normalized candidate resume job titles against the target position title after stripping seniority modifiers (Senior, Lead, Principal).",
    },
  ];

  const totalCalculated = factorDefs.reduce((acc, f) => acc + f.contribution, 0);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>⚖️</span> Score Composition & Weight Breakdown
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Deterministic formula: Match % = Σ (Factor Score × Weight). Click any row for algorithmic details.
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 border border-slate-700">
          5 Factors
        </span>
      </div>

      {/* 5 Horizontal Progress Bars */}
      <div className="space-y-4">
        {factorDefs.map((factor) => {
          const isExpanded = expandedFactor === factor.key;
          return (
            <div
              key={factor.key}
              onClick={() => setExpandedFactor(isExpanded ? null : factor.key)}
              className="bg-slate-950/70 border border-slate-800/80 rounded-xl p-3.5 hover:border-slate-700 transition cursor-pointer"
            >
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-sm text-white">{factor.label}</span>
                  <span className="text-xs text-slate-500">
                    ({factor.weight.toFixed(0)}% weight)
                  </span>
                </div>
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400">
                    Factor Score: <strong className="text-white">{factor.score.toFixed(1)}/100</strong>
                  </span>
                  <span className="text-slate-600">•</span>
                  <span className="font-bold text-indigo-400">
                    +{factor.contribution.toFixed(1)} / {factor.maxPts.toFixed(1)} pts
                  </span>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="w-full bg-slate-800 rounded-full h-2.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${factor.color} transition-all duration-700`}
                  style={{ width: `${Math.min(100, Math.max(0, factor.score))}%` }}
                />
              </div>

              {/* Expandable Explanation */}
              {isExpanded && (
                <div className="mt-3 pt-3 border-t border-slate-800/80 text-xs text-slate-300 space-y-1">
                  <p className="font-semibold text-slate-200">How this is calculated:</p>
                  <p className="text-slate-400 leading-relaxed">{factor.description}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom Summation Row */}
      <div className="mt-5 pt-4 border-t border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-slate-950/40 p-3 rounded-xl">
        <div className="text-xs text-slate-400">
          Sum of factor contributions ={" "}
          <span className="font-mono text-slate-300">
            {factorDefs.map((f) => f.contribution.toFixed(1)).join(" + ")}
          </span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-xs font-semibold text-slate-400">Final Match Score:</span>
          <span className="text-xl font-black text-white">
            {finalScore.toFixed(1)}%
          </span>
          {Math.abs(finalScore - totalCalculated) > 0.5 && (
            <span className="text-xs text-slate-500 font-mono">
              (uncapped: {totalCalculated.toFixed(1)}%)
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
