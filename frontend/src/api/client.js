/*
 * api/client.js — Axios instance pre-configured for the backend.
 *
 * Every API call in the app imports this instance instead of bare axios,
 * so the base URL and any future interceptors are defined in one place.
 */

import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8000", // FastAPI dev server
  timeout: 30000,                  // 30 s — generous for ML inference
  headers: {
    "Content-Type": "application/json",
  },
});

export default API;
