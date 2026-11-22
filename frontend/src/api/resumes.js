/**
 * api/resumes.js — Axios client methods for Candidate/Resume endpoints.
 */

import client from "./client";

/**
 * Upload a batch of resume files (PDF / DOCX).
 * @param {File[]} files - Array of File objects.
 * @param {Function} onProgress - Optional callback for upload progress (percent integer).
 * @returns {Promise<Object>} BatchUploadResponse data.
 */
export async function uploadResumes(files, onProgress) {
  const formData = new FormData();
  for (const file of files) {
    formData.append("files", file);
  }

  const response = await client.post("/api/resumes/upload", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
    onUploadProgress: (progressEvent) => {
      if (onProgress && progressEvent.total) {
        const percent = Math.round(
          (progressEvent.loaded * 100) / progressEvent.total
        );
        onProgress(percent);
      }
    },
  });
  return response.data;
}

/**
 * Fetch all candidates summary list.
 * @returns {Promise<Array>} List of CandidateListItem.
 */
export async function listCandidates() {
  const response = await client.get("/api/resumes");
  return response.data;
}

/**
 * Fetch detailed parsed candidate info by ID.
 * @param {number} candidateId
 * @returns {Promise<Object>} CandidateResponse.
 */
export async function getCandidate(candidateId) {
  const response = await client.get(`/api/resumes/${candidateId}`);
  return response.data;
}

/**
 * Delete a candidate by ID.
 * @param {number} candidateId
 * @returns {Promise<Object>}
 */
export async function deleteCandidate(candidateId) {
  const response = await client.delete(`/api/resumes/${candidateId}`);
  return response.data;
}

/**
 * Clear all candidates from the database.
 * @returns {Promise<Object>}
 */
export async function clearAllCandidates() {
  const response = await client.delete("/api/resumes");
  return response.data;
}
