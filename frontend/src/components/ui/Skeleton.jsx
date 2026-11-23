import React from "react";

export default function Skeleton({
  className = "",
  variant = "rectangular",
  width,
  height,
}) {
  const variantClasses = {
    circular: "rounded-full",
    rectangular: "rounded-2xl",
    text: "rounded-md h-4",
  };

  const style = {};
  if (width) style.width = width;
  if (height) style.height = height;

  return (
    <div
      role="status"
      aria-label="Loading..."
      style={style}
      className={`animate-pulse bg-brand-sage-soft/35 ${variantClasses[variant] || variantClasses.rectangular} ${className}`}
    />
  );
}
