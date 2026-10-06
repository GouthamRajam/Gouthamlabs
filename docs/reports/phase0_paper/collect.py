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
json.dump(out, open(sys.argv[1], "w"), indent=1, default=str)
for d, v in out.items():
    p = v["power"]["tt_025C_1v80"]
    print(d, v["iteration"], "T", v["period_ns"], "cells", v["synth_cells"], "die", v["die_area_um2"], "P_tt %.1f uW" % (p["total_w"]*1e6),
          "IR %.3f mV" % (v["ir_worst_v"]*1e3), "R_nom %.0f ohm" % v["spef"]["nom"]["total_wire_res_ohm"],
          "C_nom %.2f pF" % (v["spef"]["nom"]["total_net_cap_f"]*1e12), "maxR %.0f %s" % (v["spef"]["nom"]["max_net_res_ohm"], v["spef"]["nom"]["max_net_res_net"]),
          "WL", v["wirelength_um"], "vias", v["vias"], "skew", v["tree_skew_ns_max"])
