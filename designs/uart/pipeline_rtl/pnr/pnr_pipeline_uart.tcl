# P&R for pipeline-generated UART (run_01M426JH3YWRXXHKAKSF3J94CP)
# Target: sky130_fd_sc_hd, 50 MHz, FP_CORE_UTIL=30
# Tool: OpenROAD (Python pip package)

set SKY130 "/nix/store/pi9m3br8ni97dfybd24lldfa185py07x-source/test/sky130hd"
set STA_SKY130 "/nix/store/pi9m3br8ni97dfybd24lldfa185py07x-source/src/sta/test/sky130hd"
set SYNTH_DIR "[file dirname [file dirname [file normalize [info script]]]]/synth"
set PNR_DIR "[file dirname [file normalize [info script]]]"

# ---- Read technology ----
read_lef "$SKY130/sky130hd.tlef"
read_lef "$SKY130/sky130_fd_sc_hd.lef"
read_liberty "$STA_SKY130/sky130_fd_sc_hd__tt_025C_1v80.lib"

# ---- Read synthesized netlist ----
read_verilog "$SYNTH_DIR/pipeline_uart_synth.v"
link_design uart_top

# ---- Clock ----
create_clock -name clk -period 20.0 [get_ports clk]
set_input_delay -clock clk 2.0 [all_inputs]
set_output_delay -clock clk 2.0 [all_outputs]

# ---- Tracks ----
source "$SKY130/sky130hd.tracks"

# ---- Floorplan ----
initialize_floorplan -utilization 30 \
  -aspect_ratio 1.0 \
  -core_space 10 \
  -site unithd

# ---- IO placement ----
set_io_pin_constraint -pin_names {clk rst_n} -region left:*
set_io_pin_constraint -pin_names {rx tx} -region right:*
place_pins -hor_layers met3 -ver_layers met2

# ---- Tap cells ----
tapcell -distance 14 -tapcell_master sky130_fd_sc_hd__tapvpwrvgnd_1

# ---- PDN ----
source "$SKY130/sky130hd.pdn.tcl"
pdngen

# ---- RC ----
source "$SKY130/sky130hd.rc"
set_wire_rc -layer met2
set_wire_rc -clock -layer met5

# ---- Global placement ----
set_dont_use {sky130_fd_sc_hd__probe_p_* sky130_fd_sc_hd__probec_p_*}
global_placement -density 0.30 -pad_left 4 -pad_right 4

# ---- Estimate parasitics ----
estimate_parasitics -placement

# ---- Repair design ----
set_propagated_clocks [all_clocks]
repair_design
repair_timing -hold
repair_timing -setup

# ---- Detailed placement ----
set_placement_padding -global -left 2 -right 2
detailed_placement
check_placement

# ---- CTS ----
clock_tree_synthesis -root_buf sky130_fd_sc_hd__clkbuf_4 \
  -buf_list {sky130_fd_sc_hd__clkbuf_4} \
  -sink_clustering_enable \
  -sink_clustering_size 20 \
  -sink_clustering_max_diameter 100

repair_clock_nets

# ---- Post-CTS: repair ----
estimate_parasitics -placement
repair_timing -hold
repair_timing -setup

detailed_placement
check_placement

# ---- Global route ----
set_global_routing_layer_adjustment met1 0.5
set_global_routing_layer_adjustment met2 0.5
set_global_routing_layer_adjustment met3 0.5
set_global_routing_layer_adjustment met4 0.5
set_global_routing_layer_adjustment met5 0.5
set_routing_layers -signal met1-met5 -clock met3-met5
global_route -guide_file "$PNR_DIR/route.guide" \
  -congestion_iterations 50

# ---- Antenna repair (pre-DRT) ----
repair_antennas sky130_fd_sc_hd__diode_2 -iterations 5

estimate_parasitics -global_routing

# ---- Post-GRT STA ----
puts "=== Post-GRT STA ==="
report_checks -path_delay max -format full
report_checks -path_delay min -format full
report_tns
report_wns

# ---- Detailed route ----
detailed_route -output_drc "$PNR_DIR/route_drc.rpt" \
  -output_maze "$PNR_DIR/maze.log" \
  -bottom_routing_layer met1 \
  -top_routing_layer met5 \
  -save_guide_updates \
  -verbose 1

# ---- Post-DRT antenna check ----
check_antennas -report_file "$PNR_DIR/antenna.rpt"

# ---- Post-route parasitics ----
estimate_parasitics -global_routing

# ---- Final STA (TT corner) ----
puts "=== Final STA (TT, 50 MHz) ==="
report_checks -path_delay max -format full
report_checks -path_delay min -format full
report_tns
report_wns
report_power

# ---- Design stats ----
report_design_area

# ---- Write outputs ----
write_def "$PNR_DIR/pipeline_uart_pnr.def"
write_verilog "$PNR_DIR/pipeline_uart_pnr.v"

puts ""
puts "=== P&R COMPLETE ==="
puts "DEF: $PNR_DIR/pipeline_uart_pnr.def"
puts "Netlist: $PNR_DIR/pipeline_uart_pnr.v"
