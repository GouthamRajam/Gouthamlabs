"""Build the Phase 0 results paper (PDF) from data.json (collect.py) and the figures (figs.py)."""
import json, sys
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

S, OUT = sys.argv[1], sys.argv[2]
D = json.load(open(f"{S}/data.json"))
N = list(D)
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="Times-Roman", fontSize=10, leading=13.2, alignment=TA_JUSTIFY,
                      spaceAfter=5)
small = ParagraphStyle("s", parent=body, fontSize=8, leading=10, alignment=0, spaceAfter=0)
cell = ParagraphStyle("c", parent=small, fontName="Helvetica", fontSize=7.2, leading=8.8)
cellb = ParagraphStyle("cb", parent=cell, fontName="Helvetica-Bold")
cap = ParagraphStyle("cap", parent=body, fontSize=8.5, leading=10.5, alignment=TA_CENTER, spaceBefore=3, spaceAfter=9,
                     fontName="Times-Italic")
h1 = ParagraphStyle("h1", parent=body, fontName="Times-Bold", fontSize=12, leading=15, spaceBefore=9, spaceAfter=4, keepWithNext=1,
                    alignment=0)
h2 = ParagraphStyle("h2", parent=h1, fontSize=10.5, leading=13, spaceBefore=6, spaceAfter=3, fontName="Times-BoldItalic", keepWithNext=1)
title = ParagraphStyle("t", parent=body, fontName="Times-Bold", fontSize=17, leading=21, alignment=TA_CENTER, spaceAfter=6)
auth = ParagraphStyle("a", parent=body, alignment=TA_CENTER, fontSize=10, spaceAfter=2)
absS = ParagraphStyle("abs", parent=body, fontSize=9.2, leading=12, leftIndent=12 * mm, rightIndent=12 * mm)
P = lambda t, s=body: Paragraph(t, s)


def table(rows, widths, header_rows=1, note=None):
    data = [[P(str(c), cellb if r < header_rows else cell) for c in row] for r, row in enumerate(rows)]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=header_rows)
    st = [("LINEABOVE", (0, 0), (-1, 0), 0.9, colors.black), ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 0.5, colors.black),
          ("LINEBELOW", (0, -1), (-1, -1), 0.9, colors.black), ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("TOPPADDING", (0, 0), (-1, -1), 1.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.6),
          ("LEFTPADDING", (0, 0), (-1, -1), 2.5), ("RIGHTPADDING", (0, 0), (-1, -1), 2.5)]
    for r in range(header_rows, len(rows)):
        if (r - header_rows) % 2:
            st.append(("BACKGROUND", (0, r), (-1, r), colors.HexColor("#f3f5f8")))
    t.setStyle(TableStyle(st))
    return t


f1 = lambda x, n=1: f"{x:.{n}f}"
uW = lambda w: f"{w * 1e6:.1f}"
s = []
TOT_INST = sum(D[d]["instances"] for d in N)
TOT_DIE_MM2 = sum(D[d]["die_area_um2"] for d in N) * 1e-6
SF = D["sync_fifo"]; WI = SF["whatif"]; C2 = SF["change2_pnr"]
WI_ORIG, WI_C1, WI_C2 = WI
sg = lambda x: f"{x:+.3f}"
HOLD10 = min(D[d]["derated"]["10"]["hold_ws"] for d in N if D[d]["derated"])
HOLD10_D = min((d for d in N if D[d]["derated"]), key=lambda d: D[d]["derated"]["10"]["hold_ws"])
HOLD10_WI = min(w["hold"]["10"] for w in WI)
GA = D["counter8"]["gate_now"]
assert all(D[d]["gate_now"]["A"] == GA["A"] and D[d]["gate_now"]["B"] == GA["B"] for d in N)
IRMAX = max(D[d]["ir_worst_v"] for d in N) * 1e3
PTT = [D[d]["power"]["tt_025C_1v80"]["total_w"] for d in N]
s = []
s += [P("An AI Agent Framework for Open-Source RTL-to-GDSII on SKY130:<br/>A Proof-of-Concept on Five Small Digital Blocks", title),
      P("S2S (Spec-to-Silicon) project, Goutham Labs", auth),
      P("Phase 0 technical report, revised 7 October 2026. Framework proof-of-concept; pre-silicon results only, "
        "no wafers were fabricated.", auth),
      Spacer(1, 6)]
s.append(P(
    "<b>Abstract.</b> This report is a proof-of-concept of a framework, not of a product. S2S is an AI agent framework that "
    "orchestrates open-source EDA tools (Yosys, OpenROAD/OpenLane 2.3.10, OpenSTA, Magic, KLayout, Netgen, SymbiYosys/eqy) "
    "from a written specification through RTL to a GDSII layout on the open SkyWater SKY130 130 nm process "
    "(sky130_fd_sc_hd), and lets only the real tools decide whether a check passes. We exercised it on five small, flat, "
    f"single-clock blocks (counter8, alu8, sync_fifo, uart, spi_master; {TOT_INST:,} placed instances and "
    f"{TOT_DIE_MM2:.3f} mm<super>2</super> of die in total). Without derates, all five layouts are DRC-clean in two checkers, "
    "LVS-matched, antenna-clean, meet setup and hold at nine PVT/RC corners and are formally equivalent to their RTL. After an "
    "external review, timing with a flat +/-10% on-chip-variation (OCV) derate became a permanent hard check; SKY130 has no "
    "foundry OCV/AOCV tables, so flat derates are an engineering estimate. Under it, counter8, alu8 and uart pass all six hard "
    "checks; spi_master passes only under a relaxed clock-net fanout limit of 20 (CONDITIONAL); sync_fifo FAILS (what-if on "
    f"its signed netlist: setup {sg(WI_ORIG['setup']['10'])} ns). A design change fixed sync_fifo's timing at RTL level "
    f"({sg(WI_C2['setup']['10'])} ns setup, {sg(WI_C2['hold']['10'])} ns hold at +/-10%, what-if), but its place-and-route did "
    "not close clean within the tool budget, so the block stays FAIL and the Phase 0 gate is re-opened. Power (vector-less, "
    f"{min(PTT) * 1e6:.1f} uW-{max(PTT) * 1e3:.2f} mW at the typical corner) and static IR drop (at most {IRMAX:.2f} mV) are estimates; electromigration, dynamic IR, "
    "scan/ATPG and foundry-certified signoff were not done. The external reviewer concluded that the layouts are not "
    "commercially viable and that the framework is viable as an early-stage infrastructure prototype; we accept both points. "
    "The derated timing and the reviewer's limitations are therefore stated first (Section 1), before the method and the "
    "detailed results.", absS))

