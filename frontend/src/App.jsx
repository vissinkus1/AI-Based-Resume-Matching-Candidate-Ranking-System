/*
 * App.jsx — Root component.
 *
 * Wraps every page in the shared Layout and defines the client-side routes.
 */

import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import ErrorBoundary from "./components/ErrorBoundary";
import Home from "./pages/Home";
import Dashboard from "./pages/Dashboard";
import CandidateDetail from "./pages/CandidateDetail";

function App() {
  return (
    <ErrorBoundary>
      <Layout>
        <Routes>
          {/* Home: upload JD + resumes */}
          <Route path="/" element={<Home />} />

          {/* Ranking dashboard */}
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Individual candidate detail */}
          <Route path="/candidate/:id" element={<CandidateDetail />} />
        </Routes>
      </Layout>
    </ErrorBoundary>
  );
}

export default App;
