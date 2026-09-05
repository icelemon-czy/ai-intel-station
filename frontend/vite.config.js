import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: resolve(__dirname, "../src/ai_intel_station/adapters/web/static"),
    emptyOutDir: true,
  },
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:4173",
        // Preserve the original encoded URL — without this, vite-http-proxy
        // parses the path with `new URL` and re-encodes it, which can truncate
        // multi-byte UTF-8 characters in the `output_path` query parameter.
        changeOrigin: false,
        ws: false,
      },
    },
  },
});