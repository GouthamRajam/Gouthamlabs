# constraints.sdc - spi_master (SKY130 sky130_fd_sc_hd)
# Source: spec/spec.yaml v2 (clk 50 MHz, REQ-021, REQ-022), arch/arch.yaml.
# Single clock domain (REQ-020). Clock latency/CTS handling is left to the flow.

# ---- Clock ----
# Spec: clk 50 MHz -> 20 ns period, 50% duty.
create_clock -name clk -period 20.0 [get_ports {clk}]

# DEFAULT: clock uncertainty 0.25 ns (pnr_ranges default, allowed [0.1, 0.5]).
set_clock_uncertainty 0.25 [get_clocks {clk}]

# DEFAULT: max fanout 10 (pnr_ranges default, allowed [6, 20]).
set_max_fanout 10 [current_design]

# ---- Input delays ----
# Spec REQ-022: miso input delay 10 ns (DEFAULT - needs G1 review; placeholder value in spec).
# miso is asynchronous and passes the 2-flop synchronizer sync2; it is still constrained, not false-pathed.
set_input_delay 10.0 -clock [get_clocks {clk}] [get_ports {miso}]

# DEFAULT: 30% of period = 6.0 ns for all other non-clock inputs (spec gives no value).
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {rst_n}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {start}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {tx_data[*]}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {word_len}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {cpol}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {cpha}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {clk_div[*]}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {cs_mode}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {cs_force}]
set_input_delay 6.0 -clock [get_clocks {clk}] [get_ports {irq_clear}]

# ---- Output delays ----
# Spec REQ-022: sck, mosi, cs_n output delay 5 ns (DEFAULT - needs G1 review; placeholder value in spec).
set_output_delay 5.0 -clock [get_clocks {clk}] [get_ports {sck}]
set_output_delay 5.0 -clock [get_clocks {clk}] [get_ports {mosi}]
set_output_delay 5.0 -clock [get_clocks {clk}] [get_ports {cs_n}]

# DEFAULT: 30% of period = 6.0 ns for all other outputs (spec gives no value).
set_output_delay 6.0 -clock [get_clocks {clk}] [get_ports {busy}]
set_output_delay 6.0 -clock [get_clocks {clk}] [get_ports {done}]
set_output_delay 6.0 -clock [get_clocks {clk}] [get_ports {irq}]
set_output_delay 6.0 -clock [get_clocks {clk}] [get_ports {rx_data[*]}]
set_output_delay 6.0 -clock [get_clocks {clk}] [get_ports {start_err}]

# ---- Drive and load ----
# DEFAULT: inputs driven by sky130_fd_sc_hd__inv_2 (OpenLane default driving cell); clock port excluded.
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_2 -pin Y [get_ports {rst_n start tx_data[*] word_len cpol cpha clk_div[*] cs_mode cs_force irq_clear miso}]
# DEFAULT: 0.0334 pF load on every output (OpenLane default output load).
set_load 0.0334 [get_ports {sck mosi cs_n busy done irq rx_data[*] start_err}]
