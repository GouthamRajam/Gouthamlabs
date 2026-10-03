"""Load golden cases recorded by tests/capture_golden.py."""
from __future__ import annotations

import importlib
import json
from dataclasses import dataclass
from pathlib import Path

from s2s.tools.base import ToolSpec, evaluate
from s2s.tools.result import ToolResult

GOLDEN = Path(__file__).resolve().parent / "golden"

TOOLS = ("verilator_lint", "yosys_elab", "cocotb_sim", "sby_formal", "eqy", "opensta",
         "magic_drc", "klayout_drc", "netgen_lvs", "openlane_flow")


@dataclass
class Golden:
    tool: str
    case: str
    meta: dict
    log: str
    reports: dict[str, str]

    @property
    def id(self) -> str:
        return f"{self.tool}/{self.case}"

    @property
    def expect_pass(self) -> bool:
        return self.meta["expect"] == "pass"

    @property
    def spec(self) -> ToolSpec:
        return spec_for(self.tool)

    def evaluate(self, log: str | None = None, exit_code: int | None | str = "recorded") -> ToolResult:
        """Re-run parser + Trust Layer decision on the recorded (or a modified) log."""
        code = self.meta["exit_code"] if exit_code == "recorded" else exit_code
        return evaluate(self.spec, code, self.log if log is None else log, self.reports,
                        self.meta["timed_out"])


def spec_for(tool: str) -> ToolSpec:
    return importlib.import_module(f"s2s.tools.{tool}").SPEC


def load(tool: str, case: str) -> Golden:
    d = GOLDEN / tool / case
    reports_dir = d / "reports"
    meta = json.loads((d / "meta.json").read_text())
    reports = {name: (reports_dir / name).read_text(errors="replace") if (reports_dir / name).exists()
               else "" for name in meta["reports"]}
    return Golden(tool, case, meta, (d / "log.txt").read_text(errors="replace"), reports)


def all_goldens() -> list[Golden]:
    return [load(m.parent.parent.name, m.parent.name) for m in sorted(GOLDEN.glob("*/*/meta.json"))]
