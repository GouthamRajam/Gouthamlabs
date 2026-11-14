# constraints.sdc - sync_fifo (sky130A, sky130_fd_sc_hd)
# Source: spec/spec.yaml (clocks, interfaces, REQ-018, REQ-019), arch/arch.yaml
# Author: Sienna (synthesis agent). Every non-spec value is marked DEFAULT - needs G1 review.

# ---------------------------------------------------------------------------
# Clock: clk, 100 MHz -> 10.000 ns period (spec clocks[0], REQ-019). Single clock domain.
# ---------------------------------------------------------------------------
create_clock -name clk -period 10.000 [get_ports {clk}]

# DEFAULT - needs G1 review: clock uncertainty 0.25 ns (pnr_ranges default, range [0.1, 0.5] ns)
set_clock_uncertainty 0.25 [get_clocks {clk}]

# DEFAULT - needs G1 review: max fanout 10 (pnr_ranges default, range [6, 20])
set_max_fanout 10 [current_design]

# ---------------------------------------------------------------------------
# Input delays: DEFAULT - needs G1 review: 30% of period = 3.000 ns (spec gives no I/O budget)
# rst_n is a synchronous reset (spec resets[0]) and is timed as a normal input.
# ---------------------------------------------------------------------------
set_input_delay 3.000 -clock [get_clocks {clk}] [get_ports {rst_n}]
set_input_delay 3.000 -clock [get_clocks {clk}] [get_ports {wr_en}]
set_input_delay 3.000 -clock [get_clocks {clk}] [get_ports {wr_data[*]}]
set_input_delay 3.000 -clock [get_clocks {clk}] [get_ports {rd_en}]

# ---------------------------------------------------------------------------
# Output delays: DEFAULT - needs G1 review: 30% of period = 3.000 ns (spec gives no I/O budget)
# ---------------------------------------------------------------------------
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {rd_data[*]}]
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {full}]
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {empty}]
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {almost_full}]
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {overflow}]
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {underflow}]
set_output_delay 3.000 -clock [get_clocks {clk}] [get_ports {count[*]}]

# No timing exceptions (false paths, multicycle paths, case analysis, clock groups) are used.
# Driving cell and output load: DEFAULT - needs G1 review: left to the OpenLane 2 flow defaults.
# Clocks stay ideal here; the flow propagates clocks after CTS.
