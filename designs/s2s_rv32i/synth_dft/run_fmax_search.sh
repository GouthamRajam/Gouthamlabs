#!/usr/bin/env bash
# Fmax binary search at TT corner (nominal, no OCV derate)
set -euo pipefail
cd "$(dirname "$0")"

LIB_TT="/nix/store/pi9m3br8ni97dfybd24lldfa185py07x-source/src/sta/test/sky130hd/sky130_fd_sc_hd__tt_025C_1v80.lib"
STA=sta
SCRIPT=sta_multicorner.tcl
RESULTS_DIR=sta_results
mkdir -p "$RESULTS_DIR"

echo "========================================================"
echo "  Fmax Binary Search (TT corner, nominal)"
echo "========================================================"

lo=5.0    # 200 MHz upper bound
hi=50.0   # 20 MHz lower bound (known to pass)
best_period=$hi

for i in $(seq 1 15); do
  mid=$(echo "$lo $hi" | awk '{printf "%.2f", ($1+$2)/2}')
  tag="fmax_iter${i}_${mid}ns"
  outfile="$RESULTS_DIR/${tag}.log"

  env -u S2S_ANTHROPIC_KEY -u S2S_MODEL_PROVIDER \
    CORNER_LIB="$LIB_TT" \
    DERATE_EARLY="1.0" \
    DERATE_LATE="1.0" \
    CLK_PERIOD="$mid" \
    $STA -no_splash -exit $SCRIPT > "$outfile" 2>&1 || true

  # Parse setup slack — it's the first "slack" line in the output (after --- SETUP ---)
  setup_slack=$(awk '/--- SETUP ---/,/--- HOLD ---/' "$outfile" | grep -oP '[-0-9.]+(?=\s+slack)' | head -1)

  if [ -z "$setup_slack" ]; then
    echo "  iter $i: period=${mid}ns — could not parse slack, assuming FAIL"
    lo=$mid
    continue
  fi

  is_met=$(echo "$setup_slack" | awk '{print ($1 >= 0) ? "yes" : "no"}')
  if [ "$is_met" = "yes" ]; then
    echo "  iter $i: period=${mid}ns — setup_slack=${setup_slack}ns PASS"
    best_period=$mid
    hi=$mid
  else
    echo "  iter $i: period=${mid}ns — setup_slack=${setup_slack}ns FAIL"
    lo=$mid
  fi

  # Converge within 0.25ns
  diff=$(echo "$hi $lo" | awk '{d=$1-$2; print (d<0)?-d:d}')
  converged=$(echo "$diff" | awk '{print ($1 < 0.25) ? "yes" : "no"}')
  if [ "$converged" = "yes" ]; then
    echo "  Converged after $i iterations (range < 0.25ns)"
    break
  fi
done

fmax=$(echo "$best_period" | awk '{printf "%.2f", 1000/$1}')
echo ""
echo "========================================================"
echo "  Result: best_period=${best_period}ns  Fmax=${fmax} MHz"
echo "========================================================"
