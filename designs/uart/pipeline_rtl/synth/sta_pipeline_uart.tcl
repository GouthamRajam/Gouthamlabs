# STA for pipeline-generated UART
# Target: 50 MHz (20 ns period), sky130_fd_sc_hd TT corner

set lib_path "/nix/store/pi9m3br8ni97dfybd24lldfa185py07x-source/src/sta/test/sky130hd/sky130_fd_sc_hd__tt_025C_1v80.lib"

read_liberty $lib_path
read_verilog pipeline_uart_synth.v
link_design uart_top

create_clock -name clk -period 20.0 [get_ports clk]
set_input_delay -clock clk 2.0 [all_inputs]
set_output_delay -clock clk 2.0 [all_outputs]

report_checks -path_delay max -format full
report_checks -path_delay min -format full
report_tns
report_wns
