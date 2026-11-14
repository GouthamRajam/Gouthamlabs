# constraints.sdc for alu8 (top: alu8_top), sky130A / sky130_fd_sc_hd
# Written by Sienna (synthesis) from spec/spec.yaml v1 and arch/arch.yaml.

# Clock: spec clk = 75 MHz -> period = 1000/75 = 13.333333 ns (REQ-014), rising edge.
create_clock -name clk -period 13.333333 [get_ports {clk}]

# Clock uncertainty: DEFAULT 0.25 ns (config/pnr_ranges.yaml range [0.1, 0.5]); no jitter budget in spec.
set_clock_uncertainty 0.25 [get_clocks {clk}]

# Max fanout: DEFAULT 10 (allowed range [6, 20]).
set_max_fanout 10 [current_design]

# Input delays: DEFAULT 30% of period = 4.0 ns (spec gives no I/O budget; see open_questions).
set_input_delay 4.0 -clock [get_clocks {clk}] [get_ports {rst_n}]
set_input_delay 4.0 -clock [get_clocks {clk}] [get_ports {a[*]}]
set_input_delay 4.0 -clock [get_clocks {clk}] [get_ports {b[*]}]
set_input_delay 4.0 -clock [get_clocks {clk}] [get_ports {op[*]}]

# Output delays: DEFAULT 30% of period = 4.0 ns (spec gives no I/O budget; see open_questions).
set_output_delay 4.0 -clock [get_clocks {clk}] [get_ports {result[*]}]
set_output_delay 4.0 -clock [get_clocks {clk}] [get_ports {flag_z}]
set_output_delay 4.0 -clock [get_clocks {clk}] [get_ports {flag_c}]
set_output_delay 4.0 -clock [get_clocks {clk}] [get_ports {flag_v}]
set_output_delay 4.0 -clock [get_clocks {clk}] [get_ports {flag_n}]

# Input drive: DEFAULT sky130_fd_sc_hd__inv_2 driving every non-clock input.
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_2 -pin Y [get_ports {rst_n a[*] b[*] op[*]}]

# Output load: DEFAULT 0.0334 pF (approx. one sky130_fd_sc_hd buffer input plus routing).
set_load 0.0334 [get_ports {result[*] flag_z flag_c flag_v flag_n}]

# No false paths, multicycle paths, case analysis or clock groups: single clock domain, no CDC (REQ-014).
