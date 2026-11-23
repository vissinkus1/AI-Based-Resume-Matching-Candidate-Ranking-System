import React from "react";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import Eyebrow from "../ui/Eyebrow";

export default function CandidateHeroCard({
  candidate,
  finalScore = 0,
  band = "weak",
  isKnockout = false,
  knockoutReason = null,
  totalExp = 0,
  relExp = 0,
  jdTitle = null,
}) {
  const getBandStyles = (b) => {
    const val = (b || "").toLowerCase();
    if (val.includes("strong")) {
      return {
        strokeColor: "var(--color-band-strong, #3F7A4D)",
        textColor: "text-band-strong",
        label: "Strong Match",
      };
    }
    if (val.includes("good")) {
      return {
        strokeColor: "var(--color-band-good, #789575)",
        textColor: "text-band-good",
        label: "Good Match",
      };
    }
    if (val.includes("partial")) {
      return {
        strokeColor: "var(--color-band-partial, #C79A3B)",
        textColor: "text-band-partial",
        label: "Partial Match",
      };
    }
    return {
      strokeColor: "var(--color-band-weak, #B5654A)",
      textColor: "text-band-weak",
      label: "Weak Match",
    };
  };

  const bandStyle = getBandStyles(band);

  // Circular progress calculation
  const radius = 54;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset =
    circumference - (Math.min(100, Math.max(0, finalScore)) / 100) * circumference;

  const links = candidate?.links || {};

  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      {/* Knockout Banner */}
      {isKnockout && (
        <div className="mb-6 p-4 rounded-2xl bg-band-weak/10 border border-band-weak/30 text-band-weak flex items-start gap-3">
          <span className="text-2xl shrink-0">⚠️</span>
          <div>
            <h4 className="font-serif font-bold text-sm">Disqualification Knockout Triggered</h4>
            <p className="text-xs mt-0.5 opacity-90 leading-relaxed">
              {knockoutReason || "This candidate failed a non-negotiable safeguard rule (e.g. required skill deficit or insufficient domain experience)."}
            </p>
          </div>
        </div>
      )}

      <div className="flex flex-col lg:flex-row items-center lg:items-start justify-between gap-8">
        {/* Left: Candidate Identity & Info */}
        <div className="flex-1 text-center lg:text-left space-y-4">
          <div>
            <div className="flex flex-wrap items-center justify-center lg:justify-start gap-2.5 mb-2">
              <Badge band={band} size="sm" />
              {jdTitle && (
                <span className="text-xs text-brand-muted">
                  Evaluated for: <strong className="text-brand-ink font-serif">{jdTitle}</strong>
                </span>
              )}
            </div>

            <h1 className="font-serif text-3xl sm:text-4xl font-bold text-brand-ink tracking-tight">
              {candidate?.name || "Unknown Candidate"}
            </h1>
            {candidate?.summary && (
              <p className="text-xs sm:text-sm text-brand-muted mt-2 max-w-2xl leading-relaxed">
                {candidate.summary}
              </p>
            )}
          </div>

          {/* Contact Details */}
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-4 text-xs text-brand-muted">
            {candidate?.email && (
              <a
                href={`mailto:${candidate.email}`}
                className="flex items-center gap-1.5 hover:text-brand-forest transition font-mono"
              >
                <span>✉️</span>
                <span>{candidate.email}</span>
              </a>
            )}
            {candidate?.phone && (
              <span className="flex items-center gap-1.5 font-mono">
                <span>📞</span>
                <span>{candidate.phone}</span>
              </span>
            )}
            {candidate?.location && (
              <span className="flex items-center gap-1.5">
                <span>📍</span>
                <span>{candidate.location}</span>
              </span>
            )}
          </div>

          {/* Profile Links */}
          <div className="flex flex-wrap items-center justify-center lg:justify-start gap-3 pt-1">
            {links.github && (
              <a
                href={links.github.startsWith("http") ? links.github : `https://${links.github}`}
                target="_blank"
                rel="noreferrer"
                className="px-3.5 py-1.5 rounded-full bg-brand-ivory hover:bg-brand-sage-soft/30 text-brand-forest text-xs font-semibold border border-brand-line transition flex items-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                GitHub Profile
              </a>
            )}
            {links.linkedin && (
              <a
                href={links.linkedin.startsWith("http") ? links.linkedin : `https://${links.linkedin}`}
                target="_blank"
                rel="noreferrer"
                className="px-3.5 py-1.5 rounded-full bg-brand-ivory hover:bg-brand-sage-soft/30 text-brand-forest text-xs font-semibold border border-brand-line transition flex items-center gap-1.5"
              >
                <svg className="w-3.5 h-3.5 fill-current" viewBox="0 0 24 24">
                  <path d="M19 3a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14m-.5 15.5v-5.3a3.26 3.26 0 0 0-3.26-3.26c-.85 0-1.84.52-2.28 1.3v-1.11h-2.79v8.37h2.79v-4.93c0-.77.62-1.4 1.39-1.4a1.4 1.4 0 0 1 1.4 1.4v4.93h2.75M6.88 8.56a1.68 1.68 0 0 0 1.68-1.68c0-.93-.75-1.69-1.68-1.69a1.69 1.69 0 0 0-1.69 1.69c0 .93.76 1.68 1.69 1.68m1.39 9.94v-8.37H5.5v8.37h2.77z" />
                </svg>
                LinkedIn Profile
              </a>
            )}
          </div>

          {/* Experience highlight stats */}
          <div className="grid grid-cols-2 gap-3 pt-2 max-w-sm">
            <div className="bg-brand-ivory/60 p-3.5 rounded-2xl border border-brand-line">
              <Eyebrow>Total Career</Eyebrow>
              <p className="font-mono text-xl font-bold tabular-nums text-brand-ink mt-0.5">
                {totalExp.toFixed(1)} yrs
              </p>
            </div>
            <div className="bg-brand-ivory/60 p-3.5 rounded-2xl border border-brand-line">
              <Eyebrow>Relevant to JD</Eyebrow>
              <p className="font-mono text-xl font-bold tabular-nums text-brand-forest mt-0.5">
                {relExp.toFixed(1)} yrs
              </p>
            </div>
          </div>
        </div>

        {/* Right: Circular Score Gauge */}
        <div className="flex flex-col items-center justify-center p-6 bg-brand-ivory/50 rounded-3xl border border-brand-line min-w-[220px]">
          <div className="relative flex items-center justify-center">
            <svg className="w-36 h-36 transform -rotate-90">
              {/* Background track */}
              <circle
                cx="72"
                cy="72"
                r={radius}
                stroke="var(--color-sage-soft, #CBD5B4)"
                strokeWidth="10"
                fill="transparent"
                opacity="0.4"
              />
              {/* Foreground progress */}
              <circle
                cx="72"
                cy="72"
                r={radius}
                stroke={bandStyle.strokeColor}
                strokeWidth="10"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                fill="transparent"
                className="transition-all duration-1000 ease-out"
              />
            </svg>
            <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
              <span className="font-display text-4xl font-normal text-brand-ink tracking-tight">
                {finalScore.toFixed(1)}%
              </span>
              <span className="text-[10px] font-sans font-semibold uppercase tracking-wider text-brand-muted -mt-1">
                Overall Match
              </span>
            </div>
          </div>

          <p className="text-[11px] text-brand-muted mt-3 text-center max-w-[180px] leading-relaxed">
            Multi-factor composite score across 5 explainable dimensions
          </p>
        </div>
      </div>
    </Card>
  );
}
