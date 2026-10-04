module counter8 (clk,
    enable,
    load,
    rst_n,
    up_down,
    count,
    load_data);
 input clk;
 input enable;
 input load;
 input rst_n;
 input up_down;
 output [7:0] count;
 input [7:0] load_data;

 wire _000_;
 wire _001_;
 wire _002_;
 wire _003_;
 wire _004_;
 wire _005_;
 wire _006_;
 wire _007_;
 wire _008_;
 wire _009_;
 wire _010_;
 wire _011_;
 wire _012_;
 wire _013_;
 wire _014_;
 wire _015_;
 wire _016_;
 wire _017_;
 wire _018_;
 wire _019_;
 wire _020_;
 wire _021_;
 wire _022_;
 wire _023_;
 wire _024_;
 wire _025_;
 wire _026_;
 wire _027_;
 wire _028_;
 wire _029_;
 wire _030_;
 wire _031_;
 wire _032_;
 wire _033_;
 wire _034_;
 wire _035_;
 wire _036_;
 wire _037_;
 wire _038_;
 wire _039_;
 wire _040_;
 wire _041_;
 wire _042_;
 wire _043_;
 wire _044_;
 wire _045_;
 wire _046_;
 wire _047_;
 wire _048_;
 wire _049_;
 wire _050_;
 wire _051_;
 wire _052_;
 wire _053_;
 wire _054_;
 wire _055_;
 wire _056_;
 wire _057_;
 wire _058_;
 wire _059_;
 wire _060_;
 wire _061_;
 wire _062_;
 wire net1;
 wire net2;
 wire net3;
 wire net4;
 wire net5;
 wire net6;
 wire net7;
 wire net8;
 wire net9;
 wire net10;
 wire net11;
 wire net12;
 wire net13;
 wire net14;
 wire net15;
 wire net16;
 wire net17;
 wire net18;
 wire net19;
 wire net20;
 wire net21;
 wire net22;
 wire clknet_0_clk;
 wire clknet_1_0__leaf_clk;
 wire clknet_1_1__leaf_clk;

 sky130_fd_sc_hd__inv_2 _063_ (.A(net22),
    .Y(_008_));
 sky130_fd_sc_hd__and2_1 _064_ (.A(net1),
    .B(_008_),
    .X(_009_));
 sky130_fd_sc_hd__nand2_2 _065_ (.A(net1),
    .B(_008_),
    .Y(_010_));
 sky130_fd_sc_hd__nand2_1 _066_ (.A(net13),
    .B(_009_),
    .Y(_011_));
 sky130_fd_sc_hd__nor2_2 _067_ (.A(net1),
    .B(net22),
    .Y(_012_));
 sky130_fd_sc_hd__or3_1 _068_ (.A(net13),
    .B(net1),
    .C(net22),
    .X(_013_));
 sky130_fd_sc_hd__o2111a_1 _069_ (.A1(_008_),
    .A2(net3),
    .B1(net11),
    .C1(_011_),
    .D1(_013_),
    .X(_000_));
 sky130_fd_sc_hd__nor3b_2 _070_ (.A(net12),
    .B(net22),
    .C_N(net1),
    .Y(_014_));
 sky130_fd_sc_hd__nand2_1 _071_ (.A(net14),
    .B(net21),
    .Y(_015_));
 sky130_fd_sc_hd__or2_1 _072_ (.A(net14),
    .B(net21),
    .X(_016_));
 sky130_fd_sc_hd__a21oi_1 _073_ (.A1(_015_),
    .A2(_016_),
    .B1(net13),
    .Y(_017_));
 sky130_fd_sc_hd__a311o_1 _074_ (.A1(net13),
    .A2(_015_),
    .A3(_016_),
    .B1(_017_),
    .C1(_010_),
    .X(_018_));
 sky130_fd_sc_hd__a22oi_1 _075_ (.A1(net22),
    .A2(net4),
    .B1(_012_),
    .B2(net14),
    .Y(_019_));
 sky130_fd_sc_hd__a21boi_1 _076_ (.A1(_018_),
    .A2(_019_),
    .B1_N(net11),
    .Y(_001_));
 sky130_fd_sc_hd__nand2_1 _077_ (.A(net15),
    .B(net21),
    .Y(_020_));
 sky130_fd_sc_hd__or2_1 _078_ (.A(net15),
    .B(net21),
    .X(_021_));
 sky130_fd_sc_hd__nand2_1 _079_ (.A(_020_),
    .B(_021_),
    .Y(_022_));
 sky130_fd_sc_hd__a21boi_1 _080_ (.A1(net13),
    .A2(_016_),
    .B1_N(_015_),
    .Y(_023_));
 sky130_fd_sc_hd__xnor2_1 _081_ (.A(_022_),
    .B(_023_),
    .Y(_024_));
 sky130_fd_sc_hd__nor2_1 _082_ (.A(_010_),
    .B(_024_),
    .Y(_025_));
 sky130_fd_sc_hd__a22o_1 _083_ (.A1(net22),
    .A2(net5),
    .B1(_012_),
    .B2(net15),
    .X(_026_));
 sky130_fd_sc_hd__o21a_1 _084_ (.A1(_025_),
    .A2(_026_),
    .B1(net11),
    .X(_002_));
 sky130_fd_sc_hd__nor2_1 _085_ (.A(net16),
    .B(net21),
    .Y(_027_));
 sky130_fd_sc_hd__nand2_1 _086_ (.A(net16),
    .B(net21),
    .Y(_028_));
 sky130_fd_sc_hd__nand2b_1 _087_ (.A_N(_027_),
    .B(_028_),
    .Y(_029_));
 sky130_fd_sc_hd__o21a_1 _088_ (.A1(_022_),
    .A2(_023_),
    .B1(_020_),
    .X(_030_));
 sky130_fd_sc_hd__xnor2_1 _089_ (.A(_029_),
    .B(_030_),
    .Y(_031_));
 sky130_fd_sc_hd__nor2_1 _090_ (.A(_010_),
    .B(_031_),
    .Y(_032_));
 sky130_fd_sc_hd__a22o_1 _091_ (.A1(net22),
    .A2(net6),
    .B1(_012_),
    .B2(net16),
    .X(_033_));
 sky130_fd_sc_hd__o21a_1 _092_ (.A1(_032_),
    .A2(_033_),
    .B1(net11),
    .X(_003_));
 sky130_fd_sc_hd__or2_1 _093_ (.A(net17),
    .B(net21),
    .X(_034_));
 sky130_fd_sc_hd__nand2_1 _094_ (.A(net17),
    .B(net21),
    .Y(_035_));
 sky130_fd_sc_hd__nand2_1 _095_ (.A(_034_),
    .B(_035_),
    .Y(_036_));
 sky130_fd_sc_hd__a21o_1 _096_ (.A1(_028_),
    .A2(_030_),
    .B1(_027_),
    .X(_037_));
 sky130_fd_sc_hd__or2_1 _097_ (.A(_036_),
    .B(_037_),
    .X(_038_));
 sky130_fd_sc_hd__nand2_1 _098_ (.A(_036_),
    .B(_037_),
    .Y(_039_));
 sky130_fd_sc_hd__and3_1 _099_ (.A(_009_),
    .B(_038_),
    .C(_039_),
    .X(_040_));
 sky130_fd_sc_hd__a22o_1 _100_ (.A1(net22),
    .A2(net7),
    .B1(_012_),
    .B2(net17),
    .X(_041_));
 sky130_fd_sc_hd__o21a_1 _101_ (.A1(_040_),
    .A2(_041_),
    .B1(net11),
    .X(_004_));
 sky130_fd_sc_hd__or2_1 _102_ (.A(net18),
    .B(net21),
    .X(_042_));
 sky130_fd_sc_hd__nand2_1 _103_ (.A(net18),
    .B(net21),
    .Y(_043_));
 sky130_fd_sc_hd__nand2_1 _104_ (.A(_042_),
    .B(_043_),
    .Y(_044_));
 sky130_fd_sc_hd__a21oi_1 _105_ (.A1(_035_),
    .A2(_038_),
    .B1(_044_),
    .Y(_045_));
 sky130_fd_sc_hd__a31o_1 _106_ (.A1(_035_),
    .A2(_038_),
    .A3(_044_),
    .B1(_010_),
    .X(_046_));
 sky130_fd_sc_hd__nor2_1 _107_ (.A(_045_),
    .B(_046_),
    .Y(_047_));
 sky130_fd_sc_hd__a22o_1 _108_ (.A1(net22),
    .A2(net8),
    .B1(_012_),
    .B2(net18),
    .X(_048_));
 sky130_fd_sc_hd__o21a_1 _109_ (.A1(_047_),
    .A2(_048_),
    .B1(net11),
    .X(_005_));
 sky130_fd_sc_hd__nand2_1 _110_ (.A(net19),
    .B(_014_),
    .Y(_049_));
 sky130_fd_sc_hd__or2_1 _111_ (.A(net19),
    .B(_014_),
    .X(_050_));
 sky130_fd_sc_hd__nand2_1 _112_ (.A(_049_),
    .B(_050_),
    .Y(_051_));
 sky130_fd_sc_hd__a2111o_1 _113_ (.A1(_028_),
    .A2(_030_),
    .B1(_036_),
    .C1(_044_),
    .D1(_027_),
    .X(_052_));
 sky130_fd_sc_hd__and3_1 _114_ (.A(_035_),
    .B(_043_),
    .C(_052_),
    .X(_053_));
 sky130_fd_sc_hd__a31o_1 _115_ (.A1(_035_),
    .A2(_043_),
    .A3(_052_),
    .B1(_051_),
    .X(_054_));
 sky130_fd_sc_hd__xnor2_1 _116_ (.A(_051_),
    .B(_053_),
    .Y(_055_));
 sky130_fd_sc_hd__nor2_1 _117_ (.A(_010_),
    .B(_055_),
    .Y(_056_));
 sky130_fd_sc_hd__a22o_1 _118_ (.A1(net22),
    .A2(net9),
    .B1(_012_),
    .B2(net19),
    .X(_057_));
 sky130_fd_sc_hd__o21a_1 _119_ (.A1(_056_),
    .A2(_057_),
    .B1(net11),
    .X(_006_));
 sky130_fd_sc_hd__xnor2_1 _120_ (.A(net20),
    .B(_014_),
    .Y(_058_));
 sky130_fd_sc_hd__nand3_1 _121_ (.A(_049_),
    .B(_054_),
    .C(_058_),
    .Y(_059_));
 sky130_fd_sc_hd__a21o_1 _122_ (.A1(_049_),
    .A2(_054_),
    .B1(_058_),
    .X(_060_));
 sky130_fd_sc_hd__a22o_1 _123_ (.A1(net2),
    .A2(net10),
    .B1(_012_),
    .B2(net20),
    .X(_061_));
 sky130_fd_sc_hd__a31o_1 _124_ (.A1(_009_),
    .A2(_059_),
    .A3(_060_),
    .B1(_061_),
    .X(_062_));
 sky130_fd_sc_hd__and2_1 _125_ (.A(net11),
    .B(_062_),
    .X(_007_));
 sky130_fd_sc_hd__dfxtp_1 _126_ (.CLK(clknet_1_0__leaf_clk),
    .D(_000_),
    .Q(net13));
 sky130_fd_sc_hd__dfxtp_1 _127_ (.CLK(clknet_1_0__leaf_clk),
    .D(_001_),
    .Q(net14));
 sky130_fd_sc_hd__dfxtp_1 _128_ (.CLK(clknet_1_0__leaf_clk),
    .D(_002_),
    .Q(net15));
 sky130_fd_sc_hd__dfxtp_1 _129_ (.CLK(clknet_1_0__leaf_clk),
    .D(_003_),
    .Q(net16));
 sky130_fd_sc_hd__dfxtp_1 _130_ (.CLK(clknet_1_1__leaf_clk),
    .D(_004_),
    .Q(net17));
 sky130_fd_sc_hd__dfxtp_1 _131_ (.CLK(clknet_1_1__leaf_clk),
    .D(_005_),
    .Q(net18));
 sky130_fd_sc_hd__dfxtp_1 _132_ (.CLK(clknet_1_1__leaf_clk),
    .D(_006_),
    .Q(net19));
 sky130_fd_sc_hd__dfxtp_1 _133_ (.CLK(clknet_1_1__leaf_clk),
    .D(_007_),
    .Q(net20));
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_0_Right_0 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_1_Right_1 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_2_Right_2 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_3_Right_3 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_4_Right_4 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_5_Right_5 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_6_Right_6 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_7_Right_7 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_8_Right_8 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_9_Right_9 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_10_Right_10 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_11_Right_11 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_12_Right_12 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_13_Right_13 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_0_Left_14 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_1_Left_15 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_2_Left_16 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_3_Left_17 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_4_Left_18 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_5_Left_19 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_6_Left_20 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_7_Left_21 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_8_Left_22 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_9_Left_23 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_10_Left_24 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_11_Left_25 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_12_Left_26 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_13_Left_27 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_28 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_29 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_30 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_31 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_32 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_33 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_34 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_35 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_36 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_37 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_38 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_39 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_40 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_41 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_42 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_43 ();
 sky130_fd_sc_hd__dlymetal6s2s_1 input1 (.A(enable),
    .X(net1));
 sky130_fd_sc_hd__clkbuf_1 input2 (.A(load),
    .X(net2));
 sky130_fd_sc_hd__clkbuf_1 input3 (.A(load_data[0]),
    .X(net3));
 sky130_fd_sc_hd__clkbuf_1 input4 (.A(load_data[1]),
    .X(net4));
 sky130_fd_sc_hd__clkbuf_1 input5 (.A(load_data[2]),
    .X(net5));
 sky130_fd_sc_hd__clkbuf_1 input6 (.A(load_data[3]),
    .X(net6));
 sky130_fd_sc_hd__clkbuf_1 input7 (.A(load_data[4]),
    .X(net7));
 sky130_fd_sc_hd__clkbuf_1 input8 (.A(load_data[5]),
    .X(net8));
 sky130_fd_sc_hd__clkbuf_1 input9 (.A(load_data[6]),
    .X(net9));
 sky130_fd_sc_hd__clkbuf_1 input10 (.A(load_data[7]),
    .X(net10));
 sky130_fd_sc_hd__clkbuf_2 input11 (.A(rst_n),
    .X(net11));
 sky130_fd_sc_hd__clkbuf_1 input12 (.A(up_down),
    .X(net12));
 sky130_fd_sc_hd__buf_1 output13 (.A(net13),
    .X(count[0]));
 sky130_fd_sc_hd__buf_1 output14 (.A(net14),
    .X(count[1]));
 sky130_fd_sc_hd__buf_1 output15 (.A(net15),
    .X(count[2]));
 sky130_fd_sc_hd__buf_1 output16 (.A(net16),
    .X(count[3]));
 sky130_fd_sc_hd__buf_1 output17 (.A(net17),
    .X(count[4]));
 sky130_fd_sc_hd__buf_1 output18 (.A(net18),
    .X(count[5]));
 sky130_fd_sc_hd__buf_1 output19 (.A(net19),
    .X(count[6]));
 sky130_fd_sc_hd__buf_1 output20 (.A(net20),
    .X(count[7]));
 sky130_fd_sc_hd__clkbuf_2 fanout21 (.A(_014_),
    .X(net21));
 sky130_fd_sc_hd__clkbuf_4 fanout22 (.A(net2),
    .X(net22));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_0_clk (.A(clk),
    .X(clknet_0_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_1_0__f_clk (.A(clknet_0_clk),
    .X(clknet_1_0__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_1_1__f_clk (.A(clknet_0_clk),
    .X(clknet_1_1__leaf_clk));
 sky130_fd_sc_hd__fill_1 FILLER_0_12 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_27 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_35 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_47 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_57 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_69 ();
 sky130_fd_sc_hd__decap_3 FILLER_0_77 ();
 sky130_fd_sc_hd__decap_3 FILLER_1_48 ();
 sky130_fd_sc_hd__decap_8 FILLER_1_61 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_69 ();
 sky130_fd_sc_hd__decap_6 FILLER_1_73 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_79 ();
 sky130_fd_sc_hd__decap_6 FILLER_2_19 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_63 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_6 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_18 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_30 ();
 sky130_fd_sc_hd__decap_8 FILLER_3_42 ();
 sky130_fd_sc_hd__decap_3 FILLER_3_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_69 ();
 sky130_fd_sc_hd__decap_6 FILLER_3_73 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_79 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_7 ();
 sky130_fd_sc_hd__decap_8 FILLER_4_17 ();
 sky130_fd_sc_hd__decap_3 FILLER_4_25 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_36 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_48 ();
 sky130_fd_sc_hd__decap_8 FILLER_4_60 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_68 ();
 sky130_fd_sc_hd__decap_8 FILLER_4_72 ();
 sky130_fd_sc_hd__decap_3 FILLER_4_80 ();
 sky130_fd_sc_hd__decap_3 FILLER_5_6 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_14 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_31 ();
 sky130_fd_sc_hd__decap_4 FILLER_5_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_55 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_67 ();
 sky130_fd_sc_hd__decap_3 FILLER_5_80 ();
 sky130_fd_sc_hd__decap_8 FILLER_6_3 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_11 ();
 sky130_fd_sc_hd__decap_8 FILLER_6_20 ();
 sky130_fd_sc_hd__decap_4 FILLER_6_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_33 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_40 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_46 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_57 ();
 sky130_fd_sc_hd__decap_8 FILLER_6_69 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_7_14 ();
 sky130_fd_sc_hd__fill_2 FILLER_7_47 ();
 sky130_fd_sc_hd__decap_4 FILLER_7_52 ();
 sky130_fd_sc_hd__fill_2 FILLER_7_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_7_62 ();
 sky130_fd_sc_hd__decap_8 FILLER_7_74 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_82 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_20 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_45 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_57 ();
 sky130_fd_sc_hd__decap_4 FILLER_8_68 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_6 ();
 sky130_fd_sc_hd__decap_6 FILLER_9_18 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_24 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_28 ();
 sky130_fd_sc_hd__decap_8 FILLER_9_40 ();
 sky130_fd_sc_hd__fill_2 FILLER_9_48 ();
 sky130_fd_sc_hd__fill_2 FILLER_9_54 ();
 sky130_fd_sc_hd__fill_2 FILLER_9_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_66 ();
 sky130_fd_sc_hd__decap_6 FILLER_9_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_3 ();
 sky130_fd_sc_hd__decap_6 FILLER_10_22 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_41 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_65 ();
 sky130_fd_sc_hd__decap_6 FILLER_10_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_11_61 ();
 sky130_ef_sc_hd__decap_12 FILLER_11_68 ();
 sky130_fd_sc_hd__fill_2 FILLER_12_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_12_24 ();
 sky130_fd_sc_hd__decap_3 FILLER_12_29 ();
 sky130_fd_sc_hd__decap_8 FILLER_12_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_12_71 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_16 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_41 ();
 sky130_fd_sc_hd__decap_3 FILLER_13_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_57 ();
 sky130_fd_sc_hd__decap_8 FILLER_13_69 ();
endmodule
