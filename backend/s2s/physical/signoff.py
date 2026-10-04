"""Independent signoff runs on the final streamed GDS and final netlist (Zone 4, M0.7).

OpenLane's own signoff steps run inside the flow; these re-run every check with the S2S adapters so
the result does not rest on one tool path (Calla: "DRC with BOTH Magic and KLayout ... all on the
final streamed GDS"; Chronos: every PDK corner; Gideon/Proof: re-verify the packaged GDS):

  extract_spice   Magic: GDS -> SPICE (same settings as OpenLane's extraction, but from the GDS)
  lvs             Netgen (adapter) extracted layout vs the powered netlist
  sta_corners     OpenSTA (adapter) 3 RC corners (SPEF) x 3 library corners = 9 corners
  power           OpenSTA report_power at the 3 nominal corners, with a stated input activity
  antenna         OpenROAD check_antennas -verbose on the final ODB (per-net ratio vs limit)
  density         the PDK's own density deck (met_min_ca_density.lydrc) on the GDS
  equivalence     eqy: RTL vs a netlist, gate side read with the PDK's formal cell models
  gls             the M0.6 cocotb testbench on the final netlist (Icarus + PDK cell models)
  gds_readback    KLayout reads the GDS: top cell, layers, bounding box
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from s2s.physical import dfm
from s2s.tools import runner
from s2s.tools.cocotb_regress import run_cocotb_regress
from s2s.tools.eqy import run_eqy
from s2s.tools.klayout_drc import run_klayout_drc
from s2s.tools.netgen_lvs import run_netgen_lvs
from s2s.tools.opensta import run_opensta

MAGICRC = "/opt/pdk/sky130A/libs.tech/magic/sky130A.magicrc"
CELL_MODELS = ["/opt/pdk/sky130A/libs.ref/sky130_fd_sc_hd/verilog/primitives.v",
               "/opt/pdk/sky130A/libs.ref/sky130_fd_sc_hd/verilog/sky130_fd_sc_hd.v"]
LIB_CORNERS = {"tt": "tt_025C_1v80", "ss": "ss_100C_1v60", "ff": "ff_n40C_1v95"}
RC_CORNERS = ("nom", "min", "max")


class SignoffError(RuntimeError):
    """A signoff tool could not run (never read as a pass)."""


def extract_spice(gds: Path, top: str, workdir: Path, name: str = "ext") -> tuple[Path, dict]:
    out_dir = (workdir / "signoff" / name).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    spice = out_dir / f"{top}.spice"
    if spice.exists():
        spice.unlink()
    tcl = out_dir / "extract.tcl"
    tcl.write_text(f"""gds noduplicates true
