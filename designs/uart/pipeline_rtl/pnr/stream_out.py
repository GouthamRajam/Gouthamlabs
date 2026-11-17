#!/usr/bin/env python3
"""DEF -> GDSII stream-out for the pipeline-generated UART, using KLayout's Python API.

Cell geometry comes from the SKY130 cell GDS (never from LEF abstracts); routing, vias, pins and
tap/diode/fill placement come from the DEF. The result is written only if every DEF component
resolved to a real, non-empty cell and the instance count equals the DEF's COMPONENTS count.
Prints a JSON summary with the output SHA-256. Run with `python3 -I`; point --pylib at the folder
holding the klayout package if it is not installed system-wide.
"""
import argparse, collections, hashlib, json, re, sys
from pathlib import Path


def insert_filler(db, layout, top, def_text, masters, cell_gds):
    """Fill every empty site in every DEF ROW with sky130_fd_sc_hd__fill_{8,4,2,1} (a stand-in for
    OpenROAD filler_placement, which this design's P&R script never ran). Returns cells added."""
    site, row_h = 460, 2720
    rows = [(int(x), int(y), o, int(n)) for x, y, o, n in
            re.findall(r"ROW \S+ unithd (\d+) (\d+) (\w+) DO (\d+) BY 1 STEP 460 0 ;", def_text)]
    occupied = collections.defaultdict(list)
    for i in top.each_inst():
        if layout.cell(i.cell_index).name in masters:
            b = i.bbox()
            occupied[b.bottom].append((b.left, b.right))
    rot = {"N": db.Trans.R0, "FS": db.Trans.M0}
    lib = db.Layout()
    lib.read(cell_gds)
    fills = {}
    for w in (8, 4, 2, 1):
        name = f"sky130_fd_sc_hd__fill_{w}"
        cell = layout.cell(name) or layout.create_cell(name)
        if cell.bbox().empty():
            cell.copy_tree(lib.cell(name))
        fills[w] = cell
    added = 0
    for x0, y, orient, n in rows:
        taken = [False] * n
        for a, b in occupied.get(y, []):
            for s in range((a - x0) // site, (b - x0) // site):
                if 0 <= s < n:
                    taken[s] = True
        s = 0
        while s < n:
            if taken[s]:
                s += 1
                continue
            e = s
            while e < n and not taken[e]:
                e += 1
            left = e - s
            while left:
                w = max(k for k in (8, 4, 2, 1) if k <= left)
                x = x0 + s * site
                oy = y if orient == "N" else y + row_h
                top.insert(db.CellInstArray(fills[w].cell_index(), db.Trans(rot[orient], x, oy)))
                added += 1
                s += w
                left -= w
            s = e
    return added


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--def", dest="def_file", required=True)
    ap.add_argument("--tlef", required=True, help="technology LEF (layers, vias)")
    ap.add_argument("--lef", required=True, help="standard-cell LEF")
    ap.add_argument("--cell-gds", required=True, help="sky130_fd_sc_hd.gds")
    ap.add_argument("--map", required=True, help="KLayout sky130A.map (LEF/DEF layer map)")
    ap.add_argument("--top", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--insert-filler", action="store_true",
                    help="add fill cells to empty row sites (not part of the DEF; recorded in the summary)")
    ap.add_argument("--pylib", help="directory containing the klayout python package")
    a = ap.parse_args()
    if a.pylib:
        sys.path.insert(0, a.pylib)
    import klayout.db as db

    cfg = db.LEFDEFReaderConfiguration()
    cfg.lef_files = [a.tlef, a.lef]
    cfg.map_file = a.map
    cfg.read_all_layers = True
    cfg.macro_resolution_mode = 2          # never take LEF geometry; use FOREIGN cells from the GDS
    cfg.macro_layout_files = [a.cell_gds]
    cfg.produce_routing = True
    cfg.produce_via_geometry = True
    cfg.produce_pins = True
    cfg.produce_labels = True
    cfg.produce_cell_outlines = True
    cfg.produce_obstructions = False
    cfg.produce_blockages = False
    cfg.produce_placement_blockages = False
    cfg.produce_regions = False
    cfg.dbu = 0.001
    opts = db.LoadLayoutOptions()
    opts.lefdef_config = cfg

    layout = db.Layout()
    layout.read(a.def_file, opts)

    top = layout.cell(a.top)
    if top is None:
        print(f"ERROR: top cell {a.top} not found", file=sys.stderr)
        return 2

    text = Path(a.def_file).read_text()
    m = re.search(r"^COMPONENTS\s+(\d+)\s*;", text, re.M)
    def_components = int(m.group(1))
    masters = set(re.findall(r"^\s*-\s+\S+\s+(\S+)", text[m.end():text.index("END COMPONENTS")], re.M))

    empty = sorted(n for n in masters if layout.cell(n) is None or layout.cell(n).bbox().empty())
    # The reader also instantiates routing via cells (VIA_*) in the top cell; count only components.
    names = [layout.cell(i.cell_index).name for i in top.each_inst()]
    inst = sum(1 for n in names if n in masters)
    vias = len(names) - inst
    problems = []
    if empty:
        problems.append(f"{len(empty)} component master(s) missing or empty in the output: {empty[:8]}")
    if inst != def_components:
        problems.append(f"component instance count {inst} != DEF COMPONENTS {def_components}")
    if problems:
        for p in problems:
            print("ERROR:", p, file=sys.stderr)
        return 3

    filler_added = insert_filler(db, layout, top, text, masters, a.cell_gds) if a.insert_filler else 0
    for c in list(layout.top_cells()):
        if c.name != a.top:
            c.prune_cell()  # cells loaded from the PDK GDS but never instantiated
    assert [c.name for c in layout.top_cells()] == [a.top], "output must have exactly one top cell"
    layout.write(a.out)
    data = Path(a.out).read_bytes()
    bb = top.dbbox()
    print(json.dumps({
        "top": a.top, "out": a.out, "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "def_components": def_components, "component_instances": inst, "via_cell_instances": vias,
        "distinct_masters": len(masters), "filler_cells_added": filler_added,
        "bbox_um": [bb.left, bb.bottom, bb.right, bb.top],
        "klayout_version": db.__version__ if hasattr(db, "__version__") else "unknown",
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
