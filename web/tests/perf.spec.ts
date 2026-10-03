// Part 12.4 #2 (seat click -> panel within 100 ms) and #3 (20+ agents animate at 60 fps).
import { expect, test } from "@playwright/test";
import { shot } from "./helpers";

// Measure what a viewer sees: no Playwright trace recording (it snapshots the DOM continuously
// and costs frames), and not during page start-up.
test.use({ trace: "off" });

test("Part 12.4 #3: 20+ agents animate at 60 fps", async ({ page }) => {
  await page.goto("/?mode=demo");
  await expect.poll(async () => page.locator('.seat[data-status="working"]').count(), { timeout: 15_000 })
    .toBeGreaterThanOrEqual(20);
  await page.waitForTimeout(3000); // settle after start-up
  const working = await page.locator('.seat[data-status="working"]').count();
  const m = await page.evaluate(() => new Promise<{ frames: number; secs: number; p95: number; long: number }>((resolve) => {
    const deltas: number[] = [];
    let last = performance.now();
    const start = last;
    const step = (t: number) => {
      deltas.push(t - last); last = t;
      if (t - start < 10000) requestAnimationFrame(step);
      else {
        const s = [...deltas].sort((a, b) => a - b);
        resolve({ frames: deltas.length, secs: (t - start) / 1000, p95: s[Math.floor(s.length * 0.95)],
          long: deltas.filter((d) => d > 33.4).length });
      }
    };
    requestAnimationFrame(step);
  }));
  const fps = m.frames / m.secs;
  console.log(`${working} seats animating; ${fps.toFixed(1)} fps over ${m.secs.toFixed(1)} s; p95 frame ` +
    `${m.p95.toFixed(1)} ms; frames over 33 ms: ${m.long}`);
  await shot(page, "demo-floor-light", false);
  expect(working).toBeGreaterThanOrEqual(20);
  expect(fps).toBeGreaterThanOrEqual(55);
  });

test("Part 12.4 #2: clicking any seat opens its detail panel within 100 ms", async ({ page }) => {
  await page.goto("/?mode=demo");
  await page.waitForTimeout(2500); // let the simulation get busy (bubbles, badges, animations running)
  // Event Timing API (the browser's "interaction to next paint" measurement): for a real click, the
  // time from the input event until the next frame is painted with the result.
  await page.evaluate(() => {
    (window as any).__clicks = [];
    new PerformanceObserver((list) => {
      for (const e of list.getEntries() as (PerformanceEventTiming & { interactionId: number })[]) {
        if (e.name === "click" || e.name === "pointerup" || e.name === "pointerdown") (window as any).__clicks.push(
          { name: e.name, start: e.startTime, duration: e.duration, interactionId: e.interactionId });
      }
    }).observe({ type: "event", buffered: true, durationThreshold: 16 } as PerformanceObserverInit);
  });
  const ids = await page.locator(".seat").evaluateAll((els) => els.map((e) => e.getAttribute("data-agent")!));
  for (const id of ids) {
    await page.locator(`.seat[data-agent="${id}"]`).click();
    await expect(page.getByTestId("panel")).toHaveAttribute("data-agent", id);
  }
  await page.waitForTimeout(300);
  const entries: { name: string; duration: number; interactionId: number }[] = await page.evaluate(() => (window as any).__clicks);
  // per interaction: the longest of its input events (pointerdown/pointerup/click) = INP-style latency;
  // interactions under 16 ms are not reported by the browser (they are fast by definition)
  const perInteraction = new Map<number, number>();
  for (const e of entries) perInteraction.set(e.interactionId, Math.max(perInteraction.get(e.interactionId) ?? 0, e.duration));
  const d = [...perInteraction.values()].sort((a, b) => a - b);
  const max = d.at(-1) ?? 0;
  console.log(`${ids.length} seats clicked; ${d.length} clicks took >= 16 ms from input to painted panel; ` +
    `slowest ${max.toFixed(0)} ms, median of those ${d.length ? d[d.length >> 1].toFixed(0) : "-"} ms`);
  expect(ids.length).toBeGreaterThanOrEqual(70);
  expect(max).toBeLessThan(100);
});
