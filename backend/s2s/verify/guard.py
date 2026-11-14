"""Anti-cheating guard (MASTER_SPEC Part 8.2 #3; M0.6 acceptance 4).

Diffs each new version of the verification artifacts against the previous accepted version and
flags weakening:
  - cocotb tests: a deleted test; fewer assert statements in a test; a smaller loop/iteration or
    sample count; a new skip / expect_fail / expect_error marker; a new `assert True`/constant
    assert; a new try/except that catches AssertionError (or everything) and does not re-raise;
    a new early `return` before the test's asserts... (counted as fewer reachable asserts is not
    tracked; the static counts above are).
  - testplan.yaml: a deleted test, requirement trace or coverage bin; a changed bin expression is
    reported (it may be a legitimate fix, so Sentinel reviews it).
  - formal properties: fewer assert statements, more assume statements.
  - coverage targets: any lowered value.
Static and deterministic (Python `ast`, YAML): the same diff always gives the same flags.
Any flag requires Sentinel review before the change is accepted (and, after G2, a human).
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

import yaml

_MARKERS = ("skip", "expect_fail", "expect_error")


@dataclass
class TestInfo:
    asserts: int = 0
    loop_bounds: list[int] = field(default_factory=list)
    markers: list[str] = field(default_factory=list)
    const_asserts: int = 0
    swallow: int = 0


def _is_cocotb_test(fn: ast.AST) -> tuple[bool, list[str]]:
    for d in getattr(fn, "decorator_list", []):
        target = d.func if isinstance(d, ast.Call) else d
        name = ast.unparse(target)
        if name in ("cocotb.test", "test"):
            markers = []
            if isinstance(d, ast.Call):
                for kw in d.keywords:
                    if kw.arg in _MARKERS and not (isinstance(kw.value, ast.Constant) and kw.value.value in (False, None)):
                        markers.append(kw.arg)
            return True, markers
    return False, []


def _ints(n: ast.AST) -> list[int]:
    return [c.value for c in ast.walk(n) if isinstance(c, ast.Constant) and type(c.value) is int]


def analyze_tests(source: str) -> dict[str, TestInfo]:
    """Per cocotb test: assertion count, loop bounds, markers, constant asserts, swallowed errors.
    Helper functions called by a test count toward it (one level, by name)."""
    tree = ast.parse(source)
    funcs = {n.name: n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}

    def body_info(fn: ast.AST, seen: set[str]) -> TestInfo:
        info = TestInfo()
        for n in ast.walk(fn):
            if isinstance(n, ast.Assert):
                info.asserts += 1
                if isinstance(n.test, ast.Constant) and n.test.value:
                    info.const_asserts += 1
            elif isinstance(n, ast.Raise) and n.exc is not None and "TestFailure" in ast.unparse(n.exc):
                info.asserts += 1
            elif isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and ast.unparse(n.iter.func) == "range":
                info.loop_bounds.extend(_ints(n.iter))
            elif isinstance(n, ast.Try):
                for h in n.handlers:
                    caught = ast.unparse(h.type) if h.type is not None else "BaseException"
                    if re.search(r"AssertionError|Exception|BaseException|TestFailure", caught) and \
                            not any(isinstance(x, ast.Raise) for x in ast.walk(h)):
                        info.swallow += 1
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in funcs \
                    and n.func.id not in seen and funcs[n.func.id] is not fn:
                sub = body_info(funcs[n.func.id], seen | {n.func.id})
                info.asserts += sub.asserts
                info.loop_bounds += sub.loop_bounds
                info.const_asserts += sub.const_asserts
                info.swallow += sub.swallow
            elif isinstance(n, ast.Await) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Name) \
                    and n.value.func.id in funcs and n.value.func.id not in seen and funcs[n.value.func.id] is not fn:
                pass  # counted by the Call branch above (ast.walk visits the inner Call too)
        return info

    out: dict[str, TestInfo] = {}
    for name, fn in funcs.items():
        is_test, markers = _is_cocotb_test(fn)
        if is_test:
            info = body_info(fn, {name})
            info.markers = markers
            out[name] = info
    return out


def diff_tests(old: str, new: str, path: str) -> list[str]:
    try:
        a = analyze_tests(old)
    except SyntaxError:
        return []
    try:
        b = analyze_tests(new)
    except SyntaxError as e:
        return [f"{path}: new version does not parse ({e.msg})"]
    flags = []
    for name, ia in a.items():
        ib = b.get(name)
        if ib is None:
            flags.append(f"{path}: test '{name}' was deleted")
            continue
        if ib.asserts < ia.asserts:
            flags.append(f"{path}: test '{name}' has fewer assertions ({ia.asserts} -> {ib.asserts})")
        if sum(ib.loop_bounds) < sum(ia.loop_bounds):
            flags.append(f"{path}: test '{name}' runs fewer iterations (loop bounds {ia.loop_bounds} -> {ib.loop_bounds})")
        for m in set(ib.markers) - set(ia.markers):
            flags.append(f"{path}: test '{name}' gained a '{m}' marker")
        if ib.const_asserts > ia.const_asserts:
            flags.append(f"{path}: test '{name}' gained an always-true assert")
        if ib.swallow > ia.swallow:
            flags.append(f"{path}: test '{name}' now catches assertion errors without re-raising")
    return flags


def diff_testplan(old: str, new: str) -> list[str]:
    a, b = yaml.safe_load(old) or {}, yaml.safe_load(new) or {}
    flags = []
    tests_a = {t["name"]: t for r in a.get("requirements", []) for t in r.get("tests", [])}
    tests_b = {t["name"]: t for r in b.get("requirements", []) for t in r.get("tests", [])}
    for n in set(tests_a) - set(tests_b):
        flags.append(f"testplan: test '{n}' was removed")
    req_a = {r["id"] for r in a.get("requirements", []) if r.get("tests")}
    req_b = {r["id"] for r in b.get("requirements", []) if r.get("tests")}
    for r in req_a - req_b:
        flags.append(f"testplan: requirement {r} lost its tests")
    bins_a = {x["name"]: x for x in a.get("coverage_bins", [])}
    bins_b = {x["name"]: x for x in b.get("coverage_bins", [])}
    for n in set(bins_a) - set(bins_b):
        flags.append(f"testplan: coverage bin '{n}' was removed")
    for n in set(bins_a) & set(bins_b):
        if bins_a[n]["expr"] != bins_b[n]["expr"]:
            flags.append(f"testplan: coverage bin '{n}' changed ({bins_a[n]['expr']!r} -> {bins_b[n]['expr']!r})")
    return flags


_SV_ASSERT = re.compile(r"\bassert\s*(?:property\s*)?\(")
_SV_ASSUME = re.compile(r"\bassume\s*(?:property\s*)?\(")


def diff_properties(old: str, new: str, path: str) -> list[str]:
    strip = lambda t: re.sub(r"//[^\n]*|/\*.*?\*/", " ", t, flags=re.S)  # noqa: E731
    a, b = strip(old), strip(new)
    flags = []
    if len(_SV_ASSERT.findall(b)) < len(_SV_ASSERT.findall(a)):
        flags.append(f"{path}: fewer assertions ({len(_SV_ASSERT.findall(a))} -> {len(_SV_ASSERT.findall(b))})")
    if len(_SV_ASSUME.findall(b)) > len(_SV_ASSUME.findall(a)):
        flags.append(f"{path}: more assumptions ({len(_SV_ASSUME.findall(a))} -> {len(_SV_ASSUME.findall(b))}); "
                     "over-constraining hides bugs")
    return flags


def diff_targets(old: dict, new: dict) -> list[str]:
    return [f"coverage target '{k}' lowered ({old[k]} -> {new.get(k)})" for k in old
            if new.get(k) is None or new[k] < old[k]]


def diff_files(old: dict[str, str], new: dict[str, str]) -> list[str]:
    """Flags for a whole verification file set (path -> text). Deleted files are flagged."""
    flags = []
    for path, text in old.items():
        if path not in new:
            flags.append(f"{path}: file was deleted")
            continue
        if path.endswith(".py") and "/test_" in "/" + path:
            flags += diff_tests(text, new[path], path)
        elif path.endswith("testplan.yaml"):
            flags += diff_testplan(text, new[path])
        elif path.endswith(".sv") and "formal" in path:
            flags += diff_properties(text, new[path], path)
    return flags
