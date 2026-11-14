#!/usr/bin/env bash
# reproduce.sh: re-verify this tape-out package in a clean s2s-eda container (no network needed):
#   docker run --rm --network none -v "$PWD":/pkg -w /pkg s2s-eda bash reproduce.sh
set -uo pipefail
PKG="$(cd "$(dirname "$0")" && pwd)"
TOP="spi_master"
OUT="${S2S_REPRO_OUT:-/tmp/s2s_reproduce}"
rm -rf "$OUT"; mkdir -p "$OUT"
PDK=/opt/pdk/sky130A
cd "$PKG"

echo "== 1. manifest"
sha256sum --quiet -c MANIFEST.sha256 > "$OUT/manifest.log" 2>&1; MANIFEST_RC=$?

echo "== 2. Magic DRC on the packaged GDS"
cat > "$OUT/drc.tcl" <<EOF
gds noduplicates true
gds read $PKG/gds/$TOP.gds
load $TOP
select top cell
drc euclidean on
drc style drc(full)
drc check
drc catchup
set total 0
foreach {why boxes} [drc listall why] { set total [expr {\$total + [llength \$boxes]}] }
puts "S2S_MAGIC_DRC \$total"
quit -noprompt
EOF
magic -dnull -noconsole -rcfile $PDK/libs.tech/magic/sky130A.magicrc "$OUT/drc.tcl" > "$OUT/magic_drc.log" 2>&1
MAGIC_DRC=$(grep -oP '^S2S_MAGIC_DRC \K\d+' "$OUT/magic_drc.log" || echo none)

echo "== 3. KLayout DRC on the packaged GDS"
klayout -b -zz -r $PDK/libs.tech/klayout/drc/sky130A_mr.drc -rd input="$PKG/gds/$TOP.gds" -rd topcell=$TOP \
  -rd report="$OUT/klayout.lyrdb" -rd feol=true -rd beol=true -rd floating_metal=false -rd offgrid=true \
  -rd seal=true -rd threads=4 > "$OUT/klayout_drc.log" 2>&1
if [ -s "$OUT/klayout.lyrdb" ]; then KLAYOUT_DRC=$(grep -c '<item>' "$OUT/klayout.lyrdb" || true); else KLAYOUT_DRC=none; fi

echo "== 4. extraction + Netgen LVS"
mkdir -p "$OUT/ext"
cat > "$OUT/ext.tcl" <<EOF
gds noduplicates true
gds read $PKG/gds/$TOP.gds
load $TOP -dereference
cd $OUT/ext
extract do local
extract no capacitance
extract no coupling
extract no resistance
extract no adjust
extract unique
extract
ext2spice lvs
ext2spice -o $OUT/ext/$TOP.spice $TOP.ext
quit -noprompt
EOF
magic -dnull -noconsole -rcfile $PDK/libs.tech/magic/sky130A.magicrc "$OUT/ext.tcl" > "$OUT/extract.log" 2>&1
CELLS=""
for c in sky130_ef_sc_hd__decap_12 sky130_ef_sc_hd__fill_12 sky130_ef_sc_hd__fill_4 sky130_ef_sc_hd__fill_8 sky130_fd_sc_hd; do
  CELLS="$CELLS
readnet spice $PDK/libs.ref/sky130_fd_sc_hd/spice/$c.spice \$circuit2"
done
cat > "$OUT/lvs.tcl" <<EOF
set circuit1 [readnet spice $OUT/ext/$TOP.spice]
set circuit2 [readnet verilog /dev/null]
$CELLS
readnet verilog $PKG/netlist/$TOP.pnl.v \$circuit2
lvs "\$circuit1 $TOP" "\$circuit2 $TOP" $PDK/libs.tech/netgen/sky130A_setup.tcl $OUT/lvs.rpt -blackbox -json
EOF
netgen -batch source "$OUT/lvs.tcl" > "$OUT/lvs.log" 2>&1
LVS=$(grep -oP '^Final result:\s*\K.*' "$OUT/lvs.rpt" | tail -1)

