// Behavioral models for sky130_fd_sc_hd cells used in picorv32_synth.v
// For formal verification only — no timing, no power pins

// D Flip-Flop, positive edge triggered
module sky130_fd_sc_hd__dfxtp_1 (output reg Q, input CLK, input D);
  always @(posedge CLK) Q <= D;
endmodule

// Inverter
module sky130_fd_sc_hd__clkinv_1 (output Y, input A);
  assign Y = ~A;
endmodule

// 2-input MUX: S=0->A0, S=1->A1
module sky130_fd_sc_hd__mux2_1 (output X, input A0, input A1, input S);
  assign X = S ? A1 : A0;
endmodule

// 2-input MUX with inverted output
module sky130_fd_sc_hd__mux2i_1 (output Y, input A0, input A1, input S);
  assign Y = ~(S ? A1 : A0);
endmodule

// 4-input MUX
module sky130_fd_sc_hd__mux4_2 (output X, input A0, input A1, input A2, input A3, input S0, input S1);
  assign X = S1 ? (S0 ? A3 : A2) : (S0 ? A1 : A0);
endmodule

// Majority-3 gate
module sky130_fd_sc_hd__maj3_1 (output X, input A, input B, input C);
  assign X = (A & B) | (A & C) | (B & C);
endmodule

// Low-power input isolation (SLEEP=1 forces output high)
module sky130_fd_sc_hd__lpflow_inputiso1p_1 (output X, input A, input SLEEP);
  assign X = A | SLEEP;
endmodule

// Low-power isolation buffer source (SLEEP=1 forces output low)
module sky130_fd_sc_hd__lpflow_isobufsrc_1 (output X, input A, input SLEEP);
  assign X = A & ~SLEEP;
endmodule

// --- AND gates ---
module sky130_fd_sc_hd__and2_0 (output X, input A, input B);
  assign X = A & B;
endmodule
module sky130_fd_sc_hd__and3_1 (output X, input A, input B, input C);
  assign X = A & B & C;
endmodule
module sky130_fd_sc_hd__and3b_1 (output X, input A_N, input B, input C);
  assign X = ~A_N & B & C;
endmodule
module sky130_fd_sc_hd__and4_1 (output X, input A, input B, input C, input D);
  assign X = A & B & C & D;
endmodule
module sky130_fd_sc_hd__and4b_1 (output X, input A_N, input B, input C, input D);
  assign X = ~A_N & B & C & D;
endmodule

// --- OR gates ---
module sky130_fd_sc_hd__or3_1 (output X, input A, input B, input C);
  assign X = A | B | C;
endmodule
module sky130_fd_sc_hd__or3b_1 (output X, input A, input B, input C_N);
  assign X = A | B | ~C_N;
endmodule
module sky130_fd_sc_hd__or4_1 (output X, input A, input B, input C, input D);
  assign X = A | B | C | D;
endmodule
module sky130_fd_sc_hd__or4b_1 (output X, input A, input B, input C, input D_N);
  assign X = A | B | C | ~D_N;
endmodule

// --- NAND gates ---
module sky130_fd_sc_hd__nand2_1 (output Y, input A, input B);
  assign Y = ~(A & B);
endmodule
module sky130_fd_sc_hd__nand2b_1 (output Y, input A_N, input B);
  assign Y = ~(~A_N & B);
endmodule
module sky130_fd_sc_hd__nand3_1 (output Y, input A, input B, input C);
  assign Y = ~(A & B & C);
endmodule
module sky130_fd_sc_hd__nand3b_1 (output Y, input A_N, input B, input C);
  assign Y = ~(~A_N & B & C);
endmodule
module sky130_fd_sc_hd__nand4_1 (output Y, input A, input B, input C, input D);
  assign Y = ~(A & B & C & D);
endmodule
module sky130_fd_sc_hd__nand4b_1 (output Y, input A_N, input B, input C, input D);
  assign Y = ~(~A_N & B & C & D);
endmodule

// --- NOR gates ---
module sky130_fd_sc_hd__nor2_1 (output Y, input A, input B);
  assign Y = ~(A | B);
endmodule
module sky130_fd_sc_hd__nor2b_1 (output Y, input A, input B_N);
  assign Y = ~(A | ~B_N);
endmodule
module sky130_fd_sc_hd__nor3_1 (output Y, input A, input B, input C);
  assign Y = ~(A | B | C);