s.append(P("1. Status at a glance: derated timing and accepted limitations", h1))
s.append(P("1.1 Timing under flat on-chip-variation derates", h2))
rows = [["Block", "Source", "Nominal setup / hold", "+/-5% setup / hold", "+/-10% setup / hold", "+/-10% hard check"]]
for d in N:
    v = D[d]
    if not v["derated"]:
        continue
    d5, d10 = v["derated"]["5"], v["derated"]["10"]
    res = "PASS" if d10["passed"] else "FAIL"
    if v["clock_rule_allowed"]:
        res += " (block CONDITIONAL: clock-net fanout limit 20)"
    rows.append([d, f"recorded signoff check, {d10['corners_passed']}/{d10['corners']} corners ({v['run']})",
                 f"{sg(v['setup_ws'][0])} / {sg(v['hold_ws'][0])}", f"{sg(d5['setup_ws'])} / {sg(d5['hold_ws'])}",
                 f"{sg(d10['setup_ws'])} / {sg(d10['hold_ws'])}", res])
ocv_item = [st for c, st in SF["gate_now"]["items"] if "OCV" in c][0]
rows.append(["sync_fifo", f"recorded signoff ({SF['run']}): derated check {ocv_item}",
             f"{sg(SF['setup_ws'][0])} / {sg(SF['hold_ws'][0])}", "-", "-", "<b>FAIL</b>"])
for lab, w, res in (("signed original", WI_ORIG, "FAIL (setup)"), ("design change #1", WI_C1, "FAIL (setup)"),
                    ("design change #2", WI_C2, "timing met; block FAIL (P&amp;R not clean)")):
    rows.append([f"sync_fifo, {lab}", f"<i>what-if, not a recorded signoff</i> ({w['netlist'].replace('&', '&amp;')})",
                 f"{sg(w['setup']['0'])} / {sg(w['hold']['0'])}", f"{sg(w['setup']['5'])} / {sg(w['hold']['5'])}",
                 f"{sg(w['setup']['10'])} / {sg(w['hold']['10'])}", res])
tc = WI_ORIG["setup_tcl"], WI_ORIG["hold_tcl"]
s.append(KeepTogether([table(rows, [24, 52, 24, 24, 24, 28]),
P("Table 1. Worst setup / hold slack in ns under a flat derate (OpenSTA set_timing_derate -early 1-p -late 1+p on cell and "
  f"net delays, CRPR on, the SDC clock uncertainty of {D['counter8']['clock_uncertainty_ns']:.2f} ns still applied). "
  "Recorded rows: worst over all 9 corners, from each run's reports/sta_tool.json (checks sta_derated_5pct, sta_derated_10pct); "
  "setup is worst at SS 100 C 1.60 V with max RC and hold at FF -40 C 1.95 V with min RC in every block. sync_fifo what-if "
  "rows: OpenSTA on read-only copies of the routed netlists (logs in var/artifacts/scratch_ocv), one corner each: setup at "
  f"{tc[0]['lib']} with {tc[0]['rc']} RC, hold at {tc[1]['lib']} with {tc[1]['rc']} RC. SKY130 has no foundry OCV/AOCV "
  "tables, so flat derates are an engineering estimate.", cap)]))
s.append(P(
    "<b>sync_fifo.</b> Its signed netlist meets timing without derates but fails setup under the derate "
    f"({sg(WI_ORIG['setup']['5'])} ns at +/-5%, {sg(WI_ORIG['setup']['10'])} ns at +/-10%, what-if), on the combinational "
    "read path to the rd_data port. Two RTL design changes went through the full verification flow. Change #1 (registered "
    f"rd_data) made the derated number worse ({sg(WI_C1['setup']['10'])} ns at +/-10%) because the critical path became "
    "entirely on-chip delay, which the derate scales. Change #2 (read-mux selects taken directly from flip-flops) fixed the "
    f"timing at RTL level: {sg(WI_C2['setup']['10'])} ns setup and {sg(WI_C2['hold']['10'])} ns hold at +/-10% (what-if on "
    "its P&amp;R iteration-3 routed netlist). The block is still FAIL because its place-and-route did not close clean within the "
    f"tool budget: iteration 3 left {C2['it3']['antenna_nets']} antenna violation; iteration 4, with heuristic diode insertion, "
    f"removed it but raised the instance count from {C2['it3']['instances']:,} to {C2['it4']['instances']:,} (the inserted "
    f"diodes), which gave clock-buffer fanout up to {C2['it4']['max_clkbuf_fanout']:.0f}, {C2['it4']['slew_viol']} max-slew "
    f"and {C2['it4']['cap_viol']} max-capacitance violations. Iteration 5 (diodes off, denser placement, antenna margin 30%; "
    f"tool budget raised by the CEO to 20) left {C2['it5']['antenna_nets']} antenna violations on other long nets from input "
    "buffers. Analysis found why every iteration fails on different nets: global-route antenna repair sees the gate tied to "
    "the driver's diffusion on metal 1 (allowed side-area ratio 2,736), while the detailed route splits the net across layers "
    "(allowed ratio 400); OpenLane 2.3.10 has no antenna repair on the detailed route, so no parameter acts on it. P&amp;R "
    "stopped at 18 of 20 tool runs; the missing flow step is Phase 1 work (docs/DECISIONS.md, 2026-10-07). No derated "
    "signoff is recorded for any sync_fifo netlist, "
    "and the signed package was not modified."))

