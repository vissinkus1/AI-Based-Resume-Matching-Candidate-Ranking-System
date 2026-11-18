/*
 * pages/CandidateDetail.jsx — Individual candidate view placeholder.
 *
 * Phase 0: reads the :id param and shows a skeleton.
 * Phase 6 will render the full detail view with score breakdown.
 */

import { useParams } from "react-router-dom";

function CandidateDetail() {
  const { id } = useParams();

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Candidate Detail
      </h1>

      <div className="bg-white rounded-lg shadow p-6">
        <p className="text-gray-500">
          Viewing candidate <span className="font-mono font-bold">#{id}</span>.
        </p>
        <p className="text-gray-400 mt-4 italic">
          Detailed score breakdown, matched/missing skills, and plain-English
          explanations will appear here in Phase 6.
        </p>
      </div>
    </div>
  );
}

export default CandidateDetail;
