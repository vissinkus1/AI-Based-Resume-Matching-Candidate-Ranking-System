import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,         // Default Vite port — matches backend CORS config
    open: false,        // Don't auto-open browser
  },
});