gds read {Path(gds).resolve()}
load {top} -dereference
cd {out_dir}
extract do local
extract no capacitance
extract no coupling
extract no resistance
extract no adjust
extract unique
extract
ext2spice lvs
ext2spice -o {spice} {top}.ext
puts "S2S_EXTRACT_DONE"
quit -noprompt
""")
    cmd = ["magic", "-dnull", "-noconsole", "-rcfile", MAGICRC, str(tcl)]
    rec = runner.run(cmd, workdir, workdir / "logs" / f"magic_extract_{name}.log", "magic", 1800)
    log = Path(rec.log_path).read_text(errors="replace")
    if rec.exit_code != 0 or "S2S_EXTRACT_DONE" not in log or not spice.exists():
        raise SignoffError(f"Magic extraction failed (exit {rec.exit_code}); see {rec.log_path}")
    return spice, {"command": runner.command_str(cmd), "log": str(rec.log_path), "tool_version": rec.tool_version,
                   "devices": sum(1 for ln in spice.read_text().splitlines() if ln.startswith("X"))}


def lvs(gds: Path, powered_netlist: Path, top: str, workdir: Path, name: str = "ext"):
    spice, info = extract_spice(gds, top, workdir, name)
    r = run_netgen_lvs(spice, powered_netlist, top, workdir)
    r.metrics["extraction"] = info
    return r


def sta_corners(netlist: Path, sdc: Path, top: str, workdir: Path, spef: dict[str, Path]) -> dict:
    """9 corners: every RC corner (SPEF) x every library corner; post-route (propagated clocks)."""
    out = {}
    for rc in RC_CORNERS:
        for lib_key, lib in LIB_CORNERS.items():
            name = f"{rc}_{lib}"
            r = run_opensta(netlist, sdc, top, workdir, corner=lib, spef=spef[rc], post_route=True, tag=name, paths=3)
            out[name] = r
    return out


_POWER_TOTAL = re.compile(r"^Total\s+(\S+)\s+(\S+)\s+(\S+)\s+(\S+)", re.M)


def power(netlist: Path, sdc: Path, top: str, workdir: Path, spef: Path, activity: float) -> dict:
    """report_power at the nominal RC corner for each library corner, with the input activity stated."""
    res = {}
    for lib_key, lib in LIB_CORNERS.items():
        tcl = (workdir / ".s2s" / f"power_{top}_{lib}.tcl").resolve()
        tcl.parent.mkdir(parents=True, exist_ok=True)
        tcl.write_text(f"""read_liberty /opt/pdk/sky130A/libs.ref/sky130_fd_sc_hd/lib/sky130_fd_sc_hd__{lib}.lib
read_verilog {Path(netlist).resolve()}
link_design {top}
read_sdc {Path(sdc).resolve()}
set_propagated_clock [all_clocks]
read_spef {Path(spef).resolve()}
set_power_activity -input -activity {activity}
report_power -digits 6
puts S2S_POWER_DONE
""")
        cmd = ["sta", "-no_init", "-exit", str(tcl)]
        rec = runner.run(cmd, workdir, workdir / "logs" / f"power_{top}_{lib}.log", "opensta", 900)
        log = Path(rec.log_path).read_text(errors="replace")
        m = _POWER_TOTAL.search(log)
        if rec.exit_code != 0 or "S2S_POWER_DONE" not in log or not m:
            raise SignoffError(f"OpenSTA power at {lib} failed; see {rec.log_path}")
        res[lib] = {"internal_w": float(m.group(1)), "switching_w": float(m.group(2)),
                    "leakage_w": float(m.group(3)), "total_w": float(m.group(4)), "log": str(rec.log_path),
                    "command": runner.command_str(cmd), "tool_version": rec.tool_version}
    return res


def antenna(odb: Path, workdir: Path) -> tuple[list[dict], dict]:
    report = (workdir / "signoff" / "antenna_verbose.rpt").resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    if report.exists():
        report.unlink()
    tcl = (workdir / ".s2s" / "antenna.tcl").resolve()
    tcl.parent.mkdir(parents=True, exist_ok=True)
    tcl.write_text(dfm.antenna_tcl(Path(odb).resolve(), report))
    cmd = ["openroad", "-exit", "-no_splash", str(tcl)]
    rec = runner.run(cmd, workdir, workdir / "logs" / "antenna_verbose.log", "openroad", 900)
    log = Path(rec.log_path).read_text(errors="replace")
    m_net = re.search(r"Found (\d+) net violations", log)
    m_pin = re.search(r"Found (\d+) pin violations", log)
    if rec.exit_code != 0 or "S2S_ANT_DONE" not in log or not report.exists() or not m_net or not m_pin:
        raise SignoffError(f"OpenROAD antenna check failed; see {rec.log_path}")
    nets = dfm.parse_antenna_verbose(report.read_text())
    return nets, {"net_violations": int(m_net.group(1)), "pin_violations": int(m_pin.group(1)),
                  "nets_checked": len(nets), "worst": nets[:5], "log": str(rec.log_path),
                  "command": runner.command_str(cmd), "tool_version": rec.tool_version}


_CA = re.compile(r"^(\w+)_ca_density is ([\d.eE+-]+)", re.M)


def density(gds: Path, top: str, workdir: Path):
    r = run_klayout_drc(gds, top, workdir, deck=dfm.DENSITY_DECK, name="density")
    log = Path(r.log_path).read_text(errors="replace") if r.log_path else ""
    r.metrics["clear_area_density"] = {k: float(v) for k, v in _CA.findall(log)}
    if len(r.metrics["clear_area_density"]) < 6:
        r.passed = False
        r.reasons.append("density deck did not report all 6 layers")
    return r


def equivalence(rtl: list[Path], netlist: Path, top: str, workdir: Path, name: str):
    d = (workdir / "signoff" / f"eqy_{name}").resolve()
    d.mkdir(parents=True, exist_ok=True)
    pdk = d / "formal_pdk.v"
    rec = runner.run(["eqy.formal_pdk_proc", "--output", str(pdk), *CELL_MODELS], workdir,
                     workdir / "logs" / f"formal_pdk_{name}.log", "eqy", 600)
    if rec.exit_code != 0 or not pdk.exists():
        raise SignoffError(f"could not prepare the PDK formal cell models; see {rec.log_path}")
    eqy = d / f"{name}.eqy"
    eqy.write_text(f"""[gold]
