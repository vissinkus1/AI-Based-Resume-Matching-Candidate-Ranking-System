import React, { useState, useEffect } from "react";
import Card from "../ui/Card";
import Button from "../ui/Button";

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
    <Card padding="p-4 sm:p-5" className="bg-brand-paper mb-6">
      <div className="flex flex-col lg:flex-row items-stretch lg:items-center justify-between gap-4">
        {/* Top / Left: Search & Filters */}
        <div className="flex flex-wrap items-center gap-3 flex-1">
          {/* Search Box */}
          <div className="relative min-w-[220px] flex-1 sm:flex-initial">
            <span className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-brand-muted">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </span>
            <input
              type="text"
              placeholder="Search candidate or email..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              className="w-full pl-9 pr-8 py-2 bg-brand-ivory/60 border border-brand-line rounded-full text-xs text-brand-ink placeholder:text-brand-muted/70 focus:outline-none focus:border-brand-forest focus:ring-1 focus:ring-brand-forest transition"
            />
            {searchInput && (
              <button
                type="button"
                onClick={() => {
                  setSearchInput("");
                  onSearchChange("");
                }}
                className="absolute inset-y-0 right-0 pr-3 flex items-center text-brand-muted hover:text-brand-ink"
              >
                ✕
              </button>
            )}
          </div>

          {/* Band Dropdown */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-brand-muted uppercase font-sans font-semibold tracking-wider text-[10px]">
              Band:
            </label>
            <select
              value={band}
              onChange={(e) => onBandChange(e.target.value)}
              className="py-1.5 px-3 bg-brand-ivory/60 border border-brand-line rounded-full text-xs text-brand-ink focus:outline-none focus:border-brand-forest transition"
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
              <label className="text-xs text-brand-muted uppercase font-sans font-semibold tracking-wider text-[10px]">
                Skill:
              </label>
              <select
                value={skill}
                onChange={(e) => onSkillChange(e.target.value)}
                className="py-1.5 px-3 bg-brand-ivory/60 border border-brand-line rounded-full text-xs text-brand-ink focus:outline-none focus:border-brand-forest transition max-w-[170px] truncate"
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

          {/* Min Experience Dropdown */}
          <div className="flex items-center gap-1.5">
            <label className="text-xs text-brand-muted uppercase font-sans font-semibold tracking-wider text-[10px]">
              Min Exp:
            </label>
            <select
              value={minExperience}
              onChange={(e) => onMinExperienceChange(parseFloat(e.target.value))}
              className="py-1.5 px-3 bg-brand-ivory/60 border border-brand-line rounded-full text-xs text-brand-ink focus:outline-none focus:border-brand-forest transition"
            >
              <option value={0}>Any Experience</option>
              <option value={1}>1+ years</option>
              <option value={3}>3+ years</option>
              <option value={5}>5+ years</option>
              <option value={8}>8+ years</option>
            </select>
          </div>

          {/* Min Score Slider */}
          <div className="flex items-center gap-2 px-3 py-1 bg-brand-ivory/60 border border-brand-line rounded-full">
            <label className="text-xs text-brand-muted uppercase font-sans font-semibold tracking-wider text-[10px] whitespace-nowrap">
              Min Score:
            </label>
            <input
              type="range"
              min="0"
              max="90"
              step="5"
              value={minScore}
              onChange={(e) => onMinScoreChange(parseInt(e.target.value, 10))}
              className="w-20 accent-brand-forest cursor-pointer"
            />
            <span className="text-xs font-mono tabular-nums text-brand-ink font-semibold w-7 text-right">
              {minScore}%
            </span>
          </div>
        </div>

        {/* Right: Results Count & Reset Button */}
        <div className="flex items-center justify-between sm:justify-end gap-3 shrink-0 pt-2 lg:pt-0 border-t lg:border-t-0 border-brand-line">
          <span className="text-xs text-brand-muted font-sans font-medium">
            Showing <strong className="text-brand-ink font-mono tabular-nums">{filteredCount}</strong> of{" "}
            <span className="font-mono tabular-nums">{totalCount}</span>
          </span>

          {hasActiveFilters && (
            <Button
              variant="ghost"
              size="sm"
              onClick={onResetFilters}
              className="text-xs text-brand-forest hover:text-brand-forest/80 underline p-0 h-auto min-h-0"
            >
              Reset Filters
            </Button>
          )}
        </div>
      </div>
    </Card>
  );
}
