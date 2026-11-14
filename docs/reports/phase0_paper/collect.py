import json, hashlib, re, glob, os, sys
ROOT = "/home/user/Gouthamlabs/var/artifacts/runs"
RUNS = {"counter8": "run_01M43B9BVD8M5ANEVYTE43N0KN", "alu8": "run_01M44DR7XRWAQ9XY53AG8SRJCM",
        "sync_fifo": "run_01M43MDNVKWCHEQ0GGHPJFT602", "uart": "run_01M47BE6QKCPAEAE7RVYYJ9TEY",
        "spi_master": "run_01M484JWYZ7ADCE8N97SZV80QG"}
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
def J(p):
    try: return json.load(open(p))
    except Exception: return {}
def spef(p):
    """Sum *RES and *CAP sections of a SPEF; units from header."""
    rtot = ctot = 0.0; rmax = (0, ""); cunit = runit = 1.0; sec = None; net = ""; nres = 0; nets = 0; names = {}
    for ln in open(p, errors="replace"):
        if sec == "N" and ln.startswith("*") and len(ln.split()) == 2 and ln.split()[0][1:].isdigit():
            names[ln.split()[0]] = ln.split()[1]; continue
        if ln.startswith("*NAME_MAP"): sec = "N"; continue
        if sec == "N" and ln.startswith("*") and not ln.split()[0][1:].isdigit(): sec = None
        if ln.startswith("*C_UNIT"): v, u = ln.split()[1:3]; cunit = float(v) * {"PF": 1e-12, "FF": 1e-15}[u.upper()]
        elif ln.startswith("*R_UNIT"): v, u = ln.split()[1:3]; runit = float(v) * {"OHM": 1, "KOHM": 1e3}[u.upper()]
        elif ln.startswith("*D_NET"): net = ln.split()[1]; nets += 1; ctot += float(ln.split()[2]) * cunit; nr = 0.0
        elif ln.startswith("*RES"): sec = "R"
        elif ln.startswith("*CAP") or ln.startswith("*CONN"): sec = None
        elif ln.startswith("*END"):
            if nr > rmax[0]: rmax = (nr, net)
            sec = None
        elif sec == "R" and ln.strip() and ln.split()[0].isdigit():
            r = float(ln.split()[3]) * runit; rtot += r; nres += 1; nr += r
    return {"total_wire_res_ohm": rtot, "total_net_cap_f": ctot, "res_segments": nres, "nets": nets,
            "max_net_res_ohm": rmax[0], "max_net_res_net": names.get(rmax[1], rmax[1])}