s.append(P("1.2 Limitations raised by the external review", h2))
s.append(P(
    "An external review of the Phase 0 work raised the limitations below. We accept each of them; the right-hand "
    "column gives the current status. The reviewer's verdict was: <i>the layouts are not commercially viable; the framework is "
    "viable as an early-stage infrastructure prototype.</i> This report is written to that verdict."))
sp_ = D["spi_master"]
rows = [["#", "Limitation (reviewer)", "Accepted", "Current status"],
        ["1", f"Scale: toy blocks ({TOT_INST:,} placed instances in total, {TOT_DIE_MM2:.3f} mm<super>2</super> of die; counter8 "
              f"{D['counter8']['instances']}, alu8 {D['alu8']['instances']} instances); flat, not hierarchical; no clock-domain "
              "crossings, no UPF power intent, no bus fabrics.", "Yes",
         "Unchanged in Phase 0. The first larger design (a RISC-V core) is Phase 1 work."],
        ["2", "Hold margins measured without OCV would not survive real derates.", "Yes",
         f"Flat +/-5% and +/-10% derates are now a permanent signoff check; +/-10% is a hard check. Hold stays positive at "
         f"+/-10% for every block measured (worst recorded {HOLD10_D} {sg(HOLD10)} ns; sync_fifo what-ifs at least "
         f"{sg(HOLD10_WI)} ns). Still no foundry OCV tables, and no jitter or supply-noise margin beyond the SDC clock "
         f"uncertainty of {D['counter8']['clock_uncertainty_ns']:.2f} ns."],
        ["3", f"spi_master clock tree: the clock-net max-fanout limit was relaxed to 20 ({sp_['clock_rule_allowed']} leaf clock "
              "buffers drive more than the SDC limit of 10).", "Yes",
         f"Stays flagged CONDITIONAL. Measured clock-tree skew {sp_['tree_skew_ns_max'] * 1e3:.0f} ps. A proper CTS fix is "
         "Phase 1 work."],
        ["4", "Power and IR are vector-less estimates.", "Yes",
         f"Static IR measured (at most {IRMAX:.2f} mV); electromigration not analysed. Simulation-based (VCD/SAIF) power and dynamic IR "
         "are Phase 1 work."],
        ["5", "No DFT (no scan insertion, no ATPG) and a legacy 130 nm node.", "Yes",
         "DFT scored 0 in the derived score; scan/ATPG is Phase 1 work. Phase 0 is restricted to open tools and the open "
         "SKY130 PDK by design."]]
s.append(KeepTogether([table(rows, [6, 66, 14, 90]),
P("Table 2. Limitations from the external review and their status. None of them is closed by this report.", cap)]))

s.append(P("2. Introduction", h1))
s.append(P(
    "The question Phase 0 asks is whether a team of AI agents can drive a complete open-source flow, from a written "
    "specification to a GDSII layout, while every pass/fail decision is made by a real tool run and never by a model. The "
    "chips are the test vehicle, not the product. A digital layout is released for manufacturing (\"tape-out\") only when a "
    "set of absolute checks pass: the layout obeys the foundry's geometric rules (DRC), the layout is the same circuit as the "
    "netlist (LVS), the circuit meets its clock at every process, voltage and temperature corner, including on-chip "
    "variation (static timing analysis), and the netlist is logically the same as the verified RTL (equivalence). Around "
    "these sit engineering judgments on power, power-grid resistance, manufacturability and test. This report gives the "
    "measured values on five small blocks, states which checks were run, and separates what is proven from what is "
    "estimated or not done. No silicon was made; the final release decision (gate G4) stays a human decision and was not "
    f"taken for fabrication. The derived checklist scores (Baseline A {GA['earned_A']:g}/{GA['weights_A']:g} = {GA['A']}%, "
    f"with partial credit dft = 0 and ir_em = 0.5; Baseline B {GA['earned_B']:g}/{GA['weights_B']:g} = {GA['B']}%) are "
    "bookkeeping figures of the framework, not a measure of how close the layouts are to a product."))

s.append(P("3. Method", h1))
s.append(P(
    "<b>Process and library.</b> SkyWater SKY130A (130 nm, 1.8 V core), standard-cell library sky130_fd_sc_hd. "
    "<b>Flow.</b> Specification and RTL are produced and verified by agents (simulation with Verilator/Icarus/cocotb, coverage, "
    "SymbiYosys properties, mutation testing). Synthesis (Yosys), floorplan, placement, clock-tree synthesis (TritonCTS), routing "
    "and stream-out run in OpenLane 2.3.10. Signoff checks are then re-run independently on the final streamed GDS: DRC with "
    "Magic and KLayout, LVS with Magic extraction + Netgen, antenna with OpenROAD, density with the PDK KLayout deck, 9-corner "
    "STA with OpenSTA on extracted parasitics (SPEF), repeated with flat +/-5% and +/-10% OCV derates (Section 1.1), power with OpenSTA report_power, static IR with OpenROAD PSM, and "
    "RTL-to-final-netlist equivalence with eqy or a Yosys LEC fallback. "
    "<b>Corners.</b> Three library corners (SS 100 &deg;C 1.60 V, TT 25 &deg;C 1.80 V, FF -40 &deg;C 1.95 V) x three RC "
    "extraction corners (min, nom, max) = 9 timing corners. "
    "<b>Integrity.</b> Each block's evidence package (tapeout/) holds the GDS, netlists, SDC, SPEF, reports and a reproduce.sh that "
    "re-runs the checks in a clean container; a SHA-256 manifest covers every file (Appendix A). Tool pass/fail decides each "
    "check; the agents never decide it."))

