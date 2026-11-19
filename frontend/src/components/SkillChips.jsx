/*
 * components/SkillChips.jsx — Editable skill chip list.
 *
 * Shows skills as coloured chips. Each chip has a remove button.
 * An input field lets the recruiter add new skills.
 * A toggle button lets the recruiter flip required ↔ preferred.
 */

import { useState } from "react";

/**
 * @param {Object} props
 * @param {string[]} props.skills        — List of skill names.
 * @param {function} props.onRemove      — Called with the skill name to remove.
 * @param {function} props.onAdd         — Called with a new skill name string.
 * @param {function} [props.onToggle]    — Called with the skill name to toggle category.
 * @param {string}   props.color         — Tailwind colour: "green" or "yellow".
 * @param {string}   props.label         — Section label: "Required" or "Preferred".
 * @param {string}   [props.toggleLabel] — Label for toggle button: "→ Preferred" etc.
 */
export default function SkillChips({
  skills,
  onRemove,
  onAdd,
  onToggle,
  color = "green",
  label = "Skills",
  toggleLabel = "",
}) {
  const [newSkill, setNewSkill] = useState("");

  const bgMap = {
    green: "bg-green-100 text-green-800 border-green-300",
    yellow: "bg-yellow-100 text-yellow-800 border-yellow-300",
    blue: "bg-blue-100 text-blue-800 border-blue-300",
  };
  const chipClass = bgMap[color] || bgMap.green;

  const handleAdd = () => {
    const trimmed = newSkill.trim();
    if (trimmed && !skills.includes(trimmed)) {
      onAdd(trimmed);
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
    <div className="mb-4">
      <h4 className="text-sm font-semibold text-gray-600 mb-2">
        {label} ({skills.length})
      </h4>
      <div className="flex flex-wrap gap-2 mb-2">
        {skills.map((skill) => (
          <span
            key={skill}
            className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm border ${chipClass}`}
          >
            {skill}
            {/* Toggle button (move to other category) */}
            {onToggle && (
              <button
                onClick={() => onToggle(skill)}
                title={toggleLabel}
                className="ml-1 text-xs opacity-60 hover:opacity-100"
              >
                ⇄
              </button>
            )}
            {/* Remove button */}
            <button
              onClick={() => onRemove(skill)}
              className="ml-1 text-xs font-bold opacity-60 hover:opacity-100"
              title="Remove skill"
            >
              ×
            </button>
          </span>
        ))}
        {skills.length === 0 && (
          <span className="text-gray-400 text-sm italic">None detected</span>
        )}
      </div>
      {/* Add new skill input */}
      <div className="flex gap-2">
        <input
          type="text"
          value={newSkill}
          onChange={(e) => setNewSkill(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={`Add a ${label.toLowerCase()} skill…`}
          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-md text-sm
                     focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 outline-none"
        />
        <button
          onClick={handleAdd}
          disabled={!newSkill.trim()}
          className="px-3 py-1.5 bg-indigo-500 text-white text-sm rounded-md
                     hover:bg-indigo-600 disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Add
        </button>
      </div>
    </div>
  );
}
