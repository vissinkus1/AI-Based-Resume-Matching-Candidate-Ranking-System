import React from "react";

export default function Eyebrow({
  children,
  className = "",
  as: Component = "span",
  ...props
}) {
  return (
    <Component
      className={`block font-sans text-[11px] font-semibold uppercase tracking-eyebrow text-brand-muted ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}
