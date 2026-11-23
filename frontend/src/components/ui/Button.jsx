import React from "react";

export default function Button({
  children,
  variant = "primary",
  size = "md",
  pill = true,
  loading = false,
  disabled = false,
  className = "",
  type = "button",
  onClick,
  ...props
}) {
  const baseClasses =
    "inline-flex items-center justify-center font-sans font-medium transition-all duration-150 select-none min-h-[40px] disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest focus-visible:ring-offset-2 focus-visible:ring-offset-brand-ivory";

  const sizeClasses = {
    sm: "text-xs px-3.5 py-1.5 gap-1.5",
    md: "text-sm px-5 py-2.5 gap-2",
    lg: "text-base px-6 py-3 gap-2.5",
  };

  const roundedClasses = pill ? "rounded-full" : "rounded-2xl";

  const variantClasses = {
    primary:
      "bg-brand-forest text-brand-ivory hover:bg-brand-forest/90 active:scale-[0.99] shadow-soft font-semibold",
    secondary:
      "border border-brand-line bg-brand-paper/90 text-brand-forest hover:bg-brand-sage-soft/40 hover:border-brand-forest/60 active:scale-[0.99]",
    outlined:
      "border border-brand-forest text-brand-forest hover:bg-brand-forest hover:text-brand-ivory active:scale-[0.99]",
    ghost:
      "text-brand-forest hover:bg-brand-sage-soft/30 active:bg-brand-sage-soft/50",
    danger:
      "border border-band-weak/40 bg-band-weak/10 text-band-weak hover:bg-band-weak/20 active:scale-[0.99]",
  };

  return (
    <button
      type={type}
      disabled={disabled || loading}
      onClick={onClick}
      className={`${baseClasses} ${sizeClasses[size] || sizeClasses.md} ${roundedClasses} ${
        variantClasses[variant] || variantClasses.primary
      } ${className}`}
      {...props}
    >
      {loading && (
        <svg
          className="animate-spin -ml-1 mr-2 h-4 w-4 text-current"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            className="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            strokeWidth="3"
          />
          <path
            className="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
          />
        </svg>
      )}
      {children}
    </button>
  );
}
