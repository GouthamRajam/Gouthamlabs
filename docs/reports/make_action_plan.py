"""Builds docs/reports/S2S_action_plan_2026-10-05.pdf (full status, success and failure report)."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
                                TableStyle)

OUT = Path(__file__).with_name("S2S_action_plan_2026-10-05.pdf")
ss = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=ss["Heading1"], fontSize=16, spaceBefore=10, spaceAfter=6,
                    textColor=colors.HexColor("#1F3A5F"))
H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontSize=12.5, spaceBefore=8, spaceAfter=4,
                    textColor=colors.HexColor("#1F3A5F"))
H3 = ParagraphStyle("H3", parent=ss["Heading3"], fontSize=10.5, spaceBefore=6, spaceAfter=2)
B = ParagraphStyle("B", parent=ss["BodyText"], fontSize=9.2, leading=12.2, alignment=TA_LEFT, spaceAfter=4)
SM = ParagraphStyle("SM", parent=B, fontSize=8.2, leading=10.4, spaceAfter=0)
BUL = ParagraphStyle("BUL", parent=B, leftIndent=12, bulletIndent=2, spaceAfter=2)
TITLE = ParagraphStyle("T", parent=ss["Title"], fontSize=22, textColor=colors.HexColor("#1F3A5F"))
BOX = ParagraphStyle("BOX", parent=B, backColor=colors.HexColor("#FFF4E5"), borderColor=colors.HexColor("#E0A040"),
                     borderWidth=0.6, borderPadding=5, spaceBefore=4, spaceAfter=8)
OKBOX = ParagraphStyle("OKBOX", parent=BOX, backColor=colors.HexColor("#EAF6EC"), borderColor=colors.HexColor("#5AA469"))

story = []


def h1(t): story.append(Paragraph(t, H1))
def h2(t): story.append(Paragraph(t, H2))
def h3(t): story.append(Paragraph(t, H3))
def p(t, st=B): story.append(Paragraph(t, st))
def bullets(items):
    for it in items:
        story.append(Paragraph(it, BUL, bulletText="-"))
def box(t, ok=False): story.append(Paragraph(t, OKBOX if ok else BOX))


def table(rows, widths, head=True, zebra=True):
    data = [[Paragraph(str(c), SM) for c in r] for r in rows]
    t = Table(data, colWidths=[w * mm for w in widths], repeatRows=1 if head else 0)
    st = [("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B0B7C3")),
          ("VALIGN", (0, 0), (-1, -1), "TOP"),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 3),
          ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
    if head:
        st.append(("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#DCE4EF")))
    if zebra:
        for i in range(1 if head else 0, len(rows)):
            if i % 2 == 0:
                st.append(("BACKGROUND", (0, i), (-1, i), colors.HexColor("#F5F7FA")))
    t.setStyle(TableStyle(st))
    story.append(t)
    story.append(Spacer(1, 6))




def link(url, text=None):
    return f"<link href='{url}' color='blue'><u>{text or url}</u></link>"


# ---------------------------------------------------------------- title
story.append(Spacer(1, 22 * mm))
story.append(Paragraph("S2S - What To Do Now", TITLE))
story.append(Paragraph("The three outside suggestions, checked against published methods and the real installed tools", H2))
p("5 October 2026. Inputs: (1) OpenAI 'Production Chip Engineering Doctrine', (2) Gemini 'Design Bottleneck "
  "Resolution Plan', (3) Claude 'S2S - What To Do Now' (PDF), and the S2S status report of the same day. "
  "Everything marked <b>[verified]</b> was checked today in this environment (OpenLane 2.3.10, OpenROAD and Yosys "
  "in the s2s-eda image) or by a real tool run; everything marked <b>[source]</b> links to published material.")
box("<b>The plan in five lines.</b> (1) Freeze new runs on the 3 blocked designs until you make 5 decisions (Part 4) - "
    "more compute on the same method will not unblock them. (2) Close the 3 blockers with the field's standard "
    "methods, each one a recorded methodology decision, never a waiver. (3) Give S2S a permanent engineering memory "
    "(knowledge store + regression tests) and backfill today's lessons. (4) Move to a stable, bigger machine and "
    "qualify the S2S infrastructure itself. (5) Only then: one harder design (small RISC-V core with a clock-domain "
    "crossing) to prove the system got better because it remembered.")

# ---------------------------------------------------------------- part 1
h1("Part 1 - Verdict on the three suggestions")
p("All three agree on the big picture, and I agree with them: the blockers are known problems with known methods; "
  "the system must remember what it learns; SKY130 proves the method, not commercial readiness. They differ in "
  "precision. Where a suggestion is wrong or unsafe it is marked below - do not adopt those parts.")
table([["Point", "OpenAI", "Gemini", "Claude", "My assessment (with evidence)"],
       ["Engineering memory / lessons as permanent records + regression tests", "Strong (sections 4-11, 27-29, 50-53)",
        "Partial (caches, checkpoints)", "Strong (#4)", "AGREE - highest-leverage software change. Build it small first (Part 3B)."],
       ["Exempt clock nets from set_max_fanout", "Policy decision (58)", "Yes", "'In most real flows the answer is no'",
        "AGREE WITH A CORRECTION: commercial CTS DOES limit clock fanout (Innovus CCOpt max_fanout, typical 8-20 per "
        "buffer) but as a CTS rule the CTS engine honours. OpenROAD CTS has no fanout limit at all, and OpenLane 2.3.10 "
        "has no max-fanout checker (it only reports the count) [verified]. So: move the clock limit from the generic "
        "SDC check to an explicit clock-tree rule (Part 2.1)."],
       ["Add upper-tree CTS knobs", "Yes (11)", "Yes", "Yes (Option A)",
        "AGREE. Installed OpenLane exposes CTS_SINK_CLUSTERING_MAX_DIAMETER, CTS_DISTANCE_BETWEEN_BUFFERS, "
        "CTS_CLK_MAX_WIRE_LENGTH, CTS_CLK_BUFFERS, CTS_MAX_CAP/SLEW [verified]. -sink_clustering_levels and "
        "-balance_levels exist in OpenROAD but are NOT passed by OpenLane 2.3.10 [verified]."],
       ["Exclude equivalent mutants from the score", "Only if proven (13)", "Yes, 14/(20-k)", "Only if proven",
        "AGREE: prove, then exclude; undecided stays a miss. A 2026 RTL study (GateTruth) shows exclusion based on "
        "bounded checks inflates scores [source]."],
       ["Stop generating missing_reset mutants for reloaded registers", "-", "YES (Gemini)", "Forbidden",
        "REJECT. It hides a whole bug class and decides equivalence by assumption. Claude's PDF is right."],
       ["Scale down clk_div in the formal harness", "Only as explicit decision", "YES (Gemini)", "Only with a soundness argument",
        "ONLY WITH A WRITTEN ARGUMENT that the property does not depend on the divider width, recorded as a decision."],
       ["Per-property PDR default", "-", "Yes", "Yes", "ALREADY DONE (commits 26ded26, b18ad24); 9/12 spi_master properties proven."],
       ["Gemini 'Phase 2' commands (python -m ... --design uart --filter-equivalent)", "-", "Given", "-",
        "DO NOT EXIST. Those modules have no such CLI; they are called by the agents. Treat them as intent only."],
       ["Bigger, stable machine", "Infra qualification (22-25)", "Disk hygiene", "Yes (#5)",
        "AGREE, with a correction to Claude: compute does NOT unblock sync_fifo (policy) or the spi_master SCK "
        "properties (method). It does stop losing work (about 6 container restarts, 3 lost uart runs) and lets long proofs finish."],
       ["DFT, I/O ring, package, silicon validation, production flow", "Sections 35-39, 60", "-", "'behind the phase gates'",
        "AGREE AS ROADMAP ONLY. CLAUDE.md forbids building beyond the current phase; record them, do not build now."]],
      [33, 25, 22, 22, 68])

# ---------------------------------------------------------------- part 2
h1("Part 2 - How engineers actually solve each blocker")

h2("2.1 sync_fifo - clock-tree fanout")
p("<b>Facts.</b> The 3 violating cells are level-3 clock-tree buffers (clkbuf_3_*__f_clk) driving 11-12 loads "
  "against the SDC's set_max_fanout 10. OpenLane's own SDC applies set_max_fanout to the whole design including "
  "clock nets, STA reports it, but no OpenLane checker fails on it [verified: scripts/base.sdc line 24; "
  "steps/checker.py has no fanout checker]. OpenROAD's CTS (TritonCTS) has no max-fanout option; its "
  "controls are clustering size/diameter/levels, buffer distance, branching distance, buffer list, balance levels "
  "[verified: 'help clock_tree_synthesis' in the installed OpenROAD; " + link("https://openroad.readthedocs.io/en/latest/main/src/cts/README.html", "OpenROAD CTS docs") + "].")
p("<b>How the industry does it.</b> Clock trees are governed by CTS design rules - max transition (slew), max "
  "capacitance, max fanout per clock buffer, skew and insertion delay - which the CTS engine itself honours while "
  "building the tree (Innovus: set_ccopt_property max_fanout; typical per-buffer limits 8-20) [source: "
  + link("https://teamvlsi.com/2021/06/clock-tree-constraints-in-vlsi-ccopt-file-in-physical-design-cts-constraints.html", "TeamVLSI CTS constraints") + ", "
  + link("https://ecrionix.org/physical-design/cts/", "ecrionix CTS guide") + ", "
  + link("https://www.edaboard.com/threads/how-do-we-set-max-fanout-for-clock-nets.394774/", "edaboard thread") + "]. "
  "The generic data-path max_fanout is not how clock fanout is controlled, and resizers do not repair clock nets.")
h3("Recommended method (decision D1)")
bullets(["<b>Step 1 - try the tree-shape knobs first</b> (no policy change): add CTS_SINK_CLUSTERING_MAX_DIAMETER, "
         "CTS_DISTANCE_BETWEEN_BUFFERS and CTS_CLK_MAX_WIRE_LENGTH to config/pnr_ranges.yaml with ranges, and make "
         "Orion diagnose the tree level of each violation before picking a knob (which level, which knob controls it, "
         "expected direction). Smaller diameter / shorter buffer distance adds intermediate buffers, which is the "
         "mechanism that lowers upper-level fanout. Run as a small, recorded experiment set (3-4 runs).",
         "<b>Step 2 - if Step 1 cannot reach 10</b>: replace 'clock nets checked by the data-path set_max_fanout' "
         "with an explicit <b>clock-tree design rule</b>: clock buffer fanout limit (choose a number, e.g. 16, inside "
         "the published 8-20 band), clock slew and capacitance limits, skew target, all checked on the clock network "
         "by S2S's own checker; data nets keep max_fanout 10 unchanged. This is a methodology change (D1), recorded "
         "with the evidence above - not a waiver, because the clock tree gets its own, explicit limit.",
         "<b>Step 3 - optional, later</b>: pass -sink_clustering_levels / -balance_levels to OpenROAD through a custom "
         "OpenLane step (not available in 2.3.10 config) if Step 1 shows the level count is the limiting factor."])

h2("2.2 uart - mutants no test can catch")
p("<b>Facts.</b> 14/20 caught, identical 7 times; the same 6 survivors (3 removed resets, 1 inverted reset value, "
  "2 constant changes). The bounded screen (25 steps) cannot see one UART frame (about 160 clock cycles at the "
  "smallest divisor) and labels all 6 'unknown'. My unbounded PDR equivalence proof timed out on 4 of 4 tried "
  "(30 minutes each) [verified] - the 16-bit baud divider makes the miter as deep as spi_master's SCK problem.")
p("<b>How the field does it.</b> Equivalent mutants are the oldest known mutation-testing problem; equivalence is "
  "undecidable in general, so tools use sound approximations: Trivial Compiler Equivalence (identical optimised "
  "output means equivalent), and for hardware, sequential equivalence checking. Score = killed / (generated - proven "
  "equivalent); undecided mutants stay in the denominator [source: Papadakis et al. TCE, ICSE 2015; "
  + link("https://arxiv.org/pdf/2608.12635", "GateTruth 2026 (RTL)") + ", "
  + link("https://stryker-mutator.io/docs/mutation-testing-elements/equivalent-mutants/", "Stryker on equivalent mutants") + "].")
h3("Recommended method (decision D2)")
bullets(["<b>Rule</b>: prove-then-exclude. A mutant leaves the denominator only with an unbounded equivalence proof "
         "(PASS from a complete engine, with the proof log attached). Undecided stays missed. Recorded as a "
         "methodology change.",
         "<b>Make the proof tractable</b> (the actual engineering work): (a) <i>register-correspondence SEC</i> - match "
         "every register by name except the mutated one and prove with induction (Yosys equiv_make/equiv_induct at "
         "higher -seq); this is how commercial SEC handles large counters; (b) <i>reset-rooted proof</i> - start both "
         "designs from reset, not from all-zero, so 'missing reset' is judged on reachable states; (c) <i>cheap "
         "killer first</i> - a deep bounded search for a distinguishing input (e.g. 2-3 frames at small baud divisors); "
         "if found, the mutant is killable and the counterexample is a ready-made test for Theo.",
         "<b>Never</b>: stop generating missing_reset mutants, or exclude a mutant because it 'looks reloaded'."])

h2("2.3 spi_master - formal proofs on a deep clock divider")
p("<b>Facts.</b> k-induction cannot close; per-property PDR proves 9/12 in about 1 second each, with negative controls "
  "failing correctly [verified]. The 3 SCK-timing properties do not close: with port-only properties, nothing ties "
  "them to the hidden divider counter (up to 65 535 cycles).")
p("<b>How engineers do it.</b> (1) Unbounded engines (IC3/PDR) - already adopted. (2) <b>Helper invariants</b> "
  "relating the property to internal state - the standard way to make a property inductive (practitioners routinely "
  "add tens of lemmas) [source: " + link("https://zipcpu.com/blog/2018/03/10/induction-exercise.html", "ZipCPU induction exercise") + ", "
  + link("https://zipcpu.com/tutorial/class-verilog.pdf", "ZipCPU formal tutorial") + "]. (3) <b>Counter abstraction</b> - "
  "merge non-special counter values into one state; patented commercial technique for counters [source: US 7418678, US 9665682]. "
  "(4) Prove a small divider width and generalise with an argument, or (5) accept a bounded proof from reset.")
h3("Recommended method (decision D3)")
bullets(["Keep per-property PDR as the default (done).",
         "For the 3 SCK properties choose one: <b>(a)</b> allow a narrowly scoped class of white-box helper "
         "invariants for timing properties, written by Euclid, reviewed, kept separate from the port-level "
         "properties - this changes the independence rule for one property class; <b>(b)</b> counter abstraction "
         "with a written soundness argument; <b>(c)</b> record them as 'bounded from reset to depth N' (REQ-025's "
         "depth 400 needs hours; feasible on a bigger machine) and do not count them. spi_master already has 9 "
         "unbounded proofs, so the pass rule (>= 3) does not depend on this choice."])

# ---------------------------------------------------------------- part 3
story.append(PageBreak())
h1("Part 3 - The plan, in order")
h2("3A. Close Phase 0 honestly (after your decisions D1-D3)")
table([["Step", "Work", "Done when"],
       ["A1", "sync_fifo: add 3 CTS tree-shape knobs + level diagnosis in Orion; 3-4 recorded experiments", "Clean route, or evidence that the knobs cannot reach 10"],
       ["A2", "sync_fifo (if A1 fails and D1 = clock rule): explicit clock-tree rule checker; data nets keep 10", "Signoff passes with the new rule recorded; GDSII"],
       ["A3", "uart: register-correspondence + reset-rooted SEC for the 6 survivors; deep bounded killer search first", "Each survivor is PROVEN equivalent, PROVEN killable (with a counterexample) or stays undecided"],
       ["A4", "uart: prove-then-exclude scoring (D2); Theo gets counterexamples for any killable survivor", ">= 85% over killable mutants, with proofs attached, or a reported gap"],
       ["A5", "spi_master: finish the running verification (9 PDR proofs expected); apply D3 to the SCK properties", "G2, then M0.7 automatically"],
       ["A6", "Each finished design: evidence package, readiness report, M0.7.md", "Committed and reproducible"]],
      [12, 98, 60])
h2("3B. Give S2S a memory (start now, small)")
bullets(["<b>knowledge/</b> store (YAML in git + DB table): failures, lessons, tool_quirks, approved_methods, "
         "forbidden_methods, experiments (with IDs such as PNR-SYNCFIFO-0009), equivalent_mutants, formal_patterns.",
         "Each lesson: symptom, root cause, why earlier attempts failed, the rule for next time, a regression test. "
         "Example: <i>CTS-001 - identify the clock-tree level of a fanout violation before choosing a knob; smaller leaf "
         "clusters raise upper-level fanout (sync_fifo it. 9)</i>.",
         "Agents receive the relevant lessons in their prompt before acting (Orion, Euclid, Myra, Theo, Dex), and "
         "write new ones when a failure is closed. Orion must check the experiment ledger before repeating a setting.",
         "Backfill today's ~15 lessons (all in DECISIONS.md and the status report). Invalid experiments are recorded "
         "as invalid and never used as evidence."])
h2("3C. Infrastructure qualification")
bullets(["<b>Machine</b>: 16-32 cores, persistent disk with >= 100 GB free, no automatic restarts (a self-hosted runner or a "
         "larger dedicated environment). The current container restarted about 6 times and runs with 4-8 GB free.",
         "<b>Already done</b>: tool slots, mutation verdict cache, checkpoint resume, stage-clear on re-run.",
         "<b>Still to do</b>: exclusive run-directory lock (prevents the sync_fifo double run by design, not by "
         "rule), disk-headroom check before starting a job, waveform auto-compression, secret scanning in CI, "
         "and an 'S2S regression' suite: crash-resume test, run-isolation test, golden designs counter8 + alu8 re-run "
         "on every tool or flow change.",
         "<b>Provenance</b>: every verdict records commit, tool versions, PDK version, config hash, seed (partly in place)."])
h2("3D. Next proof (behind the phase gate)")
p("One harder design - a small RISC-V core or a two-clock FIFO with a real clock-domain crossing - through the whole "
  "flow on the stable machine with the memory running, and show measurably fewer iterations than the five Phase-0 "
  "blocks. That is the result that shows the system learns. DFT, I/O ring, packaging and silicon validation from "
  "the OpenAI doctrine are the roadmap after that, each behind its own gate.")

# ---------------------------------------------------------------- part 4
h1("Part 4 - What you need to do")
table([["#", "Decision / action", "Recommended", "Why"],
       ["D1", "sync_fifo clock fanout", "Try the 3 tree-shape knobs first; if they cannot reach 10, adopt an explicit clock-tree rule (fanout limit within 8-20, plus slew, cap and skew) and keep 10 for data nets",
        "Matches industry practice; OpenROAD CTS cannot honour a fanout limit"],
       ["D2", "uart mutation scoring", "Prove-then-exclude; undecided counts as missed",
        "Standard method; avoids the GateTruth inflation trap"],
       ["D3", "spi_master SCK properties", "(c) now - bounded from reset, not counted; research (a) white-box helper invariants as a rule change later",
        "Pass rule is already met by 9 unbounded proofs"],
       ["D4", "Machine", "Move to 16-32 cores and persistent disk before the next large run", "Stops losing work"],
       ["D5", "Engineering memory", "Approve building knowledge/ + lesson injection now", "Highest leverage"],
       ["D6", "Security", "Revoke the leaked API key if not done", "Open since early in the project"]],
      [9, 38, 70, 53])
h2("Research that would help most")
bullets(["sky130 flows in practice: do OpenLane/Caravel users constrain clock-net fanout at all, and with which limit?",
         "Yosys SEC: best scripts for sequential equivalence with register correspondence on designs with wide counters "
         "(equiv_struct / equiv_induct / scorr in ABC: 'dsec', 'dprove').",
         "Whether ABC's 'dprove' or 'scorr' (signal correspondence) closes the uart mutant miters faster than PDR.",
         "Published helper-invariant patterns for clock-divider / baud-generator properties.",
         "A stable cloud or self-hosted option for a 16-32 core runner with persistent disk."])
h2("What I will NOT do (from the suggestions)")
bullets(["Suppress any mutant class, or exclude a mutant on suspicion.",
         "Shrink a divider or add an assumption without a written soundness argument.",
         "Waive the clock-fanout violations or change set_max_fanout silently.",
         "Build DFT / I/O / package / silicon stages before the phase gate.",
         "Claim production readiness from SKY130 results."])

h1("Sources")
for s in [link("https://openroad.readthedocs.io/en/latest/main/src/cts/README.html", "OpenROAD CTS documentation"),
          link("https://openlane2.readthedocs.io/en/latest/reference/step_config_vars.html", "OpenLane 2 step configuration variables"),
          link("https://teamvlsi.com/2021/06/clock-tree-constraints-in-vlsi-ccopt-file-in-physical-design-cts-constraints.html", "TeamVLSI - clock tree constraints (CCOpt)"),
          link("https://ecrionix.org/physical-design/cts/", "ecrionix - CTS guide"),
          link("https://www.edaboard.com/threads/how-do-we-set-max-fanout-for-clock-nets.394774/", "edaboard - max fanout for clock nets"),
          link("https://arxiv.org/pdf/2608.12635", "GateTruth: auditing RTL benchmarks via mutation testing (arXiv 2026)"),
          link("https://stryker-mutator.io/docs/mutation-testing-elements/equivalent-mutants/", "Stryker - equivalent mutants"),
          "Papadakis et al., 'Trivial Compiler Equivalence', ICSE 2015",
          link("https://zipcpu.com/blog/2018/03/10/induction-exercise.html", "ZipCPU - an exercise in formal induction"),
          link("https://zipcpu.com/tutorial/class-verilog.pdf", "ZipCPU - introduction to formal methods"),
          "US patents 7418678 (counters in formal verification) and 9665682 (counter acceleration)",
          "Verified locally: OpenLane 2.3.10 source (scripts/base.sdc, steps/openroad.py, steps/checker.py), "
          "OpenROAD 'help clock_tree_synthesis', S2S runs of 5 Oct 2026"]:
    p(s, SM)


def footer(c, d):
    c.saveState()
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.grey)
    c.drawString(15 * mm, 10 * mm, "S2S - What To Do Now - 5 Oct 2026")
    c.drawRightString(195 * mm, 10 * mm, f"Page {d.page}")
    c.restoreState()


doc = SimpleDocTemplate(str(OUT), pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm, topMargin=15 * mm,
                        bottomMargin=17 * mm, title="S2S - What To Do Now", author="S2S (Claude Code)")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print(OUT)
