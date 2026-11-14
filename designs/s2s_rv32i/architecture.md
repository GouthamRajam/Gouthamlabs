# s2s_rv32i Microarchitecture

This document fully specifies the microarchitecture of the s2s_rv32i processor
core. It is the single reference for RTL implementation. Every signal name,
state encoding, and behavior described here is normative.

Provenance: hand-authored in interactive AI coding session (not by S2S
agent pipeline). No architecture or RTL borrowed from picorv32 or any other
existing core.

---

## 1. Design Philosophy

Correctness over performance. The core uses a **multi-cycle, non-pipelined**
execution model: one instruction occupies the entire datapath at a time, and
a finite state machine (FSM) sequences it through stages. This eliminates
hazard logic, forwarding paths, and pipeline flushes, making the design
straightforward to verify. At 4--5 cycles per instruction and 20 MHz, the core
delivers roughly 4--5 MIPS, which is appropriate for embedded control.

---

## 2. Pipeline Structure (Multi-Cycle Stages)

There is no pipeline. Each instruction passes through a subset of the
following FSM states, one clock cycle per state (except FETCH, MEM_READ, and
MEM_WRITE, which stall on the memory handshake).

| State       | Duration      | Work performed                                  |
|-------------|---------------|-------------------------------------------------|
| FETCH       | 1+ cycles     | Drive PC onto memory bus; latch instruction     |
| DECODE      | 1 cycle       | Decode opcode; read register file; gen immediate|
| EXECUTE     | 1 cycle       | ALU op / address calc / branch resolution       |
| MEM_READ    | 1+ cycles     | Load: drive address, latch read data            |
| MEM_WRITE   | 1+ cycles     | Store: drive address + data + strobe            |
| WRITEBACK   | 1 cycle       | Write rd; update PC; retire instruction         |
| TRAP_ENTRY  | 1 cycle       | Save mepc/mcause; disable interrupts; jump mtvec|
| MRET        | 1 cycle       | Restore mepc; re-enable interrupts              |

Cycle counts per instruction class (with zero-wait-state memory):

| Instruction class           | States traversed                        | Cycles |
|-----------------------------|-----------------------------------------|--------|
| R-type ALU                  | FETCH DECODE EXECUTE WRITEBACK          | 4      |
| I-type ALU / AUIPC          | FETCH DECODE EXECUTE WRITEBACK          | 4      |
| LUI                         | FETCH DECODE EXECUTE WRITEBACK          | 4      |
| Branch (taken or not)       | FETCH DECODE EXECUTE WRITEBACK          | 4      |
| JAL / JALR                  | FETCH DECODE EXECUTE WRITEBACK          | 4      |
| Load (LB/LH/LW/LBU/LHU)   | FETCH DECODE EXECUTE MEM_READ WRITEBACK | 5      |
| Store (SB/SH/SW)            | FETCH DECODE EXECUTE MEM_WRITE WRITEBACK| 5      |
| CSR (CSRRW/S/C/WI/SI/CI)   | FETCH DECODE EXECUTE WRITEBACK          | 4      |
| FENCE / WFI                 | FETCH DECODE WRITEBACK                  | 3      |
| ECALL / EBREAK              | FETCH DECODE TRAP_ENTRY                 | 3      |
| MRET                        | FETCH DECODE MRET                       | 3      |
| Illegal instruction         | FETCH DECODE TRAP_ENTRY                 | 3      |
| Interrupt (after WRITEBACK) | (previous instr) + TRAP_ENTRY           | +1     |

---

## 3. Datapath

### 3.1 Architectural Registers

- **PC** (32 bits): program counter. Directly driven by the FSM.
- **instruction_reg** (32 bits): latched instruction word from memory.
  Written in FETCH when mem_ready asserts.

### 3.2 Internal Pipeline Registers

These hold intermediate results between FSM states. They are written in one
state and consumed in a later state.

| Register         | Width  | Written in | Read in        | Purpose                          |
|------------------|--------|------------|----------------|----------------------------------|
| rs1_data_reg     | 32     | DECODE     | EXECUTE+       | Latched rs1 value                |
| rs2_data_reg     | 32     | DECODE     | EXECUTE+       | Latched rs2 value                |
| alu_result_reg   | 32     | EXECUTE    | MEM_*/WRITEBACK| ALU output / effective address   |
| mem_rdata_reg    | 32     | MEM_READ   | WRITEBACK      | Raw load data from memory        |
| csr_old_reg      | 32     | EXECUTE    | WRITEBACK      | Old CSR value (for rd write)     |
| csr_new_reg      | 32     | EXECUTE    | WRITEBACK      | New CSR value (for CSR write)    |
| branch_target_reg| 32     | EXECUTE    | WRITEBACK      | Computed branch/jump target      |

### 3.3 ALU

Purely combinational. Inputs: operand_a (32), operand_b (32), alu_op (4).
Output: alu_result (32).

ALU operation encoding (4-bit alu_op):

