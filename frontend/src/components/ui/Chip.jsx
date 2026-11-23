import React from "react";

export default function Chip({
  children,
  variant = "neutral",
  size = "md",
  icon,
  onRemove,
  className = "",
  title,
  ...props
}) {
  const sizeClasses = {
    sm: "text-[11px] px-2.5 py-0.5 gap-1",
    md: "text-xs px-3 py-1 gap-1.5",
    lg: "text-sm px-3.5 py-1.5 gap-2",
  };

  const variantClasses = {
    matched:
      "bg-band-strong/15 text-band-strong border border-band-strong/30 font-medium",
    partial:
      "bg-band-partial/15 text-band-partial border border-band-partial/30 font-medium",
    missing:
      "bg-band-weak/10 text-band-weak border border-band-weak/25 font-medium line-through opacity-85",
    preferred:
      "bg-band-good/15 text-band-good border border-band-good/30 font-medium",
    extra:
      "bg-brand-sage-soft/35 text-brand-ink border border-brand-line font-medium",
    neutral:
      "bg-brand-ivory text-brand-ink border border-brand-line font-medium",
    forest:
      "bg-brand-forest text-brand-ivory border border-transparent font-medium",
  };

  return (
    <span
      title={title}
      className={`inline-flex items-center rounded-full font-sans transition-colors duration-150 select-none ${
        sizeClasses[size] || sizeClasses.md
      } ${variantClasses[variant] || variantClasses.neutral} ${className}`}
      {...props}
    >
      {icon && <span className="shrink-0">{icon}</span>}
      <span className="truncate max-w-[240px]">{children}</span>
      {onRemove && (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onRemove();
          }}
          className="ml-0.5 -mr-1 p-0.5 rounded-full hover:bg-black/10 focus:outline-none cursor-pointer"
          aria-label="Remove"
        >
          <svg className="w-3 h-3" viewBox="0 0 12 12" fill="none" stroke="currentColor">
            <path d="M2.5 2.5L9.5 9.5M9.5 2.5L2.5 9.5" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
        </button>
      )}
    </span>
  );
}
