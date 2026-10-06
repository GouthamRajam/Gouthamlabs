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
    r = run_eqy(eqy, workdir, timeout_s=1800)
    if r.passed:
        r.metrics["method"] = "eqy (partitioned)"
        return r
    return _lec_fallback(r, rtl, pdk, netlist, top, workdir, name, d)


_LEC_PROVEN = re.compile(r"Of those cells (?P<p>\d+) are proven and (?P<u>\d+) are unproven")
_RECODE = re.compile(r"Recoding FSM `\$fsm\$\\(?P<sig>\S+?)\$\d+' from module `\\(?P<mod>\S+)'[^\n]*\n"
                     r"(?:[^\n]*mapping[^\n]*\n)?(?P<body>(?:[ \t]+[01]+ -> [-01]+\n)+)")
_FSM_OUTPUTS = re.compile(r"Information on FSM \$fsm\$\\(?P<sig>\S+?)\$\d+ .*?Output signals:\n(?P<body>(?:[ \t]+\d+: \S+\n)+)",
                          re.S)


def find_synth_log(netlist: Path) -> Path | None:
    """The Yosys log of the synthesis that produced `netlist` (OpenLane: <tag>/NN-yosys-synthesis/; the final
    netlist sits in <tag>/final/nl/)."""
    netlist = Path(netlist).resolve()
    for d in (netlist.parent, *list(netlist.parents)[:3]):
        hits = sorted([*d.glob("yosys-synthesis.log"), *d.glob("*-yosys-synthesis/yosys-synthesis.log")])
        if hits:
            return hits[-1]
    return None


def fsm_recodings(log: str) -> list[dict]:
    """Every FSM whose state encoding Yosys fsm_recode changed, from the synthesis log: the state signal, the
    old -> new code map (MSB first; new codes written exactly, '-' as 0, i.e. one-hot) and the FSM's public
    output signals (fsm_opt can merge a one-hot state bit with an identical output such as `ready`)."""
    outs = {m["sig"]: [ln.split(": ", 1)[1].strip()[1:] for ln in m["body"].splitlines()
                       if ln.split(": ", 1)[1].strip().startswith("\\")] for m in _FSM_OUTPUTS.finditer(log)}
    recs = []
    for m in _RECODE.finditer(log):
        pairs = re.findall(r"([01]+) -> ([-01]+)", m["body"])
        recs.append({"signal": m["sig"], "module": m["mod"], "width": len(pairs[0][1]),
                     "map": [(old, new.replace("-", "0")) for old, new in pairs], "outputs": outs.get(m["sig"], [])})
    return recs


def fsm_state_aliases(netlist_text: str, recs: list[dict]) -> tuple[str, list[str]]:
    """Verilog lines that give each recoded state register one named wire in the CHECKER's copy of the netlist
    (an alias, no logic), so equiv_make -encfile can pair it with the RTL register. Bit i is the net
    `\\<signal>[i]`; a bit with no such net was merged into an FSM output, taken only if a flip-flop drives that
    output directly. A wrong or missing pick cannot pass anything: the mapping is a hypothesis that equiv_induct
    must prove. Returns (lines, problems)."""
    lines, problems = [], []
    for r in recs:
        sig, bits = r["signal"], []
        for i in range(r["width"]):
            if f"\\{sig}[{i}] ;" in netlist_text:
                bits.append(f"\\{sig}[{i}] ")
                continue
            cands = [o for o in r["outputs"] if re.search(rf"\.Q\({re.escape(o)}\)", netlist_text)]
            if len(cands) != 1:
                problems.append(f"{sig}[{i}]: no netlist net (flip-flop-driven FSM outputs: {cands})")
                break
            bits.append(cands[0])
        else:
            lines.append(f"  wire [{r['width'] - 1}:0] \\{sig} ;\n  assign \\{sig}  = {{ {' , '.join(reversed(bits))} }};")
    return "\n".join(lines), problems


