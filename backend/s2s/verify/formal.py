"""Formal harness (Euclid, A.7; M0.6 acceptance 3): SymbiYosys on Euclid's property file.

Euclid writes formal/formal_top.sv: a wrapper module `formal_top` whose inputs are the DUT's
inputs, which instantiates the DUT by its port names (no RTL edits, no hierarchical references
into the RTL: port-level properties only, keeping 2B independent of the RTL internals). Every
property is a labelled pair: `ap_<name>: assert(...)` and `cp_<name>: cover(...)` (the cover is the
property's antecedent/trigger: the vacuity check). Assumptions are `am_<name>: assume(...)`.

The harness writes the .sby files itself:
  prove  (mode prove, k-induction, depth = coverage_targets formal_min_depth)
  bmc    (mode bmc, same depth; only if prove could not finish the induction)
  cover  (mode cover, same depth): every cp_<name> must be reached, else the property is vacuous.
  free   (mode bmc with every assertion checked, --keep-going) with the DUT replaced by a stub
         whose outputs are unconstrained: a property that still holds does not depend on the
         design at all (a tautology such as `assert(x || 1)`), so it is not meaningful.
A property counts as PROVEN only if prove passed for it, its cover was reached, and it fails
against the free stub (it constrains the design's behavior).
"""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools.sby_formal import run_sby_formal

_LABEL = re.compile(r"\b(ap|cp|am)_(\w+)\s*:\s*(assert|cover|assume)\b")
_HIER = re.compile(r"\bdut\s*\.\s*\w+")
# Per-property results come from the engine's own lines ("Assert failed in formal_top: ap_x",
# "Reached cover statement in step N at formal_top: cp_x"); sby's end summary lists only a few
# traces and then "and N further traces", so it must not be the source.
_FAILED_RE = re.compile(r"Assert failed in formal_top: ap_(\w+)|failed assertion formal_top\.ap_(\w+)")
_REACHED_RE = re.compile(r"(?<![Uu]n)[Rr]eached cover statement in step \d+ at formal_top: cp_(\w+)|"
                         r"(?<![Uu]n)reached cover statement formal_top\.cp_(\w+)")


class _Names:
    def __init__(self, rx: re.Pattern):
        self.rx = rx

    def findall(self, text: str) -> list[str]:
        return [a or b for a, b in self.rx.findall(text)]


_FAILED = _Names(_FAILED_RE)
_REACHED = _Names(_REACHED_RE)
_DONE = re.compile(r"DONE \((\w+), rc=\d+\)")


def lint_properties(text: str) -> tuple[dict[str, dict[str, bool]], list[str]]:
    """Labels found and structural problems (missing covers, hierarchical refs, too few)."""
    found: dict[str, dict[str, bool]] = {}
    for kind, name, _ in _LABEL.findall(text):
        found.setdefault(name, {"ap": False, "cp": False, "am": False})[kind] = True
    problems = []
    props = [n for n, k in found.items() if k["ap"]]
    for n in props:
        if not found[n]["cp"]:
            problems.append(f"property ap_{n} has no cover cp_{n} (vacuity check impossible)")
    if len(props) < 3:
        problems.append(f"only {len(props)} labelled assertion(s); at least 3 meaningful properties are required")
    code = re.sub(r"//[^\n]*|/\*.*?\*/", " ", text, flags=re.S)
    if _HIER.search(code):
        problems.append("properties reference DUT internals (dut.<signal>); only port-level properties are allowed")
    if not re.search(r"\bmodule\s+formal_top\b", code):
        problems.append("no module formal_top")
    return found, problems


def _sby(name: str, mode: str, depth: int, rtl: list[Path], props: Path) -> str:
    files = [*rtl, props]
    return (f"[options]\nmode {mode}\ndepth {depth}\n\n[engines]\nsmtbmc yices\n\n[script]\n"
            f"read -formal {' '.join(f.name for f in files)}\nprep -top formal_top\n"
            # vacuity = can each trigger happen under the assumptions; a failing assertion must not hide it
            + ("chformal -assert -remove\n" if mode == "cover" else "")
            + "\n[files]\n" + "\n".join(str(f.resolve()) for f in files) + "\n")


def stub_module(top: str, ports: list[dict]) -> str:
    """The DUT's port list with nothing inside: outputs are left undriven (made free by setundef)."""
    decl = ",\n".join(f"  {'input' if p['dir'] == 'in' else 'output'} wire "
                      f"{'[' + str(int(p['width']) - 1) + ':0] ' if int(p['width']) > 1 else ''}{p['name']}"
                      for p in ports)
    body = "".join(f"  wire {'[' + str(int(p['width']) - 1) + ':0] ' if int(p['width']) > 1 else ''}free_{p['name']};\n"
                   f"  assign {p['name']} = free_{p['name']};\n" for p in ports if p["dir"] == "out")
    return f"module {top} (\n{decl}\n);\n{body}endmodule\n"


class FormalHarnessError(RuntimeError):
    """The harness could not run a check (never read as a property result)."""


def _free_sby(stub: Path, props: Path, depth: int) -> str:
    files = [stub, props]
    return (f"[options]\nmode bmc\ndepth {depth}\n\n[engines]\nsmtbmc --keep-going yices\n\n[script]\n"
            f"read -formal {' '.join(f.name for f in files)}\nprep -top formal_top\nsetundef -undriven -anyseq\n\n[files]\n"
            + "\n".join(str(f.resolve()) for f in files) + "\n")


def _real_failures(log: str) -> set[str]:
    """Assertions with a real counterexample. A k-induction STEP failure ('engine_N.induction:' lines)
    starts from an arbitrary, possibly unreachable state: it means the proof did not close, not that the
    design is wrong, so it is not a failure (the base case and bmc lines are). The end summary repeats
    induction-step failures as 'failed assertion ... in step 0', so only engine lines are read."""
    return set(_FAILED.findall("\n".join(ln for ln in log.splitlines()
                                         if ".induction:" not in ln and "summary:" not in ln)))


