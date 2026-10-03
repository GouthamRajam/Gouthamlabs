#!/usr/bin/env bash
# Verify any SKY130 GDS with open-source tools and print a pass/fail summary.
# Usage: verify_gds.sh <design.gds> <layout.v netlist> [top]
# Runs: KLayout DRC, Magic DRC, Netgen LVS. (Full version wired up in M0.7.)
# This is the "verify-it-yourself" helper from the chat — fill in deck paths in M0.7.
set -e
GDS="$1"; NET="$2"; TOP="${3:-top}"
echo "TODO(M0.7): run klayout DRC on $GDS"
echo "TODO(M0.7): run magic DRC on $GDS"
echo "TODO(M0.7): run netgen LVS between $GDS extraction and $NET (top=$TOP)"
echo "Then print: DRC(klayout)=.. DRC(magic)=.. LVS=.. -> PASS/FAIL"
