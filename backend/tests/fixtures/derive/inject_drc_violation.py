# KLayout batch script (run inside s2s-eda):
#   klayout -b -r inject_drc_violation.py -rd input=spm.gds -rd output=spm_drc_bad.gds -rd top=spm
# Copies the GDS and adds ONE known DRC defect to the top cell: a 0.05 x 0.05 um square on
# SKY130 met1 drawing (68/20), far below met1's 0.14 um minimum width, placed 1 um inside
# the lower-left corner of the cell's bounding box (outside the core rows).
import pya

layout = pya.Layout()
layout.read(input)
cell = layout.cell(top)
met1 = layout.layer(68, 20)
bbox = cell.bbox()
x = bbox.left + int(1.0 / layout.dbu)
y = bbox.bottom + int(1.0 / layout.dbu)
size = int(0.05 / layout.dbu)
cell.shapes(met1).insert(pya.Box(x, y, x + size, y + size))
layout.write(output)
print(f"S2S_INJECTED met1 box {size * layout.dbu:.3f}um at ({x * layout.dbu:.3f}, {y * layout.dbu:.3f})")