read_verilog -formal -sv {' '.join(str(Path(p).resolve()) for p in rtl)}

[gate]
read_verilog -formal -sv {pdk} {Path(netlist).resolve()}

[script]
hierarchy -top {top}
proc
prep -top {top} -flatten
memory -nomap
async2sync

[strategy sat]
use sat
depth 5

[strategy pdr]
use sby
engine abc pdr -rfi
""")
    return run_eqy(eqy, workdir, timeout_s=1800)


def gls(netlist: Path, top: str, tb_dir: Path, test_module: str, workdir: Path, seeds: list[int]):
    """Gate-level simulation: the verification testbench (ports only, so it runs unchanged) on the
    final netlist, with the PDK's functional cell models in Icarus."""
    return run_cocotb_regress([Path(p) for p in CELL_MODELS] + [Path(netlist)], top, test_module, tb_dir, workdir,
                              "signoff/gls", seeds, simulators=("icarus",), coverage=False, waves=False,
                              defines={"FUNCTIONAL": 1, "UNIT_DELAY": "#0"}, timeout_s=3600)


_READBACK = r'''
import json, pya
ly = pya.Layout()
ly.read(inp)
tops = [c.name for c in ly.top_cells()]
layers = sorted({f"{i.layer}/{i.datatype}" for i in ly.layer_infos()})
c = ly.cell(top) if ly.has_cell(top) else None
b = c.bbox() if c else None
open(out, "w").write(json.dumps({"top_cells": tops, "layers": layers, "cells": ly.cells(), "dbu": ly.dbu,
    "bbox_um": [b.left * ly.dbu, b.bottom * ly.dbu, b.right * ly.dbu, b.top * ly.dbu] if b else None,
    "labels": sorted({s.text_string for li in ly.layer_indexes() for s in (c.shapes(li).each() if c else []) if s.is_text()})}))
print("S2S_READBACK_DONE")
'''


def gds_readback(gds: Path, top: str, workdir: Path, name: str = "readback") -> dict:
    script = (workdir / ".s2s" / f"{name}.py").resolve()
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(_READBACK)
    out = (workdir / "signoff" / f"{name}.json").resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    cmd = ["klayout", "-b", "-r", str(script), "-rd", f"inp={Path(gds).resolve()}", "-rd", f"top={top}",
           "-rd", f"out={out}"]
    rec = runner.run(cmd, workdir, workdir / "logs" / f"{name}.log", "klayout", 600)
    if rec.exit_code != 0 or not out.exists():
        raise SignoffError(f"KLayout could not read the GDS back; see {rec.log_path}")
    data = json.loads(out.read_text())
    data["command"] = runner.command_str(cmd)
    return data
