// Settings -> Model access and Spend controls (MASTER_SPEC Part 28), against the real e2e API.
// Test connection really calls the Anthropic API. With the deliberately invalid key below the
// API answers 401; a passing connection needs a real key (S2S_TEST_ANTHROPIC_KEY, optional).
import { readFileSync } from "node:fs";
import { expect, test } from "@playwright/test";
import { apiGet, live, shot } from "./helpers";

const FAKE_KEY = `sk-ant-api03-S2SBROWSERTEST-${Date.now().toString(36)}-K7W2`; // not a real key

test.describe.configure({ mode: "serial" });

test("Model access: key is saved server-side, masked, never kept in the browser", async ({ page, context }) => {
  const sentWithKey: string[] = [];
  const echoedKey: string[] = [];
  page.on("request", (r) => { if ((r.postData() ?? "").includes(FAKE_KEY)) sentWithKey.push(`${r.method()} ${new URL(r.url()).pathname}`); });
  page.on("response", async (r) => {
    try { if ((await r.text()).includes(FAKE_KEY.slice(0, -4))) echoedKey.push(r.url()); } catch { /* bodiless */ }
  });

  await page.goto(live());
  await page.getByTestId("tab-settings").click();
  const card = page.getByTestId("model-access");
  await expect(card).toBeVisible();
  await expect(page.getByTestId("model")).toHaveText("claude-sonnet-5-5");
  await expect(page.getByTestId("key-masked")).toHaveCount(0); // nothing saved yet
  await expect(page.getByTestId("apikey")).toHaveAttribute("type", "password");

  await page.getByTestId("apikey").fill(FAKE_KEY);
  await page.getByTestId("save-access").click();
  await expect(page.getByTestId("access-msg")).toHaveText("Saved on the server (encrypted).");
  await expect(page.getByTestId("apikey")).toHaveValue(""); // cleared after save
  await expect(page.getByTestId("key-masked")).toHaveText("Saved key: ••••••••K7W2");

  // the key went to the backend exactly once, and nothing ever sent it back
  expect(sentWithKey).toEqual(["PUT /settings/model-access"]);
  expect(echoedKey).toEqual([]);
  const stored = await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage }, cookie: document.cookie, html: document.documentElement.outerHTML }));
  expect(stored).not.toContain(FAKE_KEY);
  expect(JSON.stringify(await context.cookies())).not.toContain(FAKE_KEY);

  // after a reload the browser has no key at all; the server still reports the masked one
  await page.reload();
  await page.getByTestId("tab-settings").click();
  await expect(page.getByTestId("key-masked")).toHaveText("Saved key: ••••••••K7W2");
  await expect(page.getByTestId("apikey")).toHaveValue("");
  const view = await apiGet("/settings/model-access");
  expect(JSON.stringify(view)).not.toContain(FAKE_KEY);

  // the encrypted file on the server holds no plaintext
  const env = JSON.parse(readFileSync("test-results/e2e-env.json", "utf8"));
  const blob = readFileSync(`${env.S2S_SECRETS_DIR}/model_access.enc`, "utf8");
  expect(blob).not.toContain(FAKE_KEY);
  expect(blob.startsWith("gAAAAA")).toBe(true); // Fernet token
});

test("Test connection makes one real call: an invalid key fails with the API's own 401", async ({ page }) => {
  await page.goto(live());
  await page.getByTestId("tab-settings").click();
  await expect(page.getByTestId("key-masked")).toHaveText(/K7W2$/);
  await page.getByTestId("test-connection").click();
  const result = page.getByTestId("test-result");
  await expect(result).toHaveAttribute("data-ok", "false", { timeout: 40_000 });
  await expect(result).toContainText("✕ Failed");
  await expect(result).toContainText("claude-sonnet-5-5");
  await expect(result).toContainText("HTTP 401 authentication_error");
  await expect(result).toContainText(/\d+ ms/);
  console.log(`Test connection with the invalid key: ${await result.textContent()}`);
  await shot(page, "settings-test-invalid-key", true, "part28-screenshots");

  // the provider selector: on-prem asks for an endpoint, Bedrock says it is not wired yet
  await page.getByTestId("provider-onprem").click();
  await expect(page.getByTestId("endpoint")).toBeVisible();
  await page.getByTestId("provider-bedrock").click();
  await expect(page.getByTestId("bedrock-note")).toContainText("not wired yet");
  await page.getByTestId("provider-anthropic").click();
});

test("Test connection with a real key passes (only when S2S_TEST_ANTHROPIC_KEY is provided)", async ({ page }) => {
  const key = process.env.S2S_TEST_ANTHROPIC_KEY;
  test.skip(!key, "needs a real Anthropic API key in S2S_TEST_ANTHROPIC_KEY");
  await page.goto(live());
  await page.getByTestId("tab-settings").click();
  await page.getByTestId("apikey").fill(key!);
  await page.getByTestId("save-access").click();
  await expect(page.getByTestId("key-masked")).toHaveText(`Saved key: ••••••••${key!.slice(-4)}`);
  await page.getByTestId("test-connection").click();
  const result = page.getByTestId("test-result");
  await expect(result).toHaveAttribute("data-ok", "true", { timeout: 40_000 });
  console.log(`Test connection with the real key: ${await result.textContent()}`);
  await shot(page, "settings-test-real-key", true, "part28-screenshots");
});

test("Spend controls: caps are saved to finance.yaml and shown back", async ({ page }) => {
  await page.goto(live());
  await page.getByTestId("tab-settings").click();
  await page.getByTestId("cap-design").fill("12.5");
  await page.getByTestId("cap-daily").fill("40");
  await page.getByTestId("save-caps").click();
  await expect(page.getByTestId("caps-msg")).toHaveText("Saved to config/finance.yaml.");
  const caps = await apiGet("/settings/spend-caps");
  expect([caps.per_design_usd, caps.daily_usd]).toEqual([12.5, 40]);
  const env = JSON.parse(readFileSync("test-results/e2e-env.json", "utf8"));
  const line = readFileSync(env.S2S_FINANCE_CONFIG, "utf8").split("\n").find((l: string) => l.startsWith("spend_caps:"));
  console.log(`finance.yaml (e2e copy): ${line}`);
  expect(line).toBe("spend_caps: {per_design_usd: 12.50, daily_usd: 40.00}");
  await expect(page.getByTestId("spent-today")).toHaveText(/^\$\d/);
  await shot(page, "settings", true, "part28-screenshots");
});
