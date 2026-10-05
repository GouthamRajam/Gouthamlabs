"""OpenLane 2, driven step by step (M0.7). One run directory per design attempt (`pnr/runs/<tag>`);
each stage is one `openlane --from <first step> --to <last step>` invocation that resumes from the
previous stage's saved state, so the agents read every stage's reports before the next one runs.

Stages (Classic flow step ids, OpenLane 2.3.10):
  synthesis   Verilator.Lint .. OpenROAD.STAPrePNR
  floorplan   OpenROAD.Floorplan .. Odb.ApplyDEFTemplate          (die/core, tap cells, PDN, pins)
  placement   OpenROAD.GlobalPlacement .. OpenROAD.DetailedPlacement
  cts         OpenROAD.CTS .. OpenROAD.STAMidPNR-2
  routing     OpenROAD.GlobalRouting .. OpenROAD.STAPostPNR       (incl. antenna repair, fill, RCX, STA)
  signoff     OpenROAD.IRDropReport .. end                        (stream-out, DRC, LVS, checkers)

The config guard: the agents may set only the keys below, only within config/pnr_ranges.yaml, and
the SDC must be the Sentinel-reviewed constraints file (by hash). No rule deck, checker or quit
switch can be changed from here (anything else in config.json fails the guard).
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
from pathlib import Path

from s2s.config import _load
from s2s.tools import runner
from s2s.tools.openlane_flow import _records, _steps

PDK_ROOT = "/opt/pdk"
STAGES = {
    "synthesis": ("Verilator.Lint", "OpenROAD.STAPrePNR"),
    "floorplan": ("OpenROAD.Floorplan", "Odb.ApplyDEFTemplate"),
    "placement": ("OpenROAD.GlobalPlacement", "OpenROAD.DetailedPlacement"),
    "cts": ("OpenROAD.CTS", "OpenROAD.STAMidPNR-2"),
    "routing": ("OpenROAD.GlobalRouting", "OpenROAD.STAPostPNR"),
    "signoff": ("OpenROAD.IRDropReport", None),
}
ORDER = list(STAGES)
# config.json keys and who may change them; ranges from config/pnr_ranges.yaml
FIXED_KEYS = {"DESIGN_NAME", "VERILOG_FILES", "CLOCK_PORT", "CLOCK_PERIOD", "PNR_SDC_FILE", "SIGNOFF_SDC_FILE",
              "ERRORS_ON_UNMATCHED_IO", "FP_PIN_ORDER_CFG"}
TUNABLE = {  # config key -> (pnr_ranges key, scale from range units to config units, first stage it affects)
    "FP_CORE_UTIL": ("core_utilization_pct", 1, "floorplan"),
    "PL_TARGET_DENSITY_PCT": ("placement_density", 100, "placement"),
    "MAX_FANOUT_CONSTRAINT": ("max_fanout", 1, "synthesis"),
    "CTS_SINK_CLUSTERING_SIZE": ("cts_cluster_size", 1, "cts"),
    "GRT_ANTENNA_ITERS": ("antenna_repair_iters", 1, "routing"),
    "GRT_ANTENNA_MARGIN": ("antenna_repair_margin_pct", 1, "routing"),
}
INT_PARAMS = {"MAX_FANOUT_CONSTRAINT", "CTS_SINK_CLUSTERING_SIZE", "GRT_ANTENNA_ITERS", "GRT_ANTENNA_MARGIN"}
SYNTH_STRATEGIES = ["AREA 0", "AREA 1", "AREA 2", "AREA 3", "DELAY 0", "DELAY 1", "DELAY 2", "DELAY 3", "DELAY 4"]


def ranges() -> dict:
    return _load("pnr_ranges.yaml", "S2S_PNR_RANGES")


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def default_params() -> dict:
    r = ranges()
    return {k: round(r[rk]["default"] * scale, 6) for k, (rk, scale, _) in TUNABLE.items()}


def check_params(params: dict) -> list[str]:
    """Every tunable must be inside its pnr_ranges.yaml range."""
    r, problems = ranges(), []
    for key, value in params.items():
        if key == "SYNTH_STRATEGY":
            if value not in SYNTH_STRATEGIES:
                problems.append(f"SYNTH_STRATEGY {value!r} is not one of {SYNTH_STRATEGIES}")
            continue
        if key not in TUNABLE:
            problems.append(f"{key} is not a tunable parameter (allowed: {sorted(TUNABLE)} + SYNTH_STRATEGY)")
            continue
        rk, scale, _ = TUNABLE[key]
        lo, hi = r[rk]["min"] * scale, r[rk]["max"] * scale
        if not isinstance(value, (int, float)) or not lo - 1e-9 <= value <= hi + 1e-9:
            problems.append(f"{key} = {value} is outside config/pnr_ranges.yaml {rk} [{lo:g}, {hi:g}]")
        elif key in INT_PARAMS and float(value) != int(value):
            problems.append(f"{key} = {value} must be a whole number")
    return problems


def write_config(pnr: Path, design: str, rtl: list[Path], clock_port: str, period_ns: float, sdc: Path,
                 params: dict, pin_cfg: Path | None) -> Path:
    """Copy the frozen RTL, the reviewed SDC and the pin file into pnr/src (OpenLane reads only these
    copies, so the guard can hash exactly what the flow used) and write pnr/config.json."""
    src = pnr / "src"
    shutil.rmtree(src, ignore_errors=True)
    src.mkdir(parents=True)
    for f in rtl:
        shutil.copy2(f, src / Path(f).name)
    shutil.copy2(sdc, src / "constraints.sdc")
    cfg = {"DESIGN_NAME": design, "VERILOG_FILES": [f"dir::src/{Path(f).name}" for f in rtl],
           "CLOCK_PORT": clock_port, "CLOCK_PERIOD": period_ns, "PNR_SDC_FILE": "dir::src/constraints.sdc",
           "SIGNOFF_SDC_FILE": "dir::src/constraints.sdc", "ERRORS_ON_UNMATCHED_IO": "both",
           **{k: int(v) if k in INT_PARAMS else v for k, v in params.items()}}
    if pin_cfg:
        shutil.copy2(pin_cfg, src / "pin_order.cfg")
        cfg["FP_PIN_ORDER_CFG"] = "dir::src/pin_order.cfg"
    path = pnr / "config.json"
    path.write_text(json.dumps(cfg, indent=2) + "\n")
    return path


def config_guard(pnr: Path, *, period_ns: float, reviewed_sdc_sha: str, frozen_rtl: dict[str, str]) -> list[str]:
    """Proof's anti-loosening check on what OpenLane actually read: allowed keys only, tunables inside
    pnr_ranges.yaml, the spec clock period, the Sentinel-reviewed SDC and the G2-frozen RTL (hashes)."""
    config = json.loads((pnr / "config.json").read_text())
    problems = []
    extra = sorted(set(config) - FIXED_KEYS - set(TUNABLE) - {"SYNTH_STRATEGY"})
    if extra:
        problems.append(f"config.json sets keys outside the allowed set: {extra} (no checker, deck or quit "
                        "switch may be changed)")
    problems += check_params({k: v for k, v in config.items() if k in TUNABLE or k == "SYNTH_STRATEGY"})
    if abs(float(config.get("CLOCK_PERIOD", -1)) - period_ns) > 1e-9:
        problems.append(f"CLOCK_PERIOD {config.get('CLOCK_PERIOD')} != spec period {period_ns} ns")
    for key in ("PNR_SDC_FILE", "SIGNOFF_SDC_FILE"):
        if config.get(key) != "dir::src/constraints.sdc":
            problems.append(f"{key} is not the reviewed constraints file")
    sdc = pnr / "src" / "constraints.sdc"
    if not sdc.exists() or sha(sdc) != reviewed_sdc_sha:
        problems.append("the constraints file used by the flow is not the one Sentinel reviewed (hash differs)")
    used = {Path(v.replace("dir::", "")).name for v in config.get("VERILOG_FILES", [])}
    if used != set(frozen_rtl):
        problems.append(f"VERILOG_FILES {sorted(used)} != the G2-frozen RTL files {sorted(frozen_rtl)}")
    for name, h in frozen_rtl.items():
        f = pnr / "src" / name
        if not f.exists() or sha(f) != h:
            problems.append(f"src/{name} differs from the G2-frozen RTL (hash)")
    if config.get("ERRORS_ON_UNMATCHED_IO") != "both":
        problems.append("ERRORS_ON_UNMATCHED_IO must stay 'both'")
    return problems


def _step_dirs(run_dir: Path) -> list[Path]:
    return sorted((d for d in run_dir.iterdir() if d.is_dir() and re.match(r"^\d+-", d.name)),
                  key=lambda d: int(d.name.split("-", 1)[0]))


def step_dir(run_dir: Path, step_id: str) -> Path | None:
    """The (last) directory of a step id, e.g. 'OpenROAD.STAPostPNR' -> 54-openroad-stapostpnr."""
    slug = step_id.lower().replace(".", "-")
    hits = [d for d in _step_dirs(run_dir) if d.name.split("-", 1)[1] == slug]
    return hits[-1] if hits else None


def fork(pnr: Path, src_tag: str, dst_tag: str, before_stage: str) -> None:
    """New run tag holding the source run's steps up to (not including) `before_stage`, so the next
    invocation resumes from there with the new parameters."""
    src, dst = pnr / "runs" / src_tag, pnr / "runs" / dst_tag
    shutil.rmtree(dst, ignore_errors=True)
    dst.mkdir(parents=True)
    first = step_dir(src, STAGES[before_stage][0])
    limit = int(first.name.split("-", 1)[0]) if first else 10 ** 6
    for d in _step_dirs(src):
        if int(d.name.split("-", 1)[0]) < limit:
            shutil.copytree(d, dst / d.name, symlinks=True)
    for f in ("resolved.json",):
        if (src / f).exists():
            shutil.copy2(src / f, dst / f)
    # state files hold absolute paths of the source run: point them at the copy. OpenLane resumes from
    # the most recently MODIFIED state_out.json, so each rewritten file keeps its original timestamps.
    for state in dst.glob("*/state_*.json"):
        st = state.stat()
        state.write_text(state.read_text().replace(str(src) + "/", str(dst) + "/"))
        os.utime(state, ns=(st.st_atime_ns, st.st_mtime_ns))


def run_stage(pnr: Path, tag: str, stage: str, timeout_s: float = 3600, jobs: int = 4) -> dict:
    """One OpenLane invocation for a stage; returns status, step list, errors and the metrics of the
    last state written (the run's cumulative metrics)."""
    frm, to = STAGES[stage]
    run_dir = pnr / "runs" / tag
    first_stage = stage == ORDER[0]
    cmd = ["openlane", "--manual-pdk", "--pdk-root", PDK_ROOT, "--pdk", "sky130A", "--scl", "sky130_fd_sc_hd",
           "--run-tag", tag, "--log-level", "VERBOSE", "-j", str(jobs), "--from", frm]
    if to:
        cmd += ["--to", to]
    if first_stage:
        cmd.append("--overwrite")
    cmd.append("config.json")
    log_path = pnr / "logs" / f"openlane_{tag}_{stage}.log"
    rec = runner.run(cmd, pnr.parent, log_path, "openlane", timeout_s, cwd=pnr, env={"COLUMNS": "200"})
    log = Path(rec.log_path).read_text(errors="replace")
    flow_log = (run_dir / "flow.log").read_text(errors="replace") if (run_dir / "flow.log").exists() else ""
    errors = [msg for lvl, msg in _records(log) if lvl in ("ERROR", "CRITICAL")]
    steps = [s for s in _steps(flow_log)]
    states = [d / "state_out.json" for d in _step_dirs(run_dir) if (d / "state_out.json").exists()] \
        if run_dir.exists() else []
    metrics, views = {}, {}
    if states:
        st = json.loads(states[-1].read_text())
        metrics, views = st.get("metrics", {}), {k: v for k, v in st.items() if k != "metrics"}
    finished = "Flow complete." in log or "Flow complete." in flow_log
    ok = rec.exit_code == 0 and not rec.timed_out and finished and not errors
    return {"stage": stage, "tag": tag, "from": frm, "to": to, "ok": ok, "exit_code": rec.exit_code,
            "timed_out": rec.timed_out, "errors": errors[:20], "steps": [s["step"] for s in steps],
            "failed_steps": [s["step"] for s in steps if s["status"] == "failed"],
            "metrics": metrics, "views": views, "run_dir": str(run_dir), "log": str(log_path),
            "command": runner.command_str(cmd), "duration_s": rec.duration_s, "tool_version": rec.tool_version,
            "env_hash": rec.env_hash, "last_state": str(states[-1]) if states else None}


def corners(metrics: dict, key: str) -> dict[str, float]:
    """Per-corner values of an OpenLane metric, e.g. timing__setup__ws -> {corner: value}."""
    pre = key + "__corner:"
    return {k[len(pre):]: v for k, v in metrics.items() if k.startswith(pre)}


_SKEW = re.compile(r"^(?P<v>-?[\d.]+) (?P<what>source latency|target latency|clock uncertainty|CRPR|setup skew|hold skew)",
                   re.M)


def parse_skew(text: str) -> dict:
    """OpenROAD's report_clock_skew includes the SDC clock uncertainty; the clock tree's own skew is
    the reported skew minus that uncertainty."""
    v = {m["what"]: float(m["v"]) for m in _SKEW.finditer(text)}
    skew = v.get("setup skew", v.get("hold skew"))
    unc = v.get("clock uncertainty", 0.0)
    return {"reported_skew_ns": skew, "clock_uncertainty_ns": unc,
            "tree_skew_ns": None if skew is None else round(abs(skew - unc), 6),
            "source_latency_ns": v.get("source latency"), "target_latency_ns": v.get("target latency")}


def def_pins(def_text: str) -> list[dict]:
    """Pins from a DEF PINS section: name, direction, placed location and side of the die."""
    die = re.search(r"DIEAREA \( (-?\d+) (-?\d+) \) \( (-?\d+) (-?\d+) \)", def_text)
    x1, y1, x2, y2 = (int(g) for g in die.groups()) if die else (0, 0, 0, 0)
    out = []
    block = def_text.split("\nPINS", 1)[-1].split("END PINS", 1)[0] if "\nPINS" in def_text else ""
    for m in re.finditer(r"-\s+(\S+)\s+\+\s+NET\s+\S+(.*?)(?=\n\s*-\s|\Z)", block, re.S):
        name, body = m.group(1), m.group(2)
        d = re.search(r"\+ DIRECTION (\w+)", body)
        p = re.search(r"\+ (?:PLACED|FIXED) \( (-?\d+) (-?\d+) \)", body)
        side = None
        if p:
            x, y = int(p.group(1)), int(p.group(2))
            side = min((("W", abs(x - x1)), ("E", abs(x2 - x)), ("S", abs(y - y1)), ("N", abs(y2 - y))),
                       key=lambda t: t[1])[0]
        if " + USE POWER" in body or " + USE GROUND" in body:
            continue
        out.append({"name": name, "direction": d.group(1) if d else None, "side": side})
    return out


# --- Sienna's constraints: deterministic SDC guard ------------------------------------------------
_EXCEPTIONS = ("set_false_path", "set_multicycle_path", "set_disable_timing", "set_case_analysis",
               "set_max_delay", "set_min_delay", "set_clock_groups")
_NUM = r"(-?\d+(?:\.\d+)?)"


def _sdc_lines(text: str) -> list[tuple[str, str]]:
    """(command line, the comment block directly above it)."""
    out, comment = [], []
    joined = re.sub(r"\\\n", " ", text)
    for raw in joined.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            comment.append(line)
        elif line:
            out.append((line, " ".join(comment)))
            comment = []
        else:
            comment = []
    return out


def sdc_problems(text: str, *, clocks: list[dict], inputs: list[str], outputs: list[str]) -> tuple[list[str], dict]:
    """The constraints must state the spec clock exactly, an uncertainty and max fanout inside
    pnr_ranges.yaml, an I/O delay for every non-clock port, and no timing exception without a
    written `# JUSTIFICATION:` (never to hide timing, A.8)."""
    r = ranges()
    problems: list[str] = []
    lines = _sdc_lines(text)
    found = {"clocks": {}, "uncertainty": None, "max_fanout": None, "input_delay": {}, "output_delay": {},
             "exceptions": []}
    for line, comment in lines:
        cmd = line.split()[0]
        if cmd == "create_clock":
            p = re.search(r"-period\s+" + _NUM, line)
            port = re.search(r"get_ports\s+\{?\s*(\w+)", line)
            if p and port:
                found["clocks"][port.group(1)] = float(p.group(1))
        elif cmd == "set_clock_uncertainty":
            m = re.search(r"set_clock_uncertainty\s+(?:-\w+\s+)*" + _NUM, line)
            if m:
                found["uncertainty"] = float(m.group(1))
        elif cmd == "set_max_fanout":
            m = re.search(r"set_max_fanout\s+" + _NUM, line)
            if m:
                found["max_fanout"] = float(m.group(1))
        elif cmd in ("set_input_delay", "set_output_delay"):
            m = re.search(r"\s" + _NUM + r"\s", line + " ")
            ports = re.findall(r"get_ports\s+(\{[^}]*\}|[^\s\]]+)", line)
            names = [n for grp in ports for n in grp.strip("{}").split()]
            if "all_inputs" in line or "all_outputs" in line:
                names = ["*all*"]
            key = "input_delay" if cmd == "set_input_delay" else "output_delay"
            for n in names:
                base = re.sub(r"\[[^\]]*\]$", "", n.replace("\\", "")).replace("*", "")
                found[key][base] = float(m.group(1)) if m else None
        elif cmd in _EXCEPTIONS:
            if "JUSTIFICATION:" not in comment:
                problems.append(f"timing exception without a written '# JUSTIFICATION:' comment: {line[:120]}")
            found["exceptions"].append({"command": line[:200], "justification": comment[:300]})
    for c in clocks:
        want = round(1000.0 / float(c["freq_mhz"]), 6)
        got = found["clocks"].get(c["name"])
        if got is None:
            problems.append(f"no create_clock on port {c['name']}")
        elif abs(got - want) > 1e-6:
            problems.append(f"clock {c['name']} period {got} ns != spec {want} ns ({c['freq_mhz']} MHz)")
    u = found["uncertainty"]
    lo, hi = r["clock_uncertainty_ns"]["min"], r["clock_uncertainty_ns"]["max"]
    if u is None:
        problems.append("no set_clock_uncertainty")
    elif not lo <= u <= hi:
        problems.append(f"clock uncertainty {u} ns is outside pnr_ranges.yaml [{lo}, {hi}]")
    f = found["max_fanout"]
    flo, fhi = r["max_fanout"]["min"], r["max_fanout"]["max"]
    if f is None:
        problems.append("no set_max_fanout")
    elif not flo <= f <= fhi:
        problems.append(f"max fanout {f} is outside pnr_ranges.yaml [{flo}, {fhi}]")
    periods = [round(1000.0 / float(c["freq_mhz"]), 6) for c in clocks] or [None]
    for key, ports in (("input_delay", inputs), ("output_delay", outputs)):
        have = found[key]
        for p in ports:
            if p not in have and "*all*" not in have:
                problems.append(f"no {key.replace('_', ' ')} on port {p}")
        for p, v in have.items():
            if v is None or (periods[0] and not 0 <= v < periods[0]):
                problems.append(f"{key.replace('_', ' ')} on {p} = {v} ns is not within [0, clock period)")
    return problems, found


# --- Grid's pin file ---------------------------------------------------------------------------------
def pin_cfg_sides(text: str) -> dict[str, list[str]]:
    """OpenLane pin order file: '#N' / '#S' / '#E' / '#W' sections, one pin regex per line."""
    sides: dict[str, list[str]] = {}
    cur = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if re.fullmatch(r"#[NSEW]", line):
            cur = line[1]
            sides.setdefault(cur, [])
        elif line.startswith("#") or line.startswith("$"):
            continue
        elif cur:
            sides[cur].append(line)
    return sides


def pin_side_of(name: str, sides: dict[str, list[str]]) -> list[str]:
    return [s for s, pats in sides.items() for p in pats if re.fullmatch(p, name)]


def pin_cfg_problems(text: str, port_bits: list[str]) -> list[str]:
    """Every pin bit (e.g. count[3]) must match exactly one regex, on one side."""
    sides = pin_cfg_sides(text)
    if not sides:
        return ["pin_order.cfg has no #N/#S/#E/#W section"]
    problems = []
    for b in port_bits:
        hit = pin_side_of(b, sides)
        if not hit:
            problems.append(f"pin {b} is not matched by any pattern in pin_order.cfg")
        elif len(hit) > 1:
            problems.append(f"pin {b} is matched on several sides: {hit}")
    for s, pats in sides.items():
        for p in pats:
            try:
                re.compile(p)
            except re.error as e:
                problems.append(f"#{s} pattern {p!r} is not a valid regex: {e}")
                continue
            if not any(re.fullmatch(p, b) for b in port_bits):
                problems.append(f"#{s} pattern {p!r} matches no pin of the design")
    return problems


_PIN_PARSE = r'''
import sys
import ioplace_parser
try:
    sides = ioplace_parser.parse(open(sys.argv[1]).read())
except Exception as e:  # the parser's own message (line:column)
    print("S2S_PINCFG_ERROR " + str(e).replace("\n", " "))
    sys.exit(1)
print("S2S_PINCFG_OK " + " ".join(sorted(sides)))
'''


def pin_cfg_parser_problems(cfg: Path, workdir: Path) -> list[str]:
    """Parse the pin file with OpenLane's own parser (ioplace_parser, inside s2s-eda): its grammar is
    narrower than Python regexes (e.g. it rejects '[0-7]'), so the tool decides, not a guess."""
    workdir = workdir.resolve()
    script = workdir / ".s2s" / "pin_cfg_parse.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(_PIN_PARSE)
    rec = runner.run(["python3", str(script), str(Path(cfg).resolve())], workdir, workdir / "logs" / "pin_cfg_parse.log",
                     "openlane", 120)
    log = Path(rec.log_path).read_text(errors="replace")
    if "S2S_PINCFG_OK" in log and rec.exit_code == 0:
        return []
    err = next((ln[len("S2S_PINCFG_ERROR "):] for ln in log.splitlines() if ln.startswith("S2S_PINCFG_ERROR ")), log[-300:])
    return [f"OpenLane's pin-config parser (ioplace_parser) rejects pnr/pin_order.cfg: {err}"]


def port_bits(spec: dict) -> tuple[list[str], list[str], list[str]]:
    """(all pin bits, input port names without clocks, output port names) from spec.yaml."""
    clocks = {c["name"] for c in spec.get("clocks", [])}
    bits, ins, outs = [], [], []
    for p in spec["interfaces"]:
        w = int(p["width"])
        bits += [p["name"]] if w == 1 else [f"{p['name']}[{i}]" for i in range(w)]
        if p["dir"] == "in" and p["name"] not in clocks:
            ins.append(p["name"])
        elif p["dir"] == "out":
            outs.append(p["name"])
    return bits, ins, outs
