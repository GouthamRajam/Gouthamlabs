#!/bin/bash
# Gate-level compliance test runner.
# Runs all 39 RV32I tests on the flat synthesized gate netlist,
# compares signatures against RTL simulation results.

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RTL_WORK="$SCRIPT_DIR/../compliance/work"
GATE_WORK="$SCRIPT_DIR/gate_sim_work"
GATE_SIM="$SCRIPT_DIR/gate_compliance_sim"

NM=riscv64-unknown-elf-nm

if [ ! -f "$GATE_SIM" ]; then
    echo "ERROR: gate_compliance_sim not found. Compile first."
    exit 1
fi

TESTS=($(ls -d "$RTL_WORK"/I-*/test.hex 2>/dev/null | sed 's|.*/\(I-[^/]*\)/test.hex|\1|'))
NUM_TESTS=${#TESTS[@]}
echo "=== Gate-level compliance: $NUM_TESTS tests ==="

PASS=0
FAIL=0
SIG_MISMATCH=0
TIMEOUT=0

for test_name in "${TESTS[@]}"; do
    test_work="$GATE_WORK/$test_name"
    mkdir -p "$test_work"

    printf "  %-25s " "$test_name"

    # Get symbol addresses from ELF
    elf="$RTL_WORK/$test_name/$test_name.elf"
    if [ ! -f "$elf" ]; then
        printf "NO_ELF\n"
        FAIL=$((FAIL + 1))
        continue
    fi

    sig_begin=$($NM "$elf" | grep " rvtest_sig_begin" | awk '{print $1}')
    sig_end=$($NM "$elf" | grep " rvtest_sig_end" | awk '{print $1}')
    tohost_addr=$($NM "$elf" | grep " tohost$" | awk '{print $1}')
    [ -z "$tohost_addr" ] && tohost_addr="80008000"

    # Copy hex file
    cp "$RTL_WORK/$test_name/test.hex" "$test_work/test.hex"

    # Run gate-level simulation
    cd "$test_work"
    timeout 600 vvp "$GATE_SIM" \
        +sig_begin=0x$sig_begin +sig_end=0x$sig_end +tohost=0x$tohost_addr \
        > sim.log 2>&1
    sim_exit=$?
    cd "$SCRIPT_DIR"

    if [ $sim_exit -eq 124 ]; then
        printf "TIMEOUT\n"
        TIMEOUT=$((TIMEOUT + 1))
        continue
    fi

    sim_result=$(grep "^RESULT:" "$test_work/sim.log" | head -1 | awk '{print $2}')
    cycles=$(grep "cycles" "$test_work/sim.log" | head -1 | grep -o '[0-9]* cycles' | awk '{print $1}')

    if [ "$sim_result" != "PASS" ]; then
        printf "GATE_FAIL(%s)\n" "$sim_result"
        FAIL=$((FAIL + 1))
        continue
    fi

    # Compare signatures
    if diff -q "$test_work/dut_signature.txt" "$RTL_WORK/$test_name/dut_signature.txt" > /dev/null 2>&1; then
        printf "PASS (%s cycles, sig match)\n" "$cycles"
        PASS=$((PASS + 1))
    else
        printf "SIG_MISMATCH (%s cycles)\n" "$cycles"
        SIG_MISMATCH=$((SIG_MISMATCH + 1))
    fi
done

echo ""
echo "============================================"
echo "  GATE-LEVEL RESULTS: $PASS/$NUM_TESTS PASS"
echo "  FAIL: $FAIL  SIG_MISMATCH: $SIG_MISMATCH  TIMEOUT: $TIMEOUT"
echo "============================================"

if [ $PASS -eq $NUM_TESTS ]; then
    echo "  ALL TESTS PASS — gate netlist functionally equivalent to RTL"
    exit 0
else
    echo "  SOME TESTS FAILED — equivalence NOT proven"
    exit 1
fi
