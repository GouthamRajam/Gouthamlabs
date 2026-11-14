<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="assets/logo.svg">
    <source media="(prefers-color-scheme: light)" srcset="assets/logo-light.svg">
    <img alt="GouthamLabs" src="assets/logo-light.svg" width="520">
  </picture>
</p>

<h3 align="center">
  An AI design team that takes a written chip specification<br>
  to a tape-out-ready GDSII layout — proven at every step by real EDA tools.
</h3>

<p align="center">
  <a href="docs/paper/s2s_paper.tex"><strong>Research Paper</strong></a> ·
  <a href="docs/MASTER_SPEC.md"><strong>Full Specification</strong></a> ·
  <a href="demo/live_office.html"><strong>Live Office Demo</strong></a> ·
  <a href="docs/DECISIONS.md"><strong>Decision Log</strong></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Phase_0-4%2F5_Clean_GDSII-brightgreen?style=flat-square" alt="Phase 0">
  <img src="https://img.shields.io/badge/Phase_1-39%2F39_RV32I_Compliance-brightgreen?style=flat-square" alt="Phase 1">
  <img src="https://img.shields.io/badge/Agents-37_Specialized-blue?style=flat-square" alt="Agents">
  <img src="https://img.shields.io/badge/PDK-SkyWater_SKY130-purple?style=flat-square" alt="PDK">
  <img src="https://img.shields.io/badge/Cost-%240.39%2Fdesign-orange?style=flat-square" alt="Cost">
  <img src="https://img.shields.io/badge/License-Open_Source-green?style=flat-square" alt="License">
</p>

---

## Chip Layouts — AI-Generated, Tool-Verified

> All five Phase 0 designs placed and routed on SkyWater SKY130 `sky130_fd_sc_hd`. Metal layers: li1, met1–met5.

<p align="center">
  <img src="docs/reports/phase0_paper/fig_layouts.png" alt="Phase 0 chip layouts — counter8, alu8, sync_fifo, uart, spi_master" width="100%">
</p>

<table>
  <tr>
    <th>Design</th>
    <th>Cells</th>
    <th>Die Size</th>
    <th>DRC</th>
    <th>LVS</th>
    <th>Antenna</th>
    <th>STA (9 corners)</th>
    <th>Status</th>
  </tr>
  <tr>
    <td><strong>counter8</strong></td>
    <td>71</td>
    <td>51 x 61 &mu;m</td>
    <td>0</td>
    <td>Match</td>
    <td>0</td>
    <td>MET</td>
    <td>&#9989; PASS</td>
  </tr>
  <tr>
    <td><strong>alu8</strong></td>
    <td>156</td>
    <td>81 x 91 &mu;m</td>
    <td>0</td>
    <td>Match</td>
    <td>0</td>
    <td>MET</td>
    <td>&#9989; PASS</td>
  </tr>
  <tr>
    <td><strong>uart</strong></td>
    <td>208</td>
    <td>147 x 158 &mu;m</td>
    <td>0</td>
    <td>Match</td>
    <td>0</td>
    <td>MET</td>
    <td>&#9989; PASS</td>
  </tr>
  <tr>
    <td><strong>spi_master</strong></td>
    <td>312</td>
    <td>122 x 133 &mu;m</td>
    <td>0</td>
    <td>Match</td>
    <td>0</td>
    <td>MET*</td>
    <td>&#9888;&#65039; COND.</td>
  </tr>
  <tr>
    <td><strong>sync_fifo</strong></td>
    <td>189</td>
    <td>308 x 319 &mu;m</td>
    <td>0</td>
    <td>Match</td>
    <td>2</td>
    <td>MET</td>
    <td>&#10060; FAIL</td>
  </tr>
</table>

<sub>*Clock-net fanout rule relaxed from 10 to 20 for CTS buffers. sync_fifo has 2 bounded antenna violations (13–17% over limit).</sub>

---

## Power & IR Drop Analysis

<p align="center">
  <img src="docs/reports/phase0_paper/fig_power_ir.png" alt="Power by PVT corner and IR drop analysis" width="100%">
</p>

---

## RISC-V RV32I Core (Phase 1) — Full Signoff

<table>
  <tr>
    <td width="50%">

**PicoRV32 on SKY130 at 20 MHz**

| Metric | Value |
|--------|-------|
| RV32I compliance | **39/39 PASS** |
| Synthesis cells | 8,374 |
| Die area | 297,307 &mu;m&sup2; |
| DRC (Magic + KLayout) | **0 violations** |
| LVS (Netgen) | **Match** |
| Antenna violations | **0** |
| STA (9 PVT corners) | **All MET** |
| Power (VCD-based) | 2.606 mW |
| IR drop | 0.01% of VDD |
| GDSII size | 38.5 MB |

