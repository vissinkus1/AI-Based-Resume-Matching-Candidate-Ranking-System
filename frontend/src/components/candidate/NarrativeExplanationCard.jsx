import React from "react";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import Badge from "../ui/Badge";

export default function NarrativeExplanationCard({
  narrativeSummary = "",
  strengths = [],
  gaps = [],
  reasons = [],
}) {
  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      <SectionHeader
        eyebrow="ANALYSIS"
        title="Executive Narrative &amp; Recommendation"
        subtitle="Auditable, human-readable rationale generated from quantitative factor evaluations."
      />

      {/* Narrative Summary Paragraph */}
      {narrativeSummary && (
        <div className="bg-brand-ivory/60 border border-brand-line rounded-2xl p-4 sm:p-5 mb-6">
          <p className="font-serif text-sm sm:text-base text-brand-ink leading-relaxed font-normal">
            {narrativeSummary}
          </p>
        </div>
      )}

      {/* Strengths & Gaps Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        {/* Strengths */}
        <div className="bg-band-strong/10 border border-band-strong/30 rounded-2xl p-5 space-y-3">
          <h4 className="font-sans text-xs font-bold text-band-strong uppercase tracking-wider flex items-center gap-1.5">
            <span>✓</span> Key Candidate Strengths ({strengths.length})
          </h4>
          {strengths.length > 0 ? (
            <ul className="space-y-2">
              {strengths.map((str, idx) => (
                <li key={idx} className="text-xs text-brand-ink flex items-start gap-2">
                  <span className="text-band-strong mt-0.5 font-bold">✓</span>
                  <span>{str}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-brand-muted italic">No standout strengths detected.</p>
          )}
        </div>

        {/* Gaps */}
        <div className="bg-band-weak/10 border border-band-weak/30 rounded-2xl p-5 space-y-3">
          <h4 className="font-sans text-xs font-bold text-band-weak uppercase tracking-wider flex items-center gap-1.5">
            <span>⚠️</span> Missing Requirements &amp; Gaps ({gaps.length})
          </h4>
          {gaps.length > 0 ? (
            <ul className="space-y-2">
              {gaps.map((gap, idx) => (
                <li key={idx} className="text-xs text-brand-ink flex items-start gap-2">
                  <span className="text-band-weak mt-0.5 font-bold">✗</span>
                  <span>{gap}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-xs text-band-strong font-medium">
              ✓ No critical gaps found against required criteria!
            </p>
          )}
        </div>
      </div>

      {/* Factor Reasons Breakdown */}
      {reasons && reasons.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-serif text-sm font-bold text-brand-ink">
            Factor-by-Factor Evaluation Rationale
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {reasons.map((r, idx) => {
              const factorName = r.factor || "Factor";
              const verdict = r.verdict || "Evaluated";
              const isPositive =
                verdict.toLowerCase().includes("exceeds") ||
                verdict.toLowerCase().includes("strong") ||
                verdict.toLowerCase().includes("full") ||
                verdict.toLowerCase().includes("pass") ||
                verdict.toLowerCase().includes("high");
              const isWarning =
                verdict.toLowerCase().includes("gap") ||
                verdict.toLowerCase().includes("low") ||
                verdict.toLowerCase().includes("fail") ||
                verdict.toLowerCase().includes("missing");

              return (
                <div
                  key={idx}
                  className="bg-brand-ivory/50 border border-brand-line rounded-2xl p-3.5 flex flex-col justify-between space-y-2"
                >
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-serif font-bold text-xs text-brand-ink capitalize">
                      {factorName}
                    </span>
                    <Badge
                      variant={isPositive ? "strong" : isWarning ? "weak" : "good"}
                      size="sm"
                      dot={false}
                    >
                      {verdict}
                    </Badge>
                  </div>
                  <p className="text-[11px] text-brand-muted leading-relaxed">
                    {r.explanation || r.detail || "No additional commentary available."}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </Card>
  );
}
