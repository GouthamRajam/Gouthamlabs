"""Deterministic checks on spec.yaml, arch.yaml and the RTL file set (M0.5 acceptance 1 and 2).

Each check returns a list of problems (empty = passed). They are plain code, so the same input
always gives the same verdict; the model never decides pass/fail. The RTL tool checks (Verilator
lint, Yosys elaboration) live in s2s.tools; this module adds the structural RTL checks that tie
the RTL back to arch.yaml (one module per file, ports match, requirement trace comments).
"""
from __future__ import annotations

import ast
import re
from typing import Any

import jsonschema

from s2s.design.schemas import ARCH_SCHEMA, SPEC_SCHEMA, TASK_RESULT_SCHEMA

PHASE0_PDK, PHASE0_LIB = "sky130A", "sky130_fd_sc_hd"
MIN_SLACK_MARGIN_PCT = 15  # Kepler: "target at least 15% slack in your estimate"


def schema_problems(doc: Any, schema: dict, name: str) -> list[str]:
    v = jsonschema.Draft202012Validator(schema)
    return [f"{name}: {'/'.join(map(str, e.absolute_path)) or '(top)'}: {e.message}"
            for e in sorted(v.iter_errors(doc), key=lambda e: list(map(str, e.absolute_path)))]


def spec_schema(spec: Any) -> list[str]:
    return schema_problems(spec, SPEC_SCHEMA, "spec.yaml")


def arch_schema(arch: Any) -> list[str]:
    return schema_problems(arch, ARCH_SCHEMA, "arch.yaml")


def task_result_schema(result: Any) -> list[str]:
    return schema_problems(result, TASK_RESULT_SCHEMA, "task.result")


def _dupes(names: list[str]) -> list[str]:
    seen, out = set(), []
    for n in names:
        if n in seen and n not in out:
            out.append(n)
        seen.add(n)
    return out


def spec_consistency(spec: dict) -> list[str]:
    """Cross-field rules a valid spec must satisfy (Iris's quality bar, made mechanical)."""
    p: list[str] = []
    ifaces = {i["name"]: i for i in spec["interfaces"]}
    for d in _dupes([i["name"] for i in spec["interfaces"]]):
        p.append(f"interface '{d}' is listed more than once")
    for d in _dupes([r["id"] for r in spec["requirements"]]):
        p.append(f"requirement id {d} is used more than once")
    if spec["pdk"] != PHASE0_PDK or spec["std_cell_library"] != PHASE0_LIB:
        p.append(f"Phase 0 uses {PHASE0_PDK}/{PHASE0_LIB}, spec says {spec['pdk']}/{spec['std_cell_library']}")
    for c in spec["clocks"]:
        i = ifaces.get(c["name"])
        if not i or i["dir"] != "in" or i["width"] != 1:
            p.append(f"clock '{c['name']}' is not a 1-bit input in interfaces")
    if spec["clocks"] and abs(spec["clocks"][0]["freq_mhz"] - spec["target_clock_mhz"]) > 1e-9:
        p.append(f"target_clock_mhz {spec['target_clock_mhz']} != primary clock "
                 f"{spec['clocks'][0]['name']} at {spec['clocks'][0]['freq_mhz']} MHz")
    for r in spec["resets"]:
        i = ifaces.get(r["name"])
        if not i or i["dir"] != "in" or i["width"] != 1:
            p.append(f"reset '{r['name']}' is not a 1-bit input in interfaces")
        if r["active"] == "low" and not r["name"].endswith("_n"):
            p.append(f"active-low reset '{r['name']}' must end in _n (coding standard)")
    # Reset behavior must be specified for every output (Iris: "behavior after reset for every output").
    reset_reqs = [r for r in spec["requirements"] if r["type"] == "reset"]
    if spec["resets"] and not reset_reqs:
        p.append("no requirement of type 'reset': behavior after reset is unspecified")
    reset_text = " ".join(r["text"] + " " + r["acceptance"] for r in reset_reqs)
    for i in spec["interfaces"]:
        if i["dir"] == "out" and "reset_value" not in i and not re.search(rf"\b{re.escape(i['name'])}\b", reset_text):
            p.append(f"output '{i['name']}' has no reset_value and no reset requirement names it")
    for i in spec["interfaces"]:
        if i.get("async") and i["dir"] != "in":
            p.append(f"'{i['name']}' is marked async but is not an input")
    return p


