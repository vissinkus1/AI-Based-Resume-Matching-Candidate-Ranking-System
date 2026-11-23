import React from "react";
import { getExportCsvUrl } from "../../api/match";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Eyebrow from "../ui/Eyebrow";

export default function DashboardHeader({
  run,
  onReRun,
  reRunning = false,
}) {
  if (!run) return null;

  const runDate = run.created_at
    ? new Date(run.created_at).toLocaleString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "Recently";

  const exportUrl = getExportCsvUrl(run.id);

  return (
    <div className="space-y-4 mb-6">
      {/* Top Banner if Stale */}
      {run.is_stale && (
        <div className="bg-band-partial/15 border border-band-partial/40 rounded-2xl p-4 sm:p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 text-brand-ink">
          <div className="flex items-start gap-3">
            <span className="text-xl shrink-0 mt-0.5">⚠️</span>
            <div className="space-y-0.5">
              <p className="font-serif font-bold text-sm text-brand-ink">
                Stale Results Warning: {run.stale_reason || "Specification or candidate pool updated"}
              </p>
              <p className="text-xs text-brand-muted">
                The job description or candidate pool was modified since this run was calculated. Re-run matching to synchronize scores.
              </p>
            </div>
          </div>
          <Button
            variant="outlined"
            size="sm"
            onClick={onReRun}
            disabled={reRunning}
            loading={reRunning}
            className="shrink-0"
          >
            ⚡ Re-run Now
          </Button>
        </div>
      )}

      {/* Main Header Card */}
      <Card padding="p-6 sm:p-8" className="bg-brand-paper">
        <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5 flex-wrap">
              <Eyebrow>RUN #{run.id}</Eyebrow>
              <span className="text-brand-line">•</span>
              <span className="text-xs text-brand-muted font-mono">{runDate}</span>
              <span className="text-brand-line">•</span>
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-mono bg-brand-sage-soft/30 text-brand-ink border border-brand-line">
                all-MiniLM-L6-v2
              </span>
              {run.duration_ms && (
                <span className="text-xs text-brand-muted font-mono">
                  ({run.duration_ms} ms)
                </span>
              )}
            </div>

            <h1 className="font-display uppercase text-4xl sm:text-5xl lg:text-6xl text-brand-sage-deep tracking-tight leading-none">
              RANKING MATRIX
            </h1>

            <p className="font-serif text-lg sm:text-xl font-bold text-brand-ink mt-1">
              {run.jd_title || "Job Description Match"}
            </p>
            <p className="text-xs sm:text-sm text-brand-muted">
              Evaluated {run.candidate_count} {run.candidate_count === 1 ? "candidate" : "candidates"} across 5 explainable matching dimensions.
            </p>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 shrink-0 flex-wrap">
            <a
              href={exportUrl}
              download={`match_run_${run.id}_ranking.csv`}
              className="inline-flex items-center justify-center font-sans font-medium transition-all duration-150 select-none min-h-[40px] text-xs px-4 py-2 gap-1.5 rounded-full border border-brand-forest text-brand-forest hover:bg-brand-forest hover:text-brand-ivory active:scale-[0.99]"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <span>Export CSV</span>
            </a>

            <Button
              variant="primary"
              size="md"
              onClick={onReRun}
              disabled={reRunning}
              loading={reRunning}
            >
              <span>⚡</span>
              <span>Re-run Evaluation</span>
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}