exec(open(f"{S}/sections_new.py").read())
s += sec_tools() + sec_teams()
s.append(P("4. Designs and implementation", h1))
rows = [["Block", "Function", "Clock", "Cells (synth)", "Synth area um<super>2</super>", "Die area um<super>2</super>",
         "Placed inst.", "Util.", "Wire length um", "Vias", "Nets"]]
fn = {"counter8": "8-bit up/down counter with load", "alu8": "8-bit ALU, 8 ops, flags", "sync_fifo": "synchronous FIFO",
      "uart": "UART TX/RX, prog. baud", "spi_master": "SPI master, prog. clock"}
for d in N:
    v = D[d]
    rows.append([d, fn[d], f"{1e3 / v['period_ns']:.0f} MHz ({v['period_ns']:.2f} ns)", v["synth_cells"], f1(v["synth_area_um2"]),
                 f1(v["die_area_um2"]), v["instances"], f"{v['utilization'] * 100:.1f}%", f"{v['wirelength_um']:,}",
                 f"{v['vias']:,}", v["nets"]])
s.append(KeepTogether([table(rows, [17, 27, 20, 13, 15, 16, 13, 11, 16, 13, 10]),
P("Table 6. Implementation summary. Placed instances include tap cells, timing buffers and hold buffers; utilization is "
           "placed standard-cell area over core area. Wire length and via count are from the detailed router.", cap)]))
s.append(KeepTogether([Image(f"{S}/fig_layouts.png", width=178 * mm, height=178 * mm * 792 / 3300),
P("Figure 1. Final layouts rendered from the signed GDSII files (li1 and met1-met5 shown; to scale per panel). The "
           "horizontal met1 rails are the standard-cell power rows; vertical met4 and horizontal met5 straps form the power grid.", cap)]))

s.append(P("5. Results", h1))
s.append(P("5.1 Physical verification", h2))
rows = [["Block", "DRC Magic", "DRC KLayout", "LVS (Netgen)", "Devices", "Antenna nets", "XOR (stream-out)", "PV result"]]
for d in N:
    v = D[d]
    rows.append([d, v["drc_magic"], v["drc_klayout"], v["lvs"], v["lvs_devices"], v["antenna_nets"], v["xor"], "PASS"])
s.append(KeepTogether([table(rows, [20, 17, 18, 38, 15, 18, 22, 17]),
P("Table 7. Physical verification on the final streamed GDS. Two DRC engines with the SKY130 open rule decks agree at 0 "
           "violations; LVS matches device-for-device and net-for-net.", cap)]))

s.append(P("5.2 Timing without derates", h2))
rows = [["Block", "Clock period ns", "Worst setup slack ns (corner)", "Setup slack TT ns", "Worst hold slack ns (corner)",
         "Corners met", "Clock-tree skew ns (worst)", "Slew / cap viol.", "Hold buffers"]]
for d in N:
    v = D[d]
    rows.append([d, f"{v['period_ns']:.3f}", f"+{v['setup_ws'][0]:.4f} ({v['setup_ws'][1]})", f"+{v['tt_setup']:.4f}",
                 f"+{v['hold_ws'][0]:.4f} ({v['hold_ws'][1]})", f"{v['corners_passed']}/{v['corners']}",
                 f"{v['tree_skew_ns_max']:.4f}", f"{v['slew_viol']} / {v['cap_viol']}", v["hold_buffers"]])
s.append(KeepTogether([table(rows, [17, 14, 30, 15, 30, 13, 17, 14, 13]),
P("Table 8. Post-route static timing with extracted parasitics at 9 corners, without OCV derates (OpenSTA, propagated "
           f"clocks, {D['counter8']['clock_uncertainty_ns']:.2f} ns clock uncertainty). Total negative slack is 0 at every corner "
           "for every block. The derated results, which decide the gate, are in Table 1.", cap)]))
s.append(P(
    "Setup is limited at the slow corner (SS 100 &deg;C 1.60 V, max RC) and hold at the fast corner (FF -40 &deg;C 1.95 V, min "
    "RC), as expected. The thinnest setup margin is sync_fifo at +0.243 ns (2.4% of its 10 ns period), on the combinational read "
    "path to rd_data; a +/-5% derate already makes it negative (Table 1), which is why sync_fifo fails the gate. The thinnest "
    "hold margins are 0.10-0.14 ns at FF (alu8: 0.42 ns); these nominal margins alone say little, because real on-chip "
    f"variation erodes them. Under the +/-10% derate they stay positive (worst {HOLD10_D} {sg(HOLD10)} ns, Table 1), but only "
    "against a flat estimate, not foundry OCV data. Maximum-fanout design rules: four blocks have no "
    "violator; spi_master has eight leaf clock buffers driving 11-17 flip-flops each, which exceeds the SDC data-net limit of 10 "
    "and passes only under a relaxed clock-tree rule of 20 (Section 5.6)."))

s.append(P("5.3 Power", h2))
rows = [["Block", "Total SS 100C 1.60V uW", "Total TT 25C 1.80V uW", "Total FF -40C 1.95V uW", "TT internal uW",
         "TT switching uW", "TT leakage nW", "SS leakage nW", "Energy / cycle TT pJ", "Power density TT W/cm<super>2</super>"]]
