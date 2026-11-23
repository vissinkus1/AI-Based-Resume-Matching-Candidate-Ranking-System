import React from "react";
import Button from "./Button";

export default function EmptyState({
  icon,
  title = "No results found",
  description = "Try adjusting your filters or search terms to find what you're looking for.",
  actionLabel,
  onAction,
  className = "",
}) {
  return (
    <div
      className={`bg-brand-paper border border-brand-line rounded-3xl p-8 sm:p-12 text-center flex flex-col items-center justify-center max-w-lg mx-auto ${className}`}
    >
      <div className="w-12 h-12 rounded-full bg-brand-sage-soft/30 flex items-center justify-center text-brand-forest mb-4 border border-brand-line">
        {icon || (
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="1.5"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        )}
      </div>

      <h3 className="font-serif text-lg sm:text-xl font-bold text-brand-ink mb-2">
        {title}
      </h3>

      <p className="text-xs sm:text-sm text-brand-muted max-w-sm mb-6 leading-relaxed">
        {description}
      </p>

      {actionLabel && onAction && (
        <Button variant="outlined" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
