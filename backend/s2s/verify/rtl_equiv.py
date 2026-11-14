"""Sequential equivalence of two RTL versions at the top-level ports, from reset (an RTL design change that must not
change behaviour, e.g. a timing fix; CEO decision 2026-10-07).

Both versions go into one miter: the old modules are renamed with a prefix, the same input stream drives both, reset
is held for the first cycle, and every top-level output must be equal on every later cycle. SymbiYosys BMC checks it to
a stated depth (bounded: equal for every input sequence of that many cycles from reset). Pass/fail is the tool's.
"""
from __future__ import annotations

import re
from pathlib import Path

from s2s.tools.sby_formal import run_sby_formal

PREFIX = "s2s_old_"
ENGINE = "abc bmc3"  # bit-level BMC; much faster than smtbmc on wide flop arrays (two 16x32 FIFOs)
_DONE = re.compile(r"DONE \((PASS|FAIL|ERROR|UNKNOWN|TIMEOUT)")


def rename_modules(text: str, names: list[str], prefix: str = PREFIX) -> str:
    """Prefix every module definition and instantiation of `names` (word-boundary match on the module names)."""
    for n in sorted(names, key=len, reverse=True):
        text = re.sub(rf"\b{re.escape(n)}\b", prefix + n, text)
    return text


def miter(top: str, ports: list[dict], reset: dict | None) -> str:
    """ports: [{name, dir: in|out, width}] of the top (spec interfaces). reset: {name, active: low|high}."""
    def decl(p: dict) -> str:
        w = int(p.get("width", 1))
        return f"[{w - 1}:0] " if w > 1 else ""
    ins = [p for p in ports if p["dir"] == "in"]
    outs = [p for p in ports if p["dir"] == "out"]
    lines = [f"module s2s_equiv_miter({', '.join('input ' + decl(p) + p['name'] for p in ins)});"]
    for p in outs:
        lines.append(f"  wire {decl(p)}o_{p['name']}, n_{p['name']};")
    conn_o = ", ".join([f".{p['name']}({p['name']})" for p in ins] + [f".{p['name']}(o_{p['name']})" for p in outs])
    conn_n = ", ".join([f".{p['name']}({p['name']})" for p in ins] + [f".{p['name']}(n_{p['name']})" for p in outs])
    lines += [f"  {PREFIX}{top} u_old ({conn_o});", f"  {top} u_new ({conn_n});",
              "  reg s2s_init = 1'b1;", "  always @(posedge clk) s2s_init <= 1'b0;"]
    if reset:
        lvl = "1'b0" if reset.get("active", "low") == "low" else "1'b1"
        lines.append(f"  always @(*) if (s2s_init) assume({reset['name']} == {lvl});")
    lines.append("  always @(*) if (!s2s_init) begin")
    lines += [f"    eq_{p['name']}: assert (o_{p['name']} == n_{p['name']});" for p in outs]
    lines += ["  end", "endmodule", ""]
    return "\n".join(lines)


def check(workdir: Path, old: dict[str, str], new_files: list[Path], top: str, module_names: list[str],
          ports: list[dict], reset: dict | None, depth: int, timeout_s: float = 3600) -> dict:
    """old: {file name: text} of the previous RTL. Returns {status, passed, depth, log, failed_assertions}."""
    d = (workdir / "change" / "equiv").resolve()
    (d / "old").mkdir(parents=True, exist_ok=True)
    old_paths = []
    for name, text in sorted(old.items()):
        p = d / "old" / (PREFIX + name)  # sby copies [files] into one folder: names must differ
        p.write_text(rename_modules(text, module_names))
        old_paths.append(p)
    (d / "miter.sv").write_text(miter(top, ports, reset))
    files = [*old_paths, *[Path(f).resolve() for f in new_files], d / "miter.sv"]
    sby = d / "rtl_equiv.sby"
    sby.write_text("\n".join([
        "[options]", "mode bmc", f"depth {depth}", "", "[engines]", ENGINE, "", "[script]",
        *[f"read_verilog -sv {f.name}" for f in files[:-1]], "read_verilog -formal miter.sv",
        "prep -top s2s_equiv_miter", "", "[files]", *[str(f) for f in files], ""]))
    r = run_sby_formal(sby, workdir, timeout_s)
    log = Path(r.log_path).read_text(errors="replace") if r.log_path else ""
    status = (_DONE.findall(log) or ["ERROR"])[-1]
    failed = sorted(set(re.findall(r"\b(eq_\w+)\b", "\n".join(ln for ln in log.splitlines() if "failed" in ln.lower()))))
    return {"status": status, "passed": status == "PASS", "depth": depth, "log": str(r.log_path),
            "failed_assertions": failed, "tail": "\n".join(log.splitlines()[-25:]),
            "tool_version": r.tool_version, "method": f"SymbiYosys BMC ({ENGINE}), depth {depth}, from reset"}
