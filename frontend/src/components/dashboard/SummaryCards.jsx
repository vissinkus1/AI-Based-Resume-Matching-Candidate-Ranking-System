import React from "react";
import StatTile from "../ui/StatTile";

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
      caption: "Score ≥ 80%",
      count: bandCounts.strong || 0,
      colorClass: "text-band-strong",
    },
    {
      id: "good",
      label: "Good Match",
      caption: "Score 65–79%",
      count: bandCounts.good || 0,
      colorClass: "text-band-good",
    },
    {
      id: "partial",
      label: "Partial Match",
      caption: "Score 50–64%",
      count: bandCounts.partial || 0,
      colorClass: "text-band-partial",
    },
    {
      id: "weak",
      label: "Weak Match",
      caption: "Score < 50%",
      count: bandCounts.weak || 0,
      colorClass: "text-band-weak",
    },
  ];

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-3 sm:gap-4 mb-6">
      {/* 4 Interactive Band Cards */}
      {bands.map((b) => {
        const isSelected = selectedBand === b.id;
        const pct = totalCount > 0 ? Math.round((b.count / totalCount) * 100) : 0;
        return (
          <StatTile
            key={b.id}
            label={b.label}
            value={b.count}
            caption={`${b.caption} (${pct}%)`}
            active={isSelected}
            onClick={() => onSelectBand(isSelected ? null : b.id)}
            colorClass={b.colorClass}
            className="cursor-pointer"
          />
        );
      })}

      {/* Total Candidates */}
      <StatTile
        label="Total Pool"
        value={totalCount}
        caption="All applicants"
        colorClass="text-brand-forest"
      />

      {/* Average Score */}
      <StatTile
        label="Mean Score"
        value={averageScore !== null ? `${averageScore.toFixed(1)}%` : "—"}
        caption="Cohort average"
        colorClass="text-brand-sage"
      />

      {/* Top Candidate */}
      <StatTile
        label="Rank #1"
        value={topCandidate ? `${topCandidate.final_score.toFixed(1)}%` : "—"}
        caption={topCandidate ? topCandidate.name : "None"}
        colorClass="text-brand-forest"
      />
    </div>
  );
}
