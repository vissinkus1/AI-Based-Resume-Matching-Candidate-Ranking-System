import React from "react";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import Badge from "../ui/Badge";
import Chip from "../ui/Chip";
import Eyebrow from "../ui/Eyebrow";

export default function ExperienceComparisonCard({
  experienceBreakdown = {},
  experienceEntries = [],
  jdMinExp = null,
  jdMaxExp = null,
  totalExp = 0,
  relevantExp = 0,
}) {
  const verdict = experienceBreakdown.verdict || (relevantExp >= (jdMinExp || 0) ? "Meets Requirement" : "Below Minimum");
  const score = experienceBreakdown.score !== undefined ? experienceBreakdown.score : 0;

  // Max scale for visual comparison bar
  const maxScale = Math.max(12, totalExp + 2, (jdMaxExp || jdMinExp || 5) + 3);

  const jdMinPct = jdMinExp ? (jdMinExp / maxScale) * 100 : 0;
  const jdMaxPct = jdMaxExp ? (jdMaxExp / maxScale) * 100 : jdMinPct + 15;
  const totalPct = Math.min(100, (totalExp / maxScale) * 100);
  const relPct = Math.min(100, (relevantExp / maxScale) * 100);

  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      <SectionHeader
        eyebrow="EXPERIENCE"
        title="Experience Alignment &amp; Work History"
        subtitle="Evaluated by relevant domain duration (70%) and total career tenure (30%)."
        actions={
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-brand-muted">Score:</span>
            <span className="font-mono text-base font-bold tabular-nums text-brand-forest">
              {typeof score === "number" ? score.toFixed(1) : score}%
            </span>
            <Badge variant="good" size="sm" dot={false}>
              {verdict}
            </Badge>
          </div>
        }
      />

      {/* Visual Comparison Bar */}
      <div className="bg-brand-ivory/60 p-5 rounded-2xl border border-brand-line mb-6 space-y-3">
        <div className="flex items-center justify-between text-xs font-mono text-brand-muted">
          <span>0 yrs</span>
          <span className="font-sans font-semibold text-[10px] uppercase tracking-wider">
            Target Range vs Candidate Tenure
          </span>
          <span>{maxScale.toFixed(0)} yrs</span>
        </div>

        {/* Bar container */}
        <div className="relative h-6 bg-brand-sage-soft/30 rounded-xl overflow-hidden border border-brand-line">
          {/* JD Required Target Range Zone */}
          {jdMinExp && (
            <div
              className="absolute top-0 bottom-0 bg-brand-forest/20 border-x border-brand-forest/40 z-0"
              style={{
                left: `${jdMinPct}%`,
                width: `${Math.max(5, jdMaxPct - jdMinPct)}%`,
              }}
              title={`JD Target: ${jdMinExp}${jdMaxExp ? `–${jdMaxExp}` : "+"} years`}
            />
          )}

          {/* Candidate Total Experience */}
          <div
            className="absolute top-1 bottom-1 bg-brand-sage-soft rounded-lg opacity-70 z-10 transition-all duration-700"
            style={{ left: 0, width: `${totalPct}%` }}
            title={`Total Experience: ${totalExp.toFixed(1)} years`}
          />

          {/* Candidate Relevant Experience */}
          <div
            className="absolute top-1 bottom-1 bg-band-strong rounded-lg z-20 transition-all duration-700"
            style={{ left: 0, width: `${relPct}%` }}
            title={`Relevant Experience: ${relevantExp.toFixed(1)} years`}
          />
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center justify-between gap-3 text-xs pt-1">
          <div className="flex items-center gap-4 flex-wrap">
            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-band-strong inline-block" />
              <strong className="text-brand-ink font-mono tabular-nums">{relevantExp.toFixed(1)} yrs</strong>{" "}
              <span className="text-brand-muted">Relevant Domain</span>
            </span>

            <span className="flex items-center gap-1.5">
              <span className="w-3 h-3 rounded bg-brand-sage-soft inline-block" />
              <strong className="text-brand-ink font-mono tabular-nums">{totalExp.toFixed(1)} yrs</strong>{" "}
              <span className="text-brand-muted">Total Career</span>
            </span>

            {jdMinExp && (
              <span className="flex items-center gap-1.5">
                <span className="w-3 h-3 rounded bg-brand-forest/20 border border-brand-forest inline-block" />
                <span className="text-brand-forest font-medium">
                  Target: {jdMinExp}{jdMaxExp ? `–${jdMaxExp}` : "+"} yrs
                </span>
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Chronological Work History List */}
      <div className="space-y-3">
        <h4 className="font-serif text-sm font-bold text-brand-ink">
          Extracted Career Timeline ({experienceEntries.length} roles)
        </h4>

        {experienceEntries.length === 0 ? (
          <p className="text-xs text-brand-muted italic bg-brand-ivory/50 p-4 rounded-2xl border border-brand-line">
            No chronological work experience entries detected.
          </p>
        ) : (
          <div className="space-y-3">
            {experienceEntries.map((exp, idx) => {
              const isRel = exp.is_relevant;
              const title = exp.job_title || exp.title || "Position Title Not Specified";
              const company = exp.company || "Company Not Listed";
              const dur = exp.duration_years || exp.duration_months ? `${((exp.duration_years || 0) + (exp.duration_months || 0) / 12).toFixed(1)} yrs` : "Duration unverified";
              const skillsInEntry = exp.skills_in_entry || [];

              return (
                <div
                  key={idx}
                  className={`p-4 rounded-2xl border transition-all ${
                    isRel
                      ? "bg-brand-paper border-band-strong/40"
                      : "bg-brand-ivory/40 border-brand-line opacity-85"
                  }`}
                >
                  <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-2">
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h5 className="font-serif font-bold text-sm text-brand-ink">
                          {title}
                        </h5>
                        <Badge
                          variant={isRel ? "strong" : "neutral"}
                          size="sm"
                          dot={isRel}
                        >
                          {isRel ? "Relevant Domain" : "General Experience"}
                        </Badge>
                      </div>
                      <p className="text-xs text-brand-muted mt-0.5">
                        <strong className="text-brand-ink/90 font-medium">{company}</strong>
                        {exp.start_date && (
                          <span className="font-mono">
                            {" "}· {exp.start_date} – {exp.end_date || "Present"}
                          </span>
                        )}
                      </p>
                    </div>
                    <span className="font-mono text-xs font-semibold tabular-nums text-brand-forest shrink-0">
                      {dur}
                    </span>
                  </div>

                  {/* Bullet description if present */}
                  {exp.description && (
                    <p className="text-xs text-brand-muted line-clamp-3 mb-2.5 leading-relaxed bg-brand-ivory/60 p-2.5 rounded-xl border border-brand-line/60">
                      {exp.description}
                    </p>
                  )}

                  {/* Skills tagged in this role */}
                  {skillsInEntry.length > 0 && (
                    <div className="flex flex-wrap items-center gap-1 pt-1">
                      <span className="text-[10px] font-sans font-semibold uppercase tracking-wider text-brand-muted mr-1">
                        Domain Skills:
                      </span>
                      {skillsInEntry.map((sk) => (
                        <Chip key={sk} variant="extra" size="sm">
                          {sk}
                        </Chip>
                      ))}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </Card>
  );
}
