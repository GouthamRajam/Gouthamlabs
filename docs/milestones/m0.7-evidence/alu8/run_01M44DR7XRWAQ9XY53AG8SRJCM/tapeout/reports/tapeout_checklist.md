| # | Item | Done | Evidence |
|---|---|---|---|
| 1 | Spec approved at G1 | yes | gate gate_01M43C276RCFZE7W148MKQDK6Q |
| 2 | RTL frozen at G2; no changes since | yes | checks rtl_frozen_at_g2, constraints_not_loosened |
| 3 | Regression 100% passing on frozen RTL | yes | M0.6 check regression_100pct |
| 4 | Equivalence RTL vs final netlist proven | yes | check eqy_rtl_vs_final |
| 5 | Setup and hold met at all corners | yes | check sta_all_corners (9 corners) |
| 6 | Zero DRC (Magic and KLayout) on final GDS | yes | checks drc_magic_final_gds, drc_klayout_final_gds, package_drc_* |
| 7 | LVS clean on final GDS | yes | checks lvs_final_gds, package_lvs |
| 8 | Antenna clean | yes | check antenna_final |
| 9 | Density rules met | yes | check density_rules |
| 10 | DFM scorecard: zero high-severity open items | yes | check dfm_no_high_severity |
| 11 | Power and IR within limits | yes | checks power_estimated, ir_drop_within_limit |
| 12 | Pin list matches spec | yes | check pins_match_spec |
| 13 | All Sentinel findings closed or human-overruled | yes | all Sentinel reviews passed |
| 14 | reproduce.sh re-runs cleanly in a fresh container | yes | check reproduce_clean_container |
| 15 | versions.lock and hashes recorded | yes | tapeout/versions.lock, MANIFEST.sha256 |
| 16 | G3 approved | yes | gate gate_01M44EQ71TZYHCF6FPGZDHXEPS (approved) |
