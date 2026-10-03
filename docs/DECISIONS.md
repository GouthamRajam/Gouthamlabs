# Architecture Decisions Log
Record every non-obvious decision: date, decision, reason, alternatives considered.

- 2026-10-02 — Phase 0 uses open-source tools + SKY130 only. Reason: no cost, no NDA,
  manufacturable on open shuttles. Alternative (commercial tools) deferred to Phase 1.
- 2026-10-02 — Gate mode defaults to `auto` for Phase 0 (no money, no fabrication);
  `real_tapeout` always requires a human. Reason: see MASTER_SPEC Part 9 and Part 23.
