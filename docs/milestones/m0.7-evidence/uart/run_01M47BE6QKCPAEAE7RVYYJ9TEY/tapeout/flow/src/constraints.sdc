# constraints.sdc - uart (top: uart_top), SKY130 sky130_fd_sc_hd
# Source: spec/spec.yaml clocks: clk 50 MHz -> 20.000 ns period (from spec, exact).

# ---- Clock ----
create_clock -name clk -period 20.000 [get_ports {clk}]
# DEFAULT: clock uncertainty 0.25 ns (pre-CTS jitter + skew margin; within [0.1, 0.5] ns).
set_clock_uncertainty 0.25 [get_clocks {clk}]

# ---- Design rules ----
# DEFAULT: max fanout 10 (within [6, 20]).
set_max_fanout 10 [current_design]

# ---- Input delays ----
# DEFAULT: 30% of the 20 ns period = 6.000 ns; spec gives no external I/O timing.
set_input_delay 6.000 -clock [get_clocks {clk}] [get_ports {rst_n}]
# DEFAULT: rx is asynchronous (spec REQ-005), captured by the 2-flop synchronizer sync2.
# It is still constrained with the 30% default (no false path) so the path to the first
# synchronizer flop is timed; see open issue for a human decision on its treatment.
set_input_delay 6.000 -clock [get_clocks {clk}] [get_ports {rx}]
set_input_delay 6.000 -clock [get_clocks {clk}] [get_ports {tx_data[*]}]
set_input_delay 6.000 -clock [get_clocks {clk}] [get_ports {tx_valid}]
set_input_delay 6.000 -clock [get_clocks {clk}] [get_ports {baud_div[*]}]
set_input_delay 6.000 -clock [get_clocks {clk}] [get_ports {parity_mode[*]}]

# ---- Output delays ----
# DEFAULT: 30% of the 20 ns period = 6.000 ns; spec gives no external I/O timing.
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {tx}]
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {tx_ready}]
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {rx_data[*]}]
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {rx_valid}]
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {frame_err}]
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {parity_err}]
set_output_delay 6.000 -clock [get_clocks {clk}] [get_ports {overrun_err}]

# No false paths, multicycle paths, case analysis or clock groups are used.
# Clock propagation is left to the flow on purpose (the flow propagates the clock after CTS).
# DEFAULT: set_driving_cell / set_load intentionally not set here (flow defaults apply).
