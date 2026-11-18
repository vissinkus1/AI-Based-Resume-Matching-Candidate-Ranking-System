/*
 * pages/Dashboard.jsx — Ranking dashboard placeholder.
 *
 * Phase 0: shows what will go here.
 * Phase 5 will add the actual ranking table with sorting/filtering.
 */

function Dashboard() {
  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-800 mb-6">
        Candidate Ranking Dashboard
      </h1>

      {/* Placeholder table structure */}
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              {["Candidate", "Experience", "Match %", "Matched Skills"].map(
                (header) => (
                  <th
                    key={header}
                    className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                  >
                    {header}
                  </th>
                )
              )}
            </tr>
          </thead>
          <tbody>
            <tr>
              <td
                colSpan={4}
                className="px-6 py-12 text-center text-gray-400 italic"
              >
                No candidates yet. Upload a JD and resumes to get started.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default Dashboard;