for d in N:
    v = D[d]; p = v["power"]; t = p["tt_025C_1v80"]
    rows.append([d, uW(p["ss_100C_1v60"]["total_w"]), uW(t["total_w"]), uW(p["ff_n40C_1v95"]["total_w"]), uW(t["internal_w"]),
                 uW(t["switching_w"]), f"{t['leakage_w'] * 1e9:.2f}", f"{p['ss_100C_1v60']['leakage_w'] * 1e9:.0f}",
                 f"{t['total_w'] * v['period_ns'] * 1e-9 * 1e12:.2f}", f"{t['total_w'] / (v['die_area_um2'] * 1e-8):.2f}"])
s.append(KeepTogether([table(rows, [17, 18, 18, 18, 16, 17, 15, 15, 17, 20]),
P("Table 9. Estimated power (OpenSTA report_power, vector-less, 20% switching activity on inputs, post-route netlist "
           "with parasitics). Energy per cycle = total power x clock period. Power density uses die area.", cap)]))
s.append(KeepTogether([Image(f"{S}/fig_power_ir.png", width=165 * mm, height=165 * mm * 792 / 2420),
P("Figure 2. Left: estimated total power per corner (log scale). Right: worst static IR drop on VPWR at TT against the "
           "90 mV (5% of 1.8 V) limit (log scale).", cap)]))
s.append(P(
    "Internal (cell short-circuit and internal node) power dominates at 60-74% of the total; switching power on interconnect is "
    "the rest. Leakage is negligible at 25 &deg;C (0.5-21 nW) but rises about three orders of magnitude at 100 &deg;C (e.g. "
    "spi_master 4.65 nW at TT to 4.4 uW at SS 100 &deg;C), which is the expected subthreshold-leakage temperature dependence. "
    "sync_fifo draws the most power (5.75 mW at TT) because its storage is built from flip-flops clocked at 100 MHz. These are "
    "estimates: no simulation activity file (VCD/SAIF) was used, so real power depends on the workload."))

s.append(P("5.4 Resistance: interconnect and power grid", h2))
s.append(P(
    "A chip has no single \"resistance\". Two resistances matter for signoff: (i) the resistance of the signal wires and vias, "
    "which with their capacitance sets wire delay (RC) and is read back from the layout as SPEF parasitics, and (ii) the "
    "resistance of the power-delivery network (PDN), which causes a static IR (current x resistance) drop between the supply "
    "pins and each cell. Table 10 gives both."))
rows = [["Block", "Total wire+via R, min RC (ohm)", "Total R, nom RC (ohm)", "Total R, max RC (ohm)", "Total net C, nom (pF)",
         "Highest-R net, nom (ohm, net)", "R segments (nom)", "Worst IR drop VPWR (mV)", "Avg IR drop (mV)",
         "Worst ground bounce VGND (mV)", "IR limit (mV)"]]
for d in N:
    v = D[d]; sp = v["spef"]
    rows.append([d, f"{sp['min']['total_wire_res_ohm']:,.0f}", f"{sp['nom']['total_wire_res_ohm']:,.0f}",
                 f"{sp['max']['total_wire_res_ohm']:,.0f}", f"{sp['nom']['total_net_cap_f'] * 1e12:.2f}",
                 f"{sp['nom']['max_net_res_ohm']:.0f} ({sp['nom']['max_net_res_net']})", f"{sp['nom']['res_segments']:,}",
                 f"{v['ir_worst_v'] * 1e3:.3f}", f"{v['ir_avg_v'] * 1e3:.3f}", f"{v['vgnd_bounce_v'] * 1e3:.3f}",
                 f"{v['ir_limit_v'] * 1e3:.0f}"])
s.append(KeepTogether([table(rows, [16, 17, 16, 16, 14, 25, 14, 15, 13, 17, 12]),
P("Table 10. Interconnect resistance and capacitance summed over all routed nets from the signed SPEF files (OpenROAD "
           "extraction, three RC corners), and static PDN IR drop at TT (OpenROAD PSM).", cap)]))
s.append(P(
    "Total routed resistance scales with wire length (2.6-3.6 ohm per um of routed wire at nominal RC across the five blocks), "
    "and the max-RC corner is 2.2-2.3x nominal and 4.9-5.8x min-RC, which is why the slow-corner timing uses max RC. The "
    "highest-resistance single net is 232-561 ohm; in spi_master it is a leaf clock net (clknet_3_5__leaf_clk). The worst static "
    "IR drop is 0.05-1.37 mV, at most about 1.5% of the 90 mV budget, so the default SKY130 power grid is heavily over-provisioned for "
    "blocks of this size. Electromigration (current density in wires and vias) and dynamic (switching-transient) IR drop were "
    "<b>not analysed</b>; they are among the gaps listed in Section 7."))

rows = [["Block", "High", "Medium", "Low", "Top items"]]
for d in N:
    v = D[d]
    top = "; ".join(f"{i[0]} ({i[1]}): {i[2]}" for i in v["dfm_items"][:3])
    rows.append([d, v["dfm"]["high"], v["dfm"]["medium"], v["dfm"]["low"], top])
s.append(KeepTogether([P("5.5 Manufacturability (DFM)", h2), table(rows, [17, 10, 12, 10, 121]),
P("Table 11. DFM scorecard from KLayout geometry analysis of the final GDS (near-minimum spacing, line ends, via "
           "redundancy and density). No high-severity item in any block. All vias are single-cut.", cap)]))

s.append(P("5.6 Gate decision", h2))
KEYS = [("DRC", "DRC"), ("LVS", "LVS"), ("Antenna", "Antenna"), ("Timing met, all corners (setup", "Timing, 9 corners"),
        ("OCV", "Timing, +/-10% derate"), ("Equivalence", "Equivalence"), ("human edits", "No human edits")]