echo "== 5. STA, 9 corners"
STA_JSON="{"
for rc in nom min max; do for lib in tt_025C_1v80 ss_100C_1v60 ff_n40C_1v95; do
  cat > "$OUT/sta_${rc}_${lib}.tcl" <<EOF
read_liberty $PDK/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__${lib}.lib
read_verilog $PKG/netlist/$TOP.nl.v
link_design $TOP
read_sdc $PKG/constraints/constraints.sdc
set_propagated_clock [all_clocks]
read_spef $PKG/spef/$rc/$TOP.$rc.spef
puts "S2S_SETUP [sta::format_time [sta::worst_slack_cmd max] 4]"
puts "S2S_HOLD [sta::format_time [sta::worst_slack_cmd min] 4]"
EOF
  sta -no_init -exit "$OUT/sta_${rc}_${lib}.tcl" > "$OUT/sta_${rc}_${lib}.log" 2>&1
  S=$(grep -oP '^S2S_SETUP \K\S+' "$OUT/sta_${rc}_${lib}.log" || echo null)
  H=$(grep -oP '^S2S_HOLD \K\S+' "$OUT/sta_${rc}_${lib}.log" || echo null)
  STA_JSON="$STA_JSON\"${rc}_${lib}\": {\"setup\": $S, \"hold\": $H},"
done; done
STA_JSON="${STA_JSON%,}}"

echo "== 6. full OpenLane flow from the packaged RTL and config"
mkdir -p "$OUT/flow" && cp -r "$PKG/flow/." "$OUT/flow/"
( cd "$OUT/flow" && openlane --manual-pdk --pdk-root /opt/pdk --pdk sky130A --scl sky130_fd_sc_hd \
    --run-tag repro --overwrite -j 4 config.json > "$OUT/flow.log" 2>&1 ); FLOW_RC=$?

python3 - "$PKG" "$OUT" "$MANIFEST_RC" "$MAGIC_DRC" "$KLAYOUT_DRC" "$LVS" "$FLOW_RC" "$STA_JSON" <<'PY'
import json, sys
from pathlib import Path
pkg, out = Path(sys.argv[1]), Path(sys.argv[2])
manifest_rc, magic, klay, lvs, flow_rc, sta = sys.argv[3:9]
exp = json.loads((pkg / "expected.json").read_text())
sta = json.loads(sta)
items = {}
items["manifest"] = manifest_rc == "0"
items["magic_drc_zero"] = magic == "0"
items["klayout_drc_zero"] = klay == "0"
items["lvs_match"] = lvs.startswith("Circuits match uniquely")
items["sta_all_corners_met"] = len(sta) == 9 and all(v["setup"] is not None and v["hold"] is not None and
                                                      v["setup"] >= 0 and v["hold"] >= 0 for v in sta.values())
items["sta_matches_recorded"] = all(abs(sta[c]["setup"] - exp["sta"][c]["setup"]) < 1e-3 and
                                    abs(sta[c]["hold"] - exp["sta"][c]["hold"]) < 1e-3 for c in exp["sta"])
m = out / "flow" / "runs" / "repro" / "final" / "metrics.json"
flow = json.loads(m.read_text()) if m.exists() else {}
items["flow_completed"] = flow_rc == "0" and bool(flow)
keys = ["magic__drc_error__count", "klayout__drc_error__count", "design__lvs_error__count",
        "antenna__violating__nets", "timing__setup_vio__count", "timing__hold_vio__count"]
items["flow_signoff_clean"] = bool(flow) and all(flow.get(k) == 0 for k in keys)
items["flow_matches_recorded"] = bool(flow) and all(flow.get(k) == v for k, v in exp["flow_metrics"].items())
res = {"passed": all(items.values()), "items": items, "magic_drc": magic, "klayout_drc": klay, "lvs": lvs,
       "sta": sta, "flow_metrics": {k: flow.get(k) for k in list(exp["flow_metrics"]) + keys}}
print("S2S_REPRODUCE_RESULT " + json.dumps(res))
PY
