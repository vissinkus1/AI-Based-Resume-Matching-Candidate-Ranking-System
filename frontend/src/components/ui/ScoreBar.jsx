import React from "react";

function getBandColor(score) {
  if (score >= 75) return "bg-band-strong";
  if (score >= 60) return "bg-band-good";
  if (score >= 45) return "bg-band-partial";
  return "bg-band-weak";
}

export default function ScoreBar({
  value = 0,
  max = 100,
  label,
  showValue = true,
  variant,
  height = "h-2",
  className = "",
}) {
  const percentage = Math.min(100, Math.max(0, Math.round((value / max) * 100)));
  const fillColor = variant || getBandColor(percentage);

  return (
    <div className={`w-full ${className}`}>
      {(label || showValue) && (
        <div className="flex items-center justify-between text-xs mb-1.5 gap-2">
          {label && (
            <span className="font-sans text-brand-ink/90 font-medium truncate">
              {label}
            </span>
          )}
          {showValue && (
            <span className="font-mono tabular-nums text-brand-ink font-semibold ml-auto shrink-0">
              {typeof value === "number" ? value.toFixed(1).replace(/\.0$/, "") : value}%
            </span>
          )}
        </div>
      )}
      <div
        role="progressbar"
        aria-valuenow={percentage}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-label={label || "Score"}
        className={`w-full ${height} bg-brand-sage-soft/40 rounded-full overflow-hidden p-0.5 border border-brand-line/40`}
      >
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${fillColor}`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}
