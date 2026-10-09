# Phase 1.5 Pillar A: s2s_rv32i Static Timing Analysis at 20 MHz
# Using OpenSTA with sky130_fd_sc_hd TT corner

set lib_path "/nix/store/pi9m3br8ni97dfybd24lldfa185py07x-source/src/sta/test/sky130hd/sky130_fd_sc_hd__tt_025C_1v80.lib"

read_liberty $lib_path
read_verilog s2s_rv32i_synth.v
link_design s2s_rv32i_core

# Clock constraint: 20 MHz = 50 ns period
create_clock -name clk -period 50.0 [get_ports clk]

# Input/output delays (conservative: 20% of period)
set_input_delay -clock clk 10.0 [all_inputs]
set_output_delay -clock clk 10.0 [all_outputs]

# Don't time reset input
set_false_path -from [get_ports rst_n]

# Report timing
report_checks -path_delay max -sort_by_slack
report_checks -path_delay min -sort_by_slack
report_tns
report_wns

exit
