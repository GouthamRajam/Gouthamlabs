# PART 28 — SETTINGS: MODEL ACCESS, SPEND & DEPLOYMENT MODE

A sellable product never asks a user to edit a file. Credentials and limits are set in a
UI, saved, and stored securely on the server. This part defines that screen. It serves the
founder today and every customer later.

## 28.1 Why this exists
- No file editing. A customer (or the founder) pastes a key in a form and clicks Save.
- Secrets live server-side, encrypted at rest. Never in the browser, never in localStorage,
  never in git, never in a log. The field is masked after save (last 4 chars only).
- Many enterprise customers will not use a cloud key at all — they point S2S at an on-prem
  model. The screen must support that on day one (ties to Part 26.2 hard rules 2 and 3).

## 28.2 Screen: Settings → Model Access
Fields:
- **Provider**: Anthropic API | On-prem model endpoint | AWS Bedrock (extensible).
- **API key / credentials**: masked input, Update button. Sent to backend → stored in a
  server-side secret store (env-backed secret or DB column encrypted at rest). Returned to
  the UI only masked.
- **On-prem endpoint** (when provider = on-prem): URL inside the customer network.
- **Test connection**: makes ONE cheap model call, shows pass/fail + latency + model name.

## 28.3 Screen: Settings → Spend controls (ties to config/finance.yaml)
- **Per-design cap (USD)** and **Daily cap (USD)**: when hit, runs stop. Hard stop, no overage.
- **Model routing**: "cheap first, smart on hard steps" (default) vs "smart everywhere".
  This is the single biggest lever on cost-per-design (Part 26.3).

## 28.4 Screen: Settings → Deployment mode (ties to Part 26.2)
- **Standard (cloud model)** vs **On-prem / air-gapped**.
- On-prem mode guarantees: RTL and GDSII never leave the customer network; the foundry PDK
  stays inside the licensed EDA tool and never enters a prompt or model call.

## 28.5 Security contract (non-negotiable)
1. Secrets are write-only from the UI: you can set or replace, never read back in full.
2. Encrypted at rest; decrypted only in the backend process that makes the model call.
3. Never sent to the browser, never logged, never committed. `.env` (if used at all for
   bootstrap) is gitignored and superseded by this screen once it exists.
4. Role-gated: only an admin/owner role can change model access or deployment mode.

## 28.6 Where it is built
Thin version with M0.5 (so the founder can set the key in a UI instead of `.env`). Hardened
version (encryption at rest, role-gating, on-prem endpoint, Bedrock) matures toward the
first real customer — it does not need to be fully hardened for Phase 0, but the secret must
be server-side and gitignored from the first version.
