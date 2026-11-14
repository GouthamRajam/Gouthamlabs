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
| sync_fifo design change #2 (registered read-mux selects) | **what-if measurement**, not a recorded signoff (P&R it3 routed netlist, run_01M4AFNT5QK68FGT27TVRBYWZN) | +2.507 / +0.109 | +2.201 / +0.092 | **+1.896 / +0.075** | timing PASS; block **FAIL** (P&R not clean: antenna; stopped at tool budget) |

Change #2 solved the derated timing failure at the RTL level. Its OpenSTA nominal number matches OpenLane's own post-route STA on the same netlist (+2.5068 vs +2.5068 ns). sync_fifo stays FAIL because P&R did not close clean: one antenna violation in iteration 3 (net34, ratio 1.03); heuristic diode insertion in iteration 4 fixed it but added about 2,550 diodes (instance count 4,307 -> 6,858 in OpenLane metrics.json), giving clock-buffer fanout up to 25 and 18 max-slew violations; iteration 5 (diodes off, density 60 %, margin 30 %; budget raised by the CEO to 20) left 2 antenna violations on other input-buffer nets. Root cause: global-route antenna repair sees the gate tied to the driver diffusion on met1 (allowed ratio 2,736); the detailed route splits the net across layers (allowed 400); OpenLane 2.3.10 has no antenna repair on the detailed route. P&R stopped at 18 of 20 tool runs; only the physical cleanup is pending (Phase 1 flow step).

The nominal values for the four passing blocks are in each run's `reports/tapeout_readiness.md` ("Timing: nominal next to flat OCV derates"). sync_fifo's readiness report shows OCV as NOT RUN and the block as FAIL.

**Status:** sync_fifo is FAIL on the Phase 0 gate. Design change #2 (M0.6 run_01M4A93ZB1F1BAFC6ZQFSFB6RA, M0.7 run_01M4AFNT5QK68FGT27TVRBYWZN) fixed the timing, but its P&R did not close clean within budget, so no recorded derated signoff exists for it. The signed `tapeout/` packages were not modified.
