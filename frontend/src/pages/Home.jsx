/*
 * pages/Home.jsx — Upload page (JD + resumes).
 *
 * Phase 0: placeholder UI that calls GET /health on mount and shows
 * the backend connection status.  Upload forms will be added in Phases 1–2.
 */

import { useState, useEffect } from "react";
import API from "../api/client";

function Home() {
  // Backend status: null = loading, object = response, string = error
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    API.get("/health")
      .then((res) => {
        setHealthStatus(res.data);
        setLoading(false);
      })
      .catch((err) => {
        setHealthStatus(
          err.response?.data || { status: "unreachable", api: false, database: false }
        );
        setLoading(false);
      });
  }, []);

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Upload Job Description & Resumes
      </h1>

      {/* ── Backend status card ── */}
      <div className="bg-white rounded-lg shadow p-6 mb-8 max-w-md">
        <h2 className="text-lg font-semibold text-gray-700 mb-3">
          Backend Status
        </h2>

        {loading ? (
          <p className="text-gray-500 animate-pulse">Connecting to backend…</p>
        ) : (
          <div className="space-y-2">
            {/* API status */}
            <StatusRow
              label="API"
              ok={healthStatus?.api}
            />
            {/* Database status */}
            <StatusRow
              label="Database"
              ok={healthStatus?.database}
              error={healthStatus?.database_error}
            />
            {/* Overall */}
            <div className="pt-2 border-t">
              <span
                className={`inline-block px-3 py-1 rounded-full text-sm font-medium ${
                  healthStatus?.status === "healthy"
                    ? "bg-green-100 text-green-800"
                    : "bg-red-100 text-red-800"
                }`}
              >
                {healthStatus?.status === "healthy"
                  ? "✅ All systems operational"
                  : "❌ Backend unhealthy"}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* ── Placeholder for upload forms (Phases 1–2) ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <PlaceholderCard
          title="Job Description"
          description="Paste text or upload a PDF/DOCX/TXT file containing the job description."
        />
        <PlaceholderCard
          title="Resumes"
          description="Upload a batch of candidate resumes (PDF/DOCX). Minimum 10 files supported."
        />
      </div>
    </div>
  );
}

/* ── Helper components ── */

/** Single status row with a green/red dot. */
function StatusRow({ label, ok, error }) {
  return (
    <div className="flex items-center gap-2">
      <span
        className={`h-3 w-3 rounded-full ${ok ? "bg-green-500" : "bg-red-500"}`}
      />
      <span className="text-gray-700 font-medium">{label}:</span>
      <span className={ok ? "text-green-700" : "text-red-700"}>
        {ok ? "Connected" : error || "Disconnected"}
      </span>
    </div>
  );
}

/** Grey placeholder card for future upload forms. */
function PlaceholderCard({ title, description }) {
  return (
    <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
      <h3 className="text-lg font-semibold text-gray-600 mb-2">{title}</h3>
      <p className="text-gray-400 text-sm">{description}</p>
      <p className="text-gray-300 text-xs mt-4 italic">Coming in next phase</p>
    </div>
  );
}

export default Home;
