// The S2S API base URL: ?api=<url> in the page URL, else NEXT_PUBLIC_S2S_API, else
// http://<this host>:8000.
import type { S2SEvent } from "./types";

export function apiBase(): string {
  if (typeof window !== "undefined") {
    const q = new URLSearchParams(window.location.search).get("api");
    if (q) return q.replace(/\/$/, "");
  }
  if (process.env.NEXT_PUBLIC_S2S_API) return process.env.NEXT_PUBLIC_S2S_API.replace(/\/$/, "");
  if (typeof window !== "undefined") return `${window.location.protocol}//${window.location.hostname}:8000`;
  return "http://localhost:8000";
}

export const wsBase = () => apiBase().replace(/^http/, "ws");

export async function getJSON<T>(path: string, timeoutMs = 8000): Promise<T> {
  const ctl = new AbortController();
  const timer = setTimeout(() => ctl.abort(), timeoutMs);
  try {
    const r = await fetch(`${apiBase()}${path}`, { signal: ctl.signal, cache: "no-store" });
    if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`);
    return (await r.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}

export async function backendReachable(): Promise<boolean> {
  try {
    await getJSON<{ status: string }>("/health", 1500);
    return true;
  } catch {
    return false;
  }
}

/** All stored events of a run, oldest first (pages of 500 from GET /events). */
export async function runEvents(runId: string): Promise<S2SEvent[]> {
  const all: S2SEvent[] = [];
  let before: string | undefined;
  for (;;) {
    const q = new URLSearchParams({ run_id: runId, limit: "500", ...(before ? { before } : {}) });
    const page = await getJSON<(S2SEvent & { ts: string })[]>(`/events?${q}`);
    all.push(...page);
    if (page.length < 500) break;
    before = page[page.length - 1].id;
  }
  // events table ts may lack the trailing Z; normalize and order by time (commit order)
  return all
    .map((e) => ({ ...e, ts: e.ts.endsWith("Z") || e.ts.includes("+") ? e.ts : `${e.ts}Z` }))
    .sort((a, b) => Date.parse(a.ts) - Date.parse(b.ts) || (a.id < b.id ? -1 : 1));
}

export interface RunSummary { id: string; design_name: string | null; status: string; started_at: string; events: number }
