#!/usr/bin/env bash
# s2s-eda selftest. Run inside the container:
#   docker run --rm s2s-eda bash /opt/s2s/eda/scripts/selftest.sh
# 1. Every tool responds and reports the version pinned in versions.lock (M0.1).
# 2. The SKY130 PDK is the pinned build (M0.1).
# 3. Functional checks (M0.2): tiny real jobs proving the tools can actually do their job,
#    not just print a version: formal proof with yices and z3, a failing proof that must
#    produce a counterexample trace, an eqy equivalence proof, and cocotb simulations
#    on Verilator and Icarus. Each must give the expected real result.
# Exits non-zero if anything is missing, differs, or gives the wrong result.
set -uo pipefail

python3_cocotb() { /opt/cocotb/bin/python3 "$@"; }

LOCK="${S2S_VERSIONS_LOCK:-$(dirname "$0")/../versions.lock}"
fail=0

pinned() { grep -E "^$1=" "$LOCK" | head -1 | cut -d= -f2-; }

# check <name> <expected-version-key> <command...>
# Runs the command, prints its first output line, and requires the pinned version in it.
check() {
  local name="$1" key="$2"; shift 2
  local want out
  want="$(pinned "$key")"
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'FAIL  %-10s command not found: %s\n' "$name" "$1"; fail=1; return
  fi
  out="$("$@" 2>&1 | grep -v -e '^Warning: netgen command' | grep -m1 .)"
  if [ -z "$want" ]; then
    printf 'FAIL  %-10s no pinned version for "%s" in %s\n' "$name" "$key" "$LOCK"; fail=1
  elif [[ "$out" != *"$want"* ]]; then
    printf 'FAIL  %-10s got "%s", expected %s\n' "$name" "$out" "$want"; fail=1
  else
    printf 'OK    %-10s %s\n' "$name" "$out"
  fi
}

echo "== s2s-eda selftest (lock: $LOCK) =="
check openlane  openlane  openlane --version
check yosys     yosys     yosys -V
check openroad  openroad  openroad -version
check opensta   opensta   sta -version
check verilator verilator verilator --version
check iverilog  iverilog  iverilog -V
check cocotb    cocotb    cocotb-config --version
check sby       sby       sby --version
check eqy       eqy       eqy --version
check magic     magic     magic --version
check klayout   klayout   klayout -v
check netgen    netgen    netgen -batch quit
check make      make      make --version
check gawk      gawk      awk --version
check sed       sed       sed --version
check clang     clang     clang++ --version
check yices     yices     yices-smt2 --version
check z3        z3        z3 --version
check perl      perl      perl -e 'print "perl $^V\n"'

# PDK: the enabled sky130A must be built from the pinned open_pdks commit (as recorded
# in the PDK's own .config/nodeinfo.json), and must include the hd standard cells.
pdk_rev="$(pinned sky130_pdk)"
pdk_dir="${PDK_ROOT:-/opt/pdk}/sky130A"
lib="$pdk_dir/libs.ref/sky130_fd_sc_hd/lib"
built_rev="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["commit"]["open_pdks"])' \
  "$pdk_dir/.config/nodeinfo.json" 2>/dev/null)"
if [ -n "$pdk_rev" ] && [ "$built_rev" = "$pdk_rev" ] && [ -d "$lib" ]; then
  printf 'OK    %-10s sky130A built from open_pdks %s, sky130_fd_sc_hd present\n' "pdk" "$built_rev"
else
  printf 'FAIL  %-10s sky130A at %s: open_pdks "%s", expected %s (hd lib dir present: %s)\n' \
    "pdk" "$pdk_dir" "$built_rev" "$pdk_rev" "$([ -d "$lib" ] && echo yes || echo no)"; fail=1
fi

# Functional checks: each runs a tiny real job and requires the expected real outcome.
# func <name> <expected-regex> <command...>   (command runs in a fresh temp dir with fixtures)
T="$(mktemp -d)"
cat > "$T/inc.v" <<'V'
module inc (input wire clk, input wire rst_n, input wire en, output reg [3:0] q);
    always @(posedge clk) if (!rst_n) q <= 4'd0; else if (en) q <= q + 4'd1;