</td>
<td width="50%">

**Pipeline-Generated UART (Autonomous)**

| Stage | Result |
|-------|--------|
| Generation | 12 model calls, **0 human edits** |
| Verification | 72/72 loopback PASS |
| Synthesis (Yosys) | 474 cells |
| Gate-level sim | 72/72 PASS |
| P&R (OpenROAD) | 95,375 routed wires |
| Antenna | 0 violations |
| STA post-P&R | Setup +9.11 ns, hold +0.52 ns |
| **Cost** | **$0.39** |
| **Time** | **3.5 minutes** |

</td>
  </tr>
</table>

---

## The S2S Live Office — 37 AI Agents at Work

> Each circle is a specialized agent. The 10-stage pipeline flows left to right: Spec → Architecture → RTL → Verification → Synthesis → DFT → Floorplan → P&R → Signoff → GDSII. Real tools decide pass/fail at every stage.

<p align="center">
  <img src="docs/milestones/m0.4-screenshots/demo-floor-dark.png" alt="S2S Live Office — 37 agents organized by discipline" width="100%">
</p>

<details>
<summary><strong>Agent Replay — counter8 design run (157 events, 21 tool runs)</strong></summary>
<br>
<p align="center">
  <img src="docs/milestones/m0.5-screenshots/live-office-replay-counter8.png" alt="counter8 replay showing agent activity" width="100%">
</p>
</details>

---

## The Trust Layer

```
┌─────────────────────────────────────────────────────────────┐
│                    THE TRUST LAYER                          │
│                                                             │
│   "Real tools decide pass/fail. The AI never does."         │
│                                                             │
│   ┌─────────┐     ┌──────────────┐     ┌────────────────┐  │
│   │ AI Agent │────>│ Proposes     │────>│ Deterministic  │  │
│   │ (37)     │     │ RTL / fix /  │     │ EDA Tool       │  │
│   │          │     │ constraint   │     │ (Verilator,    │  │
│   └─────────┘     └──────────────┘     │  Yosys, STA,   │  │
│                                         │  DRC, LVS...)  │  │
│        ┌───── PASS ─────────────────────┤                │  │
│        │                                │  exit code 0   │  │
│        v                                │  + 0 errors    │  │
│   ┌─────────┐                           │  + rules met   │  │
│   │ Advance  │      FAIL ───────────────┤  + success     │  │
│   │ to next  │         │                │    marker      │  │
│   │ stage    │         v                └────────────────┘  │
│   └─────────┘    ┌──────────┐                               │
│                  │ AI tries  │                               │
│                  │ again     │──> 3 fails = human escalation │
│                  └──────────┘                                │
└─────────────────────────────────────────────────────────────┘
```

**Five conditions must ALL hold for a stage to advance:**
1. Tool exit code is 0
2. Zero error markers in output
3. No stage-specific rule violated (no latches, no logic loops, no negative slack)
4. No known failure strings
5. Positive success marker present

---

## Design Flow

```
  Z1: SPECIFICATION          Z2A: RTL              Z3: PHYSICAL           Z4: SIGNOFF
  ┌────────────────┐    ┌──────────────┐     ┌──────────────────┐    ┌──────────────┐
  │ Iris: parse     │    │ Ada: datapath │     │ Sienna: synthesis│    │ Chronos: STA │
  │ Ivy: standards  │    │ Ada-C: ctrl   │     │ Grid: floorplan  │    │ Calla: DRC   │
  │ Calla: checks   │    │ Ada-I: intf   │     │ Orion: P&R       │    │ Volta: power │
  │ Chronos: timing │    │ Juno: micro   │     │ Tick: CTS        │    │ Fabian: DFM  │
  └───────┬────────┘    └──────┬───────┘     │ Kepler: perf     │    │ Gideon: GDSII│
          │                     │             └────────┬─────────┘    └──────┬───────┘
          │                     │                      │                     │
          v                     v                      v                     v
  ┌────────────────────────────────────────────────────────────────────────────────┐
  │                              TRUST LAYER                                       │
  │              Every tool run recorded · Every result reproducible                │
  └────────────────────────────────────────────────────────────────────────────────┘
          │                     │
          │           Z2B: VERIFICATION (INDEPENDENT — cannot read RTL)
          │           ┌──────────────────┐
          └──────────>│ Mira: ref models │
                      │ Vera: testbench  │
                      │ Nadia: manager   │
                      │ Tess: DFT        │
                      │ Proof: formal    │
                      │ Sentinel: critic │
                      └──────────────────┘
```

---

## Repository Structure

