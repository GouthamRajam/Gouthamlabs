// Part 12.4 #2-#5 and the M0.4 acceptance tests (Part 13.2).
import { expect, test } from "@playwright/test";
import { apiGet, live, seed, shot, waitIdle, waitRun } from "./helpers";

test.describe.configure({ mode: "serial" });

test("clicking three seats shows their real detail panels (live data from a real dummy run)", async ({ page }) => {
  await page.goto(live());
  await expect(page.getByTestId("mode-badge")).toHaveText(/^Live$/);
  const { run_id } = seed("run", "--step-delay", "0.05");
  await waitRun(run_id);

  await page.locator('.seat[data-agent="Ada"]').click();
  const panel = page.getByTestId("panel");
  await expect(panel.getByTestId("panel-name")).toHaveText("Ada");
  await expect(panel.getByTestId("panel-role")).toHaveText("Datapath RTL");
  await expect(panel.getByTestId("panel-mission")).toHaveText("Arithmetic, pipelines, data movement");
  await expect(panel.getByTestId("panel-task")).toContainText("Write lint-clean RTL (Zone 2A)");
  await expect(panel.getByTestId("panel-plan")).toContainText("Ada plan:");
  await expect(panel.getByTestId("panel-tools")).toContainText("verilator_lint");
  await expect(panel.getByTestId("panel-files")).toContainText("rtl/output.txt");
  await expect(panel.getByTestId("panel-messages")).toContainText("→ Vera");
  await expect(panel.getByTestId("panel-timeline")).toContainText("task.completed");

  await page.locator('.seat[data-agent="Rex"]').click();
  await expect(panel.getByTestId("panel-name")).toHaveText("Rex");
  // The panel counts every check the viewer has received for Rex (live backfill includes earlier
  // runs): at least this run's 1 pass + 3 failures, in the dummy agent's 1:3 ratio.
  const stats = await panel.getByTestId("panel-stats").locator("b").allTextContents();
  const [passed, failed] = stats.map(Number);
  expect(passed).toBeGreaterThanOrEqual(1);
  expect(failed).toBe(3 * passed);
  await expect(panel.getByTestId("panel-tools")).toContainText("cocotb_sim");
  await expect(panel.getByTestId("panel-timeline")).toContainText("regression: 41/42 pass");

  await page.locator('.seat[data-agent="Lyra"]').click();
  await expect(panel.getByTestId("panel-name")).toHaveText("Lyra");
  await expect(panel.getByTestId("panel-role")).toHaveText("Technical Research");
  await expect(panel.getByTestId("panel-timeline")).toContainText("research.brief");
  await shot(page, "live-panel-lyra");
});

test("Part 12.4 #4: phone width (stacked) and light/dark themes", async ({ browser }) => {
  for (const scheme of ["light", "dark"] as const) {
    const ctx = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: scheme, isMobile: true, hasTouch: true });
    const page = await ctx.newPage();
    await page.goto("/?mode=demo");
    await page.waitForTimeout(2500);
    const layout = await page.evaluate(() => {
      const rooms = [...document.querySelectorAll(".floor > .col")].map((c) => c.getBoundingClientRect());
      const floor = document.querySelector(".floor")!.getBoundingClientRect();
      const panel = document.querySelector('[data-testid="panel"]')!.getBoundingClientRect();
      return {
        scrollW: document.documentElement.scrollWidth, innerW: window.innerWidth,
        colLefts: [...new Set(rooms.map((r) => Math.round(r.left)))], panelBelowFloor: panel.top >= floor.bottom - 1,
        bg: getComputedStyle(document.body).backgroundColor,
      };
    });
    expect(layout.scrollW).toBeLessThanOrEqual(layout.innerW); // no sideways page scroll
    expect(layout.colLefts).toHaveLength(1); // rooms stacked in one column
    expect(layout.panelBelowFloor).toBe(true);
    expect(layout.bg).toBe(scheme === "dark" ? "rgb(14, 20, 22)" : "rgb(238, 242, 241)");
    await page.locator('.seat[data-agent="Vera"]').click();
    await expect(page.getByTestId("panel-name")).toHaveText("Vera");
    await shot(page, `phone-${scheme}`, false);
    await ctx.close();
  }
  // the theme toggle overrides the system setting
  const ctx = await browser.newContext({ colorScheme: "light", viewport: { width: 1440, height: 1000 } });
  const page = await ctx.newPage();
  await page.goto("/?mode=demo&theme=dark");
  await expect.poll(() => page.evaluate(() => getComputedStyle(document.body).backgroundColor)).toBe("rgb(14, 20, 22)");
  await page.waitForTimeout(3000);
  await shot(page, "demo-floor-dark", false);
  await ctx.close();
});

