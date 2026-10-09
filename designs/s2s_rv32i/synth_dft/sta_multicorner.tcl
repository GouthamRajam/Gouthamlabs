# Pillar C: Multi-corner STA with OCV derating for s2s_rv32i
# Arguments passed via environment: CORNER_LIB, DERATE_EARLY, DERATE_LATE, CLK_PERIOD

set lib_file $::env(CORNER_LIB)
set derate_early $::env(DERATE_EARLY)
set derate_late $::env(DERATE_LATE)
set clk_period $::env(CLK_PERIOD)
set io_delay [expr {$clk_period * 0.2}]

read_liberty $lib_file
read_verilog s2s_rv32i_synth.v
link_design s2s_rv32i_core

create_clock -name clk -period $clk_period [get_ports clk]
set_input_delay -clock clk $io_delay [all_inputs]
set_output_delay -clock clk $io_delay [all_outputs]
set_false_path -from [get_ports rst_n]

if {$derate_early != 1.0 || $derate_late != 1.0} {
    set_timing_derate -early $derate_early
    set_timing_derate -late  $derate_late
}

puts "--- SETUP ---"
report_checks -path_delay max -sort_by_slack -digits 4
report_tns
report_wns

puts "--- HOLD ---"
report_checks -path_delay min -sort_by_slack -digits 4

exit
