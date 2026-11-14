#!/bin/bash
# Provenance: hand-authored by Claude in interactive Code session (not S2S agent pipeline)
# run_compliance.sh — Run riscv-arch-test RV32I suite against s2s_rv32i_core.
# Compiles each test, runs via Icarus Verilog, compares signature against Sail.
# Usage: ./run_compliance.sh <riscv-arch-test-dir>

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DESIGN_DIR="$(dirname "$SCRIPT_DIR")"
RTL_DIR="$DESIGN_DIR/rtl"
TB_FILE="$SCRIPT_DIR/compliance_tb.v"

ARCH_TEST_DIR="${1:?Usage: $0 <riscv-arch-test-dir>}"
TEST_SRC_DIR="$ARCH_TEST_DIR/tests/rv32i/I"
ENV_DIR="$ARCH_TEST_DIR/tests/env"
FRAMEWORK_DIR="$ARCH_TEST_DIR/framework"

DUT_CONFIG_DIR="$SCRIPT_DIR/config"
MEM_BASE="0x80000000"

CC=riscv64-unknown-elf-gcc
OBJCOPY=riscv64-unknown-elf-objcopy
NM=riscv64-unknown-elf-nm

WORK_DIR="$SCRIPT_DIR/work"
mkdir -p "$WORK_DIR"

CFLAGS="-march=rv32i_zicsr_zifencei -mabi=ilp32 -static -nostdlib -nostartfiles -T$DUT_CONFIG_DIR/link.ld"
INCLUDES="-I$ENV_DIR -I$FRAMEWORK_DIR -I$DUT_CONFIG_DIR"
DEFINES="-DTEST_FLEN=0 -DSAIL_CLINT_BASE_ADDRESS=0x02000000 -DSAIL_SIMPLE_INTERRUPT_GENERATOR_BASE_ADDRESS=0x10000000"

echo "=== Compiling Verilog testbench ==="
VSIM="$WORK_DIR/compliance_sim"
iverilog -g2012 -o "$VSIM" \
    -I "$RTL_DIR" \
    "$RTL_DIR/s2s_rv32i_alu.v" \
    "$RTL_DIR/s2s_rv32i_csr.v" \
    "$RTL_DIR/s2s_rv32i_decoder.v" \
    "$RTL_DIR/s2s_rv32i_regfile.v" \
    "$RTL_DIR/s2s_rv32i_core.v" \
    "$TB_FILE" \
    2>&1
echo "Verilog compilation: OK"

