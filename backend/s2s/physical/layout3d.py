"""GDSII -> 3D layer geometry for the web viewer (/projects, 3D layout).

A KLayout script (in s2s-eda) flattens the top cell, merges each layer and decomposes it into boxes
(SKY130 layout is Manhattan, so trapezoid decomposition gives rectangles). Each layer's z position and
thickness come from the PDK itself: the `render` lines of the Magic tech file (sky130A.tech), which is
the PDK's own 3D stack. The GDS layer numbers are SKY130's (the same ones the PDK DRC deck uses).

Output JSON: {top, bbox_um, layers: [{name, gds, z_um, t_um, boxes: [[x1, y1, x2, y2], ...], count,
truncated}]}. Boxes in micrometres. A display aid only: never used for any check.
"""
from __future__ import annotations

import json
from pathlib import Path

from s2s.tools import runner

TECH = "/opt/pdk/sky130A/libs.tech/magic/sky130A.tech"
# (render name in sky130A.tech, GDS layer/datatype, display name)
LAYERS = [("NWELL", "64/20", "nwell"), ("DIFF", "65/20", "diff"), ("TAP", "65/44", "tap"), ("POLY", "66/20", "poly"),
          ("CONT", "66/44", "licon"), ("LI", "67/20", "li1"), ("MCON", "67/44", "mcon"), ("MET1", "68/20", "met1"),
          ("VIA1", "68/44", "via"), ("MET2", "69/20", "met2"), ("VIA2", "69/44", "via2"), ("MET3", "70/20", "met3"),
          ("VIA3", "70/44", "via3"), ("MET4", "71/20", "met4"), ("VIA4", "71/44", "via4"), ("MET5", "72/20", "met5")]
MAX_BOXES = 60000  # per layer; beyond this the layer is marked truncated (never silently)

_SCRIPT = r'''
import json, re
import pya
heights = {}
for line in open(tech):
    m = re.match(r"\s*render\s+(\w+)\s+\S+\s+(-?[\d.]+)\s+([\d.]+)", line)
    if m:
        heights[m.group(1)] = (float(m.group(2)), float(m.group(3)))
spec = json.loads(layers)
ly = pya.Layout()
ly.read(inp)
top_cell = ly.cell(top)
dbu = ly.dbu
bb = top_cell.bbox()
out = {"top": top, "dbu": dbu, "bbox_um": [bb.left * dbu, bb.bottom * dbu, bb.right * dbu, bb.top * dbu], "layers": []}
for render, gds, name in spec:
    if render not in heights:
        continue
    l, d = (int(x) for x in gds.split("/"))
    li = ly.find_layer(l, d)
    if li is None:
        continue
    reg = pya.Region(top_cell.begin_shapes_rec(li)).merged()
    boxes, truncated = [], False
    for poly in reg.each():
        for t in poly.decompose_trapezoids():
            b = t.bbox()
            boxes.append([round(b.left * dbu, 3), round(b.bottom * dbu, 3), round(b.right * dbu, 3), round(b.top * dbu, 3)])
        if len(boxes) >= int(maxb):
            truncated = True
            break
    z, th = heights[render]
    out["layers"].append({"name": name, "gds": gds, "render": render, "z_um": z, "t_um": th,
                          "boxes": boxes[:int(maxb)], "count": len(boxes), "truncated": truncated})
open(outp, "w").write(json.dumps(out, separators=(",", ":")))
print("S2S_LAYOUT3D_DONE")
'''


def layout3d(gds: Path, top: str, workdir: Path, out: Path) -> dict:
    """Write and return the 3D layer geometry of `gds` (cached by the caller)."""
    workdir = workdir.resolve()
    script = workdir / ".s2s" / "layout3d.py"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text(_SCRIPT)
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    cmd = ["klayout", "-b", "-r", str(script), "-rd", f"inp={Path(gds).resolve()}", "-rd", f"top={top}",
           "-rd", f"tech={TECH}", "-rd", f"layers={json.dumps(LAYERS)}", "-rd", f"outp={tmp}", "-rd", f"maxb={MAX_BOXES}"]
    rec = runner.run(cmd, workdir, workdir / "logs" / "layout3d.log", "klayout", 600)
    log = Path(rec.log_path).read_text(errors="replace")
    if rec.exit_code != 0 or "S2S_LAYOUT3D_DONE" not in log or not tmp.exists():
        raise RuntimeError(f"KLayout could not convert the GDS for the 3D view; see {rec.log_path}")
    tmp.replace(out)
    return json.loads(out.read_text())
