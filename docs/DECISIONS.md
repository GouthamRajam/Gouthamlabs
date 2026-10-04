# Architecture Decisions Log
Record every non-obvious decision: date, decision, reason, alternatives considered.

- 2026-10-02 — Phase 0 uses open-source tools + SKY130 only. Reason: no cost, no NDA,
  manufacturable on open shuttles. Alternative (commercial tools) deferred to Phase 1.
- 2026-10-02 — Gate mode defaults to `auto` for Phase 0 (no money, no fabrication);
  `real_tapeout` always requires a human. Reason: see MASTER_SPEC Part 9 and Part 23.
- 2026-10-03 (M0.1) — s2s-eda is built FROM the official OpenLane 2.3.10 image, pinned
  by digest, instead of compiling each tool. Reason: it ships all Phase 0 tools except
  cocotb and the PDK as one toolchain that OpenLane was released and tested with, so
  versions are consistent by construction. 2.3.10 is the final OpenLane 2 release (the
  project continues as LibreLane 3.x); moving to LibreLane is a later, deliberate upgrade.
  Alternative considered: Ubuntu + per-tool source builds (hours of build, version-skew risk).
- 2026-10-03 (M0.1) — The SKY130 PDK is fetched by direct release URL and verified against
  sha256 sums in eda/versions.lock, then activated with `volare enable` from the local
  copy. Reason: byte-exact reproducibility, and no dependence on the GitHub API (which
  volare otherwise calls and which rate-limits / is not reachable from every build host).
  Library set = volare's sky130 default set, because OpenLane's sky130 config references
  sky130_fd_io etc. even though designs only use sky130_fd_sc_hd.
- 2026-10-03 (M0.1) — cocotb is installed into its own venv (/opt/cocotb) appended to PATH,
  because the base image's Nix Python has no pip and must stay the default python3.
- 2026-10-03 (M0.1) — docker-compose.yml has only postgres and redis for now; api, web and
  eda-runner services are added by the milestones that build them (M0.3/M0.4).
- 2026-10-03 (M0.2, approved by the human before work continued) — Fixed s2s-eda gaps found
  while building the M0.2 adapters: the image had no make, C++ compiler, perl, awk, sed or
  SMT solver, and yosys-witness lacked its `click` module. So Verilator simulation, eqy, and
  SymbiYosys's default engine could not run, although M0.1's version-only selftest passed.
  Fix: install make, clang, perl, gawk, sed, yices, z3 from the same nixpkgs revision the base
  image was built from (OpenLane 2.3.10's flake.lock), as signed prebuilt binaries pinned by
  store path in versions.lock, plus a yosys-witness wrapper that adds click. The selftest now
  also runs tiny real jobs (proofs, a counterexample, an equivalence, cocotb on Verilator and
  Icarus) so "installed but unusable" fails the selftest. Alternative considered: run only
  on the engines that worked (abc pdr, Icarus) and leave eqy unusable; rejected by the human.
- 2026-10-03 (M0.2) — Adapters run each tool with `docker run --rm --network none s2s-eda`,
  mounting the task's working directory at the same absolute path (inputs must live
  there). Every result records command, pinned tool version, env hash (image id +
  versions.lock), duration and raw log path; timeouts kill the container and return TIMEOUT.
- 2026-10-03 (M0.2) — One pass/fail path (s2s/trust/safety_net.py): exit 0 AND parser errors
  0 AND no stage-rule failure AND no known failure string in the log AND success marker
  present. No allow-list/waiver exists; a pattern that misfires on a clean log is made
  more precise (e.g. OpenSTA's benign "module ... not found. Creating black box" warnings
  for physical-only cells meant the pattern `not found` was removed, not allow-listed).
- 2026-10-03 (M0.2) — Stage rules that fail even when the tool exits 0: inferred latch or
  logic loop (Yosys), any -Wall lint warning (Verilator), any DRC violation (Magic, KLayout),
  LVS not "match", negative setup/hold slack, zero cocotb tests, sby PASS with no properties.
- 2026-10-03 (M0.2) — sby: only basecase/BMC traces are counterexamples; [induction] traces are
  reported separately (k-induction artifacts, possibly unreachable states).
- 2026-10-03 (M0.2) — netgen_lvs uses the PDK's own Netgen setup (sky130A_setup.tcl); on spm it
  gives the same result as OpenLane's LVS (330 devices / 359 nets, "Circuits match uniquely").
