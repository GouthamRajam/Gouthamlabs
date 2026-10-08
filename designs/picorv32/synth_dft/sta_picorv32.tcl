# P1.3 Step 4: Static Timing Analysis at 20 MHz target clock
# Using OpenSTA with sky130_fd_sc_hd TT corner

set lib_path "/opt/pdk/volare/sky130/versions/0fe599b2afb6708d281543108caf8310912f54af/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"

read_liberty $lib_path
read_verilog /work/picorv32_synth.v
link_design picorv32

# Clock constraint: 20 MHz = 50 ns period
create_clock -name clk -period 50.0 [get_ports clk]

# Input/output delays (conservative: 20% of period)
set_input_delay -clock clk 10.0 [all_inputs]
set_output_delay -clock clk 10.0 [all_outputs]

# Don't time clock input itself
set_false_path -from [get_ports rst]

# Report timing
report_checks -path_delay max -sort_by_slack
report_checks -path_delay min -sort_by_slack
report_tns
report_wns

exit