out = {}
for d, r in RUNS.items():
    run = f"{ROOT}/{r}"; rep = f"{run}/reports"
    g = glob.glob(f"{run}/tapeout/gds/*.gds")[0]; gh = sha(g)
    fin = [p for p in glob.glob(f"{run}/pnr/runs/*/final/gds/*.gds") if sha(p) == gh][0]
    itdir = fin.split("/final/")[0]
    m = J(f"{itdir}/final/metrics.json")
    sdc = open(f"{run}/pnr/src/constraints.sdc").read() if os.path.exists(f"{run}/pnr/src/constraints.sdc") else ""
    per = re.search(r"create_clock[^\n]*-period\s+([\d.]+)", sdc)
    pw, ir, syn, fp, cts = J(f"{rep}/power_report.json"), J(f"{rep}/ir_report.json"), J(f"{rep}/synth_report.json"), J(f"{rep}/floorplan_report.json"), J(f"{rep}/cts_report.json")
    sta, pv, dfm = J(f"{rep}/sta_signoff.json"), J(f"{rep}/pv_signoff.json"), J(f"{rep}/dfm_scorecard.json")
    rd = J(f"{run}/tapeout/reports/tapeout_readiness.json")
    sp = {}
    for c in ("nom", "min", "max"):
        f = glob.glob(f"{run}/tapeout/spef/{c}/*.spef")
        if f: sp[c] = spef(f[0])
    corners = sta.get("corners", {})
    tree_skew = max((v["setup"]["tree_skew_ns"] for v in cts.get("per_corner", {}).values()), default=None)
    out[d] = {"run": r, "iteration": itdir.split("/")[-1], "gds_sha256": gh, "gds_bytes": os.path.getsize(g),
              "period_ns": float(per.group(1)) if per else None,
              "synth_cells": syn.get("cells"), "synth_area_um2": syn.get("area_um2"),
              "die_area_um2": m.get("design__die__area"), "core_area_um2": m.get("design__core__area"),
              "instances": m.get("design__instance__count"), "instance_area_um2": m.get("design__instance__area"),
              "utilization": m.get("design__instance__utilization"), "hold_buffers": m.get("design__instance__count__hold_buffer"),
              "wirelength_um": m.get("route__wirelength"), "vias": m.get("route__vias"), "nets": m.get("route__net"),
              "max_wire_um": m.get("route__wirelength__max"),
              "power": pw.get("power_w_by_corner"), "activity": pw.get("input_activity"), "ol_power_w": pw.get("openlane_power_total_w"),
              "ir_worst_v": ir.get("worst_drop_v"), "ir_avg_v": ir.get("avg_drop_v"), "ir_limit_v": ir.get("limit_v"),
              "vgnd_bounce_v": m.get("design_powergrid__drop__worst__net:VGND__corner:nom_tt_025C_1v80"),
              "pdn_violations": m.get("design__power_grid_violation__count"),
              "setup_ws": min((v["setup_ws_ns"], k) for k, v in corners.items()),
              "hold_ws": min((v["hold_ws_ns"], k) for k, v in corners.items()),
              "tt_setup": corners.get("nom_tt_025C_1v80", {}).get("setup_ws_ns"),
              "corners_passed": sum(1 for v in corners.values() if v.get("passed")), "corners": len(corners),
              "clock_rule_allowed": len({e["pin"] for v in corners.values() for e in (v.get("clock_rule_allowed") or [])}),
              "tree_skew_ns_max": tree_skew,
              "slew_viol": m.get("design__max_slew_violation__count"), "cap_viol": m.get("design__max_cap_violation__count"),
              "drc_magic": pv.get("magic_drc", {}).get("violations"), "drc_klayout": pv.get("klayout_drc", {}).get("violations"),
              "lvs": pv.get("lvs", {}).get("verdict"), "lvs_devices": pv.get("lvs", {}).get("counts", {}).get("devices", {}).get("layout"),
              "antenna_nets": pv.get("antenna", {}).get("net_violations"), "xor": m.get("design__xor_difference__count"),
              "dfm": dfm.get("summary"), "dfm_items": [(i.get("id"), i.get("severity"), i.get("title")) for i in dfm.get("items", [])],
              "spef": sp, "hard": (rd.get("hard_checks") or {}).get("verdict"),
              "A": rd.get("baseline_A_pct"), "B": rd.get("baseline_B_pct")}
# --- Derated (flat OCV) timing and the current hard-check verdict (CEO decision 2026-10-07) ---
for d, v in out.items():
    rep = f"{ROOT}/{v['run']}/reports"
    der = J(f"{rep}/sta_tool.json").get("derated") or {}
    v["derated"] = {}
    for pct, x in der.items():
        cs = x.get("corners", {})
        v["derated"][pct] = {"early": x.get("early"), "late": x.get("late"), "setup_ws": x.get("setup_ws_ns"),
                             "hold_ws": x.get("hold_ws_ns"), "passed": x.get("passed"), "gate": x.get("gate"),
                             "corners": len(cs), "corners_passed": sum(1 for c in cs.values() if c.get("passed")),
                             "setup_corner": min(cs, key=lambda k: cs[k]["setup_ws_ns"]) if cs else None,
                             "hold_corner": min(cs, key=lambda k: cs[k]["hold_ws_ns"]) if cs else None,
                             "caveat": x.get("caveat")}
    rdn = J(f"{rep}/tapeout_readiness.json"); hc = rdn.get("hard_checks") or {}
    v["gate_now"] = {"source": "reports/tapeout_readiness.json", "verdict": hc.get("verdict"), "passed": hc.get("passed"),
                     "of": hc.get("of"), "items": [(i.get("check"), i.get("status")) for i in hc.get("items", [])],
                     "conditions": hc.get("conditions"), "phase0_gate": (rdn.get("phase0_gate") or {}).get("status"),
                     "A": rdn.get("baseline_A_pct"), "B": rdn.get("baseline_B_pct"),
                     "earned_A": rdn.get("earned_A_total"), "weights_A": rdn.get("weights_A_total"),
                     "earned_B": rdn.get("earned_B_total"), "weights_B": rdn.get("weights_B_total")}
    sdc = open(f"{ROOT}/{v['run']}/pnr/src/constraints.sdc").read()
    unc = re.search(r"set_clock_uncertainty\s+([\d.]+)", sdc)
    v["clock_uncertainty_ns"] = float(unc.group(1)) if unc else None

