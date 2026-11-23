import React from "react";
import Eyebrow from "./Eyebrow";

export default function SectionHeader({
  eyebrow,
  title,
  subtitle,
  actions,
  className = "",
  hasDivider = true,
}) {
  return (
    <div className={`space-y-1.5 ${hasDivider ? "border-b border-brand-line pb-4 mb-6" : "mb-4"} ${className}`}>
      <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
        <div>
          {eyebrow && <Eyebrow className="mb-1">{eyebrow}</Eyebrow>}
          <h2 className="font-serif text-xl sm:text-2xl font-bold text-brand-ink tracking-tight">
            {title}
          </h2>
          {subtitle && (
            <p className="text-xs sm:text-sm text-brand-muted mt-1 leading-relaxed">
              {subtitle}
            </p>
          )}
        </div>
        {actions && <div className="flex items-center gap-2 self-start sm:self-auto shrink-0">{actions}</div>}
      </div>
    </div>
  );
}
