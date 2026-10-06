import json, sys, glob
import gdstk, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
S = sys.argv[1]; D = json.load(open(f"{S}/data.json"))
ROOT = "/home/user/Gouthamlabs/var/artifacts/runs"
LAYERS = [((67, 20), "#9aa5b1", "li1"), ((68, 20), "#4c78a8", "met1"), ((69, 20), "#f58518", "met2"),
          ((70, 20), "#54a24b", "met3"), ((71, 20), "#b279a2", "met4"), ((72, 20), "#e45756", "met5")]
names = list(D)
fig, axes = plt.subplots(1, 5, figsize=(15, 3.6))
for ax, d in zip(axes, names):
    lib = gdstk.read_gds(glob.glob(f"{ROOT}/{D[d]['run']}/tapeout/gds/*.gds")[0])
    top = lib.top_level()[0]
    polys = top.get_polygons(include_paths=True)
    for (ly, dt), col, _ in LAYERS:
        pts = [p.points for p in polys if p.layer == ly and p.datatype == dt]
        ax.add_collection(PolyCollection(pts, facecolors=col, edgecolors="none", alpha=0.55 if ly < 71 else 0.35))
    (x0, y0), (x1, y1) = top.bounding_box()
    ax.set_xlim(x0, x1); ax.set_ylim(y0, y1); ax.set_aspect("equal")
    ax.set_title(f"{d}\n{x1-x0:.0f} x {y1-y0:.0f} um", fontsize=9); ax.tick_params(labelsize=6)
handles = [plt.Rectangle((0, 0), 1, 1, color=c, alpha=0.6) for _, c, _ in LAYERS]
fig.legend(handles, [n for *_, n in LAYERS], loc="lower center", ncol=6, fontsize=8, frameon=False)
fig.tight_layout(rect=(0, 0.08, 1, 1)); fig.savefig(f"{S}/fig_layouts.png", dpi=220); plt.close(fig)

fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 3.6))
cs = [("ss_100C_1v60", "SS 100C 1.60V", "#4c78a8"), ("tt_025C_1v80", "TT 25C 1.80V", "#54a24b"), ("ff_n40C_1v95", "FF -40C 1.95V", "#e45756")]
w = 0.26
for i, (c, lab, col) in enumerate(cs):
    a1.bar([k + (i - 1) * w for k in range(5)], [D[d]["power"][c]["total_w"] * 1e3 for d in names], w, label=lab, color=col)
a1.set_yscale("log"); a1.set_xticks(range(5)); a1.set_xticklabels(names, fontsize=8); a1.set_ylabel("Total power (mW, log)")
a1.set_title("Estimated power by corner (20% input activity)", fontsize=9); a1.legend(fontsize=7, frameon=False)
a2.bar(range(5), [D[d]["ir_worst_v"] * 1e3 for d in names], 0.5, color="#4c78a8", label="Worst static IR drop (VPWR, TT)")
a2.axhline(90, color="#e45756", ls="--", lw=1); a2.text(4.4, 92, "limit 90 mV (5% of 1.8 V)", fontsize=7, ha="right", color="#e45756")
a2.set_yscale("log"); a2.set_ylim(0.01, 200); a2.set_xticks(range(5)); a2.set_xticklabels(names, fontsize=8)
a2.set_ylabel("mV (log)"); a2.set_title("Static IR drop vs limit", fontsize=9)
for k, d in enumerate(names): a2.text(k, D[d]["ir_worst_v"] * 1e3 * 1.25, f"{D[d]['ir_worst_v']*1e3:.2f}", ha="center", fontsize=7)
fig.tight_layout(); fig.savefig(f"{S}/fig_power_ir.png", dpi=220); plt.close(fig)
print("figs ok")
