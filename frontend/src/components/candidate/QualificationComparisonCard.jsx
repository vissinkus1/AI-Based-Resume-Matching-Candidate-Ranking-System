import React from "react";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import Badge from "../ui/Badge";
import Eyebrow from "../ui/Eyebrow";

export default function QualificationComparisonCard({
  qualificationBreakdown = {},
  educationEntries = [],
  jdMinLevel = "None",
  jdPreferredLevel = null,
}) {
  const candidateLevel = qualificationBreakdown.candidate_highest_level || "Not detected";
  const verdict = qualificationBreakdown.verdict || "Evaluated";
  const score = qualificationBreakdown.score !== undefined ? qualificationBreakdown.score : 100;

  const isExceeds = verdict.toLowerCase().includes("exceeds");
  const isPass = verdict.toLowerCase().includes("meets") || verdict.toLowerCase().includes("pass") || score >= 90;

  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      <SectionHeader
        eyebrow="QUALIFICATION"
        title="Education &amp; Degree Qualification"
        subtitle="Compares candidate degree hierarchy against minimum required and preferred credentials."
        actions={
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-brand-muted">Score:</span>
            <span className="font-mono text-base font-bold tabular-nums text-brand-forest">
              {typeof score === "number" ? score.toFixed(1) : score}%
            </span>
            <Badge
              variant={isExceeds ? "strong" : isPass ? "good" : "weak"}
              size="sm"
              dot={false}
            >
              {isExceeds ? "Exceeds Requirement" : isPass ? "Requirement Met" : "Below Minimum"}
            </Badge>
          </div>
        }
      />

      {/* Comparison Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-6">
        <div className="bg-brand-ivory/60 p-4 rounded-2xl border border-brand-line">
          <Eyebrow>JD Required Level</Eyebrow>
          <p className="font-serif text-base font-bold text-brand-ink capitalize mt-1">
            {jdMinLevel || "Bachelor's (or equivalent)"}
          </p>
          {jdPreferredLevel && (
            <span className="text-[11px] text-brand-muted mt-1 block">
              Preferred: {jdPreferredLevel}
            </span>
          )}
        </div>

        <div className="bg-brand-ivory/60 p-4 rounded-2xl border border-brand-line">
          <Eyebrow>Candidate Highest Degree</Eyebrow>
          <p className="font-serif text-base font-bold text-brand-forest capitalize mt-1">
            {candidateLevel}
          </p>
          <span className="text-[11px] text-brand-muted mt-1 block">
            Hierarchy verified
          </span>
        </div>

        <div className="bg-brand-ivory/60 p-4 rounded-2xl border border-brand-line">
          <Eyebrow>Qualification Status</Eyebrow>
          <p className="font-serif text-base font-bold text-brand-ink mt-1">
            {verdict}
          </p>
          <span className="text-[11px] text-brand-muted mt-1 block">
            {qualificationBreakdown.reason || "Formal credential check"}
          </span>
        </div>
      </div>

      {/* Listed Education Entries */}
      {educationEntries && educationEntries.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-serif text-sm font-bold text-brand-ink">
            Reported Degrees &amp; Institutions ({educationEntries.length})
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {educationEntries.map((edu, idx) => (
              <div
                key={idx}
                className="bg-brand-ivory/40 border border-brand-line rounded-2xl p-4 flex items-start justify-between gap-3"
              >
                <div>
                  <h5 className="font-serif font-bold text-xs text-brand-ink">
                    {edu.degree || edu.degree_raw || "Degree unverified"}
                  </h5>
                  <p className="text-xs text-brand-muted mt-0.5">
                    {edu.institution || "Institution not listed"}
                  </p>
                  {edu.field_of_study && (
                    <span className="text-[11px] text-brand-forest font-medium block mt-1">
                      Field: {edu.field_of_study}
                    </span>
                  )}
                </div>
                {edu.graduation_year && (
                  <span className="font-mono text-xs font-semibold tabular-nums text-brand-muted px-2 py-0.5 bg-brand-paper rounded-full border border-brand-line">
                    {edu.graduation_year}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </Card>
  );
}
