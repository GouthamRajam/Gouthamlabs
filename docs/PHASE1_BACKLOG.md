# Phase 1 backlog (written 2026-10-07, end of Phase 0 / M0.7)

Two separate lists. Nothing here is built until the Phase 0 gate is marked PASSED by a human (PHASE_GATES.md).

## A. Phase 1: harden the harness (orchestration problems hit in Phase 0)
1. **Tool-budget hard stops land mid-iteration.** The meter stops a task once usage reaches the limit, after the run that
   reached it (sync_fifo fix #1 at 16/16; fix #2 at 14/16 could not fit any iteration: a placement iteration stops
   after CTS, a routing-only one after the DRV check, before its result is evaluated). Fix: before an iteration starts,
   check that its whole run count fits; otherwise escalate with the table instead of starting it.
2. **Container restarts lose every process.** dockerd stale pid files, Postgres/Redis down ("connection refused"),
   orchestrator, runners, bridge watchers and monitors all gone. start_all.py relaunches stale one-off jobs (old M0.6
   resumes, old autostart). Fix: a supervisor with a declarative list of long-lived services only, health checks, and
   restart; one-off jobs are resumed from the database, not from a script.
3. **Missing heartbeats on long steps.** Mutation runs, SymbiYosys/ABC proofs and OpenLane stages emit no progress, so
   the stall watchdog escalates false "stalled" alarms. Fix: tool runners emit a heartbeat while a tool is alive.
4. **Checkpoint and resume semantics.** checkpoint.step counts COMPLETED steps, and state.blocked survives into the
   resume, so an operator resume skipped the mutation step and the task completed without a mutation result (lesson
   s2s-ops-004); a synthesis resume at step 6 kept the old strategy because it is read in setup. Fix: a resume API
   that takes a step NAME, clears the block, and asserts the step's report exists afterwards.
5. **Gates.** A G2 opened in error had to be withdrawn by hand in the database; the auto rule (last record of every
   check must pass) was the only safety net. The autostart script exited on a pending G2 and had to be relaunched.
   Fix: a gate withdraw/reopen operation with an event, and launchers that wait on gate decisions instead of exiting.
6. **Mutant generator bug.** stuck_bit dropped the array index (`mem_q[a] <= mem_q;`); the lint screen passed it and
   the C++ build failed, stopping the run (fixed, lesson s2s-mut-003). Fix: screen mutants with a full build, not
   lint only.
7. **Infrastructure refusals shown to agents as design problems.** The disk-headroom guard's ERROR reached Orion as
   "independent DRV check did not run cleanly" (lesson s2s-ops-005). Fix: infrastructure errors pause the task with
   the reason; they never enter an agent's problem list. Disk: rotate/compress simulation VCDs automatically.
8. **Stale code in long-running processes.** The orchestrator keeps the code it started with (lesson s2s-ops-003); it
   had to be restarted by hand after each code change. Fix: refuse to start a stage when the code fingerprint changed.
9. **Process control.** `pkill -f` matched the operator's own shell and killed it. Fix: PID files per service; stop by
   PID only.
10. **Launch environment.** Runners started without S2S_ARTIFACT_DIR resolved to /tmp and failed a run; an autostart
    hit ModuleNotFoundError without an absolute PYTHONPATH. Fix: one launcher that sets and asserts the environment.
11. **Event schema.** An agent step emitted an event type ("result") the schema does not allow; it failed at runtime.
    Fix: validate event types at import/test time.
12. **Bridge operation.** Bridge requests are answered by a watcher that must be re-armed every 30 minutes. Fix: a
    persistent bridge service with its own restart.

## B. Phase 1: EDA / design backlog
1. DFT: scan insertion + ATPG with open tools (OpenROAD DFT + Fault); report fault coverage (dft is scored 0 today).
2. Dynamic IR drop + electromigration (Phase 0 has static IR only; EM not analysed).
3. Simulation-based power from real VCD/SAIF activity (Phase 0 power is vector-less).
4. spi_master clock-tree fix so it passes under the SDC fanout limit 10, not only the clock-net rule 20.
5. sync_fifo physical closure: design change #2 fixed the timing (+1.896 ns setup at +/-10%, what-if on its it3
   routed netlist; verified). P&R does not close because OpenLane 2.3.10 repairs antennas only on the global route,
   which cannot see the layer-split topology detailed routing creates on long input-buffer nets (met1 piece at the
   gate cut off from the driver's diffusion: allowed ratio 2,736 -> 400). Needed: a post-detailed-route antenna repair
   step (diode or layer jump at the gate on the real route, then incremental re-route); heuristic diodes cannot
   target these nets (lesson s2s-ant-001). Then a recorded derated signoff.
6. RISC-V core (the Phase 1 -> 2 gate: official compliance tests).
7. Artifact hash/provenance check ("no human edits" is NOT CHECKED today).
