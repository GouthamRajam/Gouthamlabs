# PART 27 — THE SIGNOFF COCKPIT

The Signoff Cockpit is the operator UI for looking at every parameter a run produced,
against its limit, with pass/fail and trend across runs. It is the human's window into
the thousands-to-tens-of-thousands of individual values the EDA tools emit. It reads
only from the `checks` table (Part 11) — it never computes a pass/fail itself, and the
AI never writes a value into it. The tools write; the cockpit displays.

## 27.1 Drill-down levels
Design → Run → Stage → Check → Parameter. One click per level.
- **Design**: counter8, uart, sync_fifo, alu8, spi_master (Phase 0); the RISC-V core (Phase 1+).
- **Run**: a dated attempt. The cockpit compares a parameter across the last N runs (sparkline).
- **Stage**: Verification, Synthesis/STA, Power/IR/EM, DRC, LVS, DFM/Yield, DFT.
- **Check**: one tool invocation (e.g. "Setup timing (SS corner)" by OpenSTA).
- **Parameter**: one measured value, its limit, comparison, unit, layer/corner, pass/fail, trend.

## 27.2 Parameter categories (why it is thousands)
| Stage / layer | Parameters shown | Rough count |
|---|---|---|
| Verification | test × seed pass/fail; coverage bins (line, toggle, FSM, functional, assertion) | thousands of bins |
| Synthesis / STA | per-path setup & hold slack × every timing corner; max transition/cap/fanout per net | tens of thousands of endpoints |
| Power / IR / EM | IR drop per node; electromigration per wire segment | thousands |
| DRC | violation count per design rule, per layer | hundreds–thousands |
| LVS | device and net match counts, every mismatch | per-device |
| DFM (our wedge) | metal density per window per layer; via-redundancy ratio; near-limit score per layer; hotspots | thousands of windows |
| DFT | fault coverage, per scan chain | hundreds |

## 27.3 The two views that matter
- **Fails only.** Everything not passing, across all stages — the rework list.
- **Within 5% of limit.** Parameters that pass today but sit close to their limit. This is
  the DFM/yield early-warning screen — the thing a fab person looks at that nobody else
  shows. Computed as `|value − limit| / |limit| ≤ 0.05` for passing parameters
  (skipped when the limit is 0, i.e. a "must be exactly zero" hard check).

## 27.4 Tape-out readiness coupling
Hard checks (DRC, LVS, timing endpoints, mismatches) are **pass/fail, never a percentage**.
If any hard check fails, the cockpit shows `BLOCKED`, not a score. The scored percentage
(Part 22) is shown only when all hard checks pass. The cockpit must never present a
percentage that hides a failing hard check.

## 27.5 Where it is built
A thin stub rides with the Live Office dashboard tabs (M0.4). The full cockpit is built in
**M0.8**, when real end-to-end runs produce real parameter data. Building it earlier would
show an empty shell — there are no real parameters until the agents run real tools in M0.6–M0.7.

## 27.6 Data contract (confirm in M0.3, so nothing is back-filled)
The `checks` table — or a child `check_params` table — MUST capture, per parameter:
`check_id, name, value (numeric), limit (numeric), comparison ('<='|'>='|'=='),
unit, layer_or_corner, pass (bool), run_id`, with an index on `(run_id, stage)` and
`(check_id)`. Stage-level pass/fail alone is NOT enough — the cockpit needs the
per-parameter value-vs-limit rows, or the drill-down has nothing to show.
