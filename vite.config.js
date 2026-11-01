import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Vercel runs this from the repository root. The React app itself lives in frontend/.
export default defineConfig({
  root: "frontend",
  plugins: [react()],
  // Flask on Vercel serves files in public/ and sends every other path to the API.
  build: { outDir: "../public", emptyOutDir: true },
});
