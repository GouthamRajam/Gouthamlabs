# s2s_rv32i — a small RISC-V processor core (comparison build)

## What it is
A compact 32-bit RISC-V CPU implementing the RV32I base integer instruction
set, single-hart, machine-mode, for embedded control. Synthesizable and
manufacturable on SKY130, targeting a conservative ~20 MHz clock. It is a
functional peer of a small hand-written core (picorv32) and will be
benchmarked against it.

## Instruction set
- Full RV32I base integer ISA: integer compute (add/sub, logic, shifts,
  compares), immediates (LUI/AUIPC), loads/stores (byte/half/word, signed and
  unsigned where defined), jumps (JAL/JALR), all conditional branches.
- 32 general-purpose 32-bit registers; x0 hardwired to zero.
- Illegal / all-zero instruction words must trap, not execute silently.
- Machine-mode CSRs for trap handling: status, trap-vector, exception PC,
  cause, and the cycle/instret counters.

## Interface
- Single clock and a synchronous reset (state the polarity chosen).
- One simple memory interface (valid/ready handshake) shared for instruction
  fetch and data access: address, write-data, write-strobe, read-data, and the
  valid/ready signals.
- Two interrupt inputs (external, timer) entering via the machine-mode trap
  mechanism.
- Configurable reset vector.

## Correctness bar (how it is judged)
- Judged ONLY by the official riscv-arch-test RV32I suite vs the RISC-V
  International Sail golden model. Must match the Sail reference signatures.
- Nothing is weakened to pass; real tools decide.

## Constraints
- Synthesizable Verilog, lint-clean (Verilator -Wall), elaborates in Yosys.
- Targets SKY130 (sky130_fd_sc_hd), ~20 MHz. Correctness first; PPA compared
  against the picorv32 reference.

## Provenance
- provenance: hand-authored by Claude in interactive Code session
- Phase 1.5 Pillar A — RTL was written by Claude (Opus 4.6) in Claude Code
  session, not by the S2S agent pipeline. No copying from picorv32 or any
  existing core. CORRECTED 2026-10-09: original label "agent-generated" was
  false — the S2S pipeline was never executed for this design.
