import React from "react";

export default function SemanticEvidenceCard({
  semanticBreakdown = {},
}) {
  const evidenceList = semanticBreakdown.evidence || semanticBreakdown.top_evidence || [];
  const score = semanticBreakdown.score !== undefined ? semanticBreakdown.score : 0;
  const docSim = semanticBreakdown.doc_similarity !== undefined ? semanticBreakdown.doc_similarity : 0;
  const coverageScore = semanticBreakdown.coverage_score !== undefined ? semanticBreakdown.coverage_score : 0;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl mb-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
        <div>
          <h3 className="text-lg font-bold text-white flex items-center gap-2">
            <span>🔬</span> Semantic Relevance & Sentence Alignment
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Embeddings with all-MiniLM-L6-v2 mapping JD duty sentences to candidate resume evidence.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs text-slate-400 block">Semantic Score:</span>
            <span className="text-base font-black text-teal-400">
              {typeof score === "number" ? score.toFixed(1) : score}/100
            </span>
          </div>
        </div>
      </div>

      {/* Metric pills */}
      <div className="grid grid-cols-2 sm:grid-cols-2 gap-3 mb-5">
        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Requirement Duty Coverage (60% weight)
          </span>
          <p className="text-base font-black text-white mt-0.5">
            {typeof coverageScore === "number" ? coverageScore.toFixed(1) : coverageScore}%
          </p>
        </div>

        <div className="bg-slate-950 p-3 rounded-xl border border-slate-800">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider block">
            Whole-Document Similarity (40% weight)
          </span>
          <p className="text-base font-black text-white mt-0.5">
            {typeof docSim === "number" ? docSim.toFixed(1) : docSim}%
          </p>
        </div>
      </div>

      {/* Paired Evidence Cards */}
      <div className="space-y-3">
        <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
          Top Aligned Semantic Evidence Pairs ({evidenceList.length})
        </h4>

        {evidenceList && evidenceList.length > 0 ? (
          <div className="space-y-3">
            {evidenceList.map((pair, idx) => {
              const jdSentence = pair.jd_sentence || pair.jd_duty || "Target duty";
              const resumeSentence = pair.resume_sentence || pair.candidate_evidence || "Resume duty";
              const simPct = pair.similarity !== undefined ? (pair.similarity * 100).toFixed(1) : null;
              const isHigh = pair.similarity >= 0.65;

              return (
                <div
                  key={idx}
                  className="bg-slate-950/80 border border-slate-800 rounded-xl p-4 space-y-3 hover:border-slate-700 transition"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-semibold text-slate-400">Evidence Pair #{idx + 1}</span>
                    {simPct && (
                      <span
                        className={`px-2 py-0.5 rounded text-[11px] font-bold ${
                          isHigh
                            ? "bg-teal-500/15 text-teal-300 border border-teal-500/30"
                            : "bg-slate-800 text-slate-300 border border-slate-700"
                        }`}
                      >
                        Cosine: {simPct}%
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {/* JD requirement */}
                    <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800/80">
                      <span className="text-[10px] font-bold text-indigo-400 uppercase tracking-wider block mb-1">
                        🎯 Job Description Duty:
                      </span>
                      <p className="text-slate-300 italic">"{jdSentence}"</p>
                    </div>

                    {/* Candidate resume evidence */}
                    <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800/80">
                      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wider block mb-1">
                        📄 Candidate Resume Snippet:
                      </span>
                      <p className="text-slate-300 italic">"{resumeSentence}"</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-slate-500 italic">
            Semantic similarity computed holistically across candidate resume embeddings.
          </p>
        )}
      </div>
    </div>
  );
}
