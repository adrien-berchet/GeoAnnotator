import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "path";
import os from "node:os";

// Cap Vitest worker threads to keep per-worker jsdom memory spikes under control.
const availableCpus =
  typeof os.availableParallelism === "function"
    ? os.availableParallelism()
    : os.cpus().length;
const maxThreads = Math.max(Math.min(availableCpus - 1, 4), 1);

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    maxConcurrency: maxThreads,
    poolOptions: {
      threads: {
        minThreads: 1,
        maxThreads,
      },
    },
    coverage: {
      provider: "v8",
      reporter: ["text", "html", "lcov"],
      exclude: [
        "node_modules/",
        "src/test/",
        "**/*.d.ts",
        "**/*.config.*",
        "**/mockData",
        "**/*.test.{ts,tsx}",
        "**/*.spec.{ts,tsx}",
      ],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
