# PicoRV32 SDC constraints for OpenLane P&R (P1.4)
# Target: 20 MHz (50 ns period) on sky130_fd_sc_hd

create_clock -name clk -period 50.0 [get_ports clk]

# Clock uncertainty for OCV margin (pnr_ranges.yaml: 0.1-0.5 ns)
set_clock_uncertainty 0.25 [get_clocks clk]

# Max fanout constraint (pnr_ranges.yaml: 6-20)
set_max_fanout 10 [current_design]

# Input/output delays (20% of period = 10 ns)
set_input_delay -clock clk 10.0 [all_inputs]
set_output_delay -clock clk 10.0 [all_outputs]

# JUSTIFICATION: rst is an asynchronous active-high reset with no timing relationship to clk.
# Timing this path as synchronous would create false violations.
set_false_path -from [get_ports rst]