- 2026-10-03 (M0.2) — klayout_dfm (listed in Part 7.5) is not in M0.2: the M0.2 request listed
  ten adapters without it, and its checks are defined with DFM in A.15 / M0.7.
- 2026-10-03 (M0.3) — Org structure (Part 6.2-6.4) transcribed into config/management.yaml
  `org:` (the file previously only pointed at the spec); agent ids are agent names. Teams
  the spec marks Phase 1+/2+ carry `phase:` so they are never activated in Phase 0.
- 2026-10-03 (M0.3) — Fixed a YAML syntax error in config/budgets.yaml
  (`Euclid:{...}` -> `Euclid: {...}`); the file had never been parsed before M0.3.
- 2026-10-03 (M0.3) — Resumable tasks: each agent step runs in one DB transaction that also
  writes its heartbeat and the new checkpoint; after a crash the task restarts at the first
  uncommitted step. Single active orchestrator enforced with a Postgres advisory lock;
  on start it takes over tasks a dead process left `running`.
- 2026-10-03 (M0.3) — Two kinds of events. State events (heartbeat, artifact, check, gate,
  task/stage changes...) are written in the transaction of the rows they describe and
  published after commit, ts = commit time, so the feed never shows rolled-back work. Live
  action events (agent.status, plan, tool_call, tool_result) commit and publish immediately.
  Reason: first version published everything at commit, so "tool started" appeared only when
  the step finished (p95 529 ms with 0.5 s steps; with real tools it would be minutes).
- 2026-10-03 (M0.3) — Metering commits each usage_records row immediately in its own
  transaction (a model call costs money even if its step later fails/re-runs); usage totals
  are always computed from usage_records. Budget warnings at 80% (task) / finance alerts_pct
  (run); a task at 100% of its budget is hard-stopped: paused + escalation, never continues.
- 2026-10-03 (M0.3) — Model gateway has only a dummy provider (no network, deterministic,
  priced via finance.yaml `model_prices.dummy-model`, labelled placeholder). Real providers
  and model_hint routing arrive with the real agents (M0.5). The dummy agent's tool results
  and checks are all marked `simulated: true` / "[dummy]" (Part 12 rule 5).
- 2026-10-03 (M0.3) — knowledge.embedding (pgvector) deferred to the knowledge base (M0.5);
  the Postgres image is unchanged until then.
- 2026-10-03 (M0.3) — Gates G1-G4 sit after spec+architecture, verification, signoff, gdsii
  (Part 6.1 zone exits). gates.mode=auto approves only when the stage's latest result for
  every check passed; `human` mode waits for POST /gates/{id}/decision.
- 2026-10-03 (M0.4) — Live Office seats are generated at build time from
  config/management.yaml (web/scripts/gen-org.mjs -> src/generated/org.json), so the floor
  always shows exactly the org the orchestrator loads: 66 agent seats + 5 human desks.
  Added `mission:` to the 46 teams whose Part 6.3 table has a Mission column (Div 6/7 tables
  have none, so those seats show no mission), and `org.humans` (CEO, VP Front-End,
  VP Physical, VP Platform, CFO, with the gates/approvals Part 6.1/19 give them).
- 2026-10-03 (M0.4) — Live, replay and demo all feed the same reducer (web/src/lib/store.ts
  `applyEvent`), so a visual that works in one mode works in all. Live = backfill
  `/events?limit=300` then `/ws/events` (reconnects with `since=`); replay = a stored run's
  `/events` re-timed by speed (gaps capped at 3 s); demo = a scripted run.
- 2026-10-03 (M0.4) — Demo is a simulation and is labeled as one everywhere (Part 12 rule 5):
  "Simulation" badge, banner, a SIM tag on every feed item, `detail.simulated=true` on every
  event, run ids `sim_run_*`, and a note on the dashboards. The page picks live only when the
  API answers /health; otherwise demo, never an unlabeled view.
- 2026-10-03 (M0.4) — API additions for the web app: CORS (origins from S2S_CORS_ORIGINS,
  default localhost:3000), `GET /runs` (replay picker), finance summary `today_usd` + `as_of`.
  Finance tab shows amounts rounded to the cent with exact values on hover; runway shows
  "n/a" until ledger data exists (M0.9), never an estimate.
