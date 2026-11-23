import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import Button from "./ui/Button";

export default function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const navigate = useNavigate();

  const navLinkClass = ({ isActive }) =>
    `px-4 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wider transition-all duration-150 ${
      isActive
        ? "bg-brand-paper text-brand-forest border border-brand-line shadow-sm"
        : "text-brand-muted hover:text-brand-ink hover:bg-brand-sage-soft/20"
    }`;

  const mobileNavLinkClass = ({ isActive }) =>
    `block px-4 py-2.5 rounded-2xl text-sm font-medium transition-all ${
      isActive
        ? "bg-brand-forest text-brand-ivory"
        : "text-brand-ink hover:bg-brand-sage-soft/30"
    }`;

  return (
    <nav className="sticky top-0 z-50 bg-brand-ivory/90 backdrop-blur-md border-b border-brand-line">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Left: Brand mark & title */}
          <NavLink
            to="/"
            className="flex items-center gap-3 group focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest rounded-xl p-1"
          >
            <div className="w-8 h-8 rounded-full bg-brand-forest flex items-center justify-center text-brand-ivory shadow-soft group-hover:scale-105 transition-transform duration-200">
              <svg
                className="w-4 h-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="16" y1="13" x2="8" y2="13" />
                <line x1="16" y1="17" x2="8" y2="17" />
                <polyline points="10 9 9 9 8 9" />
              </svg>
            </div>
            <div className="flex flex-col">
              <span className="font-serif text-lg sm:text-xl font-bold tracking-tight text-brand-ink group-hover:text-brand-forest transition-colors">
                KANDIDAT
              </span>
              <span className="text-[9px] font-sans font-semibold uppercase tracking-widest text-brand-muted -mt-1 hidden sm:block">
                AI Match &amp; Rank
              </span>
            </div>
          </NavLink>

          {/* Center: Navigation Links */}
          <div className="hidden md:flex items-center gap-1.5 p-1 rounded-full bg-brand-sage-soft/25 border border-brand-line/60">
            <NavLink to="/" end className={navLinkClass}>
              Upload &amp; Match
            </NavLink>
            <NavLink to="/dashboard" className={navLinkClass}>
              Rankings
            </NavLink>
          </div>

          {/* Right: Outlined Pill CTA */}
          <div className="hidden sm:flex items-center gap-3">
            <Button
              variant="outlined"
              size="sm"
              onClick={() => {
                navigate("/");
                // Trigger scroll to demo or execute sample
                setTimeout(() => {
                  const demoBtn = document.getElementById("try-demo-btn");
                  if (demoBtn) demoBtn.scrollIntoView({ behavior: "smooth" });
                }, 100);
              }}
            >
              Try sample demo
            </Button>
          </div>

          {/* Mobile menu button */}
          <div className="flex md:hidden">
            <button
              type="button"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-brand-ink hover:bg-brand-sage-soft/30 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-forest"
              aria-label="Toggle navigation menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Menu dropdown */}
      {mobileMenuOpen && (
        <div className="md:hidden border-b border-brand-line bg-brand-paper px-4 pt-2 pb-6 space-y-2 shadow-lg">
          <NavLink
            to="/"
            end
            onClick={() => setMobileMenuOpen(false)}
            className={mobileNavLinkClass}
          >
            Upload &amp; Match
          </NavLink>
          <NavLink
            to="/dashboard"
            onClick={() => setMobileMenuOpen(false)}
            className={mobileNavLinkClass}
          >
            Candidate Rankings
          </NavLink>
          <div className="pt-2">
            <Button
              variant="outlined"
              size="sm"
              className="w-full justify-center"
              onClick={() => {
                setMobileMenuOpen(false);
                navigate("/");
              }}
            >
              Try sample demo
            </Button>
          </div>
        </div>
      )}
    </nav>
  );
}
