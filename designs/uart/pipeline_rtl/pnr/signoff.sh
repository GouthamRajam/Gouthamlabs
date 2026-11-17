#!/usr/bin/env bash
# Signoff chain for the pipeline UART from a pnr_v2.tcl output directory:
#   DEF -> GDS (stream_out.py) -> KLayout DRC -> Magic DRC -> Magic extract -> Netgen LVS.
# Usage: signoff.sh <pnr_out_dir> <work_dir>
# Env:   PDK_ROOT (has sky130A/), EDA_ENV (conda env with magic, netgen), KLAYOUT_PYLIB (klayout python pkg dir)
# Every step's verdict is read from the tool's own output. The same procedure was checked against the
# signed-off counter8 design (KLayout DRC 0, Netgen "Circuits match uniquely") before being trusted.
set -u
OUT=$(readlink -f "$1"); W=$(readlink -f "$2"); mkdir -p "$W"
HERE=$(cd "$(dirname "$0")" && pwd)
P="$PDK_ROOT/sky130A"; LIB="$P/libs.ref/sky130_fd_sc_hd"; TOP=uart_top
export LD_LIBRARY_PATH="$EDA_ENV/lib:${LD_LIBRARY_PATH:-}" PDK=sky130A

echo "== 1. DEF -> GDS"
python3 -I "$HERE/stream_out.py" --pylib "$KLAYOUT_PYLIB" --def "$OUT/$TOP.def" \
  --tlef "$LIB/techlef/sky130_fd_sc_hd__nom.tlef" --lef "$LIB/lef/sky130_fd_sc_hd.lef" \
  --cell-gds "$LIB/gds/sky130_fd_sc_hd.gds" --map "$P/libs.tech/klayout/tech/sky130A.map" \
  --top $TOP --out "$W/$TOP.gds" > "$W/stream_out.json" || { echo "STREAM_OUT FAILED"; exit 2; }
grep -E '"sha256"|component_instances|def_components' "$W/stream_out.json"

echo "== 2. KLayout DRC"
QT_QPA_PLATFORM=offscreen klayout -b -zz -r "$P/libs.tech/klayout/drc/sky130A_mr.drc" \
  -rd feol=true -rd beol=true -rd floating_metal=false -rd offgrid=true -rd seal=true \
  -rd input="$W/$TOP.gds" -rd topcell=$TOP -rd top_cell=$TOP -rd report="$W/klayout_drc.lyrdb" \
  -rd threads=4 > "$W/klayout_drc.log" 2>&1
grep -q 'Writing report database' "$W/klayout_drc.log" || { echo "KLAYOUT DRC DID NOT COMPLETE"; exit 3; }
python3 -I - "$W/klayout_drc.lyrdb" <<'EOF'
import sys, collections, xml.etree.ElementTree as ET
c = collections.Counter((i.findtext('category') or '?').strip("'") for i in ET.parse(sys.argv[1]).getroot().iter('item'))
print("KLAYOUT_DRC_VIOLATIONS", sum(c.values()), dict(c))
EOF

echo "== 3. Magic DRC + extraction"
cat > "$W/magic.tcl" <<EOF
gds read $W/$TOP.gds
load $TOP
select top cell
drc style drc(full)
drc check
drc catchup
puts "S2S_MAGIC_DRC_TOTAL [drc listall count]"
foreach {why boxes} [drc listall why] { puts "S2S_MAGIC_RULE \$why | boxes: [llength \$boxes]" }
extract do local
extract no capacitance
extract no coupling
extract no resistance
extract no adjust
extract unique
extract
ext2spice lvs
ext2spice -o $W/$TOP.spice
puts "S2S_MAGIC_DONE"
quit -noprompt
EOF
PDK_ROOT=$PDK_ROOT timeout 1500 "$EDA_ENV/bin/magic" -dnull -noconsole -rcfile "$P/libs.tech/magic/sky130A.magicrc" "$W/magic.tcl" > "$W/magic.log" 2>&1
grep -q S2S_MAGIC_DONE "$W/magic.log" || { echo "MAGIC DID NOT COMPLETE"; exit 4; }
grep -E 'Total DRC errors found|S2S_MAGIC_RULE' "$W/magic.log" | sort -u

echo "== 4. Netgen LVS (powered netlist without physical-only cells)"
SP="$LIB/spice"
cat > "$W/lvs.tcl" <<EOF
set circuit1 [readnet spice $W/$TOP.spice]
set circuit2 [readnet verilog /dev/null]
foreach f {sky130_ef_sc_hd__decap_12 sky130_ef_sc_hd__fill_12 sky130_ef_sc_hd__fill_4 sky130_ef_sc_hd__fill_8 sky130_fd_sc_hd} { readnet spice $SP/\$f.spice \$circuit2 }
readnet verilog $OUT/$TOP.lvs.pnl.v \$circuit2
lvs "\$circuit1 $TOP" "\$circuit2 $TOP" $P/libs.tech/netgen/sky130A_setup.tcl $W/lvs.rpt -blackbox -json
puts "S2S_LVS_DONE"
EOF
timeout 900 "$EDA_ENV/bin/netgen" -batch source "$W/lvs.tcl" > "$W/lvs.log" 2>&1
grep -q S2S_LVS_DONE "$W/lvs.log" || { echo "NETGEN DID NOT COMPLETE"; exit 5; }
grep -E '^Final result' "$W/lvs.rpt" | tail -1
grep -E 'Number of (devices|nets)' "$W/lvs.rpt" | tail -2
