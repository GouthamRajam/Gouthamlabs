# Research notes — competitors, methods and sources

These are the public facts and methods the plan is built on. Companies hide their
recipes; researchers publish the methods. Everything here is public. Treat the
expected numbers in MASTER_SPEC as hypotheses to confirm with our own runs.

## Competitors (public, as of Oct 2026)
- ChipAgents — Series A expanded to ~$134M (Jul 2026). Agents for spec reading, RTL,
  verification, some timing work, inside existing EDA flows. Positioned as augmenting
  existing flows, not full spec-to-GDSII on its own; little public fab/DFM focus.
  Source: BusinessWire 20260729819576; chipagents.ai/blogs/chipagents-dac-2026
- Cognichip — $60M Series A (Apr 2026). "Physics-informed foundation model" trained
  across abstraction levels (RTL, post-synth netlists, circuits, spec/validation).
  Claims high parallelism and margin removal. No named customers or AI-designed
  tape-outs disclosed; no training recipe public.
  Source: techcrunch.com 2026/04/01; siliconangle.com 2026/04/01;
  semiengineering.com/cognichip-using-ai-to-speed-complex-chip-design
- Verkor.io — agent built a RISC-V core from a 219-word spec to layout in ~12h, on
  the academic ASAP7 kit; not manufactured. Source: spectrum.ieee.org/ai-chip-design

## Public methods we adopt and TEST (not anyone's secret)
From published multi-agent RTL research (e.g. ChipCraftBrain, arXiv 2604.19856;
LLM circuit-verification survey, ASP-DAC 2026; ChipMEM arXiv 2609.27067):
- Validation-first loop: generate -> compile -> simulate -> synthesize -> feed the
  structured error back as the next prompt. (= our Trust Layer + Plan/Act/Check/Report)
- A few role-specialized agents: strong/slow for hard generation, fast/cheap for
  refinement, a debug agent, an optimize agent.
- RL orchestrator (PPO) that learns which agent to call next from the reward of
  passing checks. Public reward shape: terminal (sim/lint pass) + efficiency
  (fewer tries, fewer tokens) + quality (area/timing) + progress (stages, errors).
- Symbolic-neural hybrid: solve deterministic problems (truth tables/K-maps) with a
  classical algorithm (Quine-McCluskey) at zero model cost.
- Knowledge-augmented generation (RAG) over a pattern library (= our knowledge base).
- Hierarchical decomposition: split by dependency graph, generate leaves first.
- Verification-grounded memory: remember what passed/failed (= Sage).

## Reference math (standard public methods)
- Transformers fine-tuned on (spec -> passing RTL) + preference (pass vs fail).
- RL: maximize E[ sum gamma^t r_t ]; PPO with GAE (gamma~0.99, lambda~0.95).
- RL placement: Mirhoseini et al., Nature 2021 — placement as sequential decisions,
  GNN netlist embedding, reward = -(w1*wirelength + w2*congestion + w3*density).
- GNNs predict congestion/timing/IR from the netlist graph before the slow tool runs.
- Bayesian optimization / bandits for flow-parameter tuning (what DSO.ai/Cerebrus do).
- Classical exact algorithms where sound: espresso, SAT/SMT, static timing graphs.

## Open-source stack (Phase 0 — all free)
OpenLane 2, Yosys + ABC, OpenROAD, OpenSTA, Verilator, Icarus Verilog, cocotb,
SymbiYosys, eqy, Magic, KLayout, Netgen; SkyWater SKY130 PDK (sky130A, sky130_fd_sc_hd).

## Key public data point
2024 Siemens EDA / Wilson Research Group functional verification study: first-silicon
success ~14%. Verification is the dominant cost. This is why S2S is verification-first.
