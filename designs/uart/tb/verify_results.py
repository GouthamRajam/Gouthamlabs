#!/usr/bin/env python3
"""Cross-check UART simulation results against the independent reference model.

Reads uart_results.txt (from the Verilog testbench) and verifies each
TX/RX pair against the Python UART encoder/decoder. This script is the
independent oracle — it decides pass/fail.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uart_ref_model import encode_byte, decode_bits


def main():
    results_file = sys.argv[1] if len(sys.argv) > 1 else "uart_results.txt"

    with open(results_file) as f:
        lines = [l.strip() for l in f if l.strip()]

    errors = 0
    total = 0

    for i, line in enumerate(lines):
        parts = line.split()
        tx_hex, rx_hex = parts[0], parts[1]
        tx_val = int(tx_hex, 16)
        rx_val = int(rx_hex, 16)

        # Verify the reference model's encode/decode roundtrip
        encoded = encode_byte(tx_val)
        decoded, frame_ok = decode_bits(encoded)

        if decoded != tx_val:
            print(f"REF MODEL BUG byte {i}: encode/decode roundtrip failed "
                  f"(sent 0x{tx_val:02x}, ref decoded 0x{decoded:02x})")
            errors += 1

        if not frame_ok:
            print(f"REF MODEL BUG byte {i}: frame_ok is False for valid frame")
            errors += 1

        # Verify RTL matches reference
        if rx_val != tx_val:
            print(f"MISMATCH byte {i}: sent 0x{tx_val:02x}, RTL received 0x{rx_val:02x}, "
                  f"ref expects 0x{tx_val:02x}")
            errors += 1

        total += 1

    print(f"\nIndependent verification: {total} bytes checked")
    if errors == 0:
        print(f"PASS: all {total} TX/RX pairs match the reference model")
    else:
        print(f"FAIL: {errors} errors found")

    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