endmodule
V
cat > "$T/inc_formal.v" <<'V'
module inc_formal (input wire clk, input wire rst_n, input wire en);
    wire [3:0] q;
    inc dut (.clk(clk), .rst_n(rst_n), .en(en), .q(q));
    reg past_valid = 1'b0;
    always @(posedge clk) past_valid <= 1'b1;
    always @(*) if (!past_valid) assume (!rst_n);
`ifdef BROKEN
    always @(*) if (past_valid) assert (q == 4'd0);
`else
    always @(posedge clk) if (past_valid && $past(rst_n))
        assert (q == $past(q) + ($past(en) ? 4'd1 : 4'd0));
`endif
endmodule
V
for v in yices z3 broken; do
  def=""; solver="$v"; [ "$v" = broken ] && { def="-DBROKEN"; solver=yices; }
  printf '[options]\nmode prove\ndepth 6\n[engines]\nsmtbmc %s\n[script]\nread -formal %s inc.v inc_formal.v\nprep -top inc_formal\n[files]\ninc.v\ninc_formal.v\n' \
    "$solver" "$def" > "$T/f_$v.sby"
done
cat > "$T/gate.v" <<'V'
module inc (input wire clk, input wire rst_n, input wire en, output reg [3:0] q);
    wire [3:0] n = en ? {q[3] ^ &q[2:0], q[2] ^ &q[1:0], q[1] ^ q[0], ~q[0]} : q;
    always @(posedge clk) q <= rst_n ? n : 4'd0;
endmodule
V
printf '[gold]\nread_verilog inc.v\nprep -top inc\n[gate]\nread_verilog gate.v\nprep -top inc\n[strategy sby]\nuse sby\ndepth 4\nengine smtbmc yices\n' > "$T/eq.eqy"
cat > "$T/test_inc.py" <<'V'
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles, ReadOnly
@cocotb.test()
async def counts(dut):
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())
    dut.rst_n.value = 0; dut.en.value = 1
    await ClockCycles(dut.clk, 2)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 3)
    await ReadOnly()
    assert int(dut.q.value) == 3, int(dut.q.value)
V
cat > "$T/run_cocotb.py" <<'V'
import sys
from cocotb.runner import get_runner
sim = sys.argv[1]
r = get_runner(sim)
r.build(verilog_sources=["inc.v"], hdl_toplevel="inc", build_dir="build_" + sim,
        timescale=("1ns", "1ps"))
r.test(hdl_toplevel="inc", test_module="test_inc", build_dir="build_" + sim)
V

func() {
  local name="$1" want="$2"; shift 2
  local out
  out="$(cd "$T" && "$@" 2>&1)"
  if grep -Eq "$want" <<<"$out"; then
    printf 'OK    %-10s %s\n' "$name" "$(grep -Em1 "$want" <<<"$out" | sed 's/^ *//' | cut -c1-90)"
  else
    printf 'FAIL  %-10s expected /%s/; last output: %s\n' "$name" "$want" "$(tail -n 2 <<<"$out" | tr '\n' ' ' | cut -c1-200)"; fail=1
  fi
}
echo "== functional checks =="
func sby-yices  'DONE \(PASS, rc=0\)'                sby -f f_yices.sby
func sby-z3     'DONE \(PASS, rc=0\)'                sby -f f_z3.sby
func sby-cex    'FAIL rc=2 with counterexample'        bash -c 'sby -f f_broken.sby | grep -q "DONE (FAIL, rc=2)" && test -s f_broken/engine_0/trace.vcd && echo "FAIL rc=2 with counterexample f_broken/engine_0/trace.vcd (expected)"'
func eqy        'Successfully proved designs equivalent' eqy -f eq.eqy
func cocotb-ver 'TESTS=1 PASS=1 FAIL=0'               python3_cocotb run_cocotb.py verilator
func cocotb-ivl 'TESTS=1 PASS=1 FAIL=0'               python3_cocotb run_cocotb.py icarus
rm -rf "$T"

if [ "$fail" -ne 0 ]; then echo "SELFTEST FAILED"; exit 1; fi
echo "ALL TOOLS OK"
