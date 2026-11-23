import React from "react";
import Navbar from "./Navbar";
import Divider from "./ui/Divider";

export default function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col bg-brand-ivory text-brand-ink antialiased selection:bg-brand-sage-soft selection:text-brand-ink">
      <Navbar />

      {/* Main page content */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8 sm:py-12">
        {children}
      </main>

      {/* Subtle editorial footer */}
      <footer className="w-full mt-auto border-t border-brand-line bg-brand-ivory/80 py-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs font-sans text-brand-muted">
          <div className="flex items-center gap-2">
            <span className="font-serif font-bold text-brand-ink tracking-tight">KANDIDAT</span>
            <span className="text-brand-line">•</span>
            <span>AI-Based Resume Matching &amp; Candidate Ranking Engine</span>
          </div>
          <div className="flex items-center gap-4 text-[11px] uppercase tracking-wider">
            <span>Explainable Scoring</span>
            <span className="text-brand-line">•</span>
            <span>Zero Hallucinations</span>
            <span className="text-brand-line">•</span>
            <span>Deterministic Auditing</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
