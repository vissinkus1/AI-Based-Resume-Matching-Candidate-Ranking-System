import React, { useState, useEffect } from "react";

export default function ControlsBar({
  search = "",
  onSearchChange,
  band = "",
  onBandChange,
  minScore = 0,
  onMinScoreChange,
  minExperience = 0,
  onMinExperienceChange,
  skill = "",
  onSkillChange,
  availableSkills = [],
  onResetFilters,
  hasActiveFilters = false,
  filteredCount = 0,
  totalCount = 0,
}) {
  const [searchInput, setSearchInput] = useState(search);

  // Sync internal search input when search prop changes externally (e.g. url reset)
  useEffect(() => {
    setSearchInput(search);
  }, [search]);

  // Debounce search input by 300ms
  useEffect(() => {
    const handler = setTimeout(() => {
      if (searchInput !== search) {
        onSearchChange(searchInput);
      }
    }, 300);
    return () => clearTimeout(handler);
  }, [searchInput, search, onSearchChange]);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-4 shadow-lg mb-6">
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        {/* Top / Left: Search & Filters */}
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search Box */}
          <div className="relative min-w-[220px] flex-1 sm:flex-initial">
            <span className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-500">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search candidate name or email..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-9 pr-8 py-2 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition"
            />
            {searchInput && (
              <button
                onClick={() => {
                  setSearchInput("");
                  onSearchChange("");
                }}
                className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-400 hover:text-white"
              >
                ✕
              </button>
            )}
          </div>

          {/* Band Dropdown */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-400 whitespace-nowrap">Band:</label>
            <select
              value={band}
              onChange={(e) => onBandChange(e.target.value)}
              className="py-2 px-3 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 transition"
            >
              <option value="">All Bands</option>
              <option value="strong">Strong (≥ 80%)</option>
              <option value="good">Good (65–79%)</option>
              <option value="partial">Partial (50–64%)</option>
              <option value="weak">Weak (&lt; 50%)</option>
            </select>
          </div>

          {/* Skill Filter Dropdown */}
          {availableSkills && availableSkills.length > 0 && (
            <div className="flex items-center gap-1.5">
              <label className="text-xs text-slate-400 whitespace-nowrap">Skill:</label>
              <select
                value={skill}
                onChange={(e) => onSkillChange(e.target.value)}
                className="py-2 px-3 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 transition max-w-[170px] truncate"
              >
                <option value="">All Skills</option>
                {availableSkills.map((sk) => (
                  <option key={sk} value={sk}>
                    {sk}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Min Experience Input */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-slate-400 whitespace-nowrap">Min Exp:</label>
            <input
              type="number"
              min="0"
              max="30"
              step="0.5"
              value={minExperience > 0 ? minExperience : ""}
              placeholder="0 yrs"
              onChange={(e) => onMinExperienceChange(parseFloat(e.target.value) || 0)}
              className="w-20 py-2 px-2.5 bg-slate-950 border border-slate-700 rounded-xl text-xs text-white focus:outline-none focus:border-indigo-500 transition"
            />
          </div>

          {/* Min Score Slider */}
          <div className="flex items-center gap-2 bg-slate-950/70 border border-slate-800 px-3 py-1.5 rounded-xl">
            <label className="text-xs text-slate-400 whitespace-nowrap">Min Score:</label>
            <input
              type="range"
              min="0"
              max="95"
              step="5"
              value={minScore}
              onChange={(e) => onMinScoreChange(parseInt(e.target.value, 10))}
              className="w-20 sm:w-24 accent-indigo-500 cursor-pointer"
            />
            <span className="text-xs font-mono font-bold text-indigo-400 min-w-[32px]">
              {minScore}%
            </span>
          </div>

          {/* Reset Filters Button */}
          {hasActiveFilters && (
            <button
              onClick={onResetFilters}
              className="px-3 py-2 bg-rose-500/10 hover:bg-rose-500/20 text-rose-300 border border-rose-500/30 text-xs font-medium rounded-xl transition flex items-center gap-1"
            >
              <span>✕</span> Reset
            </button>
          )}
        </div>

        {/* Right: Showing Counter */}
        <div className="flex items-center justify-end gap-2 text-xs text-slate-400 border-t lg:border-t-0 pt-2 lg:pt-0">
          <span>Showing</span>
          <span className="font-bold text-white bg-slate-800 px-2.5 py-0.5 rounded-md border border-slate-700">
            {filteredCount} of {totalCount}
          </span>
          <span>candidates</span>
        </div>
      </div>
    </div>
  );
}
