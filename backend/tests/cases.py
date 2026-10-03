"""Every adapter's real pass and fail cases, shared by the golden-capture script and the
live integration tests. Each case copies its fixture inputs into a fresh working
directory, runs the real adapter in s2s-eda, and states whether it must pass.
"""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from s2s.tools import runner
from s2s.tools.cocotb_sim import run_cocotb_sim
from s2s.tools.eqy import run_eqy
from s2s.tools.klayout_drc import run_klayout_drc
from s2s.tools.magic_drc import run_magic_drc
from s2s.tools.netgen_lvs import run_netgen_lvs
from s2s.tools.openlane_flow import run_openlane_flow
from s2s.tools.opensta import run_opensta
from s2s.tools.result import ToolResult
from s2s.tools.sby_formal import run_sby_formal
from s2s.tools.verilator_lint import run_verilator_lint
from s2s.tools.yosys_elab import run_yosys_elab

FIX = Path(__file__).resolve().parent / "fixtures"
GOLDEN = Path(__file__).resolve().parent / "golden"


@dataclass(frozen=True)
class Case:
    tool: str
    name: str  # "pass" or "fail_<what>"
    run: Callable[[Path], ToolResult]
    slow: bool = False

    @property
    def expect_pass(self) -> bool:
        return self.name.startswith("pass")

    @property
    def id(self) -> str:
        return f"{self.tool}/{self.name}"


def _copy(src: str, w: Path) -> Path:
    """Copy fixtures/<src> (file or dir) into the workdir; return the copy."""
    s = FIX / src
    d = w / Path(src).name
    if s.is_dir():
        shutil.copytree(s, d, dirs_exist_ok=True)
    else:
        shutil.copy2(s, d)
    return d


def _rtl(name: str) -> Callable[[Path], Path]:
    return lambda w: _copy(f"rtl/{name}.v", w)


def lint(name: str) -> Callable[[Path], ToolResult]:
    return lambda w: run_verilator_lint([_rtl(name)(w)], name, w)


def elab(name: str) -> Callable[[Path], ToolResult]:
    return lambda w: run_yosys_elab([_rtl(name)(w)], name, w)


def cocotb(test: str, sim: str) -> Callable[[Path], ToolResult]:
    def run(w: Path) -> ToolResult:
        _copy(f"cocotb/{test}.py", w)
        return run_cocotb_sim([_rtl("counter")(w)], "counter", test, w, simulator=sim, seed=1234,
                              coverage=(sim == "verilator"))
    return run


def sby(task: str) -> Callable[[Path], ToolResult]:
    def run(w: Path) -> ToolResult:
        _copy("rtl", w)
        d = _copy("sby", w)
        return run_sby_formal(d / f"{task}.sby", w)
    return run


def eqy(task: str) -> Callable[[Path], ToolResult]:
    def run(w: Path) -> ToolResult:
        d = _copy("eqy", w)
        return run_eqy(d / f"{task}.eqy", w)
    return run


def sta(sdc: str) -> Callable[[Path], ToolResult]:
    def run(w: Path) -> ToolResult:
        nl, s, spef = (_copy(f"spm_signoff/{f}", w) for f in ("spm.nl.v", sdc, "spm.nom.spef"))
        return run_opensta(nl, s, "spm", w, corner="tt_025C_1v80", spef=spef)
    return run


def drc_bad_gds(w: Path) -> Path:
    """spm.gds plus one injected met1 width/area defect (fixtures/derive/inject_drc_violation.py)."""
    gds = _copy("spm_signoff/spm.gds", w)
    script = _copy("derive/inject_drc_violation.py", w)
    bad = w / "spm_drc_bad.gds"
    rec = runner.run(["klayout", "-b", "-r", str(script), "-rd", f"input={gds}", "-rd", f"output={bad}",
                      "-rd", "top=spm"], w, w / "logs" / "inject_drc_violation.log", "klayout", 600)
    if rec.exit_code != 0 or not bad.exists():
        raise RuntimeError(f"could not derive DRC-violating GDS; see {rec.log_path}")
    return bad