def _width(w: Any, params: dict[str, int]) -> int | None:
    """A port width: an integer, or +, -, * of integers and module params (e.g. "DIV_W", "W+1").
    Parsed with a whitelist (model-written text is never executed)."""
    if isinstance(w, int):
        return w
    ops = {ast.Add: lambda a, b: a + b, ast.Sub: lambda a, b: a - b, ast.Mult: lambda a, b: a * b}

    def ev(n: ast.AST) -> int:
        if isinstance(n, ast.Constant) and type(n.value) is int:
            return n.value
        if isinstance(n, ast.Name) and n.id in params:
            return int(params[n.id])
        if isinstance(n, ast.BinOp) and type(n.op) in ops:
            return ops[type(n.op)](ev(n.left), ev(n.right))
        raise ValueError(n)
    try:
        return ev(ast.parse(str(w), mode="eval").body)
    except (SyntaxError, ValueError, RecursionError):
        return None


def module_ports(arch: dict, spec: dict, name: str) -> dict[str, tuple[str, int | None]]:
    m = next(x for x in arch["modules"] if x["name"] == name)
    if m.get("ports_from_spec"):
        return {i["name"]: (i["dir"], i["width"]) for i in spec["interfaces"]}
    params = m.get("params") or {}
    return {pt["name"]: (pt["dir"], _width(pt["width"], params)) for pt in m.get("ports") or []}


def arch_consistency(arch: dict, spec: dict) -> list[str]:
    """arch.yaml against itself and against spec.yaml (Kepler's quality bar, made mechanical)."""
    p: list[str] = []
    mods = {m["name"]: m for m in arch["modules"]}
    for d in _dupes([m["name"] for m in arch["modules"]]):
        p.append(f"module '{d}' is defined more than once")
    if arch["design"] != spec["design"]:
        p.append(f"arch design '{arch['design']}' != spec design '{spec['design']}'")
    if arch["top"] not in mods:
        return p + [f"top module '{arch['top']}' is not defined in modules"]
    for m in arch["modules"]:
        if not m.get("ports_from_spec") and not m.get("ports"):
            p.append(f"module '{m['name']}' has no ports")
        for pt in m.get("ports") or []:
            if _width(pt["width"], m.get("params") or {}) is None:
                p.append(f"{m['name']}.{pt['name']}: width '{pt['width']}' does not resolve from params")
        for inst in m.get("instances") or []:
            if inst not in mods:
                p.append(f"module '{m['name']}' instantiates undefined module '{inst}'")
    # every spec I/O present at the top, same direction and width; nothing extra at the top
    top = module_ports(arch, spec, arch["top"])
    for i in spec["interfaces"]:
        if i["name"] not in top:
            p.append(f"spec interface '{i['name']}' is missing from top '{arch['top']}'")
        elif top[i["name"]] != (i["dir"], i["width"]):
            p.append(f"top port '{i['name']}' is {top[i['name']]}, spec says ({i['dir']}, {i['width']})")
    for name in set(top) - {i["name"] for i in spec["interfaces"]}:
        p.append(f"top port '{name}' is not in the spec's interfaces")
    # every non-top module is used; the hierarchy has no cycle
    used = {i for m in arch["modules"] for i in m.get("instances") or []}
    for m in arch["modules"]:
        if m["name"] != arch["top"] and m["name"] not in used:
            p.append(f"module '{m['name']}' is never instantiated")
    # requirement coverage: every requirement maps to a module, every mapping is a real requirement
    req_ids = {r["id"] for r in spec["requirements"]}
    implemented = {r for m in arch["modules"] for r in m["implements"]}
    for r in sorted(req_ids - implemented):
        p.append(f"{r} is not implemented by any module")
    for r in sorted(implemented - req_ids):
        p.append(f"modules implement {r}, which is not in the spec")
    # connections: endpoints exist and widths match
    for c in arch["connections"]:
        ends = [c["from"], *c["to"]]
        widths = []
        for e in ends:
            mod, _, port = e.partition(".")
            if mod not in mods or not port:
                p.append(f"connection endpoint '{e}' is not <module>.<port> of a defined module")
                continue
            ports = module_ports(arch, spec, mod)
            if port not in ports:
                p.append(f"connection endpoint '{e}': module '{mod}' has no port '{port}'")
                continue
            widths.append(ports[port][1])
        if len(set(widths)) > 1:
            p.append(f"connection {c['from']} -> {c['to']}: port widths differ {widths}")
    # CDC: every asynchronous spec input has a synchronizer
    for i in spec["interfaces"]:
        if i.get("async") and not any(x["signal"] == i["name"] for x in arch["cdc"]):
            p.append(f"asynchronous input '{i['name']}' has no cdc entry / synchronizer")
    for sm in arch["state_machines"]:
        if sm["module"] not in mods:
            p.append(f"state machine for undefined module '{sm['module']}'")
    if arch["ppa_estimate"]["slack_margin_pct"] < MIN_SLACK_MARGIN_PCT:
        p.append(f"estimated slack margin {arch['ppa_estimate']['slack_margin_pct']}% is below "
                 f"{MIN_SLACK_MARGIN_PCT}%")
    return p


