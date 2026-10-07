# OCV-derated signoff results (CEO decision 2026-10-07)

Derated STA is a permanent signoff check. OpenSTA re-times all 9 corners with a flat derate: `set_timing_derate -early 1-p -late 1+p`, with CRPR on and the SDC's 0.25 ns clock uncertainty still applied. It runs at +/-5% (check `sta_derated_5pct`) and +/-10% (check `sta_derated_10pct`). The +/-10% run is the hard check (`config/signoff.yaml` `ocv.gate_pct`).

**Caveat:** SKY130 has no foundry OCV/AOCV tables, so flat derates are an engineering estimate, not foundry signoff.

Worst slack over the 9 corners, in ns:

| Block | Source | Nominal setup / hold | +/-5% setup / hold | +/-10% setup / hold | +/-10% gate |
|---|---|---|---|---|---|
| counter8 | recorded signoff check (run_01M43B9BVD8M5ANEVYTE43N0KN) | see report | +1.750 / +0.098 | +1.487 / +0.081 | PASS |
| alu8 | recorded signoff check (run_01M44DR7XRWAQ9XY53AG8SRJCM) | see report | +2.958 / +0.387 | +2.640 / +0.354 | PASS |
| uart | recorded signoff check (run_01M47BE6QKCPAEAE7RVYYJ9TEY) | see report | +5.172 / +0.075 | +4.674 / +0.032 | PASS |
| spi_master | recorded signoff check (run_01M484JWYZ7ADCE8N97SZV80QG) | see report | +8.650 / +0.086 | +8.363 / +0.057 | PASS (still CONDITIONAL: clock-net fanout rule 20; measured skew 6 ps; CTS fix is Phase 1) |
| sync_fifo (signed original) | **what-if measurement**, not a recorded signoff (read-only copy of the signed netlist) | +0.243 / positive | -0.082 / positive | -0.408 / positive | **FAIL** |
| sync_fifo design change #1 (registered rd_data) | **what-if measurement**, not a recorded signoff (P&R it3 routed netlist, run_01M4A7YXRDRF2TV0HY1ERGQJ0A) | +0.018 / positive | -0.523 / - | -1.063 / +0.074 | **FAIL** (worse; path now fully on-chip) |

The nominal values for the four passing blocks are in each run's `reports/tapeout_readiness.md` ("Timing: nominal next to flat OCV derates"). sync_fifo's readiness report shows OCV as NOT RUN and the block as FAIL.

**Status:** sync_fifo is FAIL on the Phase 0 gate until design change #2 (run_01M4A93ZB1F1BAFC6ZQFSFB6RA) passes recorded derated signoff. The signed `tapeout/` packages were not modified.
