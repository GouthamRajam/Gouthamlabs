"""Fabian's DFM screen (MASTER_SPEC A.15, Phase 0 checks 1-5) as a KLayout script, plus check 6
(antenna margin) from OpenROAD's verbose antenna report.

Every PDK number is read by the tool from the PDK's own decks inside s2s-eda, never typed here:
  layer numbers + min width/spacing  <- sky130A_mr.drc  (e.g. `m1.width(0.14, ...)`, `m1_wildcard = "68/20"`)
  max metal density per layer        <- met_min_ca_density.lydrc (min clear-area density -> 1 - limit)
Only the screening policy (window size, near-limit %, run length) comes from config/signoff.yaml.

Severity is decided by fixed rules here (Fabian may rank and explain items, never lower a severity):
  high    over a PDK limit (window density above max; antenna ratio >= 100%)
  medium  near a limit where yield impact is real (density >= near-max; antenna >= flag %; long
          parallel runs at near-minimum spacing; near-limit line ends)
  low     statistics worth knowing (near-limit edge fraction; single vias where a second fits;
          isolated narrow lines)
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from s2s.tools import runner

DRC_DECK = "/opt/pdk/sky130A/libs.tech/klayout/drc/sky130A_mr.drc"
DENSITY_DECK = "/opt/pdk/sky130A/libs.tech/klayout/drc/met_min_ca_density.lydrc"

# Runs inside s2s-eda: `klayout -b -r dfm.py -rd input=... -rd top=... -rd out=... -rd policy=<json>`
KLAYOUT_SCRIPT = r'''
import json, re
import pya

P = json.loads(policy)
drc = open(drc_deck).read()
dens = open(density_deck).read()

# --- PDK rules, read from the decks -------------------------------------------------------------
def wildcard(name, text):
    m = re.search(r'^\s*' + name + r'_wildcard\s*=\s*"([^"]+)"', text, re.M)
    return m.group(1) if m else None

def rule(pattern):
    m = re.search(pattern, drc, re.M)
    return float(m.group(1)) if m else None

METALS = {  # name -> (drc wildcard name, width rule regex, space rule regex, density name)
    "li":  ("li", r'^li_outside_or_touching_areaidce\.width\(([\d.]+)', r'^li_outside_or_touching_areaidce\.space\(([\d.]+)', "li1"),
    "met1": ("m1", r'^m1\.width\(([\d.]+)', r'^non_huge_m1\.space\(([\d.]+)', "m1"),
    "met2": ("m2", r'^m2\.width\(([\d.]+)', r'^non_huge_m2\.space\(([\d.]+)', "m2"),
    "met3": ("m3", r'^m3\.width\(([\d.]+)', r'^non_huge_m3\.space\(([\d.]+)', "m3"),
    "met4": ("m4", r'^m4\.width\(([\d.]+)', r'^non_huge_m4\.space\(([\d.]+)', "m4"),
    "met5": ("m5", r'^m5\.width\(([\d.]+)', r'^m5\.space\(([\d.]+)', "m5"),
}
VIAS = {  # cut -> (wildcard name, lower metal, upper metal, spacing rule regex)
    "mcon": ("mcon", "li", "met1", r'^mcon\.space\(([\d.]+)'),
    "via":  ("via", "met1", "met2", r'^\s*via\.space\(([\d.]+)'),
    "via2": ("via2", "met2", "met3", r'^\s*via2\.space\(([\d.]+)'),
    "via3": ("via3", "met3", "met4", r'^\s*via3\.space\(([\d.]+)'),
    "via4": ("via4", "met4", "met5", r'^via4\.space\(([\d.]+)'),
}
rules = {}
for name, (wc, wre, sre, dn) in METALS.items():
    lim = re.search(r'if\s+' + dn + r'_ca_density\s*&lt;\s*([\d.]+)|if\s+' + dn + r'_ca_density\s*<\s*([\d.]+)', dens)
    ca = float(lim.group(1) or lim.group(2)) if lim else None
    rules[name] = {"layer": wildcard(wc, drc), "density_layers": wildcard(dn, dens),
                   "fill_layers": wildcard(dn + "fill", dens),
                   "min_width": rule(wre), "min_space": rule(sre),
                   "max_density": round(1 - ca, 4) if ca is not None else None}
for name, (wc, lo, hi, sre) in VIAS.items():
    rules[name] = {"layer": wildcard(wc, drc), "lower": lo, "upper": hi, "min_space": rule(sre)}

ly = pya.Layout()
ly.read(input)
top_cell = ly.cell(top)
dbu = ly.dbu
um = lambda v: v * dbu
to_dbu = lambda v: int(round(v / dbu))

def parse_spec(spec):
    """'68/20' or '68/0-4,6-9,11-43,45-*' -> list of (layer, datatype) present in the layout."""
    if not spec:
        return []
    l, dts = spec.split("/")
    out = []
    for info in ly.layer_infos():
        if info.layer != int(l):
            continue
        for part in dts.split(","):
            if part == "*" or (part.endswith("-*") and info.datatype >= int(part[:-2])) or \
               ("-" in part and not part.endswith("-*") and int(part.split("-")[0]) <= info.datatype <= int(part.split("-")[1])) or \
               (part.isdigit() and info.datatype == int(part)):
                out.append((info.layer, info.datatype))
                break
    return out

def region(spec):
    """Everything on the layer, through the hierarchy (standard cells included)."""
    r = pya.Region()
    for l, d in parse_spec(spec):
        r += pya.Region(top_cell.begin_shapes_rec(ly.layer(l, d)))
    return r.merged()

def routing(spec):
    """Only the shapes the flow drew in the top cell (wires, vias, pins): the standard cells are
    foundry-qualified layouts, so the geometry screens look at routing and routing-to-cell only."""
    r = pya.Region()
    for l, d in parse_spec(spec):
        r += pya.Region(top_cell.shapes(ly.layer(l, d)))
    return r.merged()

def loc(box):
    return [round(um(box.left), 3), round(um(box.bottom), 3), round(um(box.right), 3), round(um(box.top), 3)]

bbox_r = region("235/4")
die = bbox_r.bbox() if not bbox_r.is_empty() else top_cell.bbox()
die_area = um(die.width()) * um(die.height())
N = int(P["hotspots_per_item"])
near = 1 + float(P["near_limit_pct"]) / 100.0
res = {"pdk_rules": rules, "die_um": loc(die), "dbu": dbu, "layers": {}, "vias": {}}

for name in METALS:
    r = rules[name]
    reg = region(r["layer"])
    out = {"shapes": reg.count(), "min_width": r["min_width"], "min_space": r["min_space"],
           "max_density": r["max_density"]}
    # 1. density: whole area exactly as the PDK deck computes it, plus local windows
    dreg = region(r["density_layers"]) + region(r["fill_layers"])
    out["density_global"] = round(um(um(dreg.area())) / die_area, 4) if die_area else None
    W, S = to_dbu(float(P["density_window_um"])), to_dbu(float(P["density_step_um"]))
    wins = []
    x = die.left
    while True:
        y = die.bottom
        while True:
            w = pya.Box(x, y, min(x + W, die.right), min(y + W, die.top))
            if w.area() > 0:
                d = (dreg & pya.Region(w)).area() / w.area()
                wins.append((round(d, 4), loc(w)))
            if y + W >= die.top:
                break
            y += S
        if x + W >= die.right:
            break
        x += S
    wins.sort(key=lambda t: -t[0])
    out["density_windows"] = len(wins)
    out["density_window_max"] = wins[0][0] if wins else None
    out["density_window_min"] = wins[-1][0] if wins else None
    mx = r["max_density"]
    out["density_over_max"] = [{"density": d, "at": b} for d, b in wins if mx is not None and d > mx][:N]
    out["density_near_max"] = [{"density": d, "at": b} for d, b in wins
                               if mx is not None and mx * float(P["density_near_max_pct"]) / 100 <= d <= mx][:N]
    full = reg
    cells = (full - routing(r["layer"])).merged()
    reg = routing(r["layer"])
    out["routing_shapes"] = reg.count()
    if reg.is_empty() or not r["min_width"] or not r["min_space"]:
        res["layers"][name] = out
        continue
    edges_total = reg.edges().count()
    # 2. near-limit geometry: edges within near_limit_pct of min width / min spacing
    #    (routing-to-routing spacing plus routing-to-cell spacing)
    wv = reg.width_check(to_dbu(r["min_width"] * near))
    sv = reg.space_check(to_dbu(r["min_space"] * near)) + reg.separation_check(cells, to_dbu(r["min_space"] * near))
    own = reg.edges()
    w_edges = (own & wv.edges()).count()
    s_edges = (own & sv.edges()).count()
    near_len = (own & (wv.edges() + sv.edges())).length()
    out["edges_total"] = edges_total
    out["near_min_width_edges"] = w_edges
    out["near_min_space_edges"] = s_edges
    # by length, each edge counted once: the share of the routing outline that sits at the limit
    out["near_limit_edge_fraction"] = round(near_len / own.length(), 4) if own.length() else 0.0
    out["near_min_space_hotspots"] = [loc(ep.bbox()) for ep in list(sv.each())[:N]]
    # 4. long parallel runs at near-minimum spacing (projection = the facing length)
    L = float(P["long_parallel_run_um"])
    runs = []
    proj = reg.space_check(to_dbu(r["min_space"] * near), False, pya.Region.Projection) + \
        reg.separation_check(cells, to_dbu(r["min_space"] * near), False, pya.Region.Projection)
    for ep in proj.each():
        run = um(min(ep.first.length(), ep.second.length()))
        if run >= L:
            runs.append({"length_um": round(run, 3), "space_um": round(um(ep.distance()), 4), "at": loc(ep.bbox())})
    runs.sort(key=lambda t: -t["length_um"])
    out["long_parallel_runs"] = len(runs)
    out["long_parallel_run_list"] = runs[:N]
    # 5a. narrow isolated lines: a near-minimum-width line with no other shape within the clearance
    clear = to_dbu(r["min_space"] * float(P["isolated_clearance_x_min_space"]))
    iso = []
    for poly in reg.each():
        b = poly.bbox()
        short, long_ = min(b.width(), b.height()), max(b.width(), b.height())
        if short <= to_dbu(r["min_width"] * near) and long_ >= 5 * short and poly.is_box():
            if full.interacting(pya.Region(b.enlarged(clear, clear))).count() == 1:
                iso.append({"width_um": round(um(short), 4), "length_um": round(um(long_), 3), "at": loc(b)})
    out["isolated_narrow_lines"] = len(iso)
    out["isolated_narrow_line_list"] = iso[:N]
    # 5b. line ends near limits: a short (line-end) edge facing another shape at near-minimum spacing
    # a line end is the short edge of a wire, not a contact landing pad (pads are no longer than wide)
    wires = reg.with_area(int(4 * to_dbu(r["min_width"]) ** 2), None, False)
    ends = wires.edges().with_length(0, to_dbu(r["min_width"] * near) + 1, False)
    others = (reg.edges() - ends) + cells.edges()
    le = ends.separation_check(others, to_dbu(r["min_space"] * near))
    le2 = ends.space_check(to_dbu(r["min_space"] * near))
    hot = list(le.each()) + list(le2.each())
    out["line_end_near_limit"] = len(hot)
    out["line_end_hotspots"] = [loc(ep.bbox()) for ep in hot[:N]]
    res["layers"][name] = out

# 3. single-via connections where a redundant via fits
for name in VIAS:
    r = rules[name]
    cuts = routing(r["layer"])
    lo, hi = region(rules[r["lower"]]["layer"]), region(rules[r["upper"]]["layer"])
    out = {"cuts": cuts.count(), "min_space": r["min_space"]}
    if cuts.is_empty() or not r["min_space"]:
        res["vias"][name] = out
        continue
    overlap = (lo & hi).merged()
    single, fits = 0, []
    sp = to_dbu(r["min_space"])
    for ov in overlap.each():
        inside = cuts.inside(pya.Region(ov))
        if inside.count() != 1:
            continue
        single += 1
        cut = list(inside.each())[0].bbox()
        b = ov.bbox()
        # the existing cut already meets its enclosure rules: a second cut needs the same enclosure
        enc_x = min(cut.left - b.left, b.right - cut.right)
        enc_y = min(cut.bottom - b.bottom, b.top - cut.top)
        fit_x = b.width() >= 2 * cut.width() + sp + 2 * enc_x
        fit_y = b.height() >= 2 * cut.height() + sp + 2 * enc_y
        if (fit_x or fit_y) and ov.is_box():
            fits.append(loc(cut))
    out["single_cut_connections"] = single
    out["redundant_via_fits"] = len(fits)
    out["redundant_via_fit_list"] = fits[:N]
    res["vias"][name] = out

open(out_json, "w").write(json.dumps(res, indent=1))
print("S2S_DFM_DONE")
'''


def run_dfm_layout(gds: Path, top: str, workdir: Path, policy: dict, name: str = "dfm",
                   timeout_s: float = 1800) -> dict:
    """Run the KLayout DFM script; returns its JSON plus run info. Raises on a tool failure."""
    workdir = workdir.resolve()
    sdir = workdir / ".s2s"
    sdir.mkdir(parents=True, exist_ok=True)
    script = sdir / f"{name}.py"
    script.write_text(KLAYOUT_SCRIPT)
    out = workdir / "reports" / f"{name}_layout.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    cmd = ["klayout", "-b", "-r", str(script), "-rd", f"input={Path(gds).resolve()}", "-rd", f"top={top}",
           "-rd", f"out_json={out}", "-rd", f"drc_deck={DRC_DECK}", "-rd", f"density_deck={DENSITY_DECK}",
           "-rd", f"policy={json.dumps(policy)}"]
    rec = runner.run(cmd, workdir, workdir / "logs" / f"{name}_klayout.log", "klayout", timeout_s)
    log = Path(rec.log_path).read_text()
    if rec.exit_code != 0 or "S2S_DFM_DONE" not in log or not out.exists():
        raise RuntimeError(f"KLayout DFM script failed (exit {rec.exit_code}); see {rec.log_path}: {log[-600:]}")
    data = json.loads(out.read_text())
    missing = [n for n, r in data["pdk_rules"].items()
               if not r.get("layer") or ("min_width" in r and r["min_width"] is None) or r.get("min_space") is None]
    if missing:
        raise RuntimeError(f"could not read PDK rules for {missing} from the PDK decks")
    data["run"] = {"command": runner.command_str(cmd), "log": str(rec.log_path), "tool_version": rec.tool_version,
                   "env_hash": rec.env_hash, "duration_s": rec.duration_s}
    return data


# --- check 6: antenna margin, from `check_antennas -verbose` -------------------------------------
_ANT_NET = re.compile(r"^Net: (\S+)")
_ANT_PIN = re.compile(r"^\s+Pin:\s+(\S+)")
_ANT_LAYER = re.compile(r"^\s+Layer: (\S+)")
_ANT_RATIO = re.compile(r"^\s+(Partial|Cumulative) (?:area )?ratio:\s+([\d.]+)")
_ANT_REQ = re.compile(r"^\s+Required ratio:\s+([\d.]+) \(([^)]+)\)")


def antenna_tcl(odb: Path, report: Path) -> str:
    return (f"read_db {odb}\ncheck_antennas -verbose -report_file {report}\nputs S2S_ANT_DONE\n")


def parse_antenna_verbose(text: str) -> list[dict]:
    """Per net: the worst ratio/required over its pins, layers and checks (required 0 = no limit)."""
    worst: dict[str, dict] = {}
    net = pin = layer = None
    pending = None
    for line in text.splitlines():
        if m := _ANT_NET.match(line):
            net, pin, layer = m.group(1), None, None
        elif m := _ANT_PIN.match(line):
            pin = m.group(1)
        elif m := _ANT_LAYER.match(line):
            layer = m.group(1)
        elif m := _ANT_RATIO.match(line):
            pending = float(m.group(2))
        elif (m := _ANT_REQ.match(line)) and pending is not None and net:
            req, kind = float(m.group(1)), m.group(2).strip()
            if req > 0:
                pct = 100.0 * pending / req
                w = worst.get(net)
                if w is None or pct > w["pct_of_limit"]:
                    worst[net] = {"net": net, "pin": pin, "layer": layer, "check": kind, "ratio": pending,
                                  "required": req, "pct_of_limit": round(pct, 2)}
            pending = None
    return sorted(worst.values(), key=lambda w: -w["pct_of_limit"])


# --- the scorecard items, with rule-based severity --------------------------------------------------
def items(layout: dict, antenna: list[dict], policy: dict) -> list[dict]:
    out: list[dict] = []

    def add(sev, check, title, count, locations, why, fix, owner, detail=None):
        out.append({"id": f"DFM-{len(out) + 1:03d}", "severity": sev, "check": check, "title": title,
                    "count": count, "locations": locations, "why": why, "suggested_fix": fix, "owner": owner,
                    "detail": detail or {}})

    for name, L in layout["layers"].items():
        if L.get("density_over_max"):
            add("high", "density", f"{name}: {len(L['density_over_max'])} window(s) above the PDK max density "
                f"{L['max_density']}", len(L["density_over_max"]), [w["at"] for w in L["density_over_max"]],
                "Over-dense metal dishes during CMP, thinning lines and raising resistance and shorts.",
                "Spread routing or lower utilization in these windows.", "Grid")
        elif L.get("density_near_max"):
            add("medium", "density", f"{name}: {len(L['density_near_max'])} window(s) within "
                f"{100 - policy['density_near_max_pct']}% of the PDK max density {L['max_density']}",
                len(L["density_near_max"]), [w["at"] for w in L["density_near_max"]],
                "Windows close to the density limit leave no margin for CMP variation.",
                "Spread routing in these windows.", "Orion")
        if L.get("long_parallel_runs"):
            add("medium", "parallel_run", f"{name}: {L['long_parallel_runs']} parallel run(s) >= "
                f"{policy['long_parallel_run_um']} um at near-minimum spacing", L["long_parallel_runs"],
                [r["at"] for r in L["long_parallel_run_list"]],
                "Long facing edges at minimum spacing are where a particle most likely bridges two nets.",
                "Spread these wires by one track where routing allows.", "Orion",
                {"longest_um": L["long_parallel_run_list"][0]["length_um"]})
        if L.get("line_end_near_limit"):
            add("medium", "line_end", f"{name}: {L['line_end_near_limit']} line end(s) at near-minimum spacing",
                L["line_end_near_limit"], L["line_end_hotspots"],
                "Line ends shorten in lithography; a near-minimum end-to-line gap can open or bridge.",
                "Extend spacing at these line ends or add an end extension.", "Orion")
        if L.get("isolated_narrow_lines"):
            add("low", "isolated_line", f"{name}: {L['isolated_narrow_lines']} isolated near-minimum-width line(s)",
                L["isolated_narrow_lines"], [i["at"] for i in L["isolated_narrow_line_list"]],
                "Isolated narrow lines print thinner than dense ones and are more likely to neck or open.",
                "Widen the line or route it next to a neighbour.", "Orion")
        if L.get("edges_total"):
            add("low", "near_limit_geometry", f"{name}: {L['near_limit_edge_fraction']:.1%} of routing edge length within "
                f"{policy['near_limit_pct']}% of min width/spacing", L["near_min_width_edges"] + L["near_min_space_edges"],
                L.get("near_min_space_hotspots", []),
                "The share of geometry at the limit sets how sensitive yield is to process variation.",
                "Use non-default wider/spaced rules on non-critical nets.", "Orion",
                {"fraction": L["near_limit_edge_fraction"], "edges_total": L["edges_total"]})
    for name, V in layout["vias"].items():
        if V.get("redundant_via_fits"):
            add("low", "single_via", f"{name}: {V['redundant_via_fits']} single-cut connection(s) where a second cut fits",
                V["redundant_via_fits"], V["redundant_via_fit_list"],
                "A single via is a single point of failure; a void or high resistance opens the net.",
                "Insert a redundant cut at these locations (double-via post-processing).", "Orion",
                {"single_cut_connections": V["single_cut_connections"]})
    over = [a for a in antenna if a["pct_of_limit"] >= 100]
    near = [a for a in antenna if policy["antenna_margin_flag_pct"] <= a["pct_of_limit"] < 100]
    if over:
        add("high", "antenna", f"{len(over)} net(s) at or above the antenna limit", len(over),
            [f"{a['net']} {a['pin']} {a['layer']}" for a in over],
            "Charge collected during etch can damage the gate oxide.", "Add a diode or a layer jump.", "Orion")
    if near:
        add("medium", "antenna", f"{len(near)} net(s) at >= {policy['antenna_margin_flag_pct']}% of the antenna limit",
            len(near), [f"{a['net']} {a['pin']} {a['layer']} ({a['pct_of_limit']}%)" for a in near],
            "Little antenna margin: process variation in plasma charging can turn this into damage.",
            "Add a diode or break the long run with a layer jump.", "Orion")
    return out