| alu_op | Operation       | Formula                                |
|--------|-----------------|----------------------------------------|
| 0000   | ADD             | a + b                                  |
| 0001   | SUB             | a - b                                  |
| 0010   | AND             | a & b                                  |
| 0011   | OR              | a \| b                                 |
| 0100   | XOR             | a ^ b                                  |
| 0101   | SLL             | a << b[4:0]                            |
| 0110   | SRL             | a >> b[4:0] (logical)                  |
| 0111   | SRA             | a >>> b[4:0] (arithmetic, sign-fill)   |
| 1000   | SLT             | {31'b0, $signed(a) < $signed(b)}       |
| 1001   | SLTU            | {31'b0, a < b}                         |

The ALU operand muxing is controlled by the FSM:

| Instruction class | operand_a | operand_b      | alu_op          |
|-------------------|-----------|----------------|-----------------|
| R-type            | rs1       | rs2            | per funct3/7    |
| I-type ALU        | rs1       | immediate      | per funct3(/7)  |
| Load / Store      | rs1       | immediate      | ADD             |
| AUIPC             | PC        | immediate      | ADD             |
| LUI               | 0         | immediate      | ADD             |
| JAL               | PC        | immediate      | ADD             |
| JALR              | rs1       | immediate      | ADD             |
| Branch            | PC        | immediate      | ADD (for target)|

### 3.4 Immediate Generation

Combinational. Input: instruction_reg (32). Output: immediate (32).

The immediate format is selected by the opcode field of the instruction:

| Type  | Bit assembly (MSB to LSB)                                    |
|-------|--------------------------------------------------------------|
| I     | {21{inst[31]}, inst[30:20]}                                  |
| S     | {21{inst[31]}, inst[30:25], inst[11:7]}                      |
| B     | {20{inst[31]}, inst[7], inst[30:25], inst[11:8], 1'b0}       |
| U     | {inst[31:12], 12'b0}                                         |
| J     | {12{inst[31]}, inst[19:12], inst[20], inst[30:21], 1'b0}     |

Selection by opcode:

| Opcode   | Name      | Immediate type |
|----------|-----------|----------------|
| 0110111  | LUI       | U              |
| 0010111  | AUIPC     | U              |
| 1101111  | JAL       | J              |
| 1100111  | JALR      | I              |
| 1100011  | BRANCH    | B              |
| 0000011  | LOAD      | I              |
| 0100011  | STORE     | S              |
| 0010011  | OP-IMM    | I              |
| 1110011  | SYSTEM    | I (CSR addr); also zimm = {27'b0, inst[19:15]} |

### 3.5 Branch Condition Logic

Combinational. Inputs: rs1_data (32), rs2_data (32), funct3 (3).
Output: branch_taken (1).

| funct3 | Mnemonic | Condition                  |
|--------|----------|----------------------------|
| 000    | BEQ      | rs1 == rs2                 |
| 001    | BNE      | rs1 != rs2                 |
| 100    | BLT      | $signed(rs1) < $signed(rs2)|
| 101    | BGE      | $signed(rs1) >= $signed(rs2)|
| 110    | BLTU     | rs1 < rs2 (unsigned)       |
| 111    | BGEU     | rs1 >= rs2 (unsigned)      |

funct3 values 010 and 011 are unused for branches and will be caught by the
illegal instruction decoder.

---

## 4. Control: FSM States and Transitions

### 4.1 State Encoding

Nine states. A 4-bit one-hot or binary encoding; the implementer may choose.
The states and their numeric identifiers (for the spec):

```
S_FETCH      = 0
S_DECODE     = 1
S_EXECUTE    = 2
S_MEM_READ   = 3
S_MEM_WRITE  = 4
S_WRITEBACK  = 5
S_TRAP_ENTRY = 6
S_MRET       = 7
```

### 4.2 State Transition Diagram

```
         rst_n=0
           |
           v
       +-------+
       | FETCH |<-------------------------------------+
       +---+---+                                      |
           | mem_ready                                |
           v                                          |
       +--------+                                     |
       | DECODE |                                     |
       +---+----+                                     |
           |                                          |
     +-----+------+------+------+------+              |
     |      |      |      |      |      |              |
  illegal  ecall  ebreak  mret  fence  other          |
     |      |      |             wfi     |              |
     v      v      v              |      v              |
  TRAP   TRAP   TRAP     +----+  |  +--------+         |
  ENTRY  ENTRY  ENTRY    |MRET|  |  |EXECUTE |         |
     |      |      |     +-+--+  |  +---+----+         |
     |      |      |       |     |      |               |
     +------+------+-------+-----+  +---+---+---+      |
                    |               |   |   |   |      |
                    |            R/I/U/J  Br CSR |      |
                    |               |   |   |  ld/st   |
                    |               v   v   v   |      |
                    |          +----------+  +--+--+   |
                    |          |WRITEBACK |  |MEM_R|   |
                    |          +----+-----+  |MEM_W|   |
                    |               |        +--+--+   |
                    |               |           |      |
                    |               +-----------+      |
                    |               |                   |
                    |          irq pending?             |
                    |          yes: TRAP_ENTRY          |
                    |          no:  FETCH               |
                    |               |                   |
                    +---------------+-------------------+
```

### 4.3 Detailed State Behaviors

#### S_FETCH

Signals driven:
- `mem_valid` = 1
- `mem_addr` = PC
- `mem_wstrb` = 4'b0000 (read)

Actions on `mem_ready`:
- `instruction_reg` <= `mem_rdata`
- Next state: S_DECODE

If `mem_ready` = 0, remain in S_FETCH (mem_valid stays asserted).

#### S_DECODE

Combinational in this cycle:
- Decoder extracts opcode, funct3, funct7, rs1_addr, rs2_addr, rd_addr,
  immediate, instruction type flags, and illegal-instruction signal.
- Register file read: rs1_data, rs2_data (combinational read).

Registered at end of cycle:
- `rs1_data_reg` <= rs1_data
- `rs2_data_reg` <= rs2_data

Transitions:
- If `instruction_reg` == 32'h0000_0000: S_TRAP_ENTRY (illegal instruction,
  mcause = 2, mtval = instruction_reg)
- If decoder signals `is_illegal`: S_TRAP_ENTRY (mcause = 2, mtval = instruction_reg)
- If `is_ecall`: S_TRAP_ENTRY (mcause = 11)
- If `is_ebreak`: S_TRAP_ENTRY (mcause = 3)
- If `is_mret`: S_MRET
- If `is_fence` or `is_wfi`: S_WRITEBACK (treated as NOP; PC advances by 4)
- Otherwise: S_EXECUTE

Trap info registered when transitioning to TRAP_ENTRY:
- `trap_cause_reg` <= cause code
- `trap_val_reg` <= mtval value (instruction word for illegal, 0 otherwise)
- `trap_pc_reg` <= PC (the faulting instruction's address)
- `trap_is_interrupt` <= 0

#### S_EXECUTE

ALU operation is performed combinationally. The FSM selects operand_a,
operand_b, and alu_op based on the instruction type (see section 3.3).

Registered at end of cycle:
- `alu_result_reg` <= alu_result

Per instruction class:

**R-type / I-type ALU / LUI / AUIPC:**
- Next state: S_WRITEBACK
- `alu_result_reg` holds the value to write to rd.

**JAL:**
- `branch_target_reg` <= alu_result (PC + imm_J)
- If branch_target_reg[1] != 0: S_TRAP_ENTRY (instruction address misaligned,
  mcause = 0, mtval = branch_target_reg)
- Else: S_WRITEBACK. The value for rd is PC + 4 (link address); computed
  separately and stored in `alu_result_reg`.

Note: The JAL EXECUTE cycle computes the target (PC + imm) through the ALU,
stores it in `branch_target_reg`, and stores PC + 4 in `alu_result_reg`
using a dedicated adder (PC + 4 is also needed for sequential flow, so
this adder exists anyway).

**JALR:**
- `branch_target_reg` <= (rs1_data_reg + immediate) & 32'hFFFF_FFFE (clear bit 0)
- If branch_target_reg[1] != 0: S_TRAP_ENTRY (misaligned, mcause = 0, mtval = target)
- Else: S_WRITEBACK. `alu_result_reg` <= PC + 4 for rd.

**Branch:**
- `branch_target_reg` <= PC + imm_B (from ALU: operand_a=PC, operand_b=imm)
- Evaluate branch condition (section 3.5) using rs1_data_reg and rs2_data_reg.
- If taken and branch_target_reg[1] != 0: S_TRAP_ENTRY (misaligned, mcause = 0)
- If taken and aligned: S_WRITEBACK with `branch_taken_flag` = 1
- If not taken: S_WRITEBACK with `branch_taken_flag` = 0

**Load:**
- `alu_result_reg` <= rs1_data_reg + immediate (effective address)
- Misalignment check:
  - LW (funct3=010): if alu_result[1:0] != 0 -> S_TRAP_ENTRY (mcause = 4, mtval = address)
  - LH/LHU (funct3=001/101): if alu_result[0] != 0 -> S_TRAP_ENTRY (mcause = 4)
  - LB/LBU (funct3=000/100): never misaligned
- If aligned: S_MEM_READ

**Store:**
- `alu_result_reg` <= rs1_data_reg + immediate (effective address)
- Misalignment check:
  - SW (funct3=010): if alu_result[1:0] != 0 -> S_TRAP_ENTRY (mcause = 6, mtval = address)
  - SH (funct3=001): if alu_result[0] != 0 -> S_TRAP_ENTRY (mcause = 6)
  - SB (funct3=000): never misaligned
- If aligned: S_MEM_WRITE

**CSR instruction:**
- `csr_old_reg` <= CSR read data (combinational read from CSR unit)
- `csr_new_reg` <= computed new value (see section 5.2)
- If CSR address not valid: S_TRAP_ENTRY (illegal instruction, mcause = 2)
- If write to read-only CSR (addr[11:10]==2'b11) and the instruction
  actually writes (CSRRW, or CSRRS/CSRRC with rs1 != x0, or
  CSRRWI, or CSRRSI/CSRRCI with uimm != 0): S_TRAP_ENTRY (illegal, mcause = 2)
- Otherwise: S_WRITEBACK

#### S_MEM_READ

Signals driven:
- `mem_valid` = 1
- `mem_addr` = `alu_result_reg` (word-aligned: {alu_result_reg[31:2], 2'b00})
- `mem_wstrb` = 4'b0000 (read)

On `mem_ready`:
- `mem_rdata_reg` <= `mem_rdata`
- Next state: S_WRITEBACK

#### S_MEM_WRITE

Signals driven:
- `mem_valid` = 1
- `mem_addr` = `alu_result_reg` (word-aligned: {alu_result_reg[31:2], 2'b00})
- `mem_wdata` = store data (see section 4.4)
- `mem_wstrb` = store strobe (see section 4.4)

On `mem_ready`:
- Next state: S_WRITEBACK (no register write; store does not write rd)

#### S_WRITEBACK

Actions (all in one cycle):

1. **Register write:** if the instruction writes to rd AND rd != 5'b00000,
   assert `rf_wr_en` = 1 with `rf_wr_addr` = rd_addr and `rf_wr_data` = result.

   The result source depends on instruction type:
   | Instruction type     | rd write data source                    |
   |----------------------|-----------------------------------------|
   | R/I ALU, LUI, AUIPC  | alu_result_reg                          |
   | JAL, JALR            | alu_result_reg (which holds PC+4)       |
   | Load                 | load_result (sign/zero-extended, sec 4.5)|
   | CSR                  | csr_old_reg                             |
   | Branch               | no write (rf_wr_en = 0)                 |
   | Store                | no write (rf_wr_en = 0)                 |
   | FENCE / WFI          | no write (rf_wr_en = 0)                 |

2. **CSR write:** if the instruction is a CSR instruction and it performs a
   write (see rules in S_EXECUTE), assert `csr_wr_en` = 1 with the new value
   from `csr_new_reg`.

3. **PC update:**
   | Condition                           | Next PC                  |
   |-------------------------------------|--------------------------|
   | JAL or JALR                         | branch_target_reg        |
   | Branch taken                        | branch_target_reg        |
   | Branch not taken / all others       | PC + 4                   |

4. **instret increment:** pulse `instret_inc` to the CSR unit.

5. **Interrupt check:**
   - Read `mstatus_mie`, `mie`, `mip` from the CSR unit.
   - If `mstatus_mie` == 1 AND (`mie` & `mip`) != 0:
     - Determine highest-priority pending interrupt (external > timer):
       - If mie[11] & mip[11]: mcause = 32'h8000_000B (external interrupt)
       - Else if mie[7] & mip[7]: mcause = 32'h8000_0007 (timer interrupt)
     - `trap_pc_reg` <= next_pc (the PC just computed above: the instruction
       that WOULD execute next)
     - `trap_is_interrupt` <= 1
     - Next state: S_TRAP_ENTRY
   - If no interrupt: Next state: S_FETCH

#### S_TRAP_ENTRY

Actions (one cycle):
- CSR unit receives trap signals:
  - `mepc` <= `trap_pc_reg`
  - `mcause` <= `trap_cause_reg` (with bit 31 set for interrupts)
  - `mtval` <= `trap_val_reg`
  - `mstatus.MPIE` <= `mstatus.MIE`
  - `mstatus.MIE` <= 0
- `PC` <= `mtvec` (read from CSR unit; assumed MODE=0, direct, so
  mtvec[31:2] concatenated with 2'b00)
- Next state: S_FETCH

#### S_MRET

Actions (one cycle):
- `PC` <= `mepc` (read from CSR unit)
- `mstatus.MIE` <= `mstatus.MPIE`
- `mstatus.MPIE` <= 1
- Next state: S_FETCH

### 4.4 Store Data Formatting

The store data and write strobe are computed from funct3 and the effective
address low bits (alu_result_reg[1:0]).

**Write data** (mem_wdata):

| funct3 | Size | Value                                            |
|--------|------|--------------------------------------------------|
| 000    | SB   | {4{rs2_data_reg[7:0]}}   (byte replicated x4)   |
| 001    | SH   | {2{rs2_data_reg[15:0]}}  (halfword replicated x2)|
| 010    | SW   | rs2_data_reg                                     |

**Write strobe** (mem_wstrb):

| funct3 | addr[1:0] | mem_wstrb  |
|--------|-----------|------------|
| 000 SB | 00        | 4'b0001    |
| 000 SB | 01        | 4'b0010    |
| 000 SB | 10        | 4'b0100    |
| 000 SB | 11        | 4'b1000    |
| 001 SH | 0x        | 4'b0011    |
| 001 SH | 1x        | 4'b1100    |
| 010 SW | xx        | 4'b1111    |

### 4.5 Load Data Extraction and Sign Extension

After MEM_READ, the raw 32-bit mem_rdata_reg is processed based on funct3
and addr[1:0] (saved from alu_result_reg[1:0]).

**Byte extraction** (addr[1:0] selects the byte):

| addr[1:0] | Selected byte         |
|-----------|-----------------------|
| 00        | mem_rdata_reg[7:0]    |
| 01        | mem_rdata_reg[15:8]   |
| 10        | mem_rdata_reg[23:16]  |
| 11        | mem_rdata_reg[31:24]  |

**Halfword extraction** (addr[1] selects the halfword):

| addr[1]   | Selected halfword      |
|-----------|------------------------|
| 0         | mem_rdata_reg[15:0]    |
| 1         | mem_rdata_reg[31:16]   |

**Load result** (load_result, 32 bits):

| funct3 | Name | Result                                          |
|--------|------|-------------------------------------------------|
| 000    | LB   | {{24{byte[7]}}, byte}        (sign-extend byte) |
| 001    | LH   | {{16{half[15]}}, half}       (sign-extend half) |
| 010    | LW   | mem_rdata_reg                (full word)        |
| 100    | LBU  | {24'b0, byte}                (zero-extend byte) |
| 101    | LHU  | {16'b0, half}                (zero-extend half) |

---

## 5. CSR Unit

### 5.1 Implemented CSRs

| Address | Name       | R/W | Reset value  | Description                      |
|---------|------------|-----|--------------|----------------------------------|
| 0x300   | mstatus    | RW  | 32'h0        | Machine status (MIE, MPIE only)  |
| 0x301   | misa       | RO  | 32'h4000_0100| RV32I (MXL=1, bit 8 = I ext)    |
| 0x304   | mie        | RW  | 32'h0        | Machine interrupt enable         |
| 0x305   | mtvec      | RW  | 32'h0        | Machine trap vector base         |
| 0x340   | mscratch   | RW  | 32'h0        | Machine scratch register         |
| 0x341   | mepc       | RW  | 32'h0        | Machine exception PC             |
| 0x342   | mcause     | RW  | 32'h0        | Machine trap cause               |
| 0x343   | mtval      | RW  | 32'h0        | Machine trap value               |
| 0x344   | mip        | RO* | 32'h0        | Machine interrupt pending        |
| 0xC00   | cycle      | RO  | 32'h0        | Cycle counter (low 32)           |
| 0xC01   | time       | RO  | 32'h0        | Alias of cycle (low 32)          |
| 0xC02   | instret    | RO  | 32'h0        | Instructions retired (low 32)    |
| 0xC80   | cycleh     | RO  | 32'h0        | Cycle counter (high 32)          |
| 0xC81   | timeh      | RO  | 32'h0        | Alias of cycleh (high 32)        |
| 0xC82   | instreth   | RO  | 32'h0        | Instructions retired (high 32)   |
| 0xF11   | mvendorid  | RO  | 32'h0        | Vendor ID (0 = non-commercial)   |
| 0xF12   | marchid    | RO  | 32'h0        | Architecture ID                  |
| 0xF13   | mimpid     | RO  | 32'h0        | Implementation ID                |
| 0xF14   | mhartid    | RO  | 32'h0        | Hart ID (0, single hart)         |

*mip: bits 11 (MEIP) and 7 (MTIP) reflect the synchronized external/timer
interrupt inputs. All other bits read as 0. Software writes to mip are ignored.

**mstatus bit map** (only these bits are implemented; all others read as 0):
- Bit 3: MIE (machine interrupt enable)
- Bit 7: MPIE (machine previous interrupt enable)
- Bit 12:11: MPP (machine previous privilege) = 2'b11 (always M-mode)

Writes to mstatus are masked: only bits 3 and 7 are writable. Bits 12:11
always read as 2'b11.

**mie bit map:**
- Bit 7: MTIE (machine timer interrupt enable)
- Bit 11: MEIE (machine external interrupt enable)
- All other bits read as 0 and writes are ignored.

**mtvec:** MODE field is bits [1:0]. Only MODE=0 (direct) is supported.
Writes to bits [1:0] are ignored (always read 0). The trap handler address
is mtvec[31:2] concatenated with 2'b00.

**mepc:** Bit 0 and bit 1 are always 0 (4-byte aligned). Writes mask off
the low 2 bits.

**mcause:** Full 32 bits are writable. Bit 31 indicates interrupt (1) vs
exception (0). Bits [30:0] hold the cause code.

**Counters:** cycle is a free-running 64-bit counter incremented every clock
cycle. instret is a 64-bit counter incremented when `instret_inc` is pulsed.
Both are split across two read-only CSR addresses (low/high). time/timeh
alias cycle/cycleh.

Any CSR address not in the table above is "not valid" and access traps as
an illegal instruction.

### 5.2 CSR Read/Modify/Write Operations

CSR instructions occupy opcode 1110011 with funct3 encoding the operation:

| funct3 | Mnemonic | Operation                                 |
|--------|----------|--------------------------------------------|
| 001    | CSRRW    | rd <- CSR; CSR <- rs1                      |
| 010    | CSRRS    | rd <- CSR; CSR <- CSR \| rs1               |
| 011    | CSRRC    | rd <- CSR; CSR <- CSR & ~rs1               |
| 101    | CSRRWI   | rd <- CSR; CSR <- zext(uimm)               |
| 110    | CSRRSI   | rd <- CSR; CSR <- CSR \| zext(uimm)        |
| 111    | CSRRCI   | rd <- CSR; CSR <- CSR & ~zext(uimm)        |

Where `uimm` = instruction[19:15], zero-extended to 32 bits.

**Write suppression rules** (per RISC-V spec):
- CSRRS / CSRRC: if rs1 == x0 (rs1_addr == 5'b00000), the CSR is not written.
  These become pure reads and do NOT trap on read-only CSRs.
- CSRRSI / CSRRCI: if uimm == 0, the CSR is not written.
- CSRRW / CSRRWI: always write.

**Read suppression rule:**
- CSRRW / CSRRWI: if rd == x0 (rd_addr == 5'b00000), the CSR read has no
  side effect (no value written to a register), but the read still occurs.
  (This matters only for CSRs with read side effects, which this core has none.)

The CSR new value is computed in S_EXECUTE, stored in csr_new_reg, and written
to the CSR unit in S_WRITEBACK via csr_wr_en.

---

## 6. Interrupt Handling

### 6.1 Synchronization

The two interrupt inputs (irq_external, irq_timer) are asynchronous to the
core clock. They are synchronized with a standard 2-flop synchronizer
(double-register) inside the top-level core module:

```
// Stage 1
always @(posedge clk) begin
    irq_ext_meta  <= irq_external;
    irq_tmr_meta  <= irq_timer;
end

// Stage 2
always @(posedge clk) begin
    irq_ext_sync  <= irq_ext_meta;
    irq_tmr_sync  <= irq_tmr_meta;
end
```

The synchronized values (irq_ext_sync, irq_tmr_sync) are wired to the CSR
unit, which reflects them in mip bits 11 and 7 respectively.

### 6.2 Interrupt Sampling

Interrupts are level-sensitive. They are sampled at the end of S_WRITEBACK,
after the current instruction has retired:

```
interrupt_pending = mstatus_mie & ((mie[11] & mip[11]) | (mie[7] & mip[7]));
```

If `interrupt_pending` is true, the FSM transitions to S_TRAP_ENTRY instead
of S_FETCH.

### 6.3 Interrupt Priority

When multiple interrupts are pending simultaneously:
1. Machine external interrupt (mcause = 0x8000_000B) -- highest priority
2. Machine timer interrupt (mcause = 0x8000_0007)

The FSM selects the highest-priority pending interrupt and sets trap_cause_reg
accordingly. Only one interrupt is taken per WRITEBACK; the other remains
pending and will be taken on the next instruction's WRITEBACK (if still
asserted and enabled).

### 6.4 Interrupt Latency

Best case: 1 clock cycle (TRAP_ENTRY) after WRITEBACK of the current
instruction, then FETCH of the handler = 2 cycles from retirement of the
interrupted instruction to first fetch of the handler. Worst case adds
memory wait states.

---

## 7. Trap Mechanism

### 7.1 Exception Causes

| mcause | Name                          | Detected in | Trigger                          |
|--------|-------------------------------|-------------|----------------------------------|
| 0      | Instruction address misaligned| EXECUTE     | JAL/JALR/branch target bit[1]!=0 |
| 2      | Illegal instruction           | DECODE      | Bad opcode/funct, bad CSR access |
| 3      | Breakpoint                    | DECODE      | EBREAK instruction               |
| 4      | Load address misaligned       | EXECUTE     | LH/LW address not aligned        |
| 6      | Store/AMO address misaligned  | EXECUTE     | SH/SW address not aligned        |
| 11     | Environment call from M-mode  | DECODE      | ECALL instruction                |

### 7.2 Exception Priority

Since the core executes one instruction at a time with no pipeline, at most
one exception can occur per instruction. The detection points are:

1. DECODE: illegal instruction, ecall, ebreak (these immediately go to
   TRAP_ENTRY, skipping EXECUTE)
2. EXECUTE: misaligned address, misaligned branch target, illegal CSR access
   (these go to TRAP_ENTRY, skipping MEM/WRITEBACK)

If an exception is detected, the instruction does NOT retire (no register
write, no PC update, no instret increment).

### 7.3 Exceptions vs Interrupts

- Exceptions are synchronous: detected during instruction execution, mepc
  points to the faulting instruction (the one whose execution caused the trap).
- Interrupts are asynchronous: sampled at WRITEBACK after the instruction
  retires, mepc points to the next instruction (the one that would execute
  next).

### 7.4 Trap Entry Sequence (S_TRAP_ENTRY)

1. `CSR.mepc` <= trap_pc_reg
2. `CSR.mcause` <= trap_cause_reg
3. `CSR.mtval` <= trap_val_reg (faulting instruction for illegal; faulting
   address for misaligned load/store/branch; 0 for ecall/ebreak/interrupts)
4. `CSR.mstatus.MPIE` <= `CSR.mstatus.MIE`
5. `CSR.mstatus.MIE` <= 0
6. `PC` <= `CSR.mtvec` & 32'hFFFF_FFFC (force alignment)
7. Next state: S_FETCH

### 7.5 Trap Return Sequence (S_MRET)

1. `PC` <= `CSR.mepc`
2. `CSR.mstatus.MIE` <= `CSR.mstatus.MPIE`
3. `CSR.mstatus.MPIE` <= 1
4. Next state: S_FETCH

---

## 8. Module Hierarchy

```
s2s_rv32i_core (top-level: FSM + datapath muxing + interrupt sync)
 |
 +-- s2s_rv32i_decoder    (combinational: instruction decode + immediate gen)
 |
 +-- s2s_rv32i_regfile     (synchronous write, combinational read)
 |
 +-- s2s_rv32i_alu         (combinational: arithmetic/logic operations)
 |
 +-- s2s_rv32i_csr         (synchronous: CSR registers, counters, trap logic)
```

Four submodules, one top-level module. The FSM controller and all datapath
muxing live in the top-level module. No memory controller module is needed:
the memory interface is directly driven by the FSM.

### 8.1 s2s_rv32i_core

Top-level module. Contains the FSM, PC register, pipeline registers,
interrupt synchronizers, memory interface muxes, and instantiates all
submodules.

```
module s2s_rv32i_core #(
    parameter RESET_VECTOR = 32'h0000_0000
) (
    input  wire        clk,
    input  wire        rst_n,          // active-low synchronous reset

    // Memory interface (active-high valid/ready)
    output reg  [31:0] mem_addr,
    output reg  [31:0] mem_wdata,
    output reg  [3:0]  mem_wstrb,
    input  wire [31:0] mem_rdata,
    output reg         mem_valid,
    input  wire        mem_ready,

    // Interrupt inputs (active-high, directly from external sources)
    input  wire        irq_external,
    input  wire        irq_timer
);
```

### 8.2 s2s_rv32i_decoder

Purely combinational. Takes the 32-bit instruction word and produces all
decoded fields and type flags.

```
module s2s_rv32i_decoder (
    input  wire [31:0] instr,

    // Register addresses
    output wire [4:0]  rs1_addr,
    output wire [4:0]  rs2_addr,
    output wire [4:0]  rd_addr,

    // Immediate (sign-extended, shifted as appropriate per type)
    output wire [31:0] imm,

    // Instruction fields
    output wire [6:0]  opcode,
    output wire [2:0]  funct3,
    output wire [6:0]  funct7,

    // Instruction type flags (exactly one is set for valid instructions)
    output wire        is_lui,
    output wire        is_auipc,
    output wire        is_jal,
    output wire        is_jalr,
    output wire        is_branch,
    output wire        is_load,
    output wire        is_store,
    output wire        is_alu_imm,     // OP-IMM (ADDI, SLTI, etc.)
    output wire        is_alu_reg,     // OP (ADD, SUB, etc.)
    output wire        is_fence,
    output wire        is_system,      // any SYSTEM opcode instruction

    // SYSTEM sub-type flags
    output wire        is_ecall,
    output wire        is_ebreak,
    output wire        is_mret,
    output wire        is_wfi,
    output wire        is_csr,

    // Illegal instruction flag
    output wire        is_illegal
);
```

Illegal instruction detection covers:
- Unrecognized opcode (not in the set: LUI, AUIPC, JAL, JALR, BRANCH, LOAD,
  STORE, OP-IMM, OP, FENCE, SYSTEM)
- JALR with funct3 != 000
- BRANCH with funct3 in {010, 011}
- LOAD with funct3 in {011, 110, 111}
- STORE with funct3 not in {000, 001, 010}
- OP-IMM shift: SLLI requires funct7 == 0000000; SRLI requires 0000000;
  SRAI requires 0100000. Others are illegal.
- OP (R-type): only the 10 defined funct3/funct7 combinations are legal
  (ADD 000/0000000, SUB 000/0100000, SLL 001/0000000, SLT 010/0000000,
  SLTU 011/0000000, XOR 100/0000000, SRL 101/0000000, SRA 101/0100000,
  OR 110/0000000, AND 111/0000000).
- SYSTEM funct3=000: only the four exact encodings for ECALL, EBREAK, MRET,
  WFI are legal.
- SYSTEM funct3=100: illegal.
- CSR address validation is handled separately by the CSR unit (csr_addr_valid
  signal), not by the decoder.

### 8.3 s2s_rv32i_regfile

32 entries of 32 bits. Two combinational read ports, one synchronous write
port. x0 hardwired to zero.

```
module s2s_rv32i_regfile (
    input  wire        clk,

    // Read port 1 (combinational)
    input  wire [4:0]  rs1_addr,
    output wire [31:0] rs1_data,

    // Read port 2 (combinational)
    input  wire [4:0]  rs2_addr,
    output wire [31:0] rs2_data,

    // Write port (synchronous, rising edge)
    input  wire        wr_en,
    input  wire [4:0]  wr_addr,
    input  wire [31:0] wr_data
);
```

Implementation:
- Storage: `reg [31:0] regs [1:31];` (31 entries; x0 is not stored)
- Read: `assign rs1_data = (rs1_addr == 0) ? 32'b0 : regs[rs1_addr];`
  Same for rs2.
- Write: on posedge clk, if wr_en and wr_addr != 0, `regs[wr_addr] <= wr_data`.
- No reset of register contents (the RISC-V spec does not require it, and
  omitting it saves gates). x0 reads as 0 by construction, not by reset.

### 8.4 s2s_rv32i_alu

Purely combinational. Performs the operation indicated by alu_op on the two
32-bit operands.

```
module s2s_rv32i_alu (
    input  wire [31:0] op_a,
    input  wire [31:0] op_b,
    input  wire [3:0]  alu_op,

    output reg  [31:0] result
);
```

alu_op encoding matches the table in section 3.3. Implementation uses a
case statement. The SLT/SLTU comparison reuses the subtractor output (op_a -
op_b) and checks the sign bit / carry for the result.

### 8.5 s2s_rv32i_csr

Contains all CSR registers, the cycle/instret counters, and the trap
entry/return logic.

```
module s2s_rv32i_csr (
    input  wire        clk,
    input  wire        rst_n,

    // CSR read/write interface (active in EXECUTE/WRITEBACK)
    input  wire [11:0] csr_addr,
    output reg  [31:0] csr_rdata,       // combinational read
    input  wire        csr_wen,         // write enable (pulsed in WRITEBACK)
    input  wire [31:0] csr_wdata,       // new CSR value

    // CSR address validation
    output wire        csr_valid,       // 1 if csr_addr maps to a known CSR
    output wire        csr_readonly,    // 1 if csr_addr is read-only

    // Trap entry interface (active in TRAP_ENTRY)
    input  wire        trap_enter,      // pulse: save trap state
    input  wire [31:0] trap_mepc,       // PC to save in mepc
    input  wire [31:0] trap_mcause,     // cause code
    input  wire [31:0] trap_mtval,      // trap value

    // MRET interface
    input  wire        mret_exec,       // pulse: execute MRET

    // Outputs to FSM
    output wire [31:0] mtvec_o,         // trap vector address
    output wire [31:0] mepc_o,          // saved PC for MRET
    output wire        mstatus_mie_o,   // current MIE bit
    output wire [31:0] mie_o,           // interrupt enable register
    output wire [31:0] mip_o,           // interrupt pending register

    // Interrupt pending inputs (synchronized)
    input  wire        irq_ext_sync,
    input  wire        irq_tmr_sync,

    // Counter control
    input  wire        instret_inc      // pulse when instruction retires
);
```

Internal registers:
- mstatus_mie, mstatus_mpie (single bits)
- mie_reg (32 bits, only bits 11 and 7 writable)
- mtvec_reg (32 bits, bits 1:0 forced to 0)
- mscratch_reg (32 bits)
- mepc_reg (32 bits, bits 1:0 forced to 0)
- mcause_reg (32 bits)
- mtval_reg (32 bits)
- cycle_counter (64 bits, increments every clock)
- instret_counter (64 bits, increments on instret_inc pulse)

The mip register is not stored; it is assembled combinationally:
```
assign mip_o = {20'b0, irq_ext_sync, 3'b0, irq_tmr_sync, 7'b0};
```

The mstatus register is assembled from its constituent bits:
```
assign mstatus_o = {19'b0, 2'b11, 4'b0, mstatus_mpie, 3'b0, mstatus_mie, 3'b0};
```
(Bits 12:11 = MPP = 2'b11 for M-mode.)

Trap entry logic (when trap_enter is pulsed):
```
mepc_reg     <= trap_mepc & 32'hFFFF_FFFC;
mcause_reg   <= trap_mcause;
mtval_reg    <= trap_mtval;
mstatus_mpie <= mstatus_mie;
mstatus_mie  <= 1'b0;
```

MRET logic (when mret_exec is pulsed):
```
mstatus_mie  <= mstatus_mpie;
mstatus_mpie <= 1'b1;
```

---

## 9. Memory Interface

### 9.1 Protocol

Single shared port for instruction fetch and data access. The protocol is a
simple valid/ready handshake:

- **Master (core) to slave (memory):**
  - `mem_addr[31:0]`: byte address (always word-aligned by the core: bits
    [1:0] = 00 for instruction fetch; for data access, the core sends a
    word-aligned address and uses wstrb for sub-word selection)
  - `mem_wdata[31:0]`: write data (valid only when wstrb != 0)
  - `mem_wstrb[3:0]`: byte write strobe (0000 = read, nonzero = write)
  - `mem_valid`: request is active

- **Slave (memory) to master (core):**
  - `mem_rdata[31:0]`: read data (valid when mem_ready and wstrb == 0)
  - `mem_ready`: transfer complete this cycle

Handshake rules:
1. The core asserts `mem_valid` and holds all outputs stable until `mem_ready`
   is sampled high on a rising clock edge.
2. The transfer completes on the cycle where both `mem_valid` and `mem_ready`
   are high.
3. The core deasserts `mem_valid` on the cycle after the transfer completes.
4. The core never asserts `mem_valid` when the FSM is not in FETCH, MEM_READ,
   or MEM_WRITE.

### 9.2 Arbitration

Since the design is multi-cycle with no pipeline, there is no contention:
instruction fetch (FETCH state) and data access (MEM_READ / MEM_WRITE states)
never occur simultaneously. The single port is time-multiplexed by the FSM.

### 9.3 Address Alignment

The core always drives word-aligned addresses on mem_addr (bits [1:0] = 00).
Sub-word byte selection for loads/stores is handled via:
- Stores: mem_wstrb selects which bytes to write (section 4.4)
- Loads: the full 32-bit word is read, then the core extracts the relevant
  byte(s) (section 4.5)

---

## 10. Reset Behavior

Reset is **synchronous, active-low** (rst_n). On any clock edge where
rst_n == 0:

1. `PC` <= RESET_VECTOR (module parameter, default 32'h0000_0000)
2. FSM state <= S_FETCH
3. `mem_valid` <= 0
4. All pipeline registers (instruction_reg, rs1_data_reg, etc.) <= 0
5. Interrupt synchronizer flip-flops <= 0
6. CSR unit resets all CSRs to their defined reset values (section 5.1)
7. Register file is NOT reset (x0 reads as 0 by construction; x1--x31 are
   undefined until software writes them)

On the first clock edge after rst_n goes high, the FSM enters S_FETCH and
begins fetching the instruction at RESET_VECTOR.

---

## 11. Instruction Decoding Reference

For the implementer's convenience, the complete mapping from instruction
encoding to decoder outputs and ALU control:

### 11.1 Opcode Map

| opcode[6:0] | Name    | Type | Decoder flag  |
|-------------|---------|------|---------------|
| 0110111     | LUI     | U    | is_lui        |
| 0010111     | AUIPC   | U    | is_auipc      |
| 1101111     | JAL     | J    | is_jal        |
| 1100111     | JALR    | I    | is_jalr       |
| 1100011     | BRANCH  | B    | is_branch     |
| 0000011     | LOAD    | I    | is_load       |
| 0100011     | STORE   | S    | is_store      |
| 0010011     | OP-IMM  | I    | is_alu_imm    |
| 0110011     | OP      | R    | is_alu_reg    |
| 0001111     | MISC-MEM| I    | is_fence      |
| 1110011     | SYSTEM  | I    | is_system     |

### 11.2 ALU Operation Selection

For R-type (OP, opcode 0110011):

| funct3 | funct7    | Instruction | alu_op |
|--------|-----------|-------------|--------|
| 000    | 0000000   | ADD         | ADD    |
| 000    | 0100000   | SUB         | SUB    |
| 001    | 0000000   | SLL         | SLL    |
| 010    | 0000000   | SLT         | SLT    |
| 011    | 0000000   | SLTU        | SLTU   |
| 100    | 0000000   | XOR         | XOR    |
| 101    | 0000000   | SRL         | SRL    |
| 101    | 0100000   | SRA         | SRA    |
| 110    | 0000000   | OR          | OR     |
| 111    | 0000000   | AND         | AND    |

For I-type (OP-IMM, opcode 0010011):

| funct3 | funct7 bits | Instruction | alu_op |
|--------|-------------|-------------|--------|
| 000    | --          | ADDI        | ADD    |
| 010    | --          | SLTI        | SLT    |
| 011    | --          | SLTIU       | SLTU   |
| 100    | --          | XORI        | XOR    |
| 110    | --          | ORI         | OR     |
| 111    | --          | ANDI        | AND    |
| 001    | 0000000     | SLLI        | SLL    |
| 101    | 0000000     | SRLI        | SRL    |
| 101    | 0100000     | SRAI        | SRA    |

For loads and stores: alu_op = ADD (address calculation).
For AUIPC: alu_op = ADD (PC + immediate).
For LUI: alu_op = ADD (0 + immediate).
For JAL: alu_op = ADD (PC + immediate, for target computation).
For JALR: alu_op = ADD (rs1 + immediate, for target computation).
For branches: alu_op = ADD (PC + immediate, for target computation).

---

## 12. Verification Interface Notes

For riscv-arch-test compliance:
- The test infrastructure writes a signature to a known memory region.
  The memory model connected to mem_* must support this.
- The core must execute the test binary starting at RESET_VECTOR, which
  should be set to the test entry point.
- ECALL with a specific register convention signals test completion.
  The test harness must detect this and dump the signature region.

The core design does not include a debug port, JTAG, or hardware breakpoints.
These are out of scope for RV32I compliance.

---

## 13. Area and Timing Expectations

Target: SKY130 sky130_fd_sc_hd standard cell library, 20 MHz (50 ns period).

The multi-cycle design has a short critical path because each cycle does
limited work:
- EXECUTE: ALU operation (32-bit add/shift/compare) is the longest
  combinational path.
- No forwarding muxes or bypass paths.

Expected synthesis results (rough estimates, to be confirmed by Yosys):
- Register file: 31 x 32 = 992 flip-flops (~3000 gates)
- ALU: ~800 gates (adder + shifter + comparator + muxes)
- Decoder: ~200 gates
- CSR unit: ~600 flip-flops for registers + ~400 gates for logic
- FSM + muxing: ~500 gates
- Total: roughly 5000--7000 gates (compare picorv32 ~4000--6000 gates)

The 50 ns clock period is generous for this complexity on SKY130 (typical
Fmax for a 32-bit datapath on sky130_fd_sc_hd is 50--100 MHz). Timing
closure should be straightforward.

---

## 14. Design Decisions Log

These decisions are specific to this microarchitecture. Record in
docs/DECISIONS.md as well.

1. **Multi-cycle over pipelined**: eliminates all hazard logic, simplifies
   verification, and easily meets 20 MHz. The performance cost (4--5 CPI vs
   ~1 CPI) is acceptable for embedded control.

2. **FSM in top module**: the FSM is tightly coupled with datapath muxing;
   separating it into its own module would require routing every control
   signal through ports with no architectural benefit.

3. **Register file not reset**: saves 992 flip-flop reset connections.
   Software must initialize registers before use (standard practice). x0
   reads as zero by combinational logic, not by reset.

4. **mtvec MODE=0 only (direct)**: vectored mode adds a multiplier
   (mcause * 4 + mtvec base) with no benefit for a single-interrupt-source
   design. The handler can branch on mcause in software.

5. **mtval set to faulting instruction/address**: costs minimal logic and
   aids debugging. Could be hardwired to 0 if area is critical.

6. **time aliases cycle**: no external timer input. The spec allows this.
   A real system would connect a memory-mapped timer (CLINT) externally.

7. **Active-low synchronous reset**: synchronous reset is simpler for
   synthesis (no async reset recovery timing). Active-low matches common
   convention and SKY130 cell library reset pins.

8. **Byte replication for stores**: rather than shifting rs2 to the correct
   lane, replicate the byte/halfword to all lanes and use wstrb. This is
   simpler combinationally and is a standard technique.

9. **CSR write check in EXECUTE, write in WRITEBACK**: separating the
   legality check from the actual write prevents modifying a CSR when the
   instruction will ultimately trap (e.g., writing a read-only CSR).

---

End of architecture document. This is sufficient for RTL implementation.
All signal names, state encodings, module interfaces, and behavioral
specifications are normative.
