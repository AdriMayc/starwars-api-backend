import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import tailwindcss from '@tailwindcss/vite'

const target = process.env.VITE_API_BASE_URL || "http://localhost:8080";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    proxy: {
      "/api": {
        target,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
  },
});
