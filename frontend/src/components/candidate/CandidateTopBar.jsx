import React from "react";
import { useNavigate } from "react-router-dom";
import Card from "../ui/Card";
import Button from "../ui/Button";
import Badge from "../ui/Badge";

export default function CandidateTopBar({
  rank = 1,
  totalCandidates = 1,
  prevCandidateId = null,
  nextCandidateId = null,
  runId = null,
}) {
  const navigate = useNavigate();

  const handleBack = () => {
    if (runId) {
      navigate(`/dashboard?run=${runId}`);
    } else {
      navigate("/dashboard");
    }
  };

  const handleNav = (targetId) => {
    if (targetId) {
      navigate(`/candidate/${targetId}${runId ? `?run=${runId}` : ""}`);
    }
  };

  return (
    <Card padding="p-4 sm:p-5" className="bg-brand-paper mb-6">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-4">
        {/* Back Button */}
        <Button
          variant="secondary"
          size="sm"
          onClick={handleBack}
          className="self-start sm:self-auto"
        >
          <span>←</span>
          <span>Back to Rankings</span>
        </Button>

        {/* Right: Rank badge & Prev/Next navigation */}
        <div className="flex items-center justify-between sm:justify-end gap-3">
          <Badge variant="forest" size="sm">
            Rank #{rank} of {totalCandidates} Candidates
          </Badge>

          <div className="flex items-center gap-1.5">
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleNav(prevCandidateId)}
              disabled={!prevCandidateId}
              title={prevCandidateId ? "Previous candidate" : "First candidate in ranking"}
            >
              <span>‹</span> Prev
            </Button>
            <Button
              variant="secondary"
              size="sm"
              onClick={() => handleNav(nextCandidateId)}
              disabled={!nextCandidateId}
              title={nextCandidateId ? "Next candidate" : "Last candidate in ranking"}
            >
              Next <span>›</span>
            </Button>
          </div>
        </div>
      </div>
    </Card>
  );
}