- 2026-10-03 (M0.4) — Part 12.4 #2/#3 are measured, not assumed: click-to-panel with the
  browser's Event Timing API on real clicks of all 71 seats (input -> next paint), fps by
  counting rAF frames for 10 s with 20+ agents working. Playwright trace recording is off for
  these two tests (it alone cost ~15 fps and ~50 ms per click). Rendering rules that keep clicks
  fast on CI's GPU-less software renderer (first CI run: 104 ms, profiled under 2x CPU slowdown):
  continuous animations are stepped and phase-locked (one hopping dot per working seat, not three
  independently fading dots); no full-floor `will-change` layer (it promoted 44 more elements:
  140 layers); no box-shadow transitions (not compositor-capable); feed rows memoized with
  content-visibility. Rooms keep `contain: layout`, the panel `contain: layout paint` + sticky.
- 2026-10-03 (M0.4) — Every event type's visual carries `data-effect="<type>"`; the e2e test
  watches the DOM (MutationObserver) during a real dummy run and requires an effect for all
  21 types. Transient visuals expire (tool chip 2.5 s, bubble 4.5 s, decided-gate banner 6 s,
  escalation toast 8 s); a manager's stall flag clears when that task reports progress.
- 2026-10-03 (M0.4) — Compose gains `web` (web/Dockerfile, Next.js standalone, :3000; the
  browser calls the API at <host>:8000). Playwright runs its own `next start` on :3100 against
  its own API stack (backend/scripts/e2e_stack.py: fresh DB, fast SLAs, tiny budgets on :8100)
  so tests never touch a running compose stack or its data.
