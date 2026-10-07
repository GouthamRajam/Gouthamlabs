# Trajectory format (schema 1)

One run = one JSON-lines file, in order, produced by

    cd backend && python -m s2s.records.trajectory export <run_id> -o <file>.jsonl

Sample: `docs/trajectories/sample_run_01M4AFNT5QK68FGT27TVRBYWZN.jsonl` (sync_fifo design change #2, M0.7).

## Records
Every record has `seq`, `kind`, `ts`, `id` (stable: event / check / call / analysis / decision id), `run_id`, `task_id`,
`agent` and `labels`.

| kind | from | content |
|---|---|---|
| `run` (first) | runs | design, stages, status, `autonomy` (`autonomous` or `operator_influenced`), `operator_influence` (the reasons), counts |
| `task` | tasks | agent, stage, status, budget, usage, attempts (placed before the task's first record) |
| `plan` | events | the agent's plan for a step |
| `tool_call` / `tool_result` | events | tool or model started / finished, with tool facts in `detail` |
| `model_call` | logs/model_calls.jsonl | goal, attempt, prior feedback, model hint/effort, model, `answered_by`, `operator_influenced`, bridge request ids, system prompt sha256, full prompt and answer |
| `check` | checks + check events | name, tool, tool_version, passed, metrics, command |
| `finding`, `handoff`, `escalation`, `gate`, `stage`, `task_event`, `stall`, `budget`, `artifact` | events | as recorded |
| `analysis` | analyses | what-if / diagnosis done outside the flow's steps: method, input hashes, results, sources; never a signoff |
| `decision` | docs/decisions/*.jsonl | decisions whose links include the run (structured schema, or legacy prose) |
| `outcome` (last) | runs, tasks, gates, checks | run and task status, gates, failed checks, `verdict` (pass / fail / incomplete) |

Heartbeats, agent status and manager check-ins are counted in the header and omitted (`--with-heartbeats` lists
heartbeats).

## Labels (annotations, append-only)
| label | meaning |
|---|---|
| `false_alarm` | a `stall` raised while a tool or model call was running (no heartbeats during tool runs before harness #3) |
| `operator_influenced` | an operator decision, resume or correction, or an operator note given to a model call, affected this record |
| `manual_intervention` | the operator changed task/run state, config or files by hand |
| `answered_by` | which model answered a bridge request (backfilled from the operator session for Phase 0) |

A run is `autonomous` only if nothing in it carries `operator_influenced` or `manual_intervention`.

## Model-call schemas
- Schema 2 (from 2026-10-07): carries its own `call_id`, `ts`, goal, attempt, prior feedback, provenance and system
  prompt hash. A bridge call's answering model and any operator note are recorded with
  `python -m s2s.ops.bridge assign`; a note is put inside the request, never given around it.
- Schema 1 (Phase 0): only task, agent, prompt and answer. The exporter places it at the matching model `tool_call`
  event of the task in order (`alignment: "by_order"`), finds its bridge request by the exact prompt text, and takes
  `answered_by` from the backfilled label (`source: backfilled from the operator session transcript`).

## Known limits
- Legacy decisions (116 prose entries in DECISIONS.md, `docs/decisions/legacy.jsonl`) are unstructured; only ids
  present in their text are linked. Decisions about a run that were restated in the schema `supersede` their
  legacy entry.
- Operator influence is labelled from what was recorded (operator events, the session transcript). Interventions that
  left no record cannot be labelled.
- One Phase 0 stall alarm (Rex, 2026-10-04 12:40) had no running tool and is not labelled.
