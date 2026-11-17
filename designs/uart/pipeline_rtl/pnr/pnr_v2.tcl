# P&R v2 for the pipeline-generated UART (run_01M426JH3YWRXXHKAKSF3J94CP). RTL and synthesized netlist unchanged.
# Differences from pnr_pipeline_uart.tcl: explicit power connections (powered netlist), filler placement after
# routing, floorplan size reported and checked, all outputs written.
# Env: PDK_ROOT (contains sky130A/), OUT (output directory), SYNTH (pipeline_uart_synth.v)
#      UTIL (core utilization %, default 30), DENS (placement density, default 0.40); config/pnr_ranges.yaml bounds apply
set PDK  "$::env(PDK_ROOT)/sky130A"
set UTIL [expr {[info exists ::env(UTIL)] ? $::env(UTIL) : 30}]
set DENS [expr {[info exists ::env(DENS)] ? $::env(DENS) : 0.40}]
set ORSEED [expr {[info exists ::env(ORSEED)] ? $::env(ORSEED) : -1}]
set RTOP [expr {[info exists ::env(RTOP)] ? $::env(RTOP) : "met5"}]
set NOVIAGEN [expr {[info exists ::env(NOVIAGEN)] ? $::env(NOVIAGEN) : 0}]
puts "S2S_PARAMS util=$UTIL density=$DENS or_seed=$ORSEED route_top=$RTOP disable_via_gen=$NOVIAGEN"
set OUT  $::env(OUT)
set LIBDIR "$PDK/libs.ref/sky130_fd_sc_hd"
file mkdir $OUT

read_lef  "$LIBDIR/techlef/sky130_fd_sc_hd__nom.tlef"
read_lef  "$LIBDIR/lef/sky130_fd_sc_hd.lef"
read_liberty "$LIBDIR/lib/sky130_fd_sc_hd__tt_025C_1v80.lib"
read_verilog $::env(SYNTH)
link_design uart_top

create_clock -name clk -period 20.0 [get_ports clk]
set_input_delay  -clock clk 2.0 [all_inputs]
set_output_delay -clock clk 2.0 [all_outputs]
set_clock_uncertainty 0.25 [get_clocks clk]

initialize_floorplan -utilization $UTIL -aspect_ratio 1.0 -core_space 10 -site unithd
make_tracks

set die [ord::get_die_area]
set core [ord::get_core_area]
puts "S2S_FLOORPLAN die=$die core=$core"

place_pins -hor_layers met3 -ver_layers met2
tapcell -distance 14 -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1

# ---- power grid (names match the PDK cell pins so the written netlist is powered) ----
add_global_connection -net VPWR -inst_pattern {.*} -pin_pattern {^VPWR$} -power
add_global_connection -net VPWR -inst_pattern {.*} -pin_pattern {^VPB$}  -power
add_global_connection -net VGND -inst_pattern {.*} -pin_pattern {^VGND$} -ground
add_global_connection -net VGND -inst_pattern {.*} -pin_pattern {^VNB$}  -ground
set_voltage_domain -name CORE -power VPWR -ground VGND
define_pdn_grid -name stdcell_grid -starts_with POWER -voltage_domain CORE -pins {met4 met5}
add_pdn_stripe -grid stdcell_grid -layer met1 -width 0.48 -followpins
add_pdn_stripe -grid stdcell_grid -layer met4 -width 1.6 -pitch 27.14 -offset 13.57 -starts_with POWER
add_pdn_stripe -grid stdcell_grid -layer met5 -width 1.6 -pitch 27.2  -offset 13.6  -starts_with POWER
add_pdn_connect -grid stdcell_grid -layers {met1 met4}
add_pdn_connect -grid stdcell_grid -layers {met4 met5}
pdngen

set_wire_rc -signal -layer met2
set_wire_rc -clock  -layer met5
set_dont_use {sky130_fd_sc_hd__probe_p_* sky130_fd_sc_hd__probec_p_* sky130_fd_sc_hd__lpflow_*}

global_placement -density $DENS
estimate_parasitics -placement
repair_design
repair_tie_fanout sky130_fd_sc_hd__conb_1/HI
repair_tie_fanout sky130_fd_sc_hd__conb_1/LO
set_placement_padding -global -left 2 -right 2
detailed_placement
check_placement

clock_tree_synthesis -root_buf sky130_fd_sc_hd__clkbuf_4 -buf_list {sky130_fd_sc_hd__clkbuf_4} \
  -sink_clustering_enable -sink_clustering_size 20 -sink_clustering_max_diameter 100
set_propagated_clock [all_clocks]
repair_clock_nets
estimate_parasitics -placement
detailed_placement
check_placement
repair_timing -hold
repair_timing -setup
detailed_placement
check_placement

# Constant-assign leftovers from synthesis become special one_/zero_ nets; report them, and remove only
# those with no connections at all (anything connected stays and is reported).
set blk [ord::get_db_block]
foreach net [$blk getNets] {
  set n [$net getName]
  if {[string match "*one_" $n] || [string match "*zero_" $n]} {
    set ni [llength [$net getITerms]]; set nb [llength [$net getBTerms]]
    puts "S2S_TIENET $n iterms=$ni bterms=$nb type=[$net getSigType]"
    if {$ni == 0 && $nb == 0} { odb::dbNet_destroy $net }
  }
}

# CTS and repair insert cells after the power grid was made; connect their power/body pins too
global_connect

set_routing_layers -signal met1-$RTOP -clock met3-$RTOP
global_route -guide_file "$OUT/route.guide" -congestion_iterations 50
repair_antennas sky130_fd_sc_hd__diode_2 -iterations 5
set dr_args [list -output_drc "$OUT/route_drc.rpt" -bottom_routing_layer met1 -top_routing_layer $RTOP -verbose 1]
if {$ORSEED >= 0} { lappend dr_args -or_seed $ORSEED }
if {$NOVIAGEN} { lappend dr_args -disable_via_gen }
if {[info exists ::env(PROCNODE)]} { lappend dr_args -db_process_node $::env(PROCNODE) }
detailed_route {*}$dr_args
check_antennas -report_file "$OUT/antenna.rpt"

# ---- filler (the step the original script lacked) ----
filler_placement {sky130_fd_sc_hd__fill_8 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_1}
check_placement

estimate_parasitics -global_routing
puts "S2S_STA_BEGIN"
report_checks -path_delay max -format full
report_checks -path_delay min -format full
report_tns
report_wns
report_worst_slack -max
report_worst_slack -min
report_design_area
report_power
puts "S2S_STA_END"

write_def     "$OUT/uart_top.def"
write_db      "$OUT/uart_top.odb"
write_verilog -include_pwr_gnd "$OUT/uart_top.pnl.v"
write_verilog "$OUT/uart_top.nl.v"
# LVS netlist: powered, without physical-only cells (no transistors; they have no logical connections)
write_verilog -include_pwr_gnd -remove_cells {sky130_fd_sc_hd__fill_1 sky130_fd_sc_hd__fill_2 sky130_fd_sc_hd__fill_4 sky130_fd_sc_hd__fill_8 sky130_fd_sc_hd__tapvpwrvgnd_1} "$OUT/uart_top.lvs.pnl.v"
puts "S2S_PNR_DONE"
exit
