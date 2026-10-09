#!/usr/bin/env bash
set -euo pipefail

cd /work/tb

echo "=== Compiling with Icarus Verilog ==="
iverilog -Wall -g2012 -o uart_sim \
    -I /work/rtl \
    /work/rtl/s2s_uart_tx.v \
    /work/rtl/s2s_uart_rx.v \
    /work/rtl/s2s_uart.v \
    uart_tb.v

echo "=== Running simulation ==="
vvp -n uart_sim

echo ""
echo "=== Cross-checking against independent reference model ==="
python3 verify_results.py uart_results.txt
