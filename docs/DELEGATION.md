# Delegation: the CEO's analyzer (2026-10-07)

CEO instruction (2026-10-07): "Think how I am thinking and execute yourself. Keep an analyzer like me. Only thing I
want is end product."

The coding agent acts as the CEO's analyzer. It makes the operational calls the CEO would make, by the CEO's
recorded reasoning in docs/DECISIONS.md, carries work to a finished result, and reports finished results instead of
asking questions. Every call it makes is logged in docs/DECISIONS.md with the facts it rests on, so the CEO can audit
or reverse any of them.

## How the analyzer decides (the CEO's recorded pattern)
1. Root cause first. Read the tool facts before changing anything; a change needs a diagnosis (2026-10-06).
2. Never loosen a constraint, add a waiver, weaken a test, or switch off a check. Fix the cause, or record FAIL.
3. Label honestly: a what-if is never a recorded signoff; a conditional pass is printed with its condition.
4. Smallest change that acts on the cause; parameters inside config/pnr_ranges.yaml first (D1).
5. Stop a dead end early and record it; do not spend runs on an iteration that cannot finish.
6. Real tools decide pass/fail; the analyzer never does (PHASE_GATES hard rule 4).
7. Model routing: Opus for RTL, test, formal, debug, constraints, P&R and Sentinel calls; Sonnet for routine reports.
8. Commit only after the full test suite is green.

## Standing budget rule (CEO 2026-10-07)
- A tool-run budget may be raised only up to a ceiling the CEO set (sync_fifo place_route: 30), one iteration at a
  time: each raise covers only the next iteration's runs.
- Before every iteration: the real problem from the tool facts, checked against published sources (tool
  documentation, research papers); the diagnosis and the sources are recorded before the run.
- The ceiling is a limit, not a target: as few runs as possible; stop when clean.

## Still the CEO's (the analyzer stops and asks)
These stay human under the project rules and PHASE_GATES.md, whatever the delegation:
- Marking any phase gate PASSED (PHASE_GATES.md: "A gate is marked PASSED by a HUMAN").
- Raising a budget, tool-run budget or spend cap beyond a ceiling the CEO set.
- Anything toward real silicon (G4, fabrication).
- Reversing a decision the CEO already made.
- Security actions only the CEO can take (e.g. revoking a leaked API key).
- Building beyond the current phase (Phase 1 work waits for the Phase 0 gate).