test("Part 12.4 #5: demo mode is clearly labeled; live mode never is", async ({ page }) => {
  await page.goto("/?mode=demo");
  await expect(page.getByTestId("mode-badge")).toHaveText("Simulation");
  await expect(page.getByTestId("sim-banner")).toContainText("Nothing shown here is real tool output");
  await page.waitForTimeout(3000);
  // every feed item is tagged SIM (counted in one snapshot: the simulation keeps adding events)
  const { items, tagged } = await page.evaluate(() => {
    const li = [...document.querySelectorAll(".feed li[data-type]")];
    return { items: li.length, tagged: li.filter((x) => x.querySelector(".simtag")).length };
  });
  expect(items).toBeGreaterThan(5);
  expect(tagged).toBe(items);
  await page.locator('.seat[data-agent="Iris"]').click();
  await expect(page.getByTestId("panel")).toContainText("simulated");
  await expect(page.getByTestId("run-id")).toHaveText(/^sim_run_/);
  await page.getByTestId("tab-management").click();
  await expect(page.getByTestId("dash-sim")).toBeVisible();

  await page.goto(live());
  await expect(page.getByTestId("mode-badge")).toHaveText(/^Live/);
  await expect(page.getByTestId("sim-banner")).toHaveCount(0);
  await expect(page.locator(".simtag")).toHaveCount(0);
});

test("management tab shows a seeded stall (flagged by the real watchdog)", async ({ page }) => {
  const { task_id } = seed("stall");
  await page.goto(live());
  await page.getByTestId("tab-management").click();
  const row = page.locator(`[data-testid="stalls-table"] tr[data-task="${task_id}"]`);
  await expect(row).toBeVisible();
  await expect(row).toContainText("Rex");
  await expect(row).toContainText("verification");
  await expect(row).toContainText("regression attempt 2: 41/42 pass");
  await expect(row).toContainText("20 min");
  const dash = await apiGet("/management/dashboard");
  expect(dash.stalls.map((t: { id: string }) => t.id)).toContain(task_id);
  await shot(page, "management-stall");
});

test("finance tab totals match the seeded usage records to the cent", async ({ page }) => {
  await waitIdle(); // no dummy run may add cost while we compare
  const s = seed("usage");
  const cents = (x: string | number) => `$${Number(x).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  await page.goto(live());
  await page.getByTestId("tab-finance").click();
  await expect(page.locator(`[data-testid="fin-by-run"] tr[data-key="${s.run_id}"] td.num`)).toHaveText(cents(s.seeded_usd));
  await expect(page.getByTestId("fin-total")).toHaveText(cents(s.db_total_usd));
  await expect(page.getByTestId("finance")).toContainText(`${s.records} usage records`);
  console.log(`seeded run ${s.run_id}: ${cents(s.seeded_usd)} (db ${s.seeded_usd}); total shown ${cents(s.db_total_usd)} = db ${s.db_total_usd}`);
  await shot(page, "finance");
});

test("replay mode plays a stored run back at 50x", async ({ page }) => {
  const { run_id } = seed("run", "--to", "architecture", "--step-delay", "0.3");
  await waitRun(run_id);
  const total = (await apiGet(`/events?run_id=${run_id}&limit=500`)).length;
  const t0 = Date.now();
  await page.goto(`/?mode=replay&run=${run_id}&speed=50&api=${encodeURIComponent("http://127.0.0.1:8100")}`);
  await expect(page.getByTestId("mode-badge")).toHaveText("Replay 50x");
  await expect(page.getByTestId("replay-position")).toHaveText(`${total}/${total} events`, { timeout: 60_000 });
  console.log(`replayed ${total} events of ${run_id} at 50x in ${((Date.now() - t0) / 1000).toFixed(1)} s`);
  // the run covered Spec..Architecture: exactly those two stages done, nothing current
  await expect(page.locator(".stage.done .t")).toHaveText(["Spec", "Arch"]);
  await expect(page.locator(".stage.now")).toHaveCount(0);
  await expect(page.locator(".feed li[data-type]")).toHaveCount(Math.min(total, 200));
});
