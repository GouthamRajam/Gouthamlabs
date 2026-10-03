// Part 12.4 #1: every event type in 11.2 produces a visible change.
import { expect, test, type Page } from "@playwright/test";
import { live, seed, shot, waitRun } from "./helpers";

const TYPES = [
  "agent.status", "task.started", "plan", "tool_call", "tool_result", "artifact.created", "check.passed", "check.failed",
  "handoff", "finding", "gate.requested", "gate.decided", "task.completed", "budget.warning", "escalation",
  "stage.changed", "task.heartbeat", "task.stalled", "manager.checkin", "budget.alert", "research.brief",
];

let n = 0;
const ev = (type: string, agent: string, summary: string, extra: Record<string, unknown> = {}) => ({
  id: `t_${++n}`, ts: new Date().toISOString(), run_id: "run_test", design_id: null, team: null, agent_id: agent,
  agent_name: agent, stage: "rtl", task_id: "task_t", type, status: null, summary, detail: {}, to_agent_id: null,
  progress: null, ...extra,
});
const inject = (page: Page, e: unknown) => page.evaluate((x) => (window as any).__s2s.apply(x), e);
const seat = (page: Page, id: string) => page.locator(`.seat[data-agent="${id}"]`);

test("each of the 21 event types changes what is on screen (injected, one by one)", async ({ page }) => {
  // replay mode without a run = an empty office with no event source; events come only from the test
  await page.goto("/?mode=replay&testhooks=1&api=http://127.0.0.1:9");
  await expect(seat(page, "Ada")).toBeVisible();
  const ada = seat(page, "Ada");
  const ring = () => ada.locator(".av").evaluate((el) => getComputedStyle(el).borderColor);

  // agent.status -> status ring colour
  const idleRing = await ring();
  await inject(page, ev("agent.status", "Ada", "Ada is blocked", { status: "blocked" }));
  await expect(ada).toHaveAttribute("data-status", "blocked");
  expect(await ring()).not.toBe(idleRing);
  // task.started -> bubble shows the task title
  await inject(page, ev("task.started", "Ada", "Ada started: Write the uart RTL"));
  await expect(ada.locator(".bubble")).toHaveText("Write the uart RTL");
  // plan -> bubble text
  await inject(page, ev("plan", "Ada", "Ada plan: lint, then synthesize"));
  await expect(ada.locator(".bubble")).toHaveText("Ada plan: lint, then synthesize");
  // tool_call -> pulsing tool chip
  await inject(page, ev("tool_call", "Ada", "Ada runs verilator_lint", { detail: { tool: "verilator_lint" } }));
  await expect(ada.locator(".tool-chip")).toHaveText("verilator_lint");
  // tool_result -> bubble shows the result
  await inject(page, ev("tool_result", "Ada", "verilator_lint: 0 errors", { detail: { tool: "verilator_lint" } }));
  await expect(ada.locator(".bubble")).toHaveText("verilator_lint: 0 errors");
  // artifact.created -> file chip on the seat and in the panel
  await inject(page, ev("artifact.created", "Ada", "Ada wrote rtl/uart.sv", { detail: { path: "rtl/uart.sv" } }));
  await expect(ada.locator(".bdg-files")).toHaveText("1");
  // check.passed / check.failed -> green / red flash, counters
  await inject(page, ev("check.passed", "Ada", "lint passed"));
  await expect(ada).toHaveAttribute("data-flash", "ok");
  await expect(page.getByTestId("c-pass")).toHaveText("1");
  await inject(page, ev("check.failed", "Lumen", "cdc check failed"));
  await expect(seat(page, "Lumen")).toHaveAttribute("data-flash", "bad");
  await expect(page.getByTestId("c-fail")).toHaveText("1");
  // handoff -> animated packet between the two seats
  await inject(page, ev("handoff", "Vera", "Vera -> Ada: bug report", { to_agent_id: "Ada" }));
  await expect(page.locator('svg.links [data-effect="handoff"]')).toHaveCount(1);
  // finding -> warning badge on the target agent
  await inject(page, ev("finding", "Sentinel", "Sentinel: reset not documented", { to_agent_id: "Ada" }));
  await expect(ada.locator(".bdg-finding")).toHaveText("⚠1");
  // gate.requested / gate.decided -> banner on the approving human's desk
  await inject(page, ev("gate.requested", "Atlas", "G1 requested", { detail: { gate: "G1" } }));
  await expect(seat(page, "human:vp_frontend").locator(".gate-banner")).toHaveText("G1 awaiting review");
  await expect(page.getByTestId("c-gates")).toHaveText("1");
  await inject(page, ev("gate.decided", "Atlas", "G1 approved", { detail: { gate: "G1", decision: "approve" } }));
  await expect(seat(page, "human:vp_frontend").locator(".gate-banner")).toHaveText("G1 approved");
  // task.heartbeat -> progress bar moves
  await inject(page, ev("task.heartbeat", "Ada", "Ada: 60%", { progress: 0.6 }));
  await expect(ada.locator(".prog span")).toHaveAttribute("style", /scaleX\(0\.6\)/);
  // task.completed -> progress completes, bubble
  await inject(page, ev("task.completed", "Ada", "Ada completed: Write the uart RTL", { progress: 1 }));
  await expect(ada.locator(".bubble")).toHaveText("Ada completed: Write the uart RTL");
  await expect(ada.locator(".prog")).toHaveCount(0);
  // budget.warning -> amber badge
  await inject(page, ev("budget.warning", "Rex", "Rex: tool runs at 83%"));
  await expect(seat(page, "Rex").locator(".bdg-budget")).toBeVisible();
  // escalation -> red badge + notification
  await inject(page, ev("escalation", "Rex", "regression failed 3 times", { to_agent_id: "Hale" }));
  await expect(seat(page, "Hale").locator(".bdg-esc")).toBeVisible();
  await expect(page.locator(".toast")).toContainText("regression failed 3 times");
  // stage.changed -> pipeline bar advances
  await inject(page, ev("stage.changed", "Atlas", "entered verification", { detail: { to: "verification" } }));
  await expect(page.locator(".stage.now .t")).toHaveText("Verify");
  // task.stalled -> stall badge on the seat and its manager
  await inject(page, ev("task.stalled", "Cora", "Cora: no progress", { to_agent_id: "Rhea", task_id: "task_cora" }));
  await expect(seat(page, "Cora").locator(".bdg-stall")).toBeVisible();
  await expect(seat(page, "Rhea").locator(".bdg-stall")).toBeVisible();
  // ...and both clear when the stalled task makes progress again
  await inject(page, ev("task.heartbeat", "Cora", "Cora: 50%", { task_id: "task_cora", progress: 0.5 }));
  await expect(seat(page, "Cora").locator(".bdg-stall")).toHaveCount(0);
  await expect(seat(page, "Rhea").locator(".bdg-stall")).toHaveCount(0);
  // manager.checkin -> check mark on the manager
  await inject(page, ev("manager.checkin", "Reid", "Reid checked Ada", { to_agent_id: "Ada" }));
  await expect(seat(page, "Reid").locator(".bdg-checkin")).toBeVisible();
  // budget.alert -> finance seat flashes, run spend in the top bar
  await inject(page, ev("budget.alert", "Penny", "run spend at 80%", { detail: { spent_usd: 60, pct: 80 } }));
  await expect(seat(page, "Penny")).toHaveAttribute("data-flash", "money");
  await expect(page.getByTestId("run-spend")).toHaveText("$60.00");
  // research.brief -> research seat bubble + feed
  await inject(page, ev("research.brief", "Lyra", "Lyra: brief on UART prior art"));
  await expect(seat(page, "Lyra").locator(".bubble")).toHaveText("Lyra: brief on UART prior art");

  // transient effects go away on their own: escalation toast (8 s), decided gate banner (6 s)
  await expect(page.locator(".toast")).toHaveCount(0, { timeout: 12_000 });
  await expect(seat(page, "human:vp_frontend").locator(".gate-banner")).toHaveCount(0);

  // and every type is in the activity feed
  for (const t of TYPES) await expect(page.locator(`.feed li[data-type="${t}"]`).first()).toBeAttached();
});

