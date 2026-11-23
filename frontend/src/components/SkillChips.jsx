import React, { useState } from "react";
import Chip from "./ui/Chip";
import Button from "./ui/Button";

export default function SkillChips({
  skills = [],
  onRemove,
  onAdd,
  onToggle,
  onToggleCategory,
  color,
  badgeColor,
  label = "Skills",
  toggleLabel = "Move category",
}) {
  const [newSkill, setNewSkill] = useState("");
  const handleToggle = onToggle || onToggleCategory;

  // Determine Chip variant
  const c = color || badgeColor;
  let variant = "neutral";
  if (c === "indigo" || c === "green" || label?.toLowerCase().includes("required")) {
    variant = "matched";
  } else if (c === "purple" || c === "yellow" || label?.toLowerCase().includes("preferred")) {
    variant = "preferred";
  }

  const handleAdd = () => {
    const trimmed = newSkill.trim();
    if (trimmed && !skills.includes(trimmed)) {
      if (onAdd) onAdd(trimmed);
      setNewSkill("");
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleAdd();
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {skills.map((skill) => (
          <div key={skill} className="inline-flex items-center gap-1 group">
            <Chip
              variant={variant}
              onRemove={onRemove ? () => onRemove(skill) : undefined}
            >
              {skill}
            </Chip>
            {handleToggle && (
              <button
                type="button"
                onClick={() => handleToggle(skill)}
                title={toggleLabel}
                aria-label={`Toggle category for ${skill}`}
                className="text-brand-muted hover:text-brand-forest hover:bg-brand-sage-soft/30 p-1 rounded-full text-xs transition-colors"
              >
                ⇄
              </button>
            )}
          </div>
        ))}
        {skills.length === 0 && (
          <span className="text-brand-muted text-xs italic py-1">
            No skills specified
          </span>
        )}
      </div>

      {/* Add new skill input */}
      {onAdd && (
        <div className="flex items-center gap-2 max-w-sm pt-1">
          <input
            type="text"
            value={newSkill}
            onChange={(e) => setNewSkill(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={`Add a skill...`}
            className="flex-1 px-3.5 py-1.5 text-xs bg-brand-paper border border-brand-line rounded-full text-brand-ink placeholder:text-brand-muted/70 focus:outline-none focus:ring-2 focus:ring-brand-forest/20 focus:border-brand-forest transition-all"
          />
          <Button
            variant="secondary"
            size="sm"
            onClick={handleAdd}
            disabled={!newSkill.trim()}
          >
            Add
          </Button>
        </div>
      )}
    </div>
  );
}
