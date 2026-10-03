import { execFileSync } from "node:child_process";
import { existsSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";
import type { Page } from "@playwright/test";

export const API = "http://127.0.0.1:8100";
const PY = process.env.S2S_PYTHON ?? (existsSync("../backend/.venv/bin/python") ? "../backend/.venv/bin/python" : "python3");

/** Run backend/scripts/e2e_seed.py against the e2e stack's database. */
export function seed(...args: string[]): Record<string, string> {
  const out = execFileSync(PY, ["../backend/scripts/e2e_seed.py", ...args, "--env-file", "test-results/e2e-env.json"],
    { encoding: "utf8" });
  return JSON.parse(out.trim().split("\n").pop()!);
}

/** GET JSON from the e2e API; one retry if a reused keep-alive connection was just closed. */
export async function apiGet<T = any>(path: string): Promise<T> {
  try {
    return (await (await fetch(`${API}${path}`)).json()) as T;
  } catch {
    return (await (await fetch(`${API}${path}`)).json()) as T;
  }
}

export async function runStatus(runId: string): Promise<string> {
  return (await apiGet(`/runs/${runId}`)).status;
}

export async function waitRun(runId: string, timeoutMs = 90_000): Promise<void> {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    const st = await runStatus(runId);
    if (st === "completed") return;
    if (st === "failed") throw new Error(`run ${runId} failed`);
    await new Promise((r) => setTimeout(r, 300));
  }
  throw new Error(`run ${runId} did not complete`);
}

/** Wait until no seeded dummy run is still active (finance totals must be stable). */
export async function waitIdle(timeoutMs = 90_000): Promise<void> {
  const end = Date.now() + timeoutMs;
  while (Date.now() < end) {
    if (Number(seed("active").active) === 0) return;
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error("dummy runs still active");
}

export const live = (extra = "") => `/?mode=live&api=${encodeURIComponent(API)}${extra}`;

/** Screenshots go to docs/milestones/m0.4-screenshots/ (committed with the milestone report). */
export async function shot(page: Page, name: string, fullPage = true) {
  const dir = resolve("../docs/milestones/m0.4-screenshots");
  mkdirSync(dir, { recursive: true });
  await page.screenshot({ path: `${dir}/${name}.png`, fullPage });
}