rows = [["Block"] + [k[1] for k in KEYS] + ["Hard checks (current)", "Derived score A / B"]]
for d in N:
    g = D[d]["gate_now"]
    st = [next(stt for c, stt in g["items"] if k in c) for k, _ in KEYS]
    verdict = f"<b>{g['verdict']}</b> ({g['passed']}/{g['of']})"
    rows.append([d] + st + [verdict, f"{g['A']}% / {g['B']}%"])
s.append(KeepTogether([table(rows, [17, 13, 13, 15, 21, 21, 18, 17, 21, 20]),
P(f"Table 12. Phase 0 hard checks, current state (each run's reports/tapeout_readiness.json, re-scored from recorded "
  f"results). The percentages are derived figures, not pass requirements: Baseline A = open-shuttle checklist, "
  f"{GA['earned_A']:g}/{GA['weights_A']:g} points; Baseline B = full production checklist, {GA['earned_B']:g}/{GA['weights_B']:g} "
  "points; partial credit dft = 0 and ir_em = 0.5 (static IR only). sync_fifo's derated check was not run in its signed "
  "run; the what-if measurement fails (Table 1).", cap)]))
s.append(P(
    f"The program-level Phase 0 gate (PHASE_GATES.md) is <b>{SF['gate_now']['phase0_gate']}</b>: on 2026-10-07 the CEO added "
    "timing at all corners with a flat +/-10% derate to the gate. counter8, alu8 and uart pass all six hard checks; spi_master "
    "passes them only under the approved clock-net fanout limit of 20 and would fail a flat SDC limit of 10, so it stays "
    "CONDITIONAL; sync_fifo is FAIL (Section 1.1). \"No human edits to artifacts\" is NOT CHECKED (no automated "
    "edit-detection yet). EM, dynamic IR, DFT scan/ATPG and artifact-provenance checking are deferred to Phase 1. No check "
    "was waived; the one relaxed rule is spi_master's clock-net fanout limit, which is recorded as a decision and printed as a "
    "condition on its result. The signed packages (tapeout/) of 2026-10-06 were not modified and still carry the earlier "
    "five-check verdict, under which sync_fifo had passed."))

s += sec_failures()
s += sec_compare()
s.append(P("7. What a production tape-out additionally requires: gaps of this proof-of-concept", h1))
s.append(P(
    "Table 18 lists the checks a production tape-out on a foundry process normally requires and where this proof-of-concept "
    "stands on each. It is a list of gaps, not a checklist this work is about to complete: several items (foundry-certified "
    "decks, reliability, silicon qualification) are outside what an open-PDK proof-of-concept can do at all. \"Done\" means a "
    "real tool ran and passed on these blocks; \"Partial\" means a reduced form ran; \"Not done\" means it is open work; "
    "\"n/a\" means it does not apply to these blocks. Typical pass criteria are industry practice; the exact limits come from "
    "the foundry PDK, the product specification and the qualification standard."))
C = [["Area", "Check", "Typical pass criterion", "This proof-of-concept (Phase 0)"],
     ["Scale", "Hierarchical chip integration (bus fabrics, several clock and power domains)", "Integrated chip-level signoff", "Not done (small flat single-clock blocks; Table 2)"],
     ["Function", "RTL simulation regression", "100% of tests pass, several seeds, two simulators", "Done"],
     ["Function", "Code + functional coverage", "Line >= 95%, toggle >= 90%, all functional bins hit (project targets)", "Done"],
     ["Function", "Formal property checking", "Properties proven (unbounded) or bounded depth documented; no vacuity", "Done"],
     ["Function", "Mutation / fault-injection of the testbench", "Injected-bug detection >= 85% (project target)", "Done for 4 blocks (counter8, sync_fifo 20/20; uart 19/20; spi_master 17/20); alu8 not in the M0.6 record"],
     ["Function", "Equivalence RTL vs. netlist (LEC)", "All compare points proven equivalent", "Done"],
     ["Function", "Gate-level simulation with timing", "Tests pass on final netlist; SDF-annotated GLS at corners", "Partial (functional GLS on final netlist, no SDF timing)"],
     ["Function", "CDC / RDC analysis", "All crossings synchronized and reviewed", "Not done (single-clock blocks)"],
     ["Layout", "DRC (foundry deck)", "0 violations on the foundry-certified deck", "Partial (open decks: 0)"],
     ["Layout", "LVS", "Full match, no unmatched devices/nets/pins", "Done (open deck)"],
     ["Layout", "ERC (shorts, floating gates, well taps)", "0 errors", "Partial (via LVS/DRC)"],
     ["Layout", "Antenna", "0 violating nets", "Done for the signed layouts (sync_fifo change #2 not closed)"],
     ["Layout", "Density / CMP fill", "Every layer within min/max density windows", "Done (PDK deck)"],
     ["Layout", "Litho / DFM hotspots", "No high-severity hotspot; recommended rules met", "Partial (scorecard)"],
     ["Layout", "Seal ring, pad ring, I/O cells", "Present and DRC/LVS clean at chip level", "n/a (blocks, not a chip)"],
     ["Timing", "Setup / hold at all corners", "WNS >= 0, TNS = 0 at every PVT/RC corner", "Done without derates (9 corners)"],
     ["Timing", "On-chip variation (OCV/AOCV/POCV)", "Met with foundry derates", "Partial: flat +/-5% / +/-10% estimate (no foundry tables); 4 of 5 blocks meet +/-10%, sync_fifo fails (Table 1)"],
     ["Timing", "Clock jitter and supply-noise margins", "Budgeted from the clock source and PDN analysis", f"Not done beyond the SDC clock uncertainty of {D['counter8']['clock_uncertainty_ns']:.2f} ns"],
     ["Timing", "Signal integrity / crosstalk delay and noise", "No glitch failures; SI-aware timing met", "Not done"],
     ["Timing", "Design-rule violations (slew, cap, fanout)", "0 violations", "Done (spi_master conditional: clock-net fanout limit 20)"],
     ["Timing", "Clock skew / latency / duty cycle", "Within clock budget", "Done (skew <= 0.062 ns)"],
     ["Power", "Power estimate vs. budget", "Below budget, vector-based (VCD/SAIF)", "Partial (vector-less estimate)"],
     ["Power", "Static IR drop", "Worst drop <= 5% (often 2-3%) of supply", f"Done (<= {IRMAX:.2f} mV)"],
     ["Power", "Dynamic IR drop / voltage droop", "Droop within budget during worst switching", "Not done (Phase 1)"],
     ["Power", "Electromigration (power + signal, DC/AC)", "Current density below foundry limits at max temperature", "Not done (Phase 1)"],
     ["Power", "Power intent (UPF/CPF), level shifters", "Clean low-power checks", "n/a (single domain)"],
     ["Reliability", "ESD (HBM/CDM) and latch-up", "Meets JEDEC/ESDA classes, e.g. HBM 2 kV", "Not done (chip-level)"],
     ["Reliability", "Aging: HCI, NBTI, TDDB", "Timing met at end of life (e.g. 10 years)", "Not done"],
     ["Reliability", "Self-heating / thermal", "Junction temperature within limits", "Not done"],
     ["Test", "Scan insertion + ATPG", "Stuck-at coverage >= 95% (often >= 98%), transition faults", "Not done (Phase 1; dft scored 0)"],
     ["Test", "Memory BIST, IDDQ, boundary scan", "As required by product", "n/a / not done"],
     ["Signoff", "Foundry-certified signoff (Calibre-class)", "Foundry tape-out checklist accepted", "Not done"],
     ["Signoff", "Reproducibility + data integrity", "Rebuild from sources matches; files hashed", "Done (clean container)"],
     ["Signoff", "Artifact provenance (no human edits)", "Every artifact traceable to a tool run", "Not checked (Phase 1)"],
     ["Silicon", "Wafer sort, characterization (shmoo), yield", "Functional at spec V/F/T; yield target met", "Not applicable (no silicon; G4 is a human decision)"],
     ["Silicon", "Qualification (e.g. JEDEC JESD47: HTOL, ESD, LU)", "Passes stress tests on sample lots", "Not applicable (no silicon)"]]