endmodule
module sky130_fd_sc_hd__nor3b_1 (output Y, input A, input B, input C_N);
  assign Y = ~(A | B | ~C_N);
endmodule
module sky130_fd_sc_hd__nor4_1 (output Y, input A, input B, input C, input D);
  assign Y = ~(A | B | C | D);
endmodule
module sky130_fd_sc_hd__nor4b_1 (output Y, input A, input B, input C, input D_N);
  assign Y = ~(A | B | C | ~D_N);
endmodule

// --- XOR/XNOR ---
module sky130_fd_sc_hd__xor2_1 (output X, input A, input B);
  assign X = A ^ B;
endmodule
module sky130_fd_sc_hd__xnor2_1 (output Y, input A, input B);
  assign Y = ~(A ^ B);
endmodule

// --- AND-OR (aXXo) gates: Y = (A1&A2...) | (B1&B2...) | ... ---
// a21o: (A1 & A2) | B1
module sky130_fd_sc_hd__a21o_1 (output X, input A1, input A2, input B1);
  assign X = (A1 & A2) | B1;
endmodule
// a21oi: ~((A1 & A2) | B1)
module sky130_fd_sc_hd__a21oi_1 (output Y, input A1, input A2, input B1);
  assign Y = ~((A1 & A2) | B1);
endmodule
// a21boi: ~((A1 & A2) | ~B1_N)
module sky130_fd_sc_hd__a21boi_0 (output Y, input A1, input A2, input B1_N);
  assign Y = ~((A1 & A2) | ~B1_N);
endmodule
// a22o: (A1 & A2) | (B1 & B2)
module sky130_fd_sc_hd__a22o_1 (output X, input A1, input A2, input B1, input B2);
  assign X = (A1 & A2) | (B1 & B2);
endmodule
// a22oi: ~((A1 & A2) | (B1 & B2))
module sky130_fd_sc_hd__a22oi_1 (output Y, input A1, input A2, input B1, input B2);
  assign Y = ~((A1 & A2) | (B1 & B2));
endmodule
// a211o: (A1 & A2) | B1 | C1
module sky130_fd_sc_hd__a211o_1 (output X, input A1, input A2, input B1, input C1);
  assign X = (A1 & A2) | B1 | C1;
endmodule
// a211oi: ~((A1 & A2) | B1 | C1)
module sky130_fd_sc_hd__a211oi_1 (output Y, input A1, input A2, input B1, input C1);
  assign Y = ~((A1 & A2) | B1 | C1);
endmodule
// a221o: (A1 & A2) | (B1 & B2) | C1
module sky130_fd_sc_hd__a221o_1 (output X, input A1, input A2, input B1, input B2, input C1);
  assign X = (A1 & A2) | (B1 & B2) | C1;
endmodule
// a221oi: ~((A1 & A2) | (B1 & B2) | C1)
module sky130_fd_sc_hd__a221oi_1 (output Y, input A1, input A2, input B1, input B2, input C1);
  assign Y = ~((A1 & A2) | (B1 & B2) | C1);
endmodule
// a222oi: ~((A1 & A2) | (B1 & B2) | (C1 & C2))
module sky130_fd_sc_hd__a222oi_1 (output Y, input A1, input A2, input B1, input B2, input C1, input C2);
  assign Y = ~((A1 & A2) | (B1 & B2) | (C1 & C2));
endmodule
// a31o: (A1 & A2 & A3) | B1
module sky130_fd_sc_hd__a31o_1 (output X, input A1, input A2, input A3, input B1);
  assign X = (A1 & A2 & A3) | B1;
endmodule
// a31oi: ~((A1 & A2 & A3) | B1)
module sky130_fd_sc_hd__a31oi_1 (output Y, input A1, input A2, input A3, input B1);
  assign Y = ~((A1 & A2 & A3) | B1);
endmodule
// a311oi: ~((A1 & A2 & A3) | B1 | C1)
module sky130_fd_sc_hd__a311oi_1 (output Y, input A1, input A2, input A3, input B1, input C1);
  assign Y = ~((A1 & A2 & A3) | B1 | C1);
endmodule
// a32oi: ~((A1 & A2 & A3) | (B1 & B2))
module sky130_fd_sc_hd__a32oi_1 (output Y, input A1, input A2, input A3, input B1, input B2);
  assign Y = ~((A1 & A2 & A3) | (B1 & B2));
