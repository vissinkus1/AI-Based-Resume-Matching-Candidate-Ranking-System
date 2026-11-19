/*
 * api/jd.js — API functions for Job Description endpoints.
 *
 * All JD-related API calls go through these functions so that
 * components don't import Axios directly.
 */

import API from "./client";

/**
 * Parse a JD from pasted text.
 * POST /api/jd/parse  (form-data with "text" field)
 */
export async function parseJDText(text) {
  const formData = new FormData();
  formData.append("text", text);
  const res = await API.post("/api/jd/parse", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

/**
 * Parse a JD from an uploaded file (PDF/DOCX/TXT).
 * POST /api/jd/parse  (form-data with "file" field)
 */
export async function parseJDFile(file) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await API.post("/api/jd/parse", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

/**
 * Get a single JD by ID.
 * GET /api/jd/{id}
 */
export async function getJD(id) {
  const res = await API.get(`/api/jd/${id}`);
  return res.data;
}

/**
 * List all saved JDs.
 * GET /api/jd
 */
export async function listJDs() {
  const res = await API.get("/api/jd");
  return res.data;
}

/**
 * Update a JD's parsed fields (after recruiter review).
 * PUT /api/jd/{id}
 */
export async function updateJD(id, updateData) {
  const res = await API.put(`/api/jd/${id}`, updateData);
  return res.data;
}

/**
 * Delete a JD by ID.
 * DELETE /api/jd/{id}
 */
export async function deleteJD(id) {
  const res = await API.delete(`/api/jd/${id}`);
  return res.data;
}