```
Gouthamlabs/
├── assets/                    # Logo and branding
├── config/                    # Agent budgets, SLAs, flow config
├── demo/                      # Live Office interactive demo
├── designs/
│   ├── counter8/              # 8-bit counter (Phase 0)
│   ├── alu8/                  # 8-bit ALU (Phase 0)
│   ├── uart/
│   │   ├── rtl/               # Hand-directed UART RTL
│   │   └── pipeline_rtl/      # Autonomous pipeline UART
│   │       ├── synth/         #   ├── Yosys synthesis output
│   │       └── pnr/           #   └── OpenROAD P&R output (DEF, netlist)
│   ├── sync_fifo/             # Synchronous FIFO (Phase 0)
│   ├── spi_master/            # SPI master (Phase 0)
│   ├── picorv32/              # PicoRV32 RV32I core (Phase 1)
│   └── s2s_rv32i/             # Custom RV32I core
├── docs/
│   ├── MASTER_SPEC.md         # Full specification (~28K words)
│   ├── DECISIONS.md           # 259 recorded decisions
│   ├── PHASE_GATES.md         # Phase gate criteria and status
│   ├── paper/
│   │   ├── s2s_paper.tex      # Research paper (IEEE format)
│   │   └── PUBLISHING_GUIDE.md
│   ├── reports/               # Signoff reports and figures
│   └── milestones/            # Milestone evidence and screenshots
├── s2s/                       # Framework source code
│   ├── agents/                # 37 agent definitions
│   ├── runtime/               # Agent runtime (282 lines)
│   └── tools/                 # 10 EDA tool adapters
└── CONTEXT.md                 # Start here — 1-page project overview
```

---

## Key Numbers

| Metric | Value |
|--------|-------|
| AI agents | 37 (7 disciplines) |
| EDA tools integrated | 11 |
| Phase 0 designs | 5 (4 clean GDSII) |
| Phase 1 RV32I compliance | 39/39 PASS |
| Pipeline runs logged | 25 |
| Trajectory records | 5,630 |
| Total model calls | 337 |
| Specification size | ~28,000 words |
| Cost per simple design | **$0.39** |
| Time per simple design | **3.5 minutes** |

---

## Tools & Technology

All Phase 0 work uses **exclusively open-source tools** on the **SkyWater SKY130** process:

| Tool | Role |
|------|------|
| [Yosys](https://github.com/YosysHQ/yosys) | Synthesis & elaboration |
| [OpenROAD](https://github.com/The-OpenROAD-Project/OpenROAD) | Place & route |
| [OpenSTA](https://github.com/The-OpenROAD-Project/OpenSTA) | Static timing analysis |
| [Verilator](https://github.com/verilator/verilator) | RTL lint |
| [Icarus Verilog](https://github.com/steveicarus/iverilog) | Simulation |
| [cocotb](https://github.com/cocotb/cocotb) | Python verification |
| [SymbiYosys](https://github.com/YosysHQ/sby) | Formal verification |
| [eqy](https://github.com/YosysHQ/eqy) | Equivalence checking |
| [Magic](https://github.com/RTimothyEdwards/magic) | DRC & GDSII |
| [KLayout](https://github.com/KLayout/klayout) | DRC (200+ rules) |
| [Netgen](https://github.com/RTimothyEdwards/netgen) | LVS |

---

## Honest Limitations

We state these explicitly — the project's credibility depends on it.

- **Bounded equivalence only**: Register-file re-encoding prevents full k-induction proofs; BMC depth 10 is used
- **Agent personas are prompting devices**, not real expertise. Quality comes from the tools and checks
- **Open-shuttle signoff bar**, not commercial production
- **Provenance audit**: The committed s2s_rv32i and s2s_uart RTL was hand-authored in interactive sessions, not generated by the pipeline. False "agent-generated" labels were corrected. The pipeline does work — proven by the UART trajectory with SHA-256 hashes — but the two processor-scale designs were human-directed
- **No commercial-node validation**: All results are on SKY130

---

## Getting Started

```bash
# Clone
git clone https://github.com/GouthamRajam/Gouthamlabs.git
cd Gouthamlabs

# Read the 1-page overview first
cat CONTEXT.md

# Open the Live Office demo in a browser
open demo/live_office.html

# Browse chip designs
ls designs/
```

---

## Research Paper

**"S2S: An Autonomous Multi-Agent Framework for Specification-to-GDSII Chip Design with Deterministic Tool-Based Verification"**

Author: Goutham Rajam | Format: IEEE Conference | File: [`docs/paper/s2s_paper.tex`](docs/paper/s2s_paper.tex)

See [`docs/paper/PUBLISHING_GUIDE.md`](docs/paper/PUBLISHING_GUIDE.md) for submission instructions.

---

<p align="center">
  <sub>Built by <strong>Goutham Rajam</strong> · Independent Research · Open Source</sub><br>
  <sub>All designs target SkyWater SKY130 with open-source EDA tools</sub>
</p>
