"""Tape-out Readiness Report (MASTER_SPEC Part 22), computed from the checks that actually ran.

Each check gets a result: clean (1), partial (config/readiness.yaml `partial_credit`) or not run /
failed (0). Each baseline caps what a check can earn (Part 22.3 table): Full = the result, Partial =
at most partial credit (the open-source tool is not the foundry's), No = 0, n/a = not counted toward
that baseline. Score = sum(weight x earned) / sum(weights counted). Never rounds up: one decimal,
floored.
"""
from __future__ import annotations

import math

from s2s.config import _load

# Part 22.3: (counts toward A, counts toward B); "full" | "partial" | "no" | None (n/a)
CAPS = {
    "functional_sim": ("full", "full"),
    "coverage": ("full", "full"),
    "formal_equiv": ("full", "full"),
    "drc": ("full", "partial"),
    "lvs": ("full", "partial"),
    "antenna": ("full", "full"),
    "density": ("full", "full"),
    "sta_setup_hold": ("full", "partial"),
    "power": ("full", "partial"),
    "ir_em_static": ("partial", "partial"),
    "dft_atpg": ("partial", "no"),
    "signal_integrity": (None, "no"),
    "reliability": (None, "no"),
    "foundry_signoff": (None, "no"),
    "gds_integrity_repro": ("full", "full"),
}
LABEL = {
    "functional_sim": "Functional sim (RTL + gate-level)", "coverage": "Coverage (line, toggle, functional)",
    "formal_equiv": "Formal properties + RTL/netlist equivalence", "drc": "DRC", "lvs": "LVS",
    "antenna": "Antenna", "density": "Density / fill", "sta_setup_hold": "Setup + hold STA, all PDK corners",
    "power": "Power estimate", "ir_em_static": "IR drop / EM (static)", "dft_atpg": "DFT scan + ATPG fault coverage",
    "signal_integrity": "Signal integrity / crosstalk", "reliability": "Reliability (aging, ESD, latch-up)",
    "foundry_signoff": "Foundry-certified signoff (Calibre-class)",
    "gds_integrity_repro": "GDS integrity + reproducibility",
}
CLOSE = {  # what would close each gap, and when
    "drc": "foundry-certified DRC deck (Phase 1, commercial tools)",
    "lvs": "foundry-certified LVS deck (Phase 1, commercial tools)",
    "sta_setup_hold": "OCV/AOCV and SI-aware timing (Phase 1, commercial STA)",
    "power": "vector-based power with silicon-correlated models (Phase 1)",
    "ir_em_static": "full static/dynamic IR and EM with package model (Phase 1, commercial tools)",
    "dft_atpg": "scan insertion + ATPG fault coverage (Phase 1, commercial ATPG)",
    "signal_integrity": "crosstalk/SI analysis (Phase 1, commercial tools)",
    "reliability": "aging, ESD and latch-up analysis (Phase 1-2)",
    "foundry_signoff": "Calibre-class foundry signoff (Phase 1)",
}
ASSUMPTIONS = """ASSUMPTIONS
- PDK: SkyWater SKY130 (open), library sky130_fd_sc_hd. Not a commercial foundry PDK.
- DRC/LVS: open-source Magic, KLayout and Netgen decks. A foundry's own certified
  decks (e.g. Calibre) were not run and may differ.
- Timing: OpenSTA at the PDK's typical/slow/fast corners. No on-chip variation
  (OCV/AOCV), no SI-aware timing. Clock target as stated per design.
- Power/IR: estimated at 20% switching activity unless simulation activity was used;
  IR/EM analysis limited to what the open flow supports.
- DFT: plan only in Phase 0; no ATPG fault coverage number.
- Not assessed (out of open-flow scope): signal integrity/crosstalk, aging/ESD/
  latch-up reliability, foundry-certified signoff.
- No physical silicon was manufactured or tested. All results are pre-silicon,
  from simulation and layout tools.
- Baseline A = open SKY130 shuttle requirements. Baseline B = commercial production
  tape-out on a real foundry PDK."""


def _floor1(x: float) -> float:
    return math.floor(x * 10 + 1e-9) / 10


def score(results: dict[str, dict]) -> dict:
    """results: check -> {"result": "clean"|"partial"|"not run"|"failed", "tool": str, "evidence": str,
    "note": str}. Missing checks count as not run."""
    cfg = _load("readiness.yaml", "S2S_READINESS_CONFIG")
    weights, partial = cfg["weights"], float(cfg.get("partial_credit", 0.5))
    value = {"clean": 1.0, "partial": partial, "not run": 0.0, "failed": 0.0}
    rows, num = [], {"A": 0.0, "B": 0.0}
    den = {"A": 0.0, "B": 0.0}
    for key, w in weights.items():
        r = results.get(key, {"result": "not run", "tool": "-", "evidence": "", "note": "not run"})
        v = value[r["result"]]
        row = {"check": key, "label": LABEL[key], "weight": w, **r}
        for i, base in enumerate(("A", "B")):
            cap = CAPS[key][i]
            if cap is None:
                row[f"earned_{base}"] = None
                continue
            earned = 0.0 if cap == "no" else min(v, 1.0 if cap == "full" else partial)
            row[f"earned_{base}"] = round(w * earned, 4)
            num[base] += w * earned
            den[base] += w
        rows.append(row)
    gaps = []
    for row in rows:
        full = all(row[f"earned_{b}"] is None or row[f"earned_{b}"] >= row["weight"] for b in ("A", "B"))
        if not full:
            gaps.append({"check": row["label"], "result": row["result"],
                         "closes_with": CLOSE.get(row["check"], "fix the failing check and re-run (this phase)")
                         if row["result"] in ("clean", "partial") else "fix and re-run the check (this phase)"})
    return {"baseline_A_pct": _floor1(100 * num["A"] / den["A"]), "baseline_B_pct": _floor1(100 * num["B"] / den["B"]),
            "partial_credit": partial, "rows": rows, "gaps": gaps, "assumptions": ASSUMPTIONS,
            "weights_A_total": den["A"], "weights_B_total": den["B"]}


def markdown(design: str, rep: dict, links: dict[str, str]) -> str:
    out = [f"# Tape-out Readiness Report: {design}", "",
           f"**Baseline A (open shuttle): {rep['baseline_A_pct']:.1f}% · Baseline B (commercial production): "
           f"{rep['baseline_B_pct']:.1f}%**", "",
           "Pre-silicon: no number here proves working silicon, only that the design passes the checks that were run.",
           "", "## Rubric", "",
           "| Check | Weight | Result | Earned A | Earned B | Tool (version) | Evidence |", "|---|---|---|---|---|---|---|"]
    for r in rep["rows"]:
        a = "n/a" if r["earned_A"] is None else f"{r['earned_A']:g}"
        out.append(f"| {r['label']} | {r['weight']} | {r['result']}{' - ' + r['note'] if r.get('note') else ''} | {a} | "
                   f"{r['earned_B']:g} | {r['tool']} | {r.get('evidence', '')} |")
    out += ["", f"Partial = {rep['partial_credit']:g} of the weight. A counts {rep['weights_A_total']:g} weight points "
            f"(the three n/a checks are excluded); B counts {rep['weights_B_total']:g}.", "", "## Gaps", ""]
    out += [f"- **{g['check']}** ({g['result']}): closes with {g['closes_with']}" for g in rep["gaps"]] or ["- none"]
    out += ["", "## Assumptions", "", "```", rep["assumptions"], "```", "", "## Evidence", ""]
    out += [f"- {k}: `{v}`" for k, v in links.items()]
    return "\n".join(out) + "\n"