endmodule
// a41o: (A1 & A2 & A3 & A4) | B1
module sky130_fd_sc_hd__a41o_1 (output X, input A1, input A2, input A3, input A4, input B1);
  assign X = (A1 & A2 & A3 & A4) | B1;
endmodule
// a41oi: ~((A1 & A2 & A3 & A4) | B1)
module sky130_fd_sc_hd__a41oi_1 (output Y, input A1, input A2, input A3, input A4, input B1);
  assign Y = ~((A1 & A2 & A3 & A4) | B1);
endmodule
// a2111o: (A1 & A2) | B1 | C1 | D1
module sky130_fd_sc_hd__a2111o_1 (output X, input A1, input A2, input B1, input C1, input D1);
  assign X = (A1 & A2) | B1 | C1 | D1;
endmodule
// a2111oi: ~((A1 & A2) | B1 | C1 | D1)
module sky130_fd_sc_hd__a2111oi_0 (output Y, input A1, input A2, input B1, input C1, input D1);
  assign Y = ~((A1 & A2) | B1 | C1 | D1);
endmodule

// --- OR-AND (oXXa/oXXai) gates: Y = (A1|A2...) & (B1|B2...) & ... ---
// o21a: (A1 | A2) & B1
module sky130_fd_sc_hd__o21a_1 (output X, input A1, input A2, input B1);
  assign X = (A1 | A2) & B1;
endmodule
// o21ai: ~((A1 | A2) & B1)
module sky130_fd_sc_hd__o21ai_0 (output Y, input A1, input A2, input B1);
  assign Y = ~((A1 | A2) & B1);
endmodule
// o21ba: (~A1 | A2) & B1
module sky130_fd_sc_hd__o21ba_1 (output X, input A1, input A2, input B1_N);
  assign X = (A1 | A2) & ~B1_N;
endmodule
// o21bai: ~((A1 | A2) & ~B1_N)
module sky130_fd_sc_hd__o21bai_1 (output Y, input A1, input A2, input B1_N);
  assign Y = ~((A1 | A2) & ~B1_N);
endmodule
// o22a: (A1 | A2) & (B1 | B2)
module sky130_fd_sc_hd__o22a_1 (output X, input A1, input A2, input B1, input B2);
  assign X = (A1 | A2) & (B1 | B2);
endmodule
// o22ai: ~((A1 | A2) & (B1 | B2))
module sky130_fd_sc_hd__o22ai_1 (output Y, input A1, input A2, input B1, input B2);
  assign Y = ~((A1 | A2) & (B1 | B2));
endmodule
// o211a: (A1 | A2) & B1 & C1
module sky130_fd_sc_hd__o211a_1 (output X, input A1, input A2, input B1, input C1);
  assign X = (A1 | A2) & B1 & C1;
endmodule
// o211ai: ~((A1 | A2) & B1 & C1)
module sky130_fd_sc_hd__o211ai_1 (output Y, input A1, input A2, input B1, input C1);
  assign Y = ~((A1 | A2) & B1 & C1);
endmodule
// o221ai: ~((A1 | A2) & (B1 | B2) & C1)
module sky130_fd_sc_hd__o221ai_1 (output Y, input A1, input A2, input B1, input B2, input C1);
  assign Y = ~((A1 | A2) & (B1 | B2) & C1);
endmodule
// o311ai: ~((A1 | A2 | A3) & B1 & C1)
module sky130_fd_sc_hd__o311ai_0 (output Y, input A1, input A2, input A3, input B1, input C1);
  assign Y = ~((A1 | A2 | A3) & B1 & C1);
endmodule
// o31a: (A1 | A2 | A3) & B1
module sky130_fd_sc_hd__o31a_1 (output X, input A1, input A2, input A3, input B1);
  assign X = (A1 | A2 | A3) & B1;
endmodule
// o31ai: ~((A1 | A2 | A3) & B1)
module sky130_fd_sc_hd__o31ai_1 (output Y, input A1, input A2, input A3, input B1);
  assign Y = ~((A1 | A2 | A3) & B1);
endmodule
// o32ai: ~((A1 | A2 | A3) & (B1 | B2))
module sky130_fd_sc_hd__o32ai_1 (output Y, input A1, input A2, input A3, input B1, input B2);
  assign Y = ~((A1 | A2 | A3) & (B1 | B2));
endmodule
// o41a: (A1 | A2 | A3 | A4) & B1
module sky130_fd_sc_hd__o41a_1 (output X, input A1, input A2, input A3, input A4, input B1);
  assign X = (A1 | A2 | A3 | A4) & B1;
