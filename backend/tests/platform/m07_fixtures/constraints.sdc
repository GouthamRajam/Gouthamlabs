# Hand-written test fixture (scripted model answer for offline plumbing tests). Not agent output.
create_clock -name clk -period 10.0 [get_ports {clk}]
set_clock_uncertainty 0.25 [get_clocks {clk}]
set_max_fanout 10 [current_design]
# DEFAULT: input/output delays 30% of the 10 ns period
set_input_delay 3.0 -clock [get_clocks {clk}] [get_ports {rst_n en up load load_value[*]}]
set_output_delay 3.0 -clock [get_clocks {clk}] [get_ports {count[*]}]
# DEFAULT: driving cell and load
set_driving_cell -lib_cell sky130_fd_sc_hd__inv_2 -pin Y [get_ports {rst_n en up load load_value[*]}]
set_load 0.0334 [get_ports {count[*]}]
