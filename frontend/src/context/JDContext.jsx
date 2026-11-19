/*
 * context/JDContext.jsx — React Context for the active Job Description.
 *
 * Stores the currently selected JD id and parsed data so that all pages
 * (Upload, Dashboard, Candidate Detail) can access it without prop drilling.
 */

import { createContext, useContext, useState } from "react";

const JDContext = createContext(null);

export function JDProvider({ children }) {
  // The active JD object: { id, title, parsed }
  const [activeJD, setActiveJD] = useState(null);

  return (
    <JDContext.Provider value={{ activeJD, setActiveJD }}>
      {children}
    </JDContext.Provider>
  );
}

/**
 * Hook to access the active JD context.
 * Returns { activeJD, setActiveJD }.
 */
export function useJD() {
  const ctx = useContext(JDContext);
  if (ctx === null) {
    throw new Error("useJD must be used within a JDProvider");
  }
  return ctx;
}
