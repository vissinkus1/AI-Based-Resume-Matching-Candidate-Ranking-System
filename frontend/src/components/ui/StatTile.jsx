import React from "react";

export default function StatTile({
  label,
  value,
  caption,
  icon,
  active = false,
  onClick,
  colorClass = "text-brand-sage",
  className = "",
}) {
  const isClickable = Boolean(onClick);

  return (
    <div
      role={isClickable ? "button" : undefined}
      tabIndex={isClickable ? 0 : undefined}
      onClick={onClick}
      onKeyDown={
        isClickable
          ? (e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      className={`bg-brand-paper border rounded-3xl p-5 sm:p-6 transition-all duration-200 select-none flex flex-col justify-between ${
        active
          ? "border-brand-forest ring-2 ring-brand-forest/20 shadow-md bg-brand-paper"
          : "border-brand-line shadow-soft"
      } ${
        isClickable
          ? "cursor-pointer hover:border-brand-forest/50 hover:shadow-md active:scale-[0.99]"
          : ""
      } ${className}`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="font-serif text-sm sm:text-base font-medium text-brand-ink leading-snug">
          {label}
        </h3>
        {icon && (
          <div className="text-brand-muted shrink-0 p-1 rounded-full bg-brand-sage-soft/20">
            {icon}
          </div>
        )}
      </div>

      <div className="w-8 h-[1px] bg-brand-line my-3" />

      <div>
        <div className={`font-display text-3xl sm:text-4xl font-normal tracking-tight ${colorClass}`}>
          {value}
        </div>
        {caption && (
          <p className="mt-1 font-sans text-[11px] font-semibold uppercase tracking-wider text-brand-muted truncate">
            {caption}
          </p>
        )}
      </div>
    </div>
  );
}
