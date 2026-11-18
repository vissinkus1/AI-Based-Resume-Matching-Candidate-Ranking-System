/*
 * components/Navbar.jsx — Top navigation bar.
 *
 * Shows the app name and links to the main pages.
 * Uses React Router's NavLink so the active page is highlighted.
 */

import { NavLink } from "react-router-dom";

function Navbar() {
  // Helper: apply active styling via NavLink's callback
  const linkClass = ({ isActive }) =>
    `px-3 py-2 rounded-md text-sm font-medium transition-colors ${
      isActive
        ? "bg-indigo-700 text-white"
        : "text-indigo-100 hover:bg-indigo-500 hover:text-white"
    }`;

  return (
    <nav className="bg-indigo-600 shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo / App name */}
          <NavLink to="/" className="text-white text-xl font-bold tracking-tight">
            📄 Resume Matcher
          </NavLink>

          {/* Navigation links */}
          <div className="flex space-x-2">
            <NavLink to="/" end className={linkClass}>
              Upload
            </NavLink>
            <NavLink to="/dashboard" className={linkClass}>
              Dashboard
            </NavLink>
          </div>
        </div>
      </div>
    </nav>
  );
}

export default Navbar;
