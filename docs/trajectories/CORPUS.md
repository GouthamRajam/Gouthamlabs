# Trajectory corpus

Generated from the Phase 0 database (25 runs, 7 designs).
Format: [TRAJECTORY_FORMAT.md](TRAJECTORY_FORMAT.md) (schema 1).

## Totals

| metric | value |
|---|---|
| runs | 25 |
| records | 5,630 |
| corpus size | 20.8 MB |
| autonomous runs | 12 |
| operator-influenced runs | 13 |
| verdict: pass | 19 |
| verdict: fail | 2 |
| verdict: incomplete | 4 |
| model calls | 337 |
| model calls answered (provenance known) | 223 (66%) |
| model calls backfilled (reconstructed) | 223 |
| model calls unrecorded (Phase 0 gap) | 114 (33%) |

## Autonomy breakdown

12 pure-autonomous runs (no operator_influenced or manual_intervention label). 13 operator-influenced runs.

### Model-call provenance

Phase 0 model calls (schema 1) carry no live-captured provenance: the bridge mode logged only 
the prompt and answer. Of 337 total model calls, 223 (66%) have answered_by 
recovered — 223 backfilled from the operator session transcript. 
The remaining 114 are unrecorded (early runs before the backfill data covers them). 
Schema 2 (from harness #9 onward) captures provenance live; all future runs will have 100% coverage.

## Per-run detail

| # | design | run_id | records | model calls | provenance | autonomy | verdict | size |
|---|---|---|---|---|---|---|---|---|
| 1 | counter8 | `N3FTDD2VZXX9` | 50 | 4 | 0/4 (0%) | auto | incomplete | 93 KB |
| 2 | counter8 | `XDQXP23X3CRC` | 126 | 10 | 0/10 (0%) | auto | pass | 251 KB |
| 3 | counter8 | `S31TY5Q7B51W` | 134 | 11 | 0/11 (0%) | auto | pass | 265 KB |
| 4 | counter8_seeded_flaw | `B5VZW5X6R5DA` | 16 | 1 | 0/1 (0%) | auto | pass | 21 KB |
| 5 | uart | `HKAKSF3J94CP` | 148 | 12 | 0/12 (0%) | auto | pass | 411 KB |
| 6 | counter8 | `5DX6YFAQW279` | 116 | 8 | 0/8 (0%) | auto | fail | 369 KB |
| 7 | counter8 | `F42K2CR5PYRT` | 140 | 7 | 0/7 (0%) | oper | pass | 320 KB |
| 8 | sync_fifo | `EERXXPT73EV2` | 135 | 11 | 0/11 (0%) | auto | pass | 339 KB |
| 9 | sync_fifo | `AXR1TNEE09AH` | 180 | 10 | 0/10 (0%) | oper | fail | 635 KB |
| 10 | uart | `C4BCQQVVD6A3` | 608 | 34 | 7/34 (20%) | oper | pass | 4328 KB |
| 11 | dex_triage_suite | `BTTZ4ZRYEN3H` | 55 | 10 | 0/10 (0%) | auto | incomplete | 162 KB |
| 12 | sync_fifo | `S0GAY95XD28T` | 67 | 3 | 0/3 (0%) | auto | pass | 190 KB |
| 13 | counter8 | `NEVYTE43N0KN` | 309 | 17 | 17/17 (100%) | oper | pass | 748 KB |
| 14 | alu8 | `9GEFFW2R1WX7` | 140 | 12 | 12/12 (100%) | auto | pass | 384 KB |
| 15 | spi_master | `JHW1RVZ4H8BH` | 172 | 13 | 13/13 (100%) | auto | pass | 615 KB |
| 16 | sync_fifo | `Q0GGHPJFT602` | 567 | 26 | 26/26 (100%) | oper | pass | 1420 KB |
| 17 | alu8 | `G6KW9JSPWS79` | 229 | 16 | 16/16 (100%) | oper | pass | 1415 KB |
| 18 | spi_master | `HJ8RSESA9S2W` | 389 | 26 | 26/26 (100%) | oper | pass | 3437 KB |
| 19 | alu8 | `XY53AG8SRJCM` | 293 | 17 | 17/17 (100%) | auto | pass | 788 KB |
| 20 | uart | `AE7RVYYJ9TEY` | 764 | 40 | 40/40 (100%) | oper | pass | 1898 KB |
| 21 | spi_master | `E8N97SZV80QG` | 365 | 18 | 18/18 (100%) | oper | pass | 1104 KB |
| 22 | sync_fifo | `WMJRVX21DS69` | 97 | 6 | 6/6 (100%) | oper | pass | 352 KB |
| 23 | sync_fifo | `V0HY1ERGQJ0A` | 200 | 10 | 10/10 (100%) | oper | incomplete | 523 KB |
| 24 | sync_fifo | `FC6ZQFSFB6RA` | 112 | 6 | 6/6 (100%) | oper | pass | 426 KB |
| 25 | sync_fifo | `GT27TVRBYWZN` | 218 | 9 | 9/9 (100%) | oper | incomplete | 843 KB |

## Operator influence reasons (operator-influenced runs)

### counter8 (`F42K2CR5PYRT`)
- operator event evt_01M42GA90R044DW9SBVYYFYR2Q: Operator: formal harness bug (sby summary truncation made reachable covers look vacuous and real properties look 
- the operator changed task/run state, config or files by hand: Operator: formal harness bug (sby summary truncation made reachable covers look vacuous and real p

### sync_fifo (`AXR1TNEE09AH`)
- operator event evt_01M42GA9131JJTJEMCVXQBFKZF: Operator: formal harness bug (sby summary truncation made reachable covers look vacuous and real properties look 
- the operator changed task/run state, config or files by hand: Operator: formal harness bug (sby summary truncation made reachable covers look vacuous and real p

### uart (`C4BCQQVVD6A3`)
- operator event evt_01M42NFH8MY06HXN3GPBQB4XV0: Operator: Theo testbench answer was cut off at max_tokens=32000 (the uart testbench is large); Theo/Cora max_toke
- operator event evt_01M42TAATTK1JSKEETNKJETJZJ: Operator (CEO decision): per-design cap raised to $8.00 (daily stays $15.00); uart verification resumes from its 
- the operator changed task/run state, config or files by hand: Operator (CEO decision): per-design cap raised to $8.00 (daily stays $15.00); uart verification re
- the operator changed task/run state, config or files by hand: Operator (CEO decision): uart testbench too large for one answer (cut off at 64000 tokens); Theo n
- the operator changed task/run state, config or files by hand: Operator decision (CEO): no limits on bridge model use - uart verification token budget removed (w
- the operator changed task/run state, config or files by hand: Operator decision (CEO): no limits on chat-bridge model use (no API); per-design spend cap raised 
- the operator changed task/run state, config or files by hand: Operator decision (CEO): regression round 3 hit the 2400 s harness limit (uart tests now pass and 
- the operator changed task/run state, config or files by hand: Operator decision (CEO): the unreviewed anti-cheat flag on tb/test_uart_2.py goes to Sentinel; ver
- the operator changed task/run state, config or files by hand: Operator decision (CEO): uart G2 not approved at 14/20 = 70% mutation detection (target 85%). Veri
- the operator changed task/run state, config or files by hand: Operator decision (CEO): uart verification task token budget raised 400,000 -> 1,000,000 and the t
- the operator changed task/run state, config or files by hand: Operator: Ada-C's fix changed uart_tx ports (removed tick16) and broke lint/elaboration; rtl/uart_
- the operator changed task/run state, config or files by hand: Operator: Sentinel review of the unreviewed anti-cheat flag - resumed at step 9 (separate runner)
- the operator changed task/run state, config or files by hand: Operator: Theo testbench answer was cut off at max_tokens=32000 (the uart testbench is large); The
- the operator changed task/run state, config or files by hand: Operator: uart paused by the task token budget (412971 of 400000) during Ada-C's fix attempt 2; at
- the operator changed task/run state, config or files by hand: Operator: uart verification failed on 'No space left on device' (session disk allowance), not on a

### counter8 (`NEVYTE43N0KN`)
- operator event evt_01M43KPWVJHR3436Q78HAD044W: Operator decision (CEO): counter8 floorplan failed because pnr/pin_order.cfg used regex syntax OpenLane's pin par

### sync_fifo (`Q0GGHPJFT602`)
- operator event evt_01M443KK6H2RJ6DTT0PKBMBV3A: Operator decision (CEO): sync_fifo synthesis re-run with SYNTH_STRATEGY DELAY 4 (an allowed flow setting; constra
- operator event evt_01M44T1RY5N96X5YPQXPG159DP: Operator decision CEO decision (sync_fifo, option A, commit b5ba04f): Orion may also set CTS_SINK_CLUSTERING_SIZE
- the operator changed task/run state, config or files by hand: Operator decision (CEO D1): iteration 10 = experiment PNR-SYNCFIFO-0011 (cluster size 9 on iterati
- the operator changed task/run state, config or files by hand: Operator decision (CEO): one extra place-and-route iteration (9 of an 8 budget) for sync_fifo, onl
- the operator changed task/run state, config or files by hand: Operator decision (CEO): re-run sync_fifo iteration 8 cleanly (the previous attempt was invalid); 
- the operator changed task/run state, config or files by hand: Operator decision (CEO): sync_fifo place-and-route tool-run budget raised 16 -> 32 so Orion can us
- the operator changed task/run state, config or files by hand: Operator decision (CEO): sync_fifo place-and-route tool-run budget raised 32 -> 40 so iteration 8 
- the operator changed task/run state, config or files by hand: Operator decision CEO decision (sync_fifo, option A, commit b5ba04f): Orion may also set CTS_SINK_

### alu8 (`G6KW9JSPWS79`)
- operator event evt_01M44AZHNHVRTC2XENXRF3809M: Operator: alu8 verification failed on an S2S harness bug (coverage evaluator did not short-circuit 'and', so a gu
- the operator changed task/run state, config or files by hand: Operator: alu8 verification failed on an S2S harness bug (coverage evaluator did not short-circuit

### spi_master (`HJ8RSESA9S2W`)
- operator event evt_01M44T1RXM7JR69JY2AQ9P5NFX: Operator decision CEO decision (spi_master, option A, commit f4985a1): formal depth for spi_master raised to 160 
- the operator changed task/run state, config or files by hand: Operator decision (CEO): spi_master formal adds per-property PDR proofs when the joint induction d
- the operator changed task/run state, config or files by hand: Operator decision CEO decision (spi_master, option A, commit f4985a1): formal depth for spi_master
- the operator changed task/run state, config or files by hand: Operator: CEO decision: test-plan reference fix - resumed at step 1 (separate runner)
- the operator changed task/run state, config or files by hand: Operator: container restart - resumed at step 3 (separate runner)
- the operator changed task/run state, config or files by hand: Operator: container restart - resumed at step 5 (separate runner)
- the operator changed task/run state, config or files by hand: Operator: test-plan reference fix (retry) - resumed at step 1 (separate runner)

### uart (`AE7RVYYJ9TEY`)
- operator event evt_01M47D5Q5PWC2Y5D466DZ607AD: Operator decision (CEO): uart synthesis strategy DELAY 0 (smallest that meets pre-layout timing at all corners; s
- operator event evt_01M47Q30XPE5R0JS06F0YDWKGK: Operator (D1, knobs first): Orion's escalation answered with 16 recorded experiments (reports/experiments/PNR-UAR
- the operator changed task/run state, config or files by hand: Operator: re-run equivalence with FSM encoding map - resumed at step 8 (separate runner)

### spi_master (`E8N97SZV80QG`)
- operator event evt_01M486YNYE47AMK87QRWVAMZ07: Operator: eqy_rtl_vs_synth failed on rx_data[15:8] (8 of 103 points) because synthesis merged the identical regis

### sync_fifo (`WMJRVX21DS69`)
- operator event evt_01M4A7XM299K0BG7E6H392S9ED: Operator: anti-cheat final review: guard flag 'testplan:' mapped to tb/testplan.yaml (fix flag_file) - resumed at
- the operator changed task/run state, config or files by hand: Operator: anti-cheat final review: guard flag 'testplan:' mapped to tb/testplan.yaml (fix flag_fil

### sync_fifo (`V0HY1ERGQJ0A`)
- operator event evt_01M4A83P9JXP8AQ0AEG5BGZGW1: Operator: synth_strategy DELAY 4 (CEO decision 2026-10-04 for sync_fifo) - pre-layout fail was an unbuffered 256-
- the operator changed task/run state, config or files by hand: Operator: re-run synthesis from setup so synth_strategy DELAY 4 is read and recorded (resume at st
- the operator changed task/run state, config or files by hand: Operator: synth_strategy DELAY 4 (CEO decision 2026-10-04 for sync_fifo) - pre-layout fail was an 

### sync_fifo (`FC6ZQFSFB6RA`)
- operator event evt_01M4AE4ZKCE60GQ8NQ7JZTSK14: Operator: mutation harness bug fixed at root cause (stuck_bit mutant of an indexed target dropped the index: mem_
- the operator changed task/run state, config or files by hand: Operator correction: the 05:42:57 resume started at step 8 (after the mutation step), so mutation 
- the operator changed task/run state, config or files by hand: Operator: mutation harness bug fixed at root cause (stuck_bit mutant of an indexed target dropped 
- the operator changed task/run state, config or files by hand: Operator: re-run the mutation step (step 7, myra) on the fixed generator - resumed at step 7 (sepa

### sync_fifo (`GT27TVRBYWZN`)
- bridge request br_01M4AGKYWZSGH4VNTJG9BE6GR2 was answered with an operator note given OUTSIDE the request (not in the logged prompt): Operator note (fact, from 
- bridge request br_01M4APTZ5W50MG2W5N697JJ6EQ was answered with an operator note given OUTSIDE the request (not in the logged prompt): Operator note (facts from 
- operator event evt_01M4AHA2N59WBR21P61DJ425JB: Operator decision (CEO 2026-10-07): iteration 4 = iteration 3 + RUN_HEURISTIC_DIODE_INSERTION 1 (new allowed knob
- the operator changed task/run state, config or files by hand: CEO decision 2026-10-07: final P&R iteration not started - it cannot close within the tool budget 
- the operator changed task/run state, config or files by hand: Operator decision (CEO 2026-10-07): iteration 4 = iteration 3 + RUN_HEURISTIC_DIODE_INSERTION 1 (n
- the operator changed task/run state, config or files by hand: Operator decision (CEO 2026-10-07): option A as the FINAL P&R iteration; tool-run budget 16 -> 20 

## By design

- **alu8**: 3 runs (2 autonomous, 1 operator-influenced); 3 pass, 0 fail, 0 incomplete
- **counter8**: 6 runs (4 autonomous, 2 operator-influenced); 4 pass, 1 fail, 1 incomplete
- **counter8_seeded_flaw**: 1 runs (1 autonomous, 0 operator-influenced); 1 pass, 0 fail, 0 incomplete
- **dex_triage_suite**: 1 runs (1 autonomous, 0 operator-influenced); 0 pass, 0 fail, 1 incomplete
- **spi_master**: 3 runs (1 autonomous, 2 operator-influenced); 3 pass, 0 fail, 0 incomplete
- **sync_fifo**: 8 runs (2 autonomous, 6 operator-influenced); 5 pass, 1 fail, 2 incomplete
- **uart**: 3 runs (1 autonomous, 2 operator-influenced); 3 pass, 0 fail, 0 incomplete

## Known gaps

1. **Unrecorded model-call provenance**: 114 of 337 calls (34%) have no answered_by — early Phase 0 runs 
   before the operator session transcript covers them. Schema 2 (all future runs) eliminates this gap.
2. **Phase 0 model calls lack goal/attempt/feedback**: schema 1 records carry only the prompt and answer. 
   The exporter aligns them to tool_call events by order, flagged `alignment: "by_order"`.
3. **One unlabelled stall**: Rex, 2026-10-04 12:40 — no running tool at that moment, not a false alarm.

