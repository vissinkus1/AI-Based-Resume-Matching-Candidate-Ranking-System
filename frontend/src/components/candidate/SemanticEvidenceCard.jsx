import React from "react";
import Card from "../ui/Card";
import SectionHeader from "../ui/SectionHeader";
import Eyebrow from "../ui/Eyebrow";

export default function SemanticEvidenceCard({
  semanticBreakdown = {},
  score: propScore = null,
}) {
  const evidenceList = semanticBreakdown.evidence || semanticBreakdown.top_evidence || [];
  const coverageScore =
    semanticBreakdown.requirement_coverage_score !== undefined
      ? semanticBreakdown.requirement_coverage_score
      : semanticBreakdown.coverage_score !== undefined
      ? semanticBreakdown.coverage_score
      : 0;
  const docSim =
    semanticBreakdown.whole_doc_similarity_score !== undefined
      ? semanticBreakdown.whole_doc_similarity_score
      : semanticBreakdown.doc_similarity !== undefined
      ? semanticBreakdown.doc_similarity
      : 0;
  const score =
    propScore !== null && propScore !== undefined
      ? propScore
      : semanticBreakdown.score !== undefined
      ? semanticBreakdown.score
      : Math.round((coverageScore * 0.6 + docSim * 0.4) * 10) / 10;

  return (
    <Card padding="p-6 sm:p-8" className="bg-brand-paper mb-6">
      <SectionHeader
        eyebrow="SEMANTIC EMBEDDINGS"
        title="Semantic Relevance &amp; Sentence Alignment"
        subtitle="Dense vector embeddings using all-MiniLM-L6-v2 mapping JD duty sentences to candidate resume evidence."
        actions={
          <div className="text-right">
            <span className="text-xs text-brand-muted block font-sans">Semantic Score:</span>
            <span className="font-mono text-base font-bold tabular-nums text-brand-forest">
              {typeof score === "number" ? score.toFixed(1) : score}%
            </span>
          </div>
        }
      />

      {/* Metric pills */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-6">
        <div className="bg-brand-ivory/60 p-4 rounded-2xl border border-brand-line">
          <Eyebrow>Requirement Duty Coverage (60% weight)</Eyebrow>
          <p className="font-mono text-xl font-bold tabular-nums text-brand-forest mt-1">
            {typeof coverageScore === "number" ? coverageScore.toFixed(1) : coverageScore}%
          </p>
        </div>

        <div className="bg-brand-ivory/60 p-4 rounded-2xl border border-brand-line">
          <Eyebrow>Whole-Document Similarity (40% weight)</Eyebrow>
          <p className="font-mono text-xl font-bold tabular-nums text-brand-sage mt-1">
            {typeof docSim === "number" ? docSim.toFixed(1) : docSim}%
          </p>
        </div>
      </div>

      {/* Paired Evidence Cards */}
      <div className="space-y-3">
        <h4 className="font-serif text-sm font-bold text-brand-ink">
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
                  className="bg-brand-ivory/40 border border-brand-line rounded-2xl p-4 sm:p-5 space-y-3 hover:border-brand-forest/40 transition"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-serif font-bold text-brand-ink">Evidence Pair #{idx + 1}</span>
                    {simPct && (
                      <span
                        className={`px-2.5 py-0.5 rounded-full text-[11px] font-mono font-bold ${
                          isHigh
                            ? "bg-band-strong/15 text-band-strong border border-band-strong/30"
                            : "bg-brand-sage-soft/30 text-brand-ink border border-brand-line"
                        }`}
                      >
                        Cosine: {simPct}%
                      </span>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                    {/* JD requirement */}
                    <div className="bg-brand-paper p-3.5 rounded-xl border border-brand-line space-y-1">
                      <span className="text-[10px] font-sans font-semibold text-brand-forest uppercase tracking-wider block">
                        🎯 Target Job Duty:
                      </span>
                      <p className="text-brand-ink/90 italic leading-relaxed">"{jdSentence}"</p>
                    </div>

                    {/* Candidate resume evidence */}
                    <div className="bg-brand-paper p-3.5 rounded-xl border border-brand-line space-y-1">
                      <span className="text-[10px] font-sans font-semibold text-band-strong uppercase tracking-wider block">
                        📄 Candidate Resume Snippet:
                      </span>
                      <p className="text-brand-ink/90 italic leading-relaxed">"{resumeSentence}"</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        ) : (
          <p className="text-xs text-brand-muted italic bg-brand-ivory/50 p-4 rounded-2xl border border-brand-line">
            No semantic sentence pairs stored for this run.
          </p>
        )}
      </div>
    </Card>
  );
}
