# Settings → Model Access and Spend controls (MASTER_SPEC Part 28), thin version

**Status: built and tested. One thing is still open:** a *passing* Test connection needs a
real Anthropic API key, and none exists in this environment. The button was proven against
the real Anthropic API with an invalid key: the API answered `401 authentication_error`, and
the screen showed exactly that, with the latency and model. Nothing in this report is a
mocked model result.

## What was built (plain English)

### A Settings tab in the Live Office (http://localhost:3000 → Settings)

**Model access card**
- **Provider:** Anthropic API, On-prem model endpoint, or AWS Bedrock.
- **API key field:** a password field with a Save button.
  - After saving, the field clears and shows only `Saved key: ••••••••abcd` (the last 4
    characters).
  - The key can be replaced, never read back.
- **Default model for all agents:** `claude-sonnet-5-5` (Sonnet 5.5).
- **Test connection:** makes **one** small model call (16 output tokens max, thinking off,
  no retries) and shows ✓/✕, latency in ms, the model, and the API's own error text.
- **On-prem:** asks for an endpoint URL. It must speak the Anthropic Messages API, and calls
  stay inside your network.
- **Bedrock:** can be selected and saved, but its calls are not wired yet (Part 28.6 puts
  Bedrock in the hardened version). The screen and Test connection both say so rather than
  pretend.

**Spend controls card**
- Per-design cap and daily cap, in USD.
- Saved to `config/finance.yaml` (`spend_caps:`). Only that one entry is rewritten;
  comments are kept.
- The screen also shows what has been spent today.

### Where the key lives, and how it is protected
- **Encryption at rest:** the browser sends the key once (`PUT /settings/model-access`). The
  backend encrypts it with **Fernet** (AES-128-CBC + HMAC-SHA256, from the `cryptography`
  library).
- **Files:**
  - The encrypted key is `<S2S_SECRETS_DIR>/model_access.enc`, mode **0600**.
  - The encryption key comes from `S2S_SECRETS_KEY` if that is set (the place for a key from
    a key-management service), else `<S2S_SECRETS_DIR>/master.key`, also mode 0600,
    generated once.
- **Where the folder is:**
  - Locally: `var/secrets/`, which is **git-ignored** (`var/`, `*.enc`, `master.key`).
  - In docker compose: a named volume `secrets`, mounted only into the backend containers.
- **Who reads it:** the model gateway decrypts the key in the backend process at the moment
  of each call, so a replaced key applies to the next call with no restart.
  - `ModelGateway.from_settings()` is what the M0.5 agents will use.
  - Calls go through the official `anthropic` Python SDK (1.11.0).
- **What never sees it:**
  - The API only ever returns the masked form.
  - Bad input to the Settings endpoints gets a 422 that does **not** echo what was sent.
  - The browser keeps it in no storage.
  - Nothing logs it.

### Spend caps that stop a run
- **Before** every model call, the gateway checks today's spend and the design's total spend
  against the caps.
- After every metered cost (model call or tool run), the same check runs again.
- When a cap is reached, the task stops with the existing hard-stop path: it is paused and an
  escalation is raised ("Hard budget stop: per-design spend cap reached …").
- **Honest limit:** the call that crosses the cap has already happened; its cost is only
  known when it returns. So spend can pass a cap by at most one call per task that is running
  at that moment. In the tests, that was $0.0005 to $0.001 over a $0.004 cap.

### Metering
- The Test-connection call is metered like any other call, under agent "settings".
- The Sonnet 5.5 price was added to `finance.yaml`: $2 / $10 per million tokens (Anthropic
  list price).

## Acceptance output (real runs)

### Backend: `pytest tests/platform/test_settings_part28.py -v -s` (real Postgres/Redis, real Anthropic API)
```
test_key_is_encrypted_at_rest_masked_and_write_only
PUT response: {"provider": "anthropic", "endpoint": null, "model": "claude-sonnet-5-5", "key_set": true, "key_masked": "••••••••Q9Z4", ...}
model_access.enc: mode 0o600, 356 bytes
master.key: mode 0o600, 44 bytes
ciphertext starts: gAAAAABqwYpMSxa7_SPyC7RA ...
PASSED
test_secret_files_are_gitignored
.gitignore:12:var/	var/secrets/model_access.enc
.gitignore:12:var/	var/secrets/master.key
.gitignore:13:*.enc	backend/x/model_access.enc
PASSED
test_test_connection_reaches_the_real_api
no key saved -> {'ok': False, 'latency_ms': None, 'model': None, 'error': 'no API key saved (Settings -> Model access)'}
invalid key  -> {'ok': False, 'latency_ms': 71, 'model': 'claude-sonnet-5-5', 'error': 'HTTP 401 authentication_error: API key is invalid.'}
bedrock      -> {'ok': False, 'latency_ms': None, 'model': None, 'error': "provider 'bedrock' is not wired yet (Part 28.6: hardened version)"}
PASSED
test_gateway_sends_the_stored_key
gateway call with the stored fake key -> AuthenticationError 401
PASSED
test_key_never_logged_or_stored_in_plaintext
api debug log: 9 lines; files containing key: []; events rows: 0; usage rows: 0; redis stream entries containing key: 0
PASSED
test_spend_cap_stops_the_run[per_design_usd]
finance.yaml now: spend_caps: {per_design_usd: 0.004, daily_usd: 150.00}
stop event: Hard budget stop: per-design spend cap reached: $0.0045 spent of $0.004; task paused for approval
model calls metered: 7; spent $0.004514 vs cap $0.004; paused: ['Vera', 'Ada']; run status: running
PASSED
test_spend_cap_stops_the_run[daily_usd]
finance.yaml now: spend_caps: {per_design_usd: 75.00, daily_usd: 0.004}
stop event: Hard budget stop: daily spend cap reached: $0.0050 spent of $0.004; task paused for approval
model calls metered: 8; spent $0.005045 vs cap $0.004; paused: ['Vera', 'Ada']; run status: running
PASSED
7 passed in 18.27s
```
"Never logged" was tested hard:
- The API ran at **debug** log level and was driven over HTTP: save, test, read and a bad
  request.
