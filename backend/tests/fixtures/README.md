# Test fixtures (M0.2)

Inputs for the adapter pass/fail cases in `tests/cases.py`. Every "fail" input contains
one deliberate, documented defect; the file header says what it is.

| Path | What | Used by |
|---|---|---|
| `rtl/counter.v` | clean 8-bit counter | lint, elab, cocotb, sby (pass) |
| `rtl/width_mismatch.v` | 9-bit sum into 8-bit output, line 9 | verilator_lint (fail) |
| `rtl/syntax_error.v` | missing semicolon on line 6 (tools report it at line 7) | verilator_lint, yosys_elab (fail) |
| `rtl/comb_loop.v` | combinational loop | yosys_elab (fail) |
| `rtl/latch.v` | incomplete `always @(*)` infers a latch | yosys_elab (fail) |
| `cocotb/test_counter_{pass,fail}.py` | right / wrong expected count | cocotb_sim |
| `sby/counter_{pass,fail}.sby`, `counter_formal.v` | true / false property | sby_formal |
| `eqy/adder_{pass,fail}.eqy`, `adder_*.v` | equivalent / dropped-carry adder | eqy |
| `openlane_spm/` | OpenLane 2.3.10's bundled `spm` example (Apache-2.0, copied unchanged) | openlane_flow (pass) |
| `openlane_spm/config_tight_clock.yaml` | same, 1.0 ns clock | openlane_flow (fail) |
| `spm_signoff/` | final outputs of the M0.1 OpenLane `spm` run (GDS, extracted SPICE, netlists, SDC, SPEF); checksums in `SHA256SUMS` | opensta, magic_drc, klayout_drc, netgen_lvs |
| `spm_signoff/spm_tight.sdc` | `spm.sdc` with a 1 ns clock | opensta (fail) |
| `derive/inject_drc_violation.py` | KLayout script that adds one 0.05 µm met1 square to `spm.gds` | magic_drc, klayout_drc (fail) |

The LVS failure netlist is derived in `tests/cases.py` (`lvs_bad_netlist`): flip-flop
`_252_`'s D pin in `spm.pnl.v` is rewired to its neighbour's net.