endmodule
// o41ai: ~((A1 | A2 | A3 | A4) & B1)
module sky130_fd_sc_hd__o41ai_1 (output Y, input A1, input A2, input A3, input A4, input B1);
  assign Y = ~((A1 | A2 | A3 | A4) & B1);
endmodule
// o2111ai: ~((A1 | A2) & B1 & C1 & D1)
module sky130_fd_sc_hd__o2111ai_1 (output Y, input A1, input A2, input B1, input C1, input D1);
  assign Y = ~((A1 | A2) & B1 & C1 & D1);
endmodule
// o2bb2ai: ~((!A1_N & !A2_N) | (B1 & B2))  [two inverted inputs on first group]
module sky130_fd_sc_hd__o2bb2ai_1 (output Y, input A1_N, input A2_N, input B1, input B2);
  assign Y = ~((!A1_N | !A2_N) & (B1 | B2));
endmodule

// Scan DFF cells for DFT
module sky130_fd_sc_hd__sdfxtp_1 (output reg Q, input CLK, input D, input SCD, input SCE);
  always @(posedge CLK) Q <= SCE ? SCD : D;
endmodule

module sky130_fd_sc_hd__sdfxtp_2 (output reg Q, input CLK, input D, input SCD, input SCE);
  always @(posedge CLK) Q <= SCE ? SCD : D;
endmodule

module sky130_fd_sc_hd__sdfxtp_4 (output reg Q, input CLK, input D, input SCD, input SCE);
  always @(posedge CLK) Q <= SCE ? SCD : D;
endmodule

// --- Additional cells needed by s2s_rv32i ---

// a311o: (A1 & A2 & A3) | B1 | C1
module sky130_fd_sc_hd__a311o_1 (output X, input A1, input A2, input A3, input B1, input C1);
  assign X = (A1 & A2 & A3) | B1 | C1;
endmodule

// nand4bb: ~(~A_N & ~B_N & C & D)
module sky130_fd_sc_hd__nand4bb_1 (output Y, input A_N, input B_N, input C, input D);
  assign Y = ~(~A_N & ~B_N & C & D);
endmodule

// nor4bb: Y = ~(A | B | ~C_N | ~D_N)
module sky130_fd_sc_hd__nor4bb_1 (output Y, input A, input B, input C_N, input D_N);
  assign Y = ~(A | B | ~C_N | ~D_N);
endmodule

// o221a: (A1 | A2) & (B1 | B2) & C1
module sky130_fd_sc_hd__o221a_1 (output X, input A1, input A2, input B1, input B2, input C1);
  assign X = (A1 | A2) & (B1 | B2) & C1;
endmodule

// a2bb2oi: ~((!A1_N & !A2_N) | (B1 & B2))
module sky130_fd_sc_hd__a2bb2oi_1 (output Y, input A1_N, input A2_N, input B1, input B2);
  assign Y = ~((!A1_N & !A2_N) | (B1 & B2));
endmodule

// a32o: (A1 & A2 & A3) | (B1 & B2)
module sky130_fd_sc_hd__a32o_1 (output X, input A1, input A2, input A3, input B1, input B2);
  assign X = (A1 & A2 & A3) | (B1 & B2);
endmodule

// o311a: (A1 | A2 | A3) & B1 & C1
module sky130_fd_sc_hd__o311a_1 (output X, input A1, input A2, input A3, input B1, input C1);
  assign X = (A1 | A2 | A3) & B1 & C1;
endmodule

// o32a: (A1 | A2 | A3) & (B1 | B2)
module sky130_fd_sc_hd__o32a_1 (output X, input A1, input A2, input A3, input B1, input B2);
  assign X = (A1 | A2 | A3) & (B1 | B2);
endmodule

// a21bo: (A1 & A2) | (!B1_N)
module sky130_fd_sc_hd__a21bo_1 (output X, input A1, input A2, input B1_N);
  assign X = (A1 & A2) | (~B1_N);
endmodule

// o2111a: (A1 | A2) & B1 & C1 & D1
module sky130_fd_sc_hd__o2111a_1 (output X, input A1, input A2, input B1, input C1, input D1);
  assign X = (A1 | A2) & B1 & C1 & D1;
endmodule

// xnor3: 3-input XNOR
module sky130_fd_sc_hd__xnor3_1 (output X, input A, input B, input C);
  assign X = ~(A ^ B ^ C);
endmodule
