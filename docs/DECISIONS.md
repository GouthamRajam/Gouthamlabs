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