# sync_fifo what-if derated STA (OpenSTA on read-only copies; NOT recorded signoff checks).
# Each log prints "WS <seconds>" (or "S2S_WS"); the .tcl next to it names the liberty corner, SPEF and derate.
SCR = "/home/user/Gouthamlabs/var/artifacts/scratch_ocv"
WHATIF = [("signed original", "sync_fifo", "run_01M43MDNVKWCHEQ0GGHPJFT602 (signed netlist)", {0: "_0", 5: "_5", 10: "_10"}),
          ("design change #1 (registered rd_data)", "sync_fifo_fix_it3", "run_01M4A7YXRDRF2TV0HY1ERGQJ0A, P&R it3",
           {0: "1.0", 5: "1.05", 10: "1.1"}),
          ("design change #2 (registered read-mux selects)", "sync_fifo_fix2_it3", "run_01M4AFNT5QK68FGT27TVRBYWZN, P&R it3",
           {0: "1.0", 5: "1.05", 10: "1.1"})]
def ws(log):
    m = re.search(r"^(?:S2S_)?WS\s+(\S+)", open(log).read(), re.M)
    return float(m.group(1)) * 1e9 if m else None
def tclinfo(tcl):
    t = open(tcl).read()
    lib = re.search(r"sky130_fd_sc_hd__(\w+)\.lib", t); sp = re.search(r"/(\w+)\.spef", t)
    der = re.findall(r"set_timing_derate -(early|late) ([\d.]+)", t)
    return {"lib": lib.group(1) if lib else None, "rc": sp.group(1) if sp else None, "derate": dict(der)}
wi = []
for label, sub, src, suf in WHATIF:
    row = {"label": label, "dir": f"var/artifacts/scratch_ocv/{sub}", "netlist": src, "setup": {}, "hold": {}}
    for pct, sx in suf.items():
        for kind in ("setup", "hold"):
            log = f"{SCR}/{sub}/{kind}{sx}.log"
            row[kind][pct] = ws(log)
            if pct == 10: row[f"{kind}_tcl"] = tclinfo(log[:-4] + ".tcl")
    wi.append(row)
out["sync_fifo"]["whatif"] = wi
# change #2 P&R iterations 3, 4 and 5 (why the block is still FAIL)
C2 = f"{ROOT}/run_01M4AFNT5QK68FGT27TVRBYWZN"
c2 = {}
for k in (3, 4, 5):
    it = J(f"{C2}/reports/pnr_iteration_{k}.json"); f = it.get("facts", {}); mm = J(f"{C2}/pnr/runs/it{k}/final/metrics.json")
    c2[f"it{k}"] = {"antenna_nets": f.get("antenna_violating_nets"), "slew_viol": f.get("max_slew_violations"),
                    "cap_viol": f.get("max_cap_violations"), "problems": len(it.get("problems", [])),
                    "max_clkbuf_fanout": max((p["value"] for p in (f.get("independent_drv_pins") or []) if p["pin"].startswith("clkbuf")), default=None),
                    "instances": mm.get("design__instance__count"),
                    "setup_ws": min(f.get("setup_ws_by_corner", {}).values(), default=None),
                    "hold_ws": min(f.get("hold_ws_by_corner", {}).values(), default=None),
                    "diode_insertion": it.get("params", {}).get("RUN_HEURISTIC_DIODE_INSERTION", 0)}
out["sync_fifo"]["change2_pnr"] = c2
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
for d, v in out.items():
    p = v["power"]["tt_025C_1v80"]
    print(d, v["iteration"], "T", v["period_ns"], "cells", v["synth_cells"], "die", v["die_area_um2"], "P_tt %.1f uW" % (p["total_w"]*1e6),
          "IR %.3f mV" % (v["ir_worst_v"]*1e3), "R_nom %.0f ohm" % v["spef"]["nom"]["total_wire_res_ohm"],
          "C_nom %.2f pF" % (v["spef"]["nom"]["total_net_cap_f"]*1e12), "maxR %.0f %s" % (v["spef"]["nom"]["max_net_res_ohm"], v["spef"]["nom"]["max_net_res_net"]),
          "WL", v["wirelength_um"], "vias", v["vias"], "skew", v["tree_skew_ns_max"])
