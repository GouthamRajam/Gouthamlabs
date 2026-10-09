// Scan techmap: replace regular DFFs with scan DFFs
// SCD and SCE tied to 0 — chain stitching deferred to P&R

(* techmap_celltype = "sky130_fd_sc_hd__dfxtp_1" *)
module sky130_fd_sc_hd__dfxtp_1 (output Q, input CLK, input D);
  sky130_fd_sc_hd__sdfxtp_1 _TECHMAP_REPLACE_ (
    .Q(Q),
    .CLK(CLK),
    .D(D),
    .SCD(1'b0),
    .SCE(1'b0)
  );
endmodule

(* techmap_celltype = "sky130_fd_sc_hd__dfxtp_2" *)
module sky130_fd_sc_hd__dfxtp_2 (output Q, input CLK, input D);
  sky130_fd_sc_hd__sdfxtp_2 _TECHMAP_REPLACE_ (
    .Q(Q),
    .CLK(CLK),
    .D(D),
    .SCD(1'b0),
    .SCE(1'b0)
  );
endmodule

(* techmap_celltype = "sky130_fd_sc_hd__dfxtp_4" *)
module sky130_fd_sc_hd__dfxtp_4 (output Q, input CLK, input D);
  sky130_fd_sc_hd__sdfxtp_4 _TECHMAP_REPLACE_ (
    .Q(Q),
    .CLK(CLK),
    .D(D),
    .SCD(1'b0),
    .SCE(1'b0)
  );
endmodule
