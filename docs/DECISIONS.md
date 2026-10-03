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