s.append(KeepTogether([table(C, [19, 50, 60, 47]),
P("Table 18. Checks a production tape-out additionally requires, and the status of this proof-of-concept. Project targets "
           "(coverage, mutation) are S2S's own; other criteria are typical industry values.", cap)]))

s.append(P("8. Discussion and limitations", h1))
s.append(P(
    "<b>What the proof-of-concept shows.</b> Agents drove the complete open-source flow from specification to GDSII on five "
    "blocks, and every pass/fail was decided by a tool: two DRC engines, LVS, an independent STA that must agree with the "
    "flow's own STA, and formal equivalence on the final netlist. The framework's own checks found problems that the flow "
    "reported as clean (an unpropagated clock that hid a fanout violation in uart, Table 13), and when the gate was tightened "
    "with derated timing it recorded its own block failure (sync_fifo) instead of loosening a constraint. Every number above "
    "is reproducible from the evidence packages and logs. "
    "<b>What it does not show.</b> It does not show that these layouts, or larger ones, are fit for a product (Table 2): the "
    "blocks are small and flat; timing with OCV uses a flat estimate, not foundry data; power is vector-less at 20% input "
    "activity and IR drop is static only; EM, dynamic IR, SI/crosstalk, reliability, DFT test coverage and foundry-certified "
    "decks were not run; and no silicon exists, so nothing here proves working parts. "
    "<b>Margins and conditions.</b> sync_fifo's +0.243 ns nominal setup margin did not survive a 5% derate. The nominal hold "
    f"margins (0.10-0.14 ns at FF in four blocks) stay positive at +/-10% (worst {HOLD10_D} {sg(HOLD10)} ns), but only against "
    "a flat derate. Input and output delays in the SDC are default assumptions (30% of the period) pending a real system "
    "specification, and the slack figures depend on them. spi_master's clock-tree fanout (11-17 per leaf buffer) is accepted "
    "only under a relaxed clock-net rule; the installed TritonCTS builds this tree with an average of 13 sinks per leaf "
    "buffer, and no in-range parameter reduced it."))

s.append(P("9. Conclusion and next steps", h1))
s.append(P(
    "As a framework proof-of-concept, Phase 0 shows that an agent-driven, tool-checked open flow can take small blocks from "
    "specification to GDSII and report its own failures. Without derates, all five signed layouts have 0 DRC violations "
    "(Magic and KLayout), full LVS match, 0 antenna violations and positive setup and hold slack at nine corners, at "
    f"{min(PTT) * 1e6:.1f} uW-{max(PTT) * 1e3:.2f} mW estimated power and at most {IRMAX:.2f} mV static IR drop. With the +/-10% "
    "derate as a hard check, counter8, alu8 and uart pass; spi_master is CONDITIONAL; sync_fifo is FAIL (timing fixed by a "
    "design change, physical cleanup not closed within budget). The Phase 0 gate is re-opened. The Phase 1 queue is: a "
    "RISC-V core, DFT scan insertion and ATPG with measured fault coverage, dynamic IR and electromigration analysis, "
    "simulation-based power, and a proper CTS fix for spi_master; the artifact provenance check is also deferred to Phase 1."))

