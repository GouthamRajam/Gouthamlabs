# Operating S2S (Phase 1 harness)

Run every command from `backend/` with the repo venv. Never put the model API key in the environment of a service:
the supervisor strips `S2S_ANTHROPIC_KEY` and `S2S_MODEL_PROVIDER` from every child (bridge mode is set in
`config/finance.yaml`).

## Services: up, status, down
    python -m s2s.ops.supervisor up        # dockerd, postgres, redis, then orchestrator + api; a loop keeps them up
    python -m s2s.ops.supervisor status
    python -m s2s.ops.supervisor stop api  # one service, by its PID file
    python -m s2s.ops.supervisor down      # the loop, then every service

- After a container restart everything is gone, the supervisor included: run `up` once. It removes dockerd's stale
  pid files, waits for Postgres/Redis to be healthy, then starts the services.
- The service list is `config/services.yaml`. One-off work is never a service.
- Every supervisor action is a JSON line in `var/log/supervisor.jsonl`; service output is in `var/log/<name>.log`.

## Stopping processes: by PID only
Use the supervisor (PID files in `var/run/`, checked against the kernel start time) or `kill <pid>` of a process you
identified exactly. Never kill by pattern (`pkill -f`, `killall`, `pgrep | xargs kill`, `ps | awk | kill`): on
2026-10-07 a pattern kill matched the operator's own shell. `tests/test_no_pattern_kills.py` keeps such commands out
of the code and scripts.

## Resuming a paused task: a database operation, by step name
    python -m s2s.ops.jobs resume <task_id> --reason "<why>"                 # re-runs the step that blocked it
    python -m s2s.ops.jobs resume <task_id> --reason "<why>" --step myra     # or a named step (name#k if repeated)

- The task goes back to `ready` and the orchestrator runs it; it survives restarts (no side process).
- The default resume point is the step that blocked the task (the runtime records it in `state.blocked_step`); the
  stale `blocked` flag is cleared. A resume never moves forward past a step that has not finished.
- Every resume is an `escalation` event with the reason (`detail.rule = "operator resume"`).
- Do not edit `tasks.checkpoint` or `gates` rows by hand: such edits are not in the decision record.

## Budgets
A P&R iteration starts only if all of its tool runs fit before the hard stop (check `pnr_iteration_fits_budget`).
Raising a budget is a CEO decision (docs/DELEGATION.md); record it in docs/DECISIONS.md and in the resume reason.
