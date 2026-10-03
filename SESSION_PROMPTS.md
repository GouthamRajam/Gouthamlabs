# Session prompts for the coding agent (paste one per session, in order)

Put docs/MASTER_SPEC.md and CLAUDE.md in place first. Then:

## Session 1 — M0.1 (foundations + EDA runner)
Read docs/MASTER_SPEC.md. Implement milestone M0.1 exactly as specified in Part 13.2.
Create the repo layout from Part 13.1 (empty placeholders are fine for later milestones).
Build the s2s-eda Docker image with the Phase 0 tools and the SKY130 PDK, pin versions
in eda/versions.lock, and complete eda/scripts/selftest.sh. Prove acceptance test 2 by
running OpenLane 2 on its bundled spm example and showing zero DRC and LVS errors. Show
the real command output for every acceptance test. Then write docs/milestones/M0.1.md.

## Session 2 — M0.2 (tool adapters + parsers)
Implement M0.2 per Parts 7.5 and 8.2. For each adapter, capture a real passing and a
real failing log as golden files and write parser unit tests. Implement the failure-string
safety net. Run all acceptance tests and show output. Write docs/milestones/M0.2.md.

## Session 3 — M0.3 (DB, events, API, orchestrator skeleton)
Implement M0.3 per Parts 7.6, 7.7, 11. Load org structure from config/management.yaml.
Add heartbeats, the stall watchdog, and usage-metering hooks (Part 19.2). Include a dummy
agent emitting all event types. Prove resume-after-crash. Show output. Write M0.3.md.

## Session 4 — M0.4 (Live Office)
Implement M0.4 per Part 12 (live, replay, demo modes; floor + org views; management +
finance tabs). Seat every division from Part 6. Write Playwright tests. Show output and
screenshots. Write M0.4.md.

## Session 5 — M0.5 (Zones 1 & 2A + manager runtime)
Implement M0.5 using Appendices A and A3 and schemas in Appendix B. Generic director/
manager runtime with assignment SLA and stall handling. Run on counter8 and uart. Show
output. Write M0.5.md.

## Session 6 — M0.6 (verification org: Zones 2B & 2C)
Implement M0.6 (Nadia, Rhea, Vera, Theo, Mira, Proto, Euclid, Rex, Dex, Cora, Myra) with
the independence rule, anti-cheating guard and mutation harness. Run on counter8, uart,
sync_fifo. Show output incl. mutation detection rate. Write M0.6.md.

## Session 7 — M0.7 (Zones 3 & 4)
Implement M0.7 (Mason, Sloane, Sienna, Tess plan, Grid, Orion, Tick, Chronos, Volta,
Calla, Fabian, Gideon, Proof). Drive OpenLane 2 step by step; DRC with Magic AND KLayout;
LVS with Netgen; DFM per A.15. Also complete eda/scripts/verify_gds.sh. Run all five
designs. Show output. Write M0.7.md.

## Session 8 — M0.8 (end-to-end + gates + reports)
Implement M0.8: gate review UI, full runs request->GDSII for all five designs (humans only
approve gates; Phase 0 gate mode = auto), benchmark report, and the Tape-out Readiness
Report per design (Part 22). Show output. Write M0.8.md + a one-page results summary.

## Session 9 — M0.9 (management, finance, research + Scout)
Implement M0.9 per Parts 6.6, 17, 18, 19, 21 and Appendix A3. Set up Scout per Part 21
with config/scout.yaml (standing budget 0) and the provenance ledger. Build certification
suites. Run the stall-injection, finance-reconciliation and research-brief tests. Show
output. Write M0.9.md + the first weekly CEO review pack.

## After Phase 0 passes -> Phase 1 (Part 23)
When all five blocks hit Baseline A ~100% clean, start P1: a small RISC-V (RV32I/IM) core
to clean GDS on SKY130, passing the official RISC-V compliance tests. Then human sign-off,
then an open SKY130 shuttle.
