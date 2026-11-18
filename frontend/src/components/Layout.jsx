/*
 * components/Layout.jsx — Shared page wrapper.
 *
 * Renders the Navbar at the top and the page content below it inside a
 * centered container.  Every page gets consistent padding and max-width.
 */

import Navbar from "./Navbar";

function Layout({ children }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      {/* Page content area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>

      {/* Simple footer */}
      <footer className="bg-gray-100 text-center text-gray-500 text-xs py-4">
        Resume Matcher &mdash; AI-Based Candidate Ranking System
      </footer>
    </div>
  );
}

export default Layout;
