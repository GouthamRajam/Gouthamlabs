# Trajectory / decision record: audit (2026-10-07, end of Phase 0)

Purpose: the agents and the record of how they work are the product. Each run must leave a structured,
machine-readable trajectory (diagnosis, sources, fix, verification, honest pass/fail) that is training-grade:
complete, attributable, and not polluted. Audit of what is captured today (database counts at the time of writing).

## What is captured well (structured, machine-readable)
| Store | Form | Content |
|---|---|---|
| `events` (8,052 rows) | DB rows: type, agent, stage, task, summary, `detail` JSON | plans, tool calls/results, handoffs, findings (172), escalations (193), gate requests/decisions, check pass/fail |
| `checks` (901) | DB rows: name, tool, command, tool_version, passed, `metrics` JSON | every deterministic verdict, with the tool and its numbers |
| `heartbeats` (1,840), `usage_records` (716) | DB rows | progress evidence; every model call and tool run with cost |
| `artifacts` (668) | content-addressed (sha256) | every file an agent wrote, linked to its task |
| `runs/<id>/logs/model_calls.jsonl` | JSON lines: task, agent, prompt, answer | every model call's full prompt and answer |
| `runs/<id>/reports/*.json` | JSON | tool facts per step (e.g. `pnr_iteration_<k>.json` with problems, facts and Orion's diagnosis) |
| `s2s/knowledge/seed/s2s_lessons.yaml` | YAML, schema-tested | lessons: symptom, root cause, wrong assumption, lesson, evidence, regression test |
| `var/log/supervisor.jsonl` (new) | JSON lines | service starts, restarts, stops |

## Gaps (what keeps the record from being training-grade)
1. **DECISIONS.md is prose.** 112 dated entries carry the diagnosis, sources, fix and verdict, but without a schema
   (no id, actor, linked run/task/check ids, decision type, sources list, outcome). Needed: a structured decision
   log (JSON lines or a DB table) written with each decision, with DECISIONS.md generated from it or kept as a
   human summary.
2. **Model-call provenance is incomplete.** `model_calls.jsonl` lacks the system prompt, the model that actually
   answered, a timestamp, the attempt number and the rejection feedback of earlier attempts (those are in
   `var/bridge/requests`, which is ephemeral, not linked, and not committed). In bridge mode the answering model and
   effort are not recorded at all.
3. **Out-of-band operator inputs pollute the record.** In Phase 0 some bridge answers were given with operator notes
   added to the answering prompt (e.g. "the DRV ERROR was the disk guard"; "18 of 20 tool runs used, escalate").
   The answer then depends on text that is not in the logged prompt. Needed: operator notes go through the request
   (a recorded `operator_note` field), never around it.
4. **Manual database edits are not fully recorded.** Phase 0 operators edited checkpoints, budgets and deleted a
   pending gate row by hand. Most edits have an escalation event, but the deleted gate row itself is gone and edits
   do not carry before/after values. Now replaced by `s2s.ops.jobs` (resume with reason) for resumes; budget
   changes and gate withdrawals still need an API that records before/after.
5. **Research sources are not structured.** Sources for diagnoses (tool documentation, papers) are only in
   DECISIONS.md prose; the `research_briefs` table (author, topic, summary, sources, confidence) is empty.
6. **Empty structured tables.** `findings` (Sentinel findings live only as `finding` events), `check_params`
   (measured value vs limit per check), `requirements` and `trace_links` are unused, so requirement -> test ->
   check -> verdict links must be reconstructed from text.
7. **What-if measurements live outside the database.** E.g. the OCV what-ifs (`var/artifacts/scratch_ocv/`) and the
   antenna analysis (`scratch_ant/`) are referenced from docs only; they need a recorded "analysis" record labelled
   what-if, linked to the run.
8. **Noise labels.** 71 `task.stalled` events were false alarms (tools running without heartbeats; fixed going
   forward by harness #3) but are not marked as such; a consumer cannot tell them from real stalls.
9. **No episode export.** There is no single exporter that turns one run into an ordered trajectory
   (task -> step -> model call -> tool run -> check -> decision -> outcome) with stable ids.

## Recommended next (not built; for the CEO to schedule)
A structured decision log and an episode exporter (gaps 1, 9), recorded operator notes on bridge requests and
model provenance (2, 3), an audited admin API for budget/gate changes (4), and use of `research_briefs` /
`findings` / `check_params` (5, 6), plus a label for the known-false stall events (8).
