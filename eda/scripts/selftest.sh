#!/usr/bin/env bash
# M0.1 acceptance: every tool responds. Run inside the s2s-eda container.
set -e
for t in "verilator --version" "yosys -V" "sby --help" "klayout -v" "magic --version" "netgen -batch quit"; do
  echo "== $t =="; eval "$t" || { echo "FAIL: $t"; exit 1; }
done
echo "ALL TOOLS OK"
