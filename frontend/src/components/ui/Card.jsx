import React from "react";

export default function Card({
  children,
  className = "",
  padding = "p-6 sm:p-8",
  hover = false,
  as: Component = "div",
  ...props
}) {
  return (
    <Component
      className={`bg-brand-paper border border-brand-line rounded-3xl shadow-soft ${padding} ${
        hover ? "transition-all duration-200 hover:border-brand-forest/40 hover:shadow-md" : ""
      } ${className}`}
      {...props}
    >
      {children}
    </Component>
  );
}