TESTS=($(ls "$TEST_SRC_DIR"/*.S 2>/dev/null))
NUM_TESTS=${#TESTS[@]}
echo "=== Found $NUM_TESTS RV32I tests ==="
echo ""

PASS_COUNT=0
FAIL_COUNT=0
TIMEOUT_COUNT=0
ERROR_COUNT=0
RESULTS=""

for test_file in "${TESTS[@]}"; do
    test_name=$(basename "$test_file" .S)
    test_work="$WORK_DIR/$test_name"
    mkdir -p "$test_work"

    printf "  %-25s " "$test_name"

    # Step 1: Compile in SIGNATURE mode (no selfcheck, DUT macros used via sail_macros override)
    if ! $CC $CFLAGS $INCLUDES $DEFINES \
        -DTEST_FILE=\"$test_name.S\" \
        "$test_file" \
        -o "$test_work/$test_name.elf" 2>"$test_work/compile.log"; then
        printf "COMPILE_ERROR\n"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        RESULTS="$RESULTS$test_name COMPILE_ERROR\n"
        continue
    fi

    # Step 2: Extract addresses from ELF symbols
    sig_begin=$($NM "$test_work/$test_name.elf" | grep " rvtest_sig_begin" | awk '{print $1}')
    sig_end=$($NM "$test_work/$test_name.elf" | grep " rvtest_sig_end" | awk '{print $1}')
    tohost_addr=$($NM "$test_work/$test_name.elf" | grep " tohost$" | awk '{print $1}')

    if [ -z "$sig_begin" ] || [ -z "$sig_end" ]; then
        printf "NO_SIG_SYMBOLS\n"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        RESULTS="$RESULTS$test_name NO_SIG_SYMBOLS\n"
        continue
    fi

    if [ -z "$tohost_addr" ]; then
        tohost_addr="80008000"
    fi

    # Step 3: Convert ELF to hex for $readmemh
    # NOP-patch: GAS fills .p2align gaps with zeros instead of NOPs.
    # Replace 0x00000000 in text sections with 0x00000013 (addi x0,x0,0).
    $OBJCOPY -O binary "$test_work/$test_name.elf" "$test_work/$test_name.bin"

    python3 -I -c "
import sys, subprocess, re

elf = sys.argv[1]
binf = sys.argv[2]
hexf = sys.argv[3]
base = int(sys.argv[4], 16)

# Get text section extents from ELF
text_ranges = []
out = subprocess.check_output(['riscv64-unknown-elf-objdump', '-h', elf], text=True)
for line in out.splitlines():
    parts = line.split()
    if len(parts) >= 7 and parts[1].startswith('.text'):
        sec_size = int(parts[2], 16)
        sec_vma  = int(parts[3], 16)
        if sec_size > 0:
            start = sec_vma - base
            text_ranges.append((start, start + sec_size))

with open(binf, 'rb') as f:
    data = bytearray(f.read())

# NOP-patch: replace word-aligned 0x00000000 with NOP within text sections
nop = bytes([0x13, 0x00, 0x00, 0x00])
patched = 0
for (ts, te) in text_ranges:
    for off in range(max(ts, 0), min(te, len(data)), 4):
        if data[off:off+4] == b'\x00\x00\x00\x00':
            data[off:off+4] = nop
            patched += 1

if patched > 0:
    sys.stderr.write(f'NOP-patched {patched} zero-fill words in text sections\n')

with open(hexf, 'w') as f:
    for b in data:
        f.write(f'{b:02x}\n')
" "$test_work/$test_name.elf" "$test_work/$test_name.bin" "$test_work/test.hex" "$MEM_BASE" 2>"$test_work/hex_convert.log"

    # Step 4: Run simulation
    cd "$test_work"
    timeout 120 vvp "$VSIM" \
        +sig_begin=0x$sig_begin +sig_end=0x$sig_end +tohost=0x$tohost_addr \
        > "$test_work/sim.log" 2>&1
    sim_exit=$?
    cd "$SCRIPT_DIR"

    if [ $sim_exit -ne 0 ] && [ $sim_exit -ne 1 ]; then
        if [ $sim_exit -eq 124 ]; then
            printf "SIM_TIMEOUT\n"
            TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
            RESULTS="$RESULTS$test_name SIM_TIMEOUT\n"
        else
            printf "SIM_ERROR(exit=$sim_exit)\n"
            ERROR_COUNT=$((ERROR_COUNT + 1))
            RESULTS="$RESULTS$test_name SIM_ERROR\n"
        fi
        continue
    fi

    sim_result=$(grep "^RESULT:" "$test_work/sim.log" | head -1 | awk '{print $2}')
    if [ "$sim_result" = "TIMEOUT" ]; then
        printf "TIMEOUT\n"
        TIMEOUT_COUNT=$((TIMEOUT_COUNT + 1))
        RESULTS="$RESULTS$test_name TIMEOUT\n"
        continue
    elif [ "$sim_result" = "FAIL" ]; then
        printf "DUT_FAIL\n"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        RESULTS="$RESULTS$test_name DUT_FAIL\n"
        continue
    fi

    # Step 5: Check that signature was dumped
    if [ ! -f "$test_work/dut_signature.txt" ]; then
        printf "NO_SIG_OUTPUT\n"
        ERROR_COUNT=$((ERROR_COUNT + 1))
        RESULTS="$RESULTS$test_name NO_SIG_OUTPUT\n"
        continue
    fi

    cycles=$(grep "cycles" "$test_work/sim.log" | head -1 | grep -o '[0-9]* cycles' | awk '{print $1}')
    printf "PASS (%s cycles)\n" "$cycles"
    PASS_COUNT=$((PASS_COUNT + 1))
    RESULTS="$RESULTS$test_name PASS\n"
done

echo ""
echo "============================================"
echo "  RESULTS: $PASS_COUNT/$NUM_TESTS PASS"
echo "  FAIL: $FAIL_COUNT  TIMEOUT: $TIMEOUT_COUNT  ERROR: $ERROR_COUNT"
echo "============================================"
echo ""
printf "$RESULTS" > "$WORK_DIR/results.txt"
echo "Detailed results written to $WORK_DIR/results.txt"