test("a real dummy run streamed over /ws/events renders a visible effect for every event type", async ({ page }) => {
  await page.goto(live());
  await expect(page.getByTestId("mode-badge")).toHaveText(/Live/);
  await expect(page.getByTestId("mode-badge")).not.toHaveText(/connecting|closed/);
  // record every visible effect that appears on the page (elements tagged with the event type)
  await page.evaluate(() => {
    const seen = new Set<string>();
    (window as any).__effects = seen;
    const note = (el: Element) => { const e = el.getAttribute?.("data-effect"); if (e) seen.add(e); };
    new MutationObserver((muts) => {
      for (const m of muts) {
        if (m.type === "attributes") {
          const el = m.target as Element;
          if (m.attributeName === "data-effect") note(el);
          if (m.attributeName === "data-status") seen.add("agent.status");
        }
        m.addedNodes.forEach((nd) => { if (nd instanceof Element) { note(nd); nd.querySelectorAll("[data-effect]").forEach(note); } });
      }
    }).observe(document.body, { subtree: true, childList: true, attributes: true, attributeFilter: ["data-effect", "data-status"] });
  });
  const { run_id } = seed("run", "--hang"); // hang -> real stall + escalation; small budgets -> warning + alerts
  await waitRun(run_id);
  await page.waitForTimeout(1500);
  const seen: string[] = await page.evaluate(() => [...(window as any).__effects]);
  const missing = TYPES.filter((t) => !seen.includes(t));
  console.log(`visible effects seen for ${TYPES.length - missing.length}/${TYPES.length} event types` +
    (missing.length ? `; missing: ${missing}` : ""));
  await shot(page, "live-after-run");
  expect(missing).toEqual([]);
});
