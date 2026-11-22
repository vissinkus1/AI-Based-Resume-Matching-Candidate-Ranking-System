/*
 * api/match.js — Client-side API functions for Matching and Ranking endpoints.
 */

import API from "./client";

/**
 * Execute AI matching and ranking for a JD against candidates.
 * POST /api/match/run
 */
export async function runMatch(jdId, candidateIds = null) {
  const payload = {
    jd_id: jdId,
    candidate_ids: candidateIds && candidateIds.length > 0 ? candidateIds : null,
  };
  const res = await API.post("/api/match/run", payload);
  return res.data;
}

/**
 * List historical match runs.
 * GET /api/match/runs
 */
export async function listRuns(jdId = null, limit = 50) {
  const params = { limit };
  if (jdId) {
    params.jd_id = jdId;
  }
  const res = await API.get("/api/match/runs", { params });
  return res.data;
}

/**
 * Get detailed metadata and distribution for a specific run.
 * GET /api/match/runs/{run_id}
 */
export async function getRun(runId) {
  const res = await API.get(`/api/match/runs/${runId}`);
  return res.data;
}

/**
 * Get paginated ranking results for a run with optional filtering/sorting.
 * GET /api/match/runs/{run_id}/results
 */
export async function getResults(runId, params = {}) {
  const res = await API.get(`/api/match/runs/${runId}/results`, { params });
  return res.data;
}

/**
 * Get full explainable detail for a single candidate within a run.
 * GET /api/match/runs/{run_id}/results/{candidate_id}
 */
export async function getCandidateResult(runId, candidateId) {
  const res = await API.get(`/api/match/runs/${runId}/results/${candidateId}`);
  return res.data;
}

/**
 * Return the direct URL for streaming CSV export of a match run.
 */
export function getExportCsvUrl(runId) {
  const baseURL = API.defaults.baseURL || "http://localhost:8000";
  return `${baseURL}/api/match/runs/${runId}/export.csv`;
}

/**
 * Get the latest match run, optionally filtered by jd_id.
 * GET /api/match/runs/latest
 */
export async function getLatestRun(jdId = null) {
  const params = jdId ? { jd_id: jdId } : {};
  const res = await API.get("/api/match/runs/latest", { params });
  return res.data;
}

/**
 * Delete a match run and its associated ranking results.
 * DELETE /api/match/runs/{run_id}
 */
export async function deleteRun(runId) {
  const res = await API.delete(`/api/match/runs/${runId}`);
  return res.data;
}

/**
 * Retrieve active algorithm scoring weights and thresholds.
 * GET /api/match/config
 */
export async function getScoringConfig() {
  const res = await API.get("/api/match/config");
  return res.data;
}