def _pdr_sby(name: str, rtl: list[Path], props: Path) -> str:
    """Unbounded proof of ONE property with ABC's PDR (IC3): every other assertion and every cover is
    removed (not assumed), the assumptions stay. PASS is a full proof from the initial state; FAIL is a
    reachable counterexample."""
    files = [*rtl, props]
    return (f"[options]\nmode prove\n\n[engines]\nabc pdr\n\n[script]\n"
            f"read -formal {' '.join(f.name for f in files)}\nprep -top formal_top\n"
            f"chformal -cover -remove\nchformal -assert -remove c:ap_* c:ap_{name} %d\n"
            "\n[files]\n" + "\n".join(str(f.resolve()) for f in files) + "\n")


def run_formal(workdir: Path, rtl: list[Path], props: Path, depth: int, timeout_s: float = 600,
               top: str | None = None, ports: list[dict] | None = None) -> dict:
    fdir = workdir / "formal"
    fdir.mkdir(exist_ok=True)
    found, problems = lint_properties(props.read_text())
    out: dict = {"depth": depth, "lint_problems": problems, "properties": {}, "runs": {}}
    names = [n for n, k in found.items() if k["ap"]]
    results = {}
    for mode in ("prove", "cover"):
        f = fdir / f"props_{mode}.sby"
        f.write_text(_sby(f.stem, mode, depth, rtl, props))
        results[mode] = run_sby_formal(f, workdir, timeout_s)
    prove_log = Path(results["prove"].log_path).read_text() if results["prove"].log_path else ""
    prove_status = (_DONE.findall(prove_log) or ["ERROR"])[-1]
    failed = _real_failures(prove_log)
    bounded_ok = None
    if prove_status not in ("PASS", "FAIL"):  # induction did not close: bounded check instead
        f = fdir / "props_bmc.sby"
        f.write_text(_sby(f.stem, "bmc", depth, rtl, props))
        results["bmc"] = run_sby_formal(f, workdir, timeout_s)
        bmc_log = Path(results["bmc"].log_path).read_text() if results["bmc"].log_path else ""
        failed |= _real_failures(bmc_log)
        bounded_ok = (_DONE.findall(bmc_log) or ["ERROR"])[-1] == "PASS"
    pdr: dict[str, str] = {}
    if prove_status != "PASS":  # the joint induction did not close: prove each property alone with PDR
        for n in names:
            if n in failed:
                continue
            f = fdir / f"pdr_{n}.sby"
            f.write_text(_pdr_sby(n, rtl, props))
            results[f"pdr_{n}"] = r = run_sby_formal(f, workdir, min(timeout_s, 1800))
            log = Path(r.log_path).read_text() if r.log_path else ""
            pdr[n] = (_DONE.findall(log) or ["TIMEOUT" if r.timed_out else "ERROR"])[-1]
            if pdr[n] == "FAIL":
                failed.add(n)
    cover_log = Path(results["cover"].log_path).read_text() if results["cover"].log_path else ""
    reached = set(_REACHED.findall(cover_log))
    depends: set[str] | None = None
    if top and ports:
        stub = fdir / "stub" / f"{top}.v"
        stub.parent.mkdir(exist_ok=True)
        stub.write_text(stub_module(top, ports))
        f = fdir / "props_free.sby"
        f.write_text(_free_sby(stub, props, min(depth, 12)))
        results["free"] = run_sby_formal(f, workdir, timeout_s)
        free_log = Path(results["free"].log_path).read_text() if results["free"].log_path else ""
        free_status = (_DONE.findall(free_log) or ["ERROR"])[-1]
        if free_status not in ("PASS", "FAIL"):
            raise FormalHarnessError(f"free-stub check did not run ({free_status}): " + "; ".join(results["free"].reasons[:2]))
        depends = set(_FAILED.findall(free_log))
    for n in names:
        if n in failed:
            status = "failed"
        elif prove_status == "PASS":
            status = "proven"
        elif pdr.get(n) == "PASS":
            status = "proven"
        elif bounded_ok:
            status = f"bounded (no violation in {depth} steps; induction did not close)"
        else:
            status = "unknown"
        meaningful = True if depends is None else n in depends
        out["properties"][n] = {"status": status, "cover_reached": n in reached,
                                "method": ("k-induction" if prove_status == "PASS" else
                                           "pdr (alone)" if pdr.get(n) == "PASS" else None),
                                "pdr": pdr.get(n), "depends_on_design": meaningful,
                                "counts": status == "proven" and n in reached and meaningful}
    out["runs"] = {m: {"status": r.status, "passed": r.passed, "log": r.log_path, "reasons": r.reasons[:3],
                       "tool_version": r.tool_version, "counterexample_vcd": r.metrics.get("counterexample_vcd")}
                   for m, r in results.items()}
    out["prove_status"] = prove_status
    out["proven_meaningful"] = sum(1 for p in out["properties"].values() if p["counts"])
    out["vacuous"] = [n for n, p in out["properties"].items() if not p["cover_reached"]]
    out["tautologies"] = [n for n, p in out["properties"].items() if not p["depends_on_design"]]
    # a proof the solver cannot finish within the time limit is a property problem (too expensive)
    # (a per-property PDR run that does not finish only leaves that property bounded: reported, not a defect)
    out["timed_out"] = [m for m, r in results.items() if r.timed_out and not m.startswith("pdr_")]
    out["pdr_not_closed"] = sorted(n for n, s in pdr.items() if s != "PASS" and n not in failed)
    out["failed"] = sorted(failed & set(names))
    return out
