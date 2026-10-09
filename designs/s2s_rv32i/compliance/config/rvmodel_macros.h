// Provenance: hand-authored by Claude in interactive Code session (not S2S agent pipeline)
// rvmodel_macros.h — DUT-specific macros for s2s_rv32i_core
// Uses HTIF-style termination via tohost memory-mapped address.

#ifndef _RVMODEL_MACROS_H
#define _RVMODEL_MACROS_H

// s2s_rv32i implements machine-mode CSRs (mstatus, mtvec, mepc, mcause, mtval,
// mscratch, mie, mip, misa, cycle/instret counters).
#define STANDARD_SM_SUPPORTED

#define RVMODEL_DATA_SECTION \
        .pushsection .tohost,"aw",@progbits;                \
        .balign 8; .global tohost; tohost: .dword 0;         \
        .balign 8; .global fromhost; fromhost: .dword 0;     \
        .popsection

///// STARTUP /////

#define RVMODEL_BOOT

///// TERMINATION /////

// HTIF: write 1 to tohost for PASS, 3 for FAIL
#define RVMODEL_HALT_PASS  \
  li x1, 1                ;\
  la t0, tohost           ;\
  write_tohost_pass:      ;\
    sw x1, 0(t0)          ;\
    sw x0, 4(t0)          ;\
    j write_tohost_pass   ;\

#define RVMODEL_HALT_FAIL \
  li x1, 3                ;\
  la t0, tohost           ;\
  write_tohost_fail:      ;\
    sw x1, 0(t0)          ;\
    sw x0, 4(t0)          ;\
    j write_tohost_fail   ;\

///// IO /////

#define RVMODEL_IO_INIT(_R1, _R2, _R3)

#define RVMODEL_IO_WRITE_STR(_R1, _R2, _R3, _STR_PTR)

///// Access Fault /////

#define RVMODEL_ACCESS_FAULT_ADDRESS 0x00000000

///// Interrupt Latency /////

#define RVMODEL_INTERRUPT_LATENCY 10
#define RVMODEL_TIMER_INT_SOON_DELAY 5000

///// Machine Timer /////

// s2s_rv32i does not have memory-mapped timer registers (CLINT).
// Timer interrupts are directly wired as inputs.
// Do not define RVMODEL_MTIMECMP_ADDRESS or RVMODEL_MTIME_ADDRESS
// to skip timer interrupt tests.

///// Machine Interrupts /////

#define RVMODEL_MAX_CYCLES_PER_TIMER_TICK 1

#endif // _RVMODEL_MACROS_H