def _lec_fallback(eqy_res, rtl: list[Path], pdk: Path, netlist: Path, top: str, workdir: Path, name: str, d: Path):
    """eqy did not prove the designs (its partitioning cannot always pair memories / registers; it can also
    error without a counterexample). Second, independent proof: Yosys sequential equivalence with register
    correspondence (equiv_make on bit-level names, equiv_simple + equiv_induct; matched registers are
    assumed to start equal, as in standard LEC). Passes only if EVERY $equiv point is proven; any unproven
    point keeps the check failed. The eqy result stays in the metrics.

    Re-encoded FSMs (Yosys fsm_recode, e.g. binary -> one-hot) have no name correspondence. Their old -> new
    state mapping is read from the synthesis log and given to equiv_make -encfile (Yosys' own mechanism; the
    open-source counterpart of the FSM-encoding guidance commercial LEC reads from synthesis, e.g. Formality SVF).
    The mapping is a correspondence hypothesis that equiv_induct must prove like every other point."""
    import dataclasses
    ys = d / f"{name}_lec.ys"
    slog = find_synth_log(netlist)
    recs = fsm_recodings(slog.read_text(errors="replace")) if slog else []
    gate_nl, encopt, keep, fsm_problems = Path(netlist).resolve(), "", "", []
    if recs:
        nl_text = gate_nl.read_text()
        alias, fsm_problems = fsm_state_aliases(nl_text, recs)
        if alias and nl_text.count("endmodule") == 1:
            # the checker reads its own copy with the alias wires; the signed-off netlist is not touched
            gate_nl = d / f"{name}_gate.nl.v"
            gate_nl.write_text(nl_text.replace("endmodule", alias + "\nendmodule"))
            enc = d / f"{name}_fsm.enc"
            enc.write_text("".join(f".fsm {r['module']} {r['signal']}\n" + "".join(f".map {o} {n}\n" for o, n in r["map"])
                                   for r in recs))
            encopt = f"-encfile {enc} "
            keep = "".join(f" w:{r['signal']} %d" for r in recs)
        elif alias:
            fsm_problems.append("netlist has more than one module; FSM alias wires not added")
    prep = "hierarchy -top {t}\nproc\nflatten\nopt_clean\nmemory -nomap\nmemory_map\nopt_clean\nsplitnets -format []"
    prep = prep + (f" w:*{keep}" if keep else "")
    ys.write_text(f"""read_verilog -sv {' '.join(str(Path(p).resolve()) for p in rtl)}
{prep.format(t=top)}
rename {top} gold
design -stash gold
read_verilog -sv {pdk} {gate_nl}
{prep.format(t=top)}
rename {top} gate
design -stash gate
design -copy-from gold -as gold gold
design -copy-from gate -as gate gate
async2sync
equiv_make {encopt}gold gate equiv
hierarchy -top equiv
equiv_simple -seq 5
equiv_induct -seq 5
equiv_status
equiv_status -assert
""")
    log = workdir / "logs" / f"lec_{name}.log"
    rec = runner.run(["yosys", "-q", "-l", str(log), str(ys)], workdir, workdir / "logs" / f"lec_{name}_run.log",
                     "yosys", 2400)
    text = log.read_text(errors="replace") if log.exists() else ""
    counts = [(int(m["p"]), int(m["u"])) for m in _LEC_PROVEN.finditer(text)]
    proven, unproven = counts[-1] if counts else (0, None)
    ok = (rec.exit_code == 0 and not rec.timed_out and "Equivalence successfully proven!" in text
          and unproven == 0 and proven > 0)
    metrics = {**eqy_res.metrics, "method": "yosys LEC (equiv_make/equiv_simple/equiv_induct, register correspondence)"
               if ok else "eqy failed; yosys LEC fallback did not prove", "eqy_status": eqy_res.metrics.get("status"),
               "eqy_reasons": eqy_res.reasons[:3], "lec_points_proven": proven, "lec_points_unproven": unproven,
               "lec_log": str(log), "fsm_recoded": [r["signal"] for r in recs],
               "fsm_encfile": encopt.split()[1] if encopt else None, "fsm_problems": fsm_problems,
               "synth_log": str(slog) if slog else None}
    if ok and recs:
        metrics["method"] += " + FSM encoding map from the synthesis log (equiv_make -encfile)"
    if ok:
        metrics["status"] = "PASS"
    reasons = [] if ok else [*eqy_res.reasons[:3], f"yosys LEC: {proven} proven, {unproven} unproven"
                                                    + (" (timed out)" if rec.timed_out else "")]
    return dataclasses.replace(eqy_res, passed=ok, status="PASS" if ok else eqy_res.status, metrics=metrics,
                               reasons=reasons, command=["yosys", "-q", "-l", str(log), str(ys)])


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