- 2026-10-03 (M0.3 schema) — Added check_params child table (migration 0002) for per-parameter value-vs-limit rows per Part 27.6; plain FK to checks and runs, run_id/stage denormalized onto each row, column named limit_value (limit is reserved).
- 2026-10-03 (Part 28) — Settings -> Model access/Spend controls, thin version: key stored server-side as a Fernet-encrypted file (S2S_SECRETS_DIR, 0600; key from S2S_SECRETS_KEY or a generated master.key; var/ git-ignored; compose volume `secrets`), write-only from the UI (masked to last 4), read by the gateway per call via the official anthropic SDK; default model claude-sonnet-5-5 for all agents. Spend caps live in config/finance.yaml `spend_caps` (UI rewrites that entry; compose mounts ./config) and are checked before every model call and after every metered cost; a reached cap pauses the task via the existing hard-stop path (overshoot <= one in-flight call per running task). Bedrock selectable, not wired (Part 28.6). No auth/roles yet.
- 2026-10-04 (M0.5) — Spend caps set to $2.00 per design and $5.00 per day (Settings -> Spend controls, at the CEO's request). API key loaded from env S2S_ANTHROPIC_KEY into the encrypted Settings store through `PUT /settings/model-access`; never printed or logged.
- 2026-10-04 (M0.5) — One task per stage (spec, architecture, rtl), run by the stage's team lead; inside it each agent acts in its own metered model call (usage_records.agent_id = that agent). Agents answer in a JSON schema (Messages API structured outputs): their B.6 task.result fields plus files/findings/report. The runtime runs every check itself (jsonschema, s2s.design.checks, Verilator, Yosys); the model cannot report a check result. Model: claude-sonnet-5-5 for all agents; effort per agent in agents/defs (medium for writers and Sentinel, low for Ivy/Pascal/Watt/Sage). Sentinel's `model_hint: reviewer` maps to the same model in Phase 0.
- 2026-10-04 (M0.5) — No server-side refusal fallback to another model: a refusal or a cut-off answer is metered and fails the task visibly (ModelOutputError). Reason: a fallback model may have a different price, and finance.yaml only prices claude-sonnet-5-5; add fallbacks together with their prices.
- 2026-10-04 (M0.5) — Writers get the Appendix B example (verbatim) plus the exact JSON Schema their file is checked against in the task envelope's `constraints`. Found in the first real run: without it Iris guessed field names three times and the stage correctly paused for a human ($0.21).
- 2026-10-04 (M0.5) — Additions to the Appendix B schemas, needed to make checks mechanical: arch.yaml modules carry `kind` (datapath|control|interface: Reid assigns them to Ada / Ada-C / Ada-I) and `implements` (REQ ids); spec.yaml outputs may carry `reset_value`. Consistency rules: s2s/design/checks.py (spec: Phase 0 PDK/library, clocks/resets are 1-bit inputs, *_n for active-low, reset behavior for every output; arch: top ports = spec I/O, every REQ mapped, widths match on connections, async inputs have CDC entries, slack margin >= 15%; RTL: one module per file, REQ trace comments, elaborated top ports = arch).
- 2026-10-04 (M0.5) — Runtime enforces agents/defs reads_from/writes_to, and for RTL each engineer may write only the modules Reid assigned (others are refused, not written, and reported as a finding). Added after the second real run, where Ada-I rewrote Ada's module.
- 2026-10-04 (M0.5) — Sentinel: only `blocking` findings stop a stage (A.17 rule); after one author revision, blocking findings left pause the task for a human. Major/minor findings are recorded as `finding` events and in reports/sentinel_*.json and stay open for human gate review; G1 auto-approval (Phase 0) does not wait on them.
- 2026-10-04 (M0.5) — Manager/director loops are rules, not model calls, in Phase 0 (A3.1/A3.2 prompts stored for M0.9 reports): assignment brief + SLA, stall review (reassign if no worker holds the task, else escalate one level up; a director who manages a team directly escalates to Atlas), 100% spot check by re-hashing task.result outputs, hourly director review, unresolved manager escalations forwarded to the division's human owner. M0.3's stall test now also asserts the manager's stall review (its original single watchdog escalation assertion is unchanged).
- 2026-10-04 (M0.5) — Knowledge base Phase 0: seed YAML (failure cases, tool knowledge, patterns, checklists; every entry with source URL checked reachable, date, confidence, owner Sage) + lessons Sage writes per run (var/artifacts/knowledge/lessons.jsonl). kb_search is deterministic keyword retrieval, no model call. Model prompts/answers are kept per run in logs/model_calls.jsonl (plaintext under git-ignored var/; Part 7.3 asks for encryption at rest: not done yet).
- 2026-10-04 (M0.6) — Spend caps raised to $5.00 per design and $15.00 per day (CEO request). The M0.6 run of a design belongs to the same design row as its M0.5 run, so cost per design and the per-design cap cover both milestones.
- 2026-10-04 (M0.6) — Independence rule enforced by path permissions: Vera, Mira, Theo, Proto and Euclid (2B) cannot read rtl/**; their only view of the RTL is tb/dut_ports.json (port names/directions/widths extracted by Yosys). Dex and Cora (2C) may read RTL. Formal properties are port-level only (no dut.<signal>), in a wrapper module `formal_top` (open-source Yosys has no SVA bind/`->`; implications written `(!a || b)`).
- 2026-10-04 (M0.6) — N-version reference models: two Mira instances write models independently (neither sees the other's); both run in the sandbox on 2000 seeded random transactions from Vera's transaction format; any difference goes to Vera, who decides from the spec or raises a spec question (pauses for a human).
- 2026-10-04 (M0.6) — Coverage is measured by the tools only: line and toggle from Verilator's coverage.dat (merged over seeds 1-3); functional bins are boolean expressions over port names evaluated on the simulator's own VCD (sampled before each rising clock edge) with a whitelisted expression parser. A testbench cannot claim coverage it did not produce. Targets from config/coverage_targets.yaml.
- 2026-10-04 (M0.6) — Formal: SymbiYosys prove (k-induction) + cover at formal_min_depth; a property counts only if proven, its cover is reached (vacuity) and it FAILS against a stub DUT with free outputs (otherwise it is a tautology). Vacuous/tautological properties go straight back to Euclid.
- 2026-10-04 (M0.6) — Mutation (Myra): deterministic engine (6 bug types of A3.12 plus wrong-operand), type-balanced seeded sample; each mutant screened with real tools: must compile, and is set aside if Yosys equiv_induct PROVES it equivalent (an undetectable mutant). Detection = a failing test or a hang; a run that could not build/run is a harness error, never a detection, and the unmutated RTL must pass the same path first. Fewer than 20 distinct non-equivalent mutants fails the check. Mutant builds use -Wno-fatal (a warning does not stop a real simulation). Found while validating: an unmounted testbench had made every mutant "detected" (fixed before any real run).
- 2026-10-04 (M0.6) — Anti-cheating guard (Part 8.2 #3): AST/YAML diff of every verification change (deleted tests, fewer asserts, smaller loop bounds, new skip/expect_fail, always-true asserts, swallowed AssertionError, removed/changed bins, fewer asserts / more assumes in formal). Any flag -> Sentinel review; rejected changes are reverted. Always-true assertions are also rejected statically in any testbench version.
- 2026-10-04 (M0.6) — Rex and Myra run as rules in Phase 0 (scheduling, seeds, flaky detection by same-seed re-run; deterministic mutation) like the managers; their prompts are stored for M0.9. Model-written testbench and model code only ever runs inside s2s-eda with networking off; static checks forbid file/exec/os access.
