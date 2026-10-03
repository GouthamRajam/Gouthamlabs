#!/usr/bin/env bash
# M0.1 acceptance: every Phase 0 tool responds and reports the version pinned in
# versions.lock, and the SKY130 PDK is installed. Run inside the s2s-eda container:
#   docker run --rm s2s-eda bash /opt/s2s/eda/scripts/selftest.sh
# Exits non-zero if any tool is missing, fails to run, or reports a different version.
set -uo pipefail

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

if [ "$fail" -ne 0 ]; then echo "SELFTEST FAILED"; exit 1; fi
echo "ALL TOOLS OK"
