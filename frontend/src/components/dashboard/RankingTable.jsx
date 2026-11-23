import React from "react";
import { useNavigate } from "react-router-dom";
import Badge from "../ui/Badge";
import Chip from "../ui/Chip";
import ScoreBar from "../ui/ScoreBar";
import EmptyState from "../ui/EmptyState";
import Skeleton from "../ui/Skeleton";
import Card from "../ui/Card";

export default function RankingTable({
  results = [],
  runId,
  loading = false,
  sortBy = "rank",
  order = "asc",
  onSortChange,
  onResetFilters,
}) {
  const navigate = useNavigate();

  const handleRowClick = (candidateId) => {
    navigate(`/candidate/${candidateId}?run=${runId}`);
  };

  const getSortIcon = (field) => {
    if (sortBy !== field) {
      return (
        <span className="text-brand-muted/50 ml-1 text-[10px]">▲▼</span>
      );
    }
    return order === "asc" ? (
      <span className="text-brand-forest ml-1 text-[11px]">▲</span>
    ) : (
      <span className="text-brand-forest ml-1 text-[11px]">▼</span>
    );
  };

  const handleHeaderSort = (field) => {
    if (sortBy === field) {
      onSortChange(field, order === "asc" ? "desc" : "asc");
    } else {
      onSortChange(field, field === "score" || field === "experience" ? "desc" : "asc");
    }
  };

  // Loading Skeletons
  if (loading) {
    return (
      <Card padding="p-6" className="space-y-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex items-center justify-between gap-4 py-3 border-b border-brand-line last:border-0">
            <div className="flex items-center gap-3 w-1/4">
              <Skeleton variant="circular" width="32px" height="32px" />
              <div className="space-y-1.5 flex-1">
                <Skeleton variant="text" width="75%" />
                <Skeleton variant="text" width="50%" />
              </div>
            </div>
            <Skeleton variant="rectangular" width="80px" height="20px" />
            <Skeleton variant="rectangular" width="120px" height="12px" />
            <Skeleton variant="rectangular" width="180px" height="24px" />
            <Skeleton variant="rectangular" width="60px" height="20px" />
          </div>
        ))}
      </Card>
    );
  }

  // Empty State
  if (!results || results.length === 0) {
    return (
      <EmptyState
        title="No Matching Candidates Found"
        description="No candidates matched your filter criteria or search query. Try adjusting the score threshold, experience filter, or selected band."
        actionLabel="Reset All Filters"
        onAction={onResetFilters}
      />
    );
  }

  return (
    <div className="space-y-4">
      {/* ── Desktop & Tablet View (Wide Table) ── */}
      <div className="hidden md:block bg-brand-paper border border-brand-line rounded-3xl overflow-hidden shadow-soft">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-brand-ink">
            <thead className="bg-brand-ivory/70 text-brand-muted uppercase font-sans font-semibold text-[11px] tracking-wider border-b border-brand-line select-none">
              <tr>
                {/* 1. Candidate */}
                <th
                  onClick={() => handleHeaderSort("name")}
                  className="py-3.5 px-4 cursor-pointer hover:text-brand-ink transition"
                >
                  Candidate {getSortIcon("name")}
                </th>

                {/* 2. Experience */}
                <th
                  onClick={() => handleHeaderSort("experience")}
                  className="py-3.5 px-4 cursor-pointer hover:text-brand-ink transition"
                >
                  Experience {getSortIcon("experience")}
                </th>

                {/* 3. Match % */}
                <th
                  onClick={() => handleHeaderSort("score")}
                  className="py-3.5 px-4 cursor-pointer hover:text-brand-ink transition min-w-[170px]"
                >
                  Match % {getSortIcon("score")}
                </th>

                {/* 4. Matched Skills */}
                <th className="py-3.5 px-4">
                  Matched Skills
                </th>

                {/* 5. Rank */}
                <th
                  onClick={() => handleHeaderSort("rank")}
                  className="py-3.5 px-3 cursor-pointer hover:text-brand-ink transition text-center"
                >
                  Rank {getSortIcon("rank")}
                </th>

                {/* 6. Band */}
                <th className="py-3.5 px-3 text-center">
                  Band
                </th>

                {/* 7. Missing Required */}
                <th className="py-3.5 px-3 text-center">
                  Missing Req.
                </th>

                {/* 8. Knockout */}
                <th className="py-3.5 px-3 text-center">
                  Knockout
                </th>
              </tr>
            </thead>

            <tbody className="divide-y divide-brand-line">
              {results.map((row) => {
                const totalExp = row.total_experience_years || 0;
                const relExp = row.relevant_experience_years !== undefined ? row.relevant_experience_years : totalExp;
                const topSkills = row.matched_top_skills || [];
                const missingCount = row.missing_required_count || 0;
                const missingSkills = row.missing_required_skills || [];

                return (
                  <tr
                    key={row.candidate_id}
                    onClick={() => handleRowClick(row.candidate_id)}
                    className="hover:bg-brand-sage-soft/15 cursor-pointer transition-colors group"
                  >
                    {/* 1. Candidate: Name + email */}
                    <td className="py-3.5 px-4">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-brand-forest/10 text-brand-forest font-serif font-bold text-xs flex items-center justify-center border border-brand-line group-hover:scale-105 transition-transform">
                          {(row.name || "?").charAt(0).toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="font-serif font-bold text-brand-ink text-sm group-hover:text-brand-forest transition-colors truncate">
                            {row.name || "Unknown Candidate"}
                          </p>
                          <p className="text-xs text-brand-muted truncate font-mono">
                            {row.email || "No email"}
                          </p>
                        </div>
                      </div>
                    </td>

                    {/* 2. Experience */}
                    <td className="py-3.5 px-4 whitespace-nowrap">
                      <span className="font-mono font-semibold tabular-nums text-brand-ink">
                        {totalExp.toFixed(1)} yrs
                      </span>{" "}
                      <span className="text-[11px] font-mono tabular-nums text-brand-forest font-medium">
                        ({relExp.toFixed(1)} rel)
                      </span>
                    </td>

                    {/* 3. Match % Progress Bar */}
                    <td className="py-3.5 px-4 whitespace-nowrap min-w-[170px]">
                      <ScoreBar
                        value={row.final_score}
                        band={row.band}
                        showValue={true}
                        height="h-2"
                      />
                    </td>

                    {/* 4. Matched Skills (up to 5 chips + +N more badge) */}
                    <td className="py-3.5 px-4">
                      <div className="flex flex-wrap items-center gap-1 max-w-[280px]">
                        {topSkills.slice(0, 5).map((sk) => (
                          <Chip key={sk} variant="matched" size="sm">
                            {sk}
                          </Chip>
                        ))}
                        {topSkills.length > 5 && (
                          <span
                            className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-brand-ivory text-brand-muted border border-brand-line cursor-help"
                            title={topSkills.slice(5).join(", ")}
                          >
                            +{topSkills.length - 5}
                          </span>
                        )}
                        {topSkills.length === 0 && (
                          <span className="text-xs text-brand-muted italic">None matched</span>
                        )}
                      </div>
                    </td>

                    {/* 5. Rank */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      <span className="font-display text-lg text-brand-sage-deep">
                        #{row.original_rank || row.rank}
                      </span>
                    </td>

                    {/* 6. Band badge */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      <Badge band={row.band} size="sm" />
                    </td>

                    {/* 7. Missing Required */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      {missingCount > 0 ? (
                        <span
                          className="px-2.5 py-0.5 rounded-full text-xs font-mono font-semibold bg-band-weak/10 text-band-weak border border-band-weak/25 cursor-help"
                          title={missingSkills.length > 0 ? `Missing: ${missingSkills.join(", ")}` : "Missing required skills"}
                        >
                          {missingCount} missing
                        </span>
                      ) : (
                        <span className="text-xs text-band-strong font-semibold">✓ All met</span>
                      )}
                    </td>

                    {/* 8. Knockout */}
                    <td className="py-3.5 px-3 text-center whitespace-nowrap">
                      {row.is_knockout ? (
                        <Badge
                          variant="knockout"
                          size="sm"
                          dot={false}
                          title={row.knockout_reason || "Candidate disqualified by safety rules"}
                        >
                          ⚠️ Knockout
                        </Badge>
                      ) : (
                        <span className="text-brand-muted/40 text-xs">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* ── Mobile View (< md breakpoint cards) ── */}
      <div className="md:hidden space-y-3">
        {results.map((row) => {
          const totalExp = row.total_experience_years || 0;
          const relExp = row.relevant_experience_years !== undefined ? row.relevant_experience_years : totalExp;
          const topSkills = row.matched_top_skills || [];

          return (
            <Card
              key={row.candidate_id}
              padding="p-5"
              onClick={() => handleRowClick(row.candidate_id)}
              className="hover:border-brand-forest/50 transition cursor-pointer space-y-3"
            >
              {/* Header: Rank + Name + Band */}
              <div className="flex items-start justify-between gap-2">
                <div className="flex items-center gap-2.5">
                  <span className="font-display text-xl text-brand-sage-deep">
                    #{row.original_rank || row.rank}
                  </span>
                  <div>
                    <h4 className="font-serif font-bold text-brand-ink text-base leading-tight">
                      {row.name || "Unknown Candidate"}
                    </h4>
                    <p className="text-xs text-brand-muted font-mono">{row.email}</p>
                  </div>
                </div>
                <Badge band={row.band} size="sm" />
              </div>

              {/* Score & Experience Bar */}
              <div className="bg-brand-ivory/50 p-3.5 rounded-2xl border border-brand-line space-y-2">
                <ScoreBar
                  value={row.final_score}
                  band={row.band}
                  label="Composite Score:"
                  showValue={true}
                />
                <div className="flex items-center justify-between text-xs text-brand-ink pt-1 border-t border-brand-line/60">
                  <span className="text-brand-muted">Experience:</span>
                  <span className="font-mono font-semibold tabular-nums">
                    {totalExp.toFixed(1)} yrs <span className="text-brand-forest">({relExp.toFixed(1)} rel)</span>
                  </span>
                </div>
              </div>

              {/* Matched Skills */}
              {topSkills.length > 0 && (
                <div className="space-y-1.5">
                  <p className="text-[10px] font-sans font-semibold text-brand-muted uppercase tracking-wider">
                    Top Matched Skills:
                  </p>
                  <div className="flex flex-wrap gap-1">
                    {topSkills.slice(0, 5).map((sk) => (
                      <Chip key={sk} variant="matched" size="sm">
                        {sk}
                      </Chip>
                    ))}
                    {topSkills.length > 5 && (
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-brand-ivory text-brand-muted border border-brand-line">
                        +{topSkills.length - 5}
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Knockout banner if any */}
              {row.is_knockout && (
                <div className="bg-band-weak/10 border border-band-weak/30 rounded-xl p-2.5 text-xs text-band-weak flex items-center gap-2">
                  <span>⚠️</span>
                  <span>Knockout: {row.knockout_reason || "Disqualified"}</span>
                </div>
              )}
            </Card>
          );
        })}
      </div>
    </div>
  );
}
