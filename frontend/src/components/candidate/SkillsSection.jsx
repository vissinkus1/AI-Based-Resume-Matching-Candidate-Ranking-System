import React from "react";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import Chip from "../ui/Chip";
import Eyebrow from "../ui/Eyebrow";

export default function SkillsSection({
  skillsBreakdown = {},
}) {
  const matchedRequired = skillsBreakdown.matched_required || [];
  const matchedPreferred = skillsBreakdown.matched_preferred || [];
  const partial = skillsBreakdown.partial || [];
  const missingRequired = skillsBreakdown.missing_required || [];
  const missingPreferred = skillsBreakdown.missing_preferred || [];
  const extraSkills = skillsBreakdown.extra_skills || [];

  const requiredCount = skillsBreakdown.required_count || (matchedRequired.length + missingRequired.length);
  const matchedReqCount = skillsBreakdown.matched_required_count || matchedRequired.length;
  const coveragePct = requiredCount > 0 ? Math.round((matchedReqCount / requiredCount) * 100) : 0;

  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      {/* Section Header with Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6 pb-4 border-b border-brand-line">
        <div>
          <Eyebrow>COMPETENCY TAXONOMY</Eyebrow>
          <h3 className="font-serif text-xl sm:text-2xl font-bold text-brand-ink mt-0.5">
            Skill Coverage &amp; Match Matrix
          </h3>
          <p className="text-xs text-brand-muted mt-0.5">
            Granular evaluation of required, preferred, parent-child, and extra competencies.
          </p>
        </div>

        {/* Coverage summary badges */}
        <div className="flex items-center gap-3">
          <div className="bg-brand-ivory/60 px-4 py-2 rounded-2xl border border-brand-line text-center">
            <span className="text-[10px] font-sans font-semibold text-brand-muted uppercase tracking-wider block">
              Required Met
            </span>
            <span className="font-mono text-base font-bold tabular-nums text-band-strong">
              {matchedReqCount} of {requiredCount}
            </span>
          </div>

          <div className="bg-brand-ivory/60 px-4 py-2 rounded-2xl border border-brand-line text-center">
            <span className="text-[10px] font-sans font-semibold text-brand-muted uppercase tracking-wider block">
              Coverage
            </span>
            <span className="font-mono text-base font-bold tabular-nums text-brand-forest">
              {coveragePct}%
            </span>
          </div>
        </div>
      </div>

      <div className="space-y-6">
        {/* 1. Matched Required Skills */}
        <div className="space-y-2.5">
          <h4 className="font-serif text-xs font-bold text-band-strong uppercase tracking-wider flex items-center gap-2">
            <span>✓</span> Matched Required Skills ({matchedRequired.length})
          </h4>
          {matchedRequired.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {matchedRequired.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                const matchType = typeof item === "object" ? item.match_type || item.type || "exact" : "exact";
                const evidence = typeof item === "object" ? item.evidence : null;

                return (
                  <Chip
                    key={idx}
                    variant="matched"
                    title={evidence ? `Resume Evidence: "${evidence}"` : `Matched via ${matchType}`}
                  >
                    <span>{name}</span>
                    <span className="text-[9px] font-mono font-bold uppercase opacity-75">
                      ({matchType})
                    </span>
                  </Chip>
                );
              })}
            </div>
          ) : (
            <p className="text-xs text-band-weak italic">No required skills were matched.</p>
          )}
        </div>

        {/* 2. Partial / Inferred Skills */}
        {partial.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="font-serif text-xs font-bold text-band-partial uppercase tracking-wider flex items-center gap-2">
              <span>≈</span> Partial / Parent-Child Credits ({partial.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {partial.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                const reason = typeof item === "object" ? item.reason || item.matched_via : "partial";
                const credit = typeof item === "object" ? item.credit : null;

                return (
                  <Chip
                    key={idx}
                    variant="partial"
                    title={`Reason: ${reason}`}
                  >
                    <span>{name}</span>
                    {credit !== null && credit !== undefined && (
                      <span className="text-[9px] font-mono font-bold">
                        ({(credit * 100).toFixed(0)}% credit)
                      </span>
                    )}
                  </Chip>
                );
              })}
            </div>
          </div>
        )}

        {/* 3. Matched Preferred Skills */}
        {matchedPreferred.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="font-serif text-xs font-bold text-brand-forest uppercase tracking-wider flex items-center gap-2">
              <span>★</span> Matched Nice-to-Have Skills ({matchedPreferred.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {matchedPreferred.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                return (
                  <Chip key={idx} variant="preferred">
                    {name}
                  </Chip>
                );
              })}
            </div>
          </div>
        )}

        {/* 4. Missing Required Skills */}
        {missingRequired.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="font-serif text-xs font-bold text-band-weak uppercase tracking-wider flex items-center gap-2">
              <span>✗</span> Missing Required Skills ({missingRequired.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {missingRequired.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                return (
                  <Chip key={idx} variant="missing">
                    {name}
                  </Chip>
                );
              })}
            </div>
          </div>
        )}

        {/* 5. Missing Preferred Skills */}
        {missingPreferred.length > 0 && (
          <div className="space-y-2.5">
            <h4 className="font-serif text-xs font-bold text-brand-muted uppercase tracking-wider flex items-center gap-2">
              <span>○</span> Missing Preferred Skills ({missingPreferred.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {missingPreferred.map((item, idx) => {
                const name = typeof item === "string" ? item : item.skill || item.name;
                return (
                  <Chip key={idx} variant="neutral" className="opacity-70 line-through">
                    {name}
                  </Chip>
                );
              })}
            </div>
          </div>
        )}

        {/* 6. Extra Skills Detected */}
        {extraSkills.length > 0 && (
          <div className="space-y-2.5 pt-2 border-t border-brand-line">
            <h4 className="font-serif text-xs font-bold text-brand-muted uppercase tracking-wider flex items-center gap-2">
              <span>+</span> Additional Skills on Resume ({extraSkills.length})
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {extraSkills.slice(0, 20).map((sk, idx) => (
                <Chip key={idx} variant="extra" size="sm">
                  {sk}
                </Chip>
              ))}
              {extraSkills.length > 20 && (
                <span className="text-[11px] font-mono text-brand-muted self-center">
                  +{extraSkills.length - 20} more
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
}
