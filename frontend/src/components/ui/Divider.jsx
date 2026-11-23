import React from "react";

export default function Divider({
  className = "",
  vertical = false,
  ...props
}) {
  if (vertical) {
    return (
      <div
        role="separator"
        aria-orientation="vertical"
        className={`w-[1px] bg-brand-line self-stretch ${className}`}
        {...props}
      />
    );
  }

  return (
    <hr
      role="separator"
      className={`border-0 border-t border-brand-line w-full my-4 ${className}`}
      {...props}
    />
  );
}
