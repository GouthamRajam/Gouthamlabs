# constraints.sdc - counter8 (sky130_fd_sc_hd), generated from spec/spec.yaml
# Clock: spec clk, 100 MHz = 10 ns period (REQ-011).
create_clock -name clk -period 10.0 [get_ports clk]

# DEFAULT: clock uncertainty 0.25 ns (config/pnr_ranges.yaml range [0.1, 0.5]).
set_clock_uncertainty 0.25 [get_clocks clk]

# DEFAULT: max fanout 10 (config/pnr_ranges.yaml range [6, 20]).
set_max_fanout 10 [current_design]

# DEFAULT: input delay = 30% of the 10 ns period = 3.0 ns on every non-clock input
# (spec states no input timing; all inputs synchronous to clk).
set_input_delay -clock clk 3.0 [get_ports rst_n]
set_input_delay -clock clk 3.0 [get_ports enable]
set_input_delay -clock clk 3.0 [get_ports load]
set_input_delay -clock clk 3.0 [get_ports up_down]
set_input_delay -clock clk 3.0 [get_ports {load_data[*]}]

# DEFAULT: output delay = 30% of the 10 ns period = 3.0 ns on the only output (count).
set_output_delay -clock clk 3.0 [get_ports {count[*]}]
