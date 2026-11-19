/*
 * main.jsx — Application entry point.
 *
 * Mounts the React app into the #root div with BrowserRouter
 * so React Router can manage client-side navigation.
 * Wraps everything in the JDProvider for shared JD state.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { JDProvider } from "./context/JDContext";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <JDProvider>
        <App />
      </JDProvider>
    </BrowserRouter>
  </React.StrictMode>
);