- Then every file in the test's folder, the events table, the usage records and the Redis
  event stream were searched for the key. It was found in none of them.

### Browser: `npx playwright test settings.spec.ts` (real web app → real API → real Anthropic API)
```
  ✓  1 settings.spec.ts › Model access: key is saved server-side, masked, never kept in the browser
Test connection with the invalid key: ✕ Failed · 39 ms · claude-sonnet-5-5 · HTTP 401 authentication_error: API key is invalid.
  ✓  2 settings.spec.ts › Test connection makes one real call: an invalid key fails with the API's own 401
  -  3 settings.spec.ts › Test connection with a real key passes (only when S2S_TEST_ANTHROPIC_KEY is provided)
finance.yaml (e2e copy): spend_caps: {per_design_usd: 12.50, daily_usd: 40.00}
  ✓  4 settings.spec.ts › Spend controls: caps are saved to finance.yaml and shown back
```
Test 1 checks five things:
- The key went to the backend **exactly once** (`PUT /settings/model-access`).
- No response ever contained it.
- `localStorage`, `sessionStorage`, cookies and the page HTML don't contain it.
- After a reload the field is empty but the masked key is still shown.
- The encrypted file on the server holds no plaintext.

Test 3 is skipped here because there is no real key. Run it with
`S2S_TEST_ANTHROPIC_KEY=<your key> npx playwright test settings.spec.ts`.

### Through docker compose (rebuilt images)
```
PUT  -> {"provider":"anthropic",...,"key_set":true,"key_masked":"••••••••C0MP",...}
api container:   -rw------- master.key   -rw------- model_access.enc   (gAAAAABqwYir-sxD... ciphertext)
orchestrator container decrypts the same secret: key ends C0MP model claude-sonnet-5-5
key in all container logs: 0 occurrences
```
- **What this proves:** the api and orchestrator containers share the encrypted secret.
- **One environment quirk:** in this cloud sandbox, containers can't reach the internet
  directly; outbound HTTPS is intercepted by the sandbox's own certificate. So Test
  connection from the compose API answered `could not reach the provider: APIConnectionError`.
- **Re-run trusting that certificate:** the same container code reached the real API, with
  the compose file unchanged:
  `{'ok': False, 'latency_ms': 92, 'model': 'claude-sonnet-5-5', 'error': 'HTTP 401 authentication_error: API key is invalid.'}`.
  On a normal machine no extra step is needed.
- **Cleanup:** the test key was then deleted from the compose volume, so the stack starts
  with no key.

### Full suites after the change
- Backend: `182 passed, 4 skipped` (the skips are the opt-in slow OpenLane runs).
- Playwright: `13 passed, 1 skipped` (the real-key test).

## Screenshots
- `part28-screenshots/settings-test-invalid-key.png`: Test connection's real 401 result.
- `part28-screenshots/settings.png`: masked key and saved caps.

## Known limits (thin version, per Part 28.6)
- **No login or roles yet.** Anyone who can reach the API can replace the key or the caps;
  Part 28.5 #4 comes with the hardened version. The key still can never be *read* through the
  API.
- **Encryption key placement.** When `S2S_SECRETS_KEY` is not set, the encryption key file
  sits next to the encrypted file. That protects the key in a copied database or a log, but
  not against someone holding the whole secrets volume. For production, set
  `S2S_SECRETS_KEY` from a key-management service.
- **Bedrock** is selectable but not wired.
- **Deployment-mode screen** (Part 28.4) and **model routing** (Part 28.3) were not part of
  this request.
- **Cap overshoot:** a cap can be passed by at most one in-flight call per running task (see
  above).
- **Real-agent features left for M0.5:** server-side refusal fallbacks and the effort setting
  for the agents' real calls. Only the call plumbing exists now.
- **Old placeholders:** `.env.example` still lists `ANTHROPIC_API_KEY`, but nothing reads it
  any more; the Settings screen replaces it.
