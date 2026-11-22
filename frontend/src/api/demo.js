/*
 * api/demo.js — Client-side API functions for one-click demo seeding.
 */

import API from "./client";

/**
 * Seed demo dataset (JD + 12 resumes) and execute ranking in one click.
 * POST /api/demo/seed?jd={java|react|aiml}&reset=true
 */
export async function seedDemo(jdKey = "java", reset = true) {
  const res = await API.post("/api/demo/seed", null, {
    params: { jd: jdKey, reset },
  });
  return res.data;
}
