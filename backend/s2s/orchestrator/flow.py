"""The Phase 0 design flow (MASTER_SPEC Part 6.1): stages, owning teams, order and gates.

2A (rtl) and 2B (test_build) both start from the approved architecture and run in
parallel; they meet in verification closure (2C).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Stage:
    name: str
    team_id: str  # owning team in config/management.yaml; its lead agent runs the task
    depends_on: tuple[str, ...]
    title: str
    gate_after: str | None = None  # human gate on leaving this stage (G1..G4)


STAGES: tuple[Stage, ...] = (
    Stage("spec", "spec_requirements", (), "Write the design specification"),
    Stage("architecture", "micro_architecture", ("spec",), "Define the micro-architecture", "G1"),
    Stage("rtl", "datapath_rtl", ("architecture",), "Write lint-clean RTL (Zone 2A)"),
    Stage("test_build", "test_planning", ("architecture",), "Build the test environment (Zone 2B)"),
    Stage("verification", "regression_ops", ("rtl", "test_build"),
          "Close verification: regression, coverage, formal (Zone 2C)", "G2"),
    Stage("synthesis", "synthesis_constraints", ("verification",), "Synthesize with constraints"),
    Stage("dft", "dft", ("synthesis",), "Insert design-for-test"),
    Stage("floorplan", "floorplan_power_grid", ("dft",), "Floorplan and power grid"),
    Stage("place_route", "place_route", ("floorplan",), "Place and route"),
    Stage("signoff", "timing_signoff", ("place_route",), "Signoff: timing, power, DRC/LVS", "G3"),
    Stage("gdsii", "tapeout_release", ("signoff",), "Assemble the GDSII tape-out package", "G4"),
)
STAGE_NAMES = tuple(s.name for s in STAGES)


def stage(name: str) -> Stage:
    return next(s for s in STAGES if s.name == name)


def select_stages(from_stage: str | None = None, to_stage: str | None = None) -> list[Stage]:
    """The contiguous slice of the flow from `from_stage` to `to_stage` (inclusive)."""
    names = list(STAGE_NAMES)
    lo = names.index(from_stage) if from_stage else 0
    hi = names.index(to_stage) if to_stage else len(names) - 1
    if lo > hi:
        raise ValueError(f"from_stage {from_stage!r} comes after to_stage {to_stage!r}")
    return list(STAGES[lo:hi + 1])
