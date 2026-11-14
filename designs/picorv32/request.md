# picorv32 — design request

RISC-V RV32I single-issue, in-order processor core. Implements the base integer
instruction set (RV32I, volume 1 v2.1) with machine-mode CSRs for trap handling
(mstatus, mtvec, mepc, mcause, mtval, mie, mip, mcycle, minstret). No M, C, or
F extensions in this version.

Memory interface: simple valid/ready handshake, 32-bit address, 32-bit data,
byte-enable strobes, single-cycle access assumed for timing closure. Instruction
and data share one port (Von Neumann); a Harvard wrapper is out of scope.

Reset: synchronous active-high, boots from a configurable reset vector (default
0x0000_0000). Interrupt: one external IRQ line, one timer IRQ line; trap
entry/return via mtvec/mepc.

Pipeline: single-cycle or multi-cycle (agent decides based on timing closure at
the target clock); pipelining is allowed but not required for P1.1.

Verification target: 100% pass on the official RISC-V architecture test suite
(riscv-arch-test, RV32I) in RTL simulation, plus equivalence through synthesis.

Target clock: 50 MHz on SKY130.
