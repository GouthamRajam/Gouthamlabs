# S2S — Spec-to-Silicon

An AI design team that takes a written chip spec to a tape-out-ready GDSII layout,
proves every step with real EDA tools, and lets human experts approve at clear gates.

- **What to read first:** `docs/MASTER_SPEC.md` (the full specification, v2.4).
- **How to build:** `SESSION_PROMPTS.md` — paste one session prompt per coding session,
  in order (M0.1 → M0.9). Each milestone has acceptance tests that define "done".
- **Research behind the plan:** `docs/RESEARCH_NOTES.md`.
- **Config:** `config/` holds budgets, management SLAs, finance, Scout, readiness and flow ranges.
- **Benchmark chips:** `designs/` holds the five Phase 0 design requests.
- **Live Office demo (simulation):** open `demo/live_office.html` in a browser.

## Status
Scaffold only. No code is implemented yet — that is built milestone by milestone,
starting at M0.1 (foundations and the EDA runner).

## Phase 0 goal
Five small digital blocks (counter8, uart, sync_fifo, alu8, spi_master) each reach a
clean GDSII on SKY130 with no human edits, verified by open-source tools, with a
Tape-out Readiness Report per design.

## Important before you start
This project sits in the semiconductor field. If you are employed in that field,
have an employment lawyer review your invention-assignment and outside-activity
terms first. Build only on personal equipment and time, with open-source tools and
public designs. This note is not legal advice.
