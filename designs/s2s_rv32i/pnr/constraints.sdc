# s2s_rv32i SDC constraints for OpenLane P&R
# Target: 20 MHz (50 ns period) on sky130_fd_sc_hd
# Identical constraint structure to PicoRV32 P1.4 for fair PPA comparison

create_clock -name clk -period 50.0 [get_ports clk]

# Clock uncertainty for OCV margin (pnr_ranges.yaml: 0.1-0.5 ns)
set_clock_uncertainty 0.25 [get_clocks clk]

# Max fanout constraint (pnr_ranges.yaml: 6-20)
set_max_fanout 10 [current_design]

# Input/output delays (20% of period = 10 ns)
set_input_delay -clock clk 10.0 [all_inputs]
set_output_delay -clock clk 10.0 [all_outputs]

# JUSTIFICATION: rst_n is an active-low synchronous reset. Although synchronous,
# the reset deassertion path is not performance-critical at 20 MHz. Setting a
# false_path avoids false violations from the reset tree.
set_false_path -from [get_ports rst_n]
