import React from "react";

export default function Badge({
  band,
  children,
  variant,
  size = "md",
  dot = true,
  className = "",
}) {
  // Normalize band input if provided
  let resolvedVariant = variant || "neutral";
  let label = children;

  if (band) {
    const b = String(band).toLowerCase();
    if (b.includes("strong")) {
      resolvedVariant = "strong";
      label = label || "Strong Match";
    } else if (b.includes("good")) {
      resolvedVariant = "good";
      label = label || "Good Match";
    } else if (b.includes("partial")) {
      resolvedVariant = "partial";
      label = label || "Partial Match";
    } else if (b.includes("weak")) {
      resolvedVariant = "weak";
      label = label || "Weak Match";
    }
  }

  const sizeClasses = {
    sm: "text-[11px] px-2 py-0.5 gap-1.5",
    md: "text-xs px-2.5 py-1 gap-1.5",
    lg: "text-sm px-3.5 py-1.5 gap-2",
  };

  const variantStyles = {
    strong: {
      wrap: "bg-band-strong/15 text-band-strong border border-band-strong/30",
      dot: "bg-band-strong",
    },
    good: {
      wrap: "bg-band-good/15 text-band-good border border-band-good/30",
      dot: "bg-band-good",
    },
    partial: {
      wrap: "bg-band-partial/15 text-band-partial border border-band-partial/30",
      dot: "bg-band-partial",
    },
    weak: {
      wrap: "bg-band-weak/15 text-band-weak border border-band-weak/30",
      dot: "bg-band-weak",
    },
    knockout: {
      wrap: "bg-band-weak/20 text-band-weak border border-band-weak/40 font-semibold",
      dot: "bg-band-weak",
    },
    neutral: {
      wrap: "bg-brand-sage-soft/30 text-brand-ink border border-brand-line",
      dot: "bg-brand-muted",
    },
    forest: {
      wrap: "bg-brand-forest text-brand-ivory border border-transparent",
      dot: "bg-brand-ivory",
    },
  };

  const style = variantStyles[resolvedVariant] || variantStyles.neutral;

  return (
    <span
      className={`inline-flex items-center rounded-full font-sans font-medium tracking-wide uppercase select-none ${
        sizeClasses[size] || sizeClasses.md
      } ${style.wrap} ${className}`}
    >
      {dot && (
        <span
          className={`w-1.5 h-1.5 rounded-full shrink-0 ${style.dot}`}
          aria-hidden="true"
        />
      )}
      <span>{label}</span>
    </span>
  );
}
