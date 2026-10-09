#!/usr/bin/env bash
# Run multi-corner STA across 3 corners × 3 OCV derate levels + Fmax search
set -euo pipefail
cd "$(dirname "$0")"

LIB_DIR="/nix/store/pi9m3br8ni97dfybd24lldfa185py07x-source/src/sta/test/sky130hd"
STA=sta
SCRIPT=sta_multicorner.tcl
CLK_PERIOD=50.0  # 20 MHz starting point

declare -A CORNERS=(
  [TT]="$LIB_DIR/sky130_fd_sc_hd__tt_025C_1v80.lib"
  [SS]="$LIB_DIR/sky130_fd_sc_hd__ss_n40C_1v40.lib"
  [FF]="$LIB_DIR/sky130_fd_sc_hd__ff_n40C_1v95.lib"
)

DERATES=(
  "1.0:1.0:nominal"
  "0.95:1.05:ocv5pct"
  "0.90:1.10:ocv10pct"
)

RESULTS_DIR=sta_results
mkdir -p "$RESULTS_DIR"

echo "========================================================"
echo "  Multi-Corner OCV-Derated STA — s2s_rv32i"
echo "  Target: 20 MHz ($CLK_PERIOD ns period)"
echo "========================================================"

for corner in TT SS FF; do
  lib="${CORNERS[$corner]}"
  for derate_spec in "${DERATES[@]}"; do
    IFS=: read -r early late label <<< "$derate_spec"
    tag="${corner}_${label}"
    outfile="$RESULTS_DIR/${tag}.log"

    echo ""
    echo "--- Running: $tag (early=$early, late=$late) ---"
    env -u S2S_ANTHROPIC_KEY -u S2S_MODEL_PROVIDER \
      CORNER_LIB="$lib" \
      DERATE_EARLY="$early" \
      DERATE_LATE="$late" \
      CLK_PERIOD="$CLK_PERIOD" \
      $STA -no_splash -exit $SCRIPT > "$outfile" 2>&1 || true

    echo "  Output: $outfile"
    # Extract key metrics
    if grep -q "Slack" "$outfile" 2>/dev/null; then
      grep -E "(Slack|slack|wns|tns)" "$outfile" | head -5
    elif grep -q "No paths found" "$outfile" 2>/dev/null; then
      echo "  WARNING: No paths found"
    else
      tail -3 "$outfile"
    fi
  done
done

echo ""
echo "All STA corner results saved to $RESULTS_DIR/"
echo "For Fmax search, run: bash run_fmax_search.sh"