def lvs_bad_netlist(w: Path) -> Path:
    """spm.pnl.v with flip-flop _252_'s D pin miswired to its neighbour's net."""
    src = (FIX / "spm_signoff" / "spm.pnl.v").read_text()
    old = " sky130_fd_sc_hd__dfrtp_1 _252_ (.CLK(clknet_3_7__leaf_clk),\n    .D(\\dsa[0].y_out_next ),"
    new = " sky130_fd_sc_hd__dfrtp_1 _252_ (.CLK(clknet_3_7__leaf_clk),\n    .D(\\dsa[0].last_carry_next ),"
    if src.count(old) != 1:
        raise RuntimeError("spm.pnl.v fixture changed; cannot derive the LVS-mismatch netlist")
    bad = w / "spm_lvs_bad.pnl.v"
    bad.write_text(src.replace(old, new))
    return bad


def magic(bad: bool) -> Callable[[Path], ToolResult]:
    return lambda w: run_magic_drc(drc_bad_gds(w) if bad else _copy("spm_signoff/spm.gds", w), "spm", w)


def klayout(bad: bool) -> Callable[[Path], ToolResult]:
    return lambda w: run_klayout_drc(drc_bad_gds(w) if bad else _copy("spm_signoff/spm.gds", w), "spm", w)


def lvs(bad: bool) -> Callable[[Path], ToolResult]:
    def run(w: Path) -> ToolResult:
        spice = _copy("spm_signoff/spm.spice", w)
        nl = lvs_bad_netlist(w) if bad else _copy("spm_signoff/spm.pnl.v", w)
        return run_netgen_lvs(spice, nl, "spm", w)
    return run


def openlane(config: str, tag: str) -> Callable[[Path], ToolResult]:
    def run(w: Path) -> ToolResult:
        d = _copy("openlane_spm", w)
        return run_openlane_flow(d / config, w, run_tag=tag)
    return run


CASES: list[Case] = [
    Case("verilator_lint", "pass", lint("counter")),
    Case("verilator_lint", "fail_width_mismatch", lint("width_mismatch")),
    Case("verilator_lint", "fail_syntax_error", lint("syntax_error")),
    Case("yosys_elab", "pass", elab("counter")),
    Case("yosys_elab", "fail_comb_loop", elab("comb_loop")),
    Case("yosys_elab", "fail_latch", elab("latch")),
    Case("yosys_elab", "fail_syntax_error", elab("syntax_error")),
    Case("cocotb_sim", "pass_verilator", cocotb("test_counter_pass", "verilator")),
    Case("cocotb_sim", "fail_verilator", cocotb("test_counter_fail", "verilator")),
    Case("cocotb_sim", "pass_icarus", cocotb("test_counter_pass", "icarus")),
    Case("cocotb_sim", "fail_icarus", cocotb("test_counter_fail", "icarus")),
    Case("sby_formal", "pass", sby("counter_pass")),
    Case("sby_formal", "fail_assertion", sby("counter_fail")),
    Case("eqy", "pass", eqy("adder_pass")),
    Case("eqy", "fail_not_equivalent", eqy("adder_fail")),
    Case("opensta", "pass", sta("spm.sdc")),
    Case("opensta", "fail_setup", sta("spm_tight.sdc")),
    Case("magic_drc", "pass", magic(False)),
    Case("magic_drc", "fail_met1_width", magic(True)),
    Case("klayout_drc", "pass", klayout(False)),
    Case("klayout_drc", "fail_met1_width", klayout(True)),
    Case("netgen_lvs", "pass", lvs(False)),
    Case("netgen_lvs", "fail_miswired", lvs(True)),
    Case("openlane_flow", "pass", openlane("config.yaml", "pass"), slow=True),
    Case("openlane_flow", "fail_timing", openlane("config_tight_clock.yaml", "fail_timing"), slow=True),
]