REFS = [
    "SkyWater Open Source PDK documentation, foundry-provided libraries (sky130_fd_sc_hd site, density). https://skywater-pdk.readthedocs.io/en/main/contents/libraries/foundry-provided.html",
    "SkyWater PDK, device details (metal sheet resistance). https://skywater-pdk.readthedocs.io/en/main/rules/device-details.html",
    "SkyWater PDK, periphery rules (minimum widths). https://skywater-pdk.readthedocs.io/en/main/rules/periphery.html",
    "SkyWater PDK, resistance-values table (contact/via resistance). https://foss-eda-tools.googlesource.com/skywater-pdk/+/b844d2f0815ee53ec010f926ca7b678d9f919527%5E%21",
    "sky130_fd_sc_hd liberty tt_025C_1v80 (cell area, leakage), open_pdks commit 0fe599b2, as installed in the s2s-eda image.",
    "A. Ajami, K. Banerjee et al., IR-drop analysis, ISQED 2003. https://web.ece.ucsb.edu/Faculty/Banerjee/pubs/ISQED_IRDrop_2003.pdf",
    "CAST Inc., H16550S UART IP core brief. https://www.cast-inc.com/pdfs/cast_h16550s-brief-asic.pdf",
    "CAST Inc., SPI-MS SPI master/slave IP. https://cast-inc.com/interfaces/serial-communications/spi-ms",
    "SPI core with APB interface, Silterra 0.18 um (UiTM repository). https://ir.uitm.edu.my/id/eprint/52072",
    "Texas Instruments, TL16C550D asynchronous communications element, datasheet. https://www.ti.com/lit/ds/symlink/tl16c550d.pdf",
    "UART on SKY130 with Yosys + OpenROAD (open-source project). https://github.com/raghunandanr487-collab/uart_on_openroad",
    "Tiny Tapeout FAQ and clock specification. https://tinytapeout.com/faq/ ; https://www.tinytapeout.com/specs/clock/",
    "Efabless Caravel harness documentation (user area). https://caravel-harness.readthedocs.io/",
    "ExperiarCore SDC, Efabless SKY130 MPW-6 shuttle. https://foss-eda-tools.googlesource.com/third_party/shuttle/sky130/mpw-006/slot-032/+/13a164dc6c63b6a005987b3b3c3b982e518f4302/sdc/ExperiarCore.sdc",
    "Siemens EDA, test coverage targets, DVCon India 2025. https://dvcon-proceedings.org/wp-content/uploads/P1-DVConIndia2025_Final_Paper_0782.pdf",
    "OpenLane 2 (2.3.10), OpenROAD, OpenSTA, Magic, KLayout, Netgen, Yosys, SymbiYosys, Verilator, Icarus Verilog, cocotb: versions as listed in Table 3 and each package's versions.lock.",
]
s.append(P("References", h1))
for i, r in enumerate(REFS, 1):
    s.append(P(f"[{i}] {r}", small))
s.append(P("Appendix A. Data and reproducibility", h1))
rows = [["Block", "Run", "P&amp;R iteration", "GDS size (bytes)", "GDS SHA-256"]]
for d in N:
    v = D[d]
    rows.append([d, v["run"], v["iteration"], f"{v['gds_bytes']:,}", v["gds_sha256"]])
s.append(KeepTogether([table(rows, [17, 50, 15, 18, 76]),
P("Table A1. Signed layouts. Each package (docs/milestones/m0.7-evidence/&lt;block&gt;/&lt;run&gt;/tapeout/) holds "
           "MANIFEST.sha256 over every file and reproduce.sh, which re-runs DRC, LVS and the checks in a network-isolated "
           "container. Tool versions: OpenLane 2.3.10, OpenSTA 2.6.0; full versions in each package's versions.lock.", cap)]))
s.append(P(
    "<b>Source of each figure.</b> Implementation, routing, DRV and PDN counts: OpenLane final/metrics.json of the iteration "
    "whose GDS hash equals the packaged GDS. Timing: reports/sta_signoff.json (S2S OpenSTA, 9 corners). Power: "
    "reports/power_report.json. IR: reports/ir_report.json. Physical verification: reports/pv_signoff.json. Resistance and "
    "capacitance: sums over the packaged tapeout/spef/{min,nom,max}/*.spef. DFM: reports/dfm_scorecard.json. Derated timing "
    "(Table 1, recorded rows): reports/sta_tool.json key \"derated\". sync_fifo what-if rows: OpenSTA logs (line \"WS\" or "
    "\"S2S_WS\", in seconds) and their .tcl scripts in var/artifacts/scratch_ocv/{sync_fifo, sync_fifo_fix_it3, "
    "sync_fifo_fix2_it3}. sync_fifo change #2 P&amp;R facts: reports/pnr_iteration_{3,4}.json and pnr/runs/it{3,4}/final/"
    "metrics.json of run_01M4AFNT5QK68FGT27TVRBYWZN. Current hard checks (Table 12): each run's reports/tapeout_readiness.json; "
    "the signed packages' copies (tapeout/reports/) keep the 2026-10-06 five-check verdict.", small))


def footer(c, doc):
    c.saveState(); c.setFont("Times-Roman", 8)
    c.drawString(18 * mm, 10 * mm, "S2S Phase 0 - framework proof-of-concept on open SKY130 - pre-silicon, no silicon made")
    c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"{doc.page}"); c.restoreState()


merged = []
for f in s:  # a heading directly before a kept-together table goes into that block
    if isinstance(f, KeepTogether) and merged and isinstance(merged[-1], Paragraph) and merged[-1].style.name in ("h1", "h2"):
        f = KeepTogether([merged.pop()] + list(f._content))
    merged.append(f)
s = merged
doc = SimpleDocTemplate(OUT, pagesize=A4, leftMargin=17 * mm, rightMargin=17 * mm, topMargin=16 * mm, bottomMargin=17 * mm,
                        title="An AI Agent Framework for Open-Source RTL-to-GDSII on SKY130: Phase 0 Proof-of-Concept",
                        author="S2S project, Goutham Labs", subject="Phase 0 framework proof-of-concept: derated timing, limitations, signoff checks")
doc.build(s, onFirstPage=footer, onLaterPages=footer)
print("built", OUT)
