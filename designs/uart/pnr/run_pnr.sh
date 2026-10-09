#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
DESIGN_DIR="$REPO_ROOT/designs/uart"
PNR_DIR="$DESIGN_DIR/pnr"
RUN_DIR="$PNR_DIR/run"

echo "========================================================"
echo "  s2s_uart P&R via OpenLane 2.3.10 (s2s-eda)"
echo "  Config: FP_CORE_UTIL=30, antenna pre-DRT, 50 MHz"
echo "========================================================"

SRC_DIR="$PNR_DIR/src"
mkdir -p "$SRC_DIR" "$RUN_DIR"

cp "$DESIGN_DIR/rtl/"*.v "$SRC_DIR/"
cp "$PNR_DIR/constraints.sdc" "$SRC_DIR/"

echo "RTL files: $(ls "$SRC_DIR/"*.v | wc -l)"
echo "Config: $PNR_DIR/config.json"
echo ""

docker run --rm \
  --network=host \
  -v "$PNR_DIR:/work/design" \
  -v "$RUN_DIR:/work/run" \
  -e PDK_ROOT=/opt/pdk \
  -e PDK=sky130A \
  -e STD_CELL_LIBRARY=sky130_fd_sc_hd \
  -w /work \
  s2s-eda \
  bash -c '
    set -euo pipefail
    echo "OpenLane version:"
    openlane --version
    echo ""

    openlane /work/design/config.json \
      --run-tag s2s_uart_run \
      --design-dir /work/design \
      2>&1 | tee /work/run/openlane.log

    echo ""
    echo "P&R complete. Results in /work/run/"
  '

echo ""
echo "Run directory: $RUN_DIR"
echo "Done."