_MODULE_DECL = re.compile(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_]*)", re.M)


def rtl_structure(files: dict[str, str], arch: dict) -> list[str]:
    """Coding standard (Appendix D 2, 10, 11) and arch coverage, from the RTL text."""
    p: list[str] = []
    by_module: dict[str, str] = {}
    for path, text in files.items():
        declared = _MODULE_DECL.findall(_strip_comments(text))
        stem = path.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        if len(declared) != 1:
            p.append(f"{path}: {len(declared)} module declarations (one module per file)")
        elif declared[0] != stem:
            p.append(f"{path}: declares module '{declared[0]}' (file name must equal module name)")
        for d in declared:
            by_module[d] = text
        code = _strip_comments(text)
        for bad, why in ((r"\binitial\b", "initial block"), (r"#\s*\d", "# delay"),
                         (r"\$(display|write|monitor|finish|stop)\b", "system task")):
            if re.search(bad, code):
                p.append(f"{path}: {why} in synthesizable code (coding standard 10)")
    for m in arch["modules"]:
        if m["name"] not in by_module:
            p.append(f"arch module '{m['name']}' has no RTL file rtl/{m['name']}.v")
            continue
        for r in m["implements"]:
            if r not in by_module[m["name"]]:
                p.append(f"rtl/{m['name']}.v: no '// {r}' trace comment (coding standard 11)")
    for extra in set(by_module) - {m["name"] for m in arch["modules"]}:
        p.append(f"RTL module '{extra}' is not in arch.yaml")
    return p


def _strip_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    return re.sub(r"//[^\n]*", " ", text)


def rtl_ports(yosys_json: dict, arch: dict, spec: dict) -> list[str]:
    """Ports of the elaborated top (from `yosys write_json`) against arch.yaml."""
    p: list[str] = []
    mod = yosys_json.get("modules", {}).get(arch["top"])
    if mod is None:
        return [f"top module '{arch['top']}' not found in the elaborated design"]
    got = {n: ({"input": "in", "output": "out", "inout": "inout"}[x["direction"]], len(x["bits"]))
           for n, x in mod["ports"].items()}
    want = module_ports(arch, spec, arch["top"])
    for n, w in want.items():
        if n not in got:
            p.append(f"top port '{n}' from arch.yaml is missing in the RTL")
        elif got[n] != w:
            p.append(f"top port '{n}' is {got[n]} in the RTL, arch.yaml says {w}")
    for n in set(got) - set(want):
        p.append(f"RTL top port '{n}' is not in arch.yaml")
    return p
