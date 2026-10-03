import { existsSync } from "node:fs";
import { defineConfig, devices } from "@playwright/test";

// Python for the backend e2e stack: S2S_PYTHON, else the backend venv if present, else python3.
const PY = process.env.S2S_PYTHON ?? (existsSync("../backend/.venv/bin/python") ? "../backend/.venv/bin/python" : "python3");
export const E2E_API = "http://127.0.0.1:8100";

export default defineConfig({
  testDir: "tests",
  timeout: 120_000,
  expect: { timeout: 15_000 },
  workers: 1, // tests share one backend stack and seed data into it
  fullyParallel: false,
  reporter: [["list"]],
  use: { baseURL: "http://localhost:3100", trace: "retain-on-failure", ...devices["Desktop Chrome"], viewport: { width: 1440, height: 1000 } },
  webServer: [
    {
      // real API + orchestrator on a fresh database (needs Postgres + Redis: `docker compose up -d postgres redis`)
      command: `${PY} ../backend/scripts/e2e_stack.py --port 8100 --env-file test-results/e2e-env.json`,
      url: `${E2E_API}/health`, timeout: 120_000, reuseExistingServer: false, stdout: "pipe",
    },
    {
      // its own port, so a running `docker compose` web (:3000, possibly an older build) is never reused
      command: "npx next start -p 3100", url: "http://localhost:3100", timeout: 120_000, reuseExistingServer: false,
    },
  ],
});
