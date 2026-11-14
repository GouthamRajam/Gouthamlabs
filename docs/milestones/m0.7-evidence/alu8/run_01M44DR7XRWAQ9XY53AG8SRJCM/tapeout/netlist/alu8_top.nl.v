module alu8_top (clk,
    flag_c,
    flag_n,
    flag_v,
    flag_z,
    rst_n,
    a,
    b,
    op,
    result);
 input clk;
 output flag_c;
 output flag_n;
 output flag_v;
 output flag_z;
 input rst_n;
 input [7:0] a;
 input [7:0] b;
 input [2:0] op;
 output [7:0] result;

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
 wire _063_;
 wire _064_;
 wire _065_;
 wire _066_;
 wire _067_;
 wire _068_;
 wire _069_;
 wire _070_;
 wire _071_;
 wire _072_;
 wire _073_;
 wire _074_;
 wire _075_;
 wire _076_;
 wire _077_;
 wire _078_;
 wire _079_;
 wire _080_;
 wire _081_;
 wire _082_;
 wire _083_;
 wire _084_;
 wire _085_;
 wire _086_;
 wire _087_;
 wire _088_;
 wire _089_;
 wire _090_;
 wire _091_;
 wire _092_;
 wire _093_;
 wire _094_;
 wire _095_;
 wire _096_;
 wire _097_;
 wire _098_;
 wire _099_;
 wire _100_;
 wire _101_;
 wire _102_;
 wire _103_;
 wire _104_;
 wire _105_;
 wire _106_;
 wire _107_;
 wire _108_;
 wire _109_;
 wire _110_;
 wire _111_;
 wire _112_;
 wire _113_;
 wire _114_;
 wire _115_;
 wire _116_;
 wire _117_;
 wire _118_;
 wire _119_;
 wire _120_;
 wire _121_;
 wire _122_;
 wire _123_;
 wire _124_;
 wire _125_;
 wire _126_;
 wire _127_;
 wire _128_;
 wire _129_;
 wire _130_;
 wire _131_;
 wire _132_;
 wire _133_;
 wire _134_;
 wire _135_;
 wire _136_;
 wire _137_;
 wire _138_;
 wire _139_;
 wire _140_;
 wire _141_;
 wire _142_;
 wire _143_;
 wire _144_;
 wire _145_;
 wire _146_;
 wire _147_;
 wire _148_;
 wire _149_;
 wire _150_;
 wire _151_;
 wire _152_;
 wire _153_;
 wire _154_;
 wire _155_;
 wire _156_;
 wire _157_;
 wire _158_;
 wire _159_;
 wire _160_;
 wire _161_;
 wire _162_;
 wire _163_;
 wire _164_;
 wire _165_;
 wire _166_;
 wire _167_;
 wire _168_;
 wire _169_;
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
 wire net23;
 wire net24;
 wire net25;
 wire net26;
 wire net27;
 wire net28;
 wire net29;
 wire net30;
 wire net31;
 wire net32;
 wire net33;
 wire net34;
 wire net35;
 wire net36;
 wire net37;
 wire net38;
 wire net39;
 wire net40;
 wire net41;
 wire net42;
 wire net43;
 wire net44;
 wire net45;
 wire clknet_0_clk;
 wire clknet_1_0__leaf_clk;
 wire clknet_1_1__leaf_clk;
 wire net46;
 wire net47;
 wire net48;
 wire net49;
 wire net50;
 wire net51;
 wire net52;
 wire net53;

 sky130_fd_sc_hd__inv_2 _170_ (.A(net44),
    .Y(_111_));
 sky130_fd_sc_hd__inv_2 _171_ (.A(net17),
    .Y(_112_));
 sky130_fd_sc_hd__and2b_2 _172_ (.A_N(net19),
    .B(net18),
    .X(_113_));
 sky130_fd_sc_hd__and2_1 _173_ (.A(_112_),
    .B(_113_),
    .X(_114_));
 sky130_fd_sc_hd__nand2_2 _174_ (.A(net35),
    .B(_113_),
    .Y(_115_));
 sky130_fd_sc_hd__nand2_1 _175_ (.A(net16),
    .B(net40),
    .Y(_116_));
 sky130_fd_sc_hd__and3_1 _176_ (.A(net19),
    .B(net17),
    .C(net18),
    .X(_117_));
 sky130_fd_sc_hd__nand3_1 _177_ (.A(net19),
    .B(net17),
    .C(net18),
    .Y(_118_));
 sky130_fd_sc_hd__or3b_4 _178_ (.A(net19),
    .B(net18),
    .C_N(net17),
    .X(_119_));
 sky130_fd_sc_hd__nand2_4 _179_ (.A(net34),
    .B(_119_),
    .Y(_120_));
 sky130_fd_sc_hd__xor2_1 _180_ (.A(net15),
    .B(_120_),
    .X(_121_));
 sky130_fd_sc_hd__and2_1 _181_ (.A(net7),
    .B(_121_),
    .X(_122_));
 sky130_fd_sc_hd__nor2_1 _182_ (.A(net7),
    .B(_121_),
    .Y(_123_));
 sky130_fd_sc_hd__nor2_1 _183_ (.A(_122_),
    .B(_123_),
    .Y(_124_));
 sky130_fd_sc_hd__xor2_1 _184_ (.A(net14),
    .B(_120_),
    .X(_125_));
 sky130_fd_sc_hd__or2_1 _185_ (.A(net41),
    .B(_125_),
    .X(_126_));
 sky130_fd_sc_hd__or3b_1 _186_ (.A(net13),
    .B(_117_),
    .C_N(_119_),
    .X(_127_));
 sky130_fd_sc_hd__a21bo_1 _187_ (.A1(net34),
    .A2(_119_),
    .B1_N(net13),
    .X(_128_));
 sky130_fd_sc_hd__and3_1 _188_ (.A(net5),
    .B(_127_),
    .C(_128_),
    .X(_129_));
 sky130_fd_sc_hd__nand2_1 _189_ (.A(net41),
    .B(_125_),
    .Y(_130_));
 sky130_fd_sc_hd__a21o_1 _190_ (.A1(net41),
    .A2(_125_),
    .B1(_129_),
    .X(_131_));
 sky130_fd_sc_hd__a21oi_1 _191_ (.A1(_127_),
    .A2(_128_),
    .B1(net5),
    .Y(_132_));
 sky130_fd_sc_hd__nor2_1 _192_ (.A(_129_),
    .B(_132_),
    .Y(_133_));
 sky130_fd_sc_hd__xor2_1 _193_ (.A(net12),
    .B(_120_),
    .X(_134_));
 sky130_fd_sc_hd__nor2_1 _194_ (.A(net42),
    .B(_134_),
    .Y(_135_));
 sky130_fd_sc_hd__or2_1 _195_ (.A(net42),
    .B(_134_),
    .X(_136_));
 sky130_fd_sc_hd__xnor2_1 _196_ (.A(net11),
    .B(_120_),
    .Y(_137_));
 sky130_fd_sc_hd__and2b_1 _197_ (.A_N(_137_),
    .B(net3),
    .X(_138_));
 sky130_fd_sc_hd__xnor2_1 _198_ (.A(net3),
    .B(_137_),
    .Y(_139_));
 sky130_fd_sc_hd__or3b_1 _199_ (.A(net44),
    .B(_117_),
    .C_N(_119_),
    .X(_140_));
 sky130_fd_sc_hd__a21o_1 _200_ (.A1(net33),
    .A2(_119_),
    .B1(net36),
    .X(_141_));
 sky130_fd_sc_hd__and3_1 _201_ (.A(net2),
    .B(_140_),
    .C(_141_),
    .X(_142_));
 sky130_fd_sc_hd__a21o_1 _202_ (.A1(_140_),
    .A2(_141_),
    .B1(net2),
    .X(_143_));
 sky130_fd_sc_hd__and2b_1 _203_ (.A_N(_142_),
    .B(_143_),
    .X(_144_));
 sky130_fd_sc_hd__and2_1 _204_ (.A(net38),
    .B(net1),
    .X(_145_));
 sky130_fd_sc_hd__mux2_1 _205_ (.A0(_120_),
    .A1(net1),
    .S(net37),
    .X(_146_));
 sky130_fd_sc_hd__a21o_1 _206_ (.A1(_143_),
    .A2(_146_),
    .B1(_142_),
    .X(_147_));
 sky130_fd_sc_hd__and2_1 _207_ (.A(_139_),
    .B(_147_),
    .X(_148_));
 sky130_fd_sc_hd__and2_1 _208_ (.A(net42),
    .B(_134_),
    .X(_149_));
 sky130_fd_sc_hd__a211o_1 _209_ (.A1(_139_),
    .A2(_147_),
    .B1(_149_),
    .C1(_138_),
    .X(_150_));
 sky130_fd_sc_hd__nor2_1 _210_ (.A(_135_),
    .B(_149_),
    .Y(_151_));
 sky130_fd_sc_hd__and3_1 _211_ (.A(_133_),
    .B(_136_),
    .C(_150_),
    .X(_152_));
 sky130_fd_sc_hd__and2_1 _212_ (.A(_126_),
    .B(_131_),
    .X(_153_));
 sky130_fd_sc_hd__and2_1 _213_ (.A(_126_),
    .B(_130_),
    .X(_154_));
 sky130_fd_sc_hd__a41o_1 _214_ (.A1(_133_),
    .A2(_136_),
    .A3(_150_),
    .A4(_154_),
    .B1(_153_),
    .X(_155_));
 sky130_fd_sc_hd__a21oi_1 _215_ (.A1(_124_),
    .A2(_155_),
    .B1(_122_),
    .Y(_156_));
 sky130_fd_sc_hd__and2b_1 _216_ (.A_N(_156_),
    .B(net40),
    .X(_157_));
 sky130_fd_sc_hd__xnor2_1 _217_ (.A(net40),
    .B(_156_),
    .Y(_158_));
 sky130_fd_sc_hd__xor2_2 _218_ (.A(net16),
    .B(_120_),
    .X(_159_));
 sky130_fd_sc_hd__nand2_1 _219_ (.A(_158_),
    .B(_159_),
    .Y(_160_));
 sky130_fd_sc_hd__o211a_1 _220_ (.A1(net17),
    .A2(net18),
    .B1(net34),
    .C1(_119_),
    .X(_161_));
 sky130_fd_sc_hd__a21oi_4 _221_ (.A1(net19),
    .A2(net34),
    .B1(_161_),
    .Y(_162_));
 sky130_fd_sc_hd__o21a_1 _222_ (.A1(_158_),
    .A2(_159_),
    .B1(_162_),
    .X(_163_));
 sky130_fd_sc_hd__or2_1 _223_ (.A(net16),
    .B(net40),
    .X(_164_));
 sky130_fd_sc_hd__and3b_2 _224_ (.A_N(net18),
    .B(net19),
    .C(net35),
    .X(_165_));
 sky130_fd_sc_hd__a22o_1 _225_ (.A1(net17),
    .A2(_113_),
    .B1(_116_),
    .B2(_165_),
    .X(_166_));
 sky130_fd_sc_hd__and4b_2 _226_ (.A_N(net11),
    .B(net19),
    .C(net35),
    .D(net18),
    .X(_167_));
 sky130_fd_sc_hd__and3b_1 _227_ (.A_N(net38),
    .B(net36),
    .C(net40),
    .X(_168_));
 sky130_fd_sc_hd__a221o_1 _228_ (.A1(_164_),
    .A2(_166_),
    .B1(_167_),
    .B2(_168_),
    .C1(_114_),
    .X(_169_));
 sky130_fd_sc_hd__and4bb_2 _229_ (.A_N(net11),
    .B_N(net18),
    .C(net17),
    .D(net19),
    .X(_012_));
 sky130_fd_sc_hd__mux4_1 _230_ (.A0(net40),
    .A1(net7),
    .A2(net41),
    .A3(net5),
    .S0(net38),
    .S1(net44),
    .X(_013_));
 sky130_fd_sc_hd__and4b_1 _231_ (.A_N(net18),
    .B(net17),
    .C(net19),
    .D(net11),
    .X(_014_));
 sky130_fd_sc_hd__mux2_1 _232_ (.A0(net2),
    .A1(net1),
    .S(net37),
    .X(_015_));
 sky130_fd_sc_hd__mux4_1 _233_ (.A0(net42),
    .A1(net3),
    .A2(net2),
    .A3(net1),
    .S0(net37),
    .S1(net44),
    .X(_016_));
 sky130_fd_sc_hd__a221o_1 _234_ (.A1(_012_),
    .A2(_013_),
    .B1(_014_),
    .B2(_016_),
    .C1(_169_),
    .X(_017_));
 sky130_fd_sc_hd__a21oi_1 _235_ (.A1(_160_),
    .A2(_163_),
    .B1(_017_),
    .Y(_018_));
 sky130_fd_sc_hd__a21oi_1 _236_ (.A1(_114_),
    .A2(_116_),
    .B1(_018_),
    .Y(_019_));
 sky130_fd_sc_hd__and2_1 _237_ (.A(net43),
    .B(_019_),
    .X(_000_));
 sky130_fd_sc_hd__a21o_1 _238_ (.A1(_158_),
    .A2(_159_),
    .B1(_157_),
    .X(_020_));
 sky130_fd_sc_hd__nand2b_1 _239_ (.A_N(_156_),
    .B(_020_),
    .Y(_021_));
 sky130_fd_sc_hd__a21bo_1 _240_ (.A1(net8),
    .A2(_159_),
    .B1_N(_156_),
    .X(_022_));
 sky130_fd_sc_hd__and4_1 _241_ (.A(net43),
    .B(_162_),
    .C(_021_),
    .D(_022_),
    .X(_001_));
 sky130_fd_sc_hd__xor2_1 _242_ (.A(_124_),
    .B(_155_),
    .X(_023_));
 sky130_fd_sc_hd__and2b_1 _243_ (.A_N(net37),
    .B(net1),
    .X(_024_));
 sky130_fd_sc_hd__mux2_1 _244_ (.A0(net3),
    .A1(net2),
    .S(net37),
    .X(_025_));
 sky130_fd_sc_hd__mux2_1 _245_ (.A0(_024_),
    .A1(_025_),
    .S(net36),
    .X(_026_));
 sky130_fd_sc_hd__and2b_1 _246_ (.A_N(net38),
    .B(net7),
    .X(_027_));
 sky130_fd_sc_hd__a21oi_1 _247_ (.A1(net38),
    .A2(net40),
    .B1(_027_),
    .Y(_028_));
 sky130_fd_sc_hd__nor2_1 _248_ (.A(net45),
    .B(_028_),
    .Y(_029_));
 sky130_fd_sc_hd__o31a_1 _249_ (.A1(net15),
    .A2(net7),
    .A3(net35),
    .B1(_113_),
    .X(_030_));
 sky130_fd_sc_hd__a221o_1 _250_ (.A1(_014_),
    .A2(_026_),
    .B1(_029_),
    .B2(_167_),
    .C1(_030_),
    .X(_031_));
 sky130_fd_sc_hd__and2_1 _251_ (.A(net41),
    .B(net38),
    .X(_032_));
 sky130_fd_sc_hd__mux4_1 _252_ (.A0(net7),
    .A1(net6),
    .A2(net5),
    .A3(net4),
    .S0(net39),
    .S1(net45),
    .X(_033_));
 sky130_fd_sc_hd__a22o_1 _253_ (.A1(_124_),
    .A2(_165_),
    .B1(_012_),
    .B2(_033_),
    .X(_034_));
 sky130_fd_sc_hd__a211o_1 _254_ (.A1(_162_),
    .A2(_023_),
    .B1(_031_),
    .C1(_034_),
    .X(_035_));
 sky130_fd_sc_hd__o21ai_1 _255_ (.A1(_115_),
    .A2(_122_),
    .B1(_035_),
    .Y(_036_));
 sky130_fd_sc_hd__nor2_1 _256_ (.A(_129_),
    .B(_152_),
    .Y(_037_));
 sky130_fd_sc_hd__nor2_1 _257_ (.A(_165_),
    .B(_037_),
    .Y(_038_));
 sky130_fd_sc_hd__or3b_1 _258_ (.A(_161_),
    .B(_038_),
    .C_N(_154_),
    .X(_039_));
 sky130_fd_sc_hd__or3b_1 _259_ (.A(_154_),
    .B(_037_),
    .C_N(_162_),
    .X(_040_));
 sky130_fd_sc_hd__mux4_1 _260_ (.A0(net41),
    .A1(net42),
    .A2(net5),
    .A3(net3),
    .S0(net44),
    .S1(net37),
    .X(_041_));
 sky130_fd_sc_hd__and2_1 _261_ (.A(_012_),
    .B(_041_),
    .X(_042_));
 sky130_fd_sc_hd__mux2_1 _262_ (.A0(net41),
    .A1(net7),
    .S(net38),
    .X(_043_));
 sky130_fd_sc_hd__and3b_1 _263_ (.A_N(net38),
    .B(net45),
    .C(net40),
    .X(_044_));
 sky130_fd_sc_hd__a21o_1 _264_ (.A1(net36),
    .A2(_043_),
    .B1(_044_),
    .X(_045_));
 sky130_fd_sc_hd__o31a_1 _265_ (.A1(net14),
    .A2(net41),
    .A3(net35),
    .B1(_113_),
    .X(_046_));
 sky130_fd_sc_hd__a31o_1 _266_ (.A1(_111_),
    .A2(_014_),
    .A3(_015_),
    .B1(_046_),
    .X(_047_));
 sky130_fd_sc_hd__a211oi_1 _267_ (.A1(_167_),
    .A2(_045_),
    .B1(_047_),
    .C1(_042_),
    .Y(_048_));
 sky130_fd_sc_hd__a32o_1 _268_ (.A1(_039_),
    .A2(_040_),
    .A3(_048_),
    .B1(_130_),
    .B2(_114_),
    .X(_049_));
 sky130_fd_sc_hd__a21o_1 _269_ (.A1(_136_),
    .A2(_150_),
    .B1(_133_),
    .X(_050_));
 sky130_fd_sc_hd__and3b_1 _270_ (.A_N(_152_),
    .B(_162_),
    .C(_050_),
    .X(_051_));
 sky130_fd_sc_hd__mux4_1 _271_ (.A0(net5),
    .A1(net41),
    .A2(net7),
    .A3(net40),
    .S0(net38),
    .S1(net45),
    .X(_052_));
 sky130_fd_sc_hd__mux4_1 _272_ (.A0(net5),
    .A1(net42),
    .A2(net3),
    .A3(net2),
    .S0(net37),
    .S1(net44),
    .X(_053_));
 sky130_fd_sc_hd__and3_1 _273_ (.A(_111_),
    .B(_014_),
    .C(_024_),
    .X(_054_));
 sky130_fd_sc_hd__or3_1 _274_ (.A(net13),
    .B(net5),
    .C(net35),
    .X(_055_));
 sky130_fd_sc_hd__a22o_1 _275_ (.A1(_167_),
    .A2(_052_),
    .B1(_055_),
    .B2(_113_),
    .X(_056_));
 sky130_fd_sc_hd__a211o_1 _276_ (.A1(_012_),
    .A2(_053_),
    .B1(_054_),
    .C1(_056_),
    .X(_057_));
 sky130_fd_sc_hd__a211o_1 _277_ (.A1(_133_),
    .A2(_165_),
    .B1(_051_),
    .C1(_057_),
    .X(_058_));
 sky130_fd_sc_hd__o21ai_1 _278_ (.A1(_115_),
    .A2(_129_),
    .B1(_058_),
    .Y(_059_));
 sky130_fd_sc_hd__nor2_1 _279_ (.A(_138_),
    .B(_148_),
    .Y(_060_));
 sky130_fd_sc_hd__a21oi_1 _280_ (.A1(_162_),
    .A2(_060_),
    .B1(_165_),
    .Y(_061_));
 sky130_fd_sc_hd__and4_1 _281_ (.A(net11),
    .B(net19),
    .C(net35),
    .D(net18),
    .X(_062_));
 sky130_fd_sc_hd__o31a_1 _282_ (.A1(net35),
    .A2(net42),
    .A3(net12),
    .B1(_113_),
    .X(_063_));
 sky130_fd_sc_hd__mux2_1 _283_ (.A0(net42),
    .A1(net5),
    .S(net37),
    .X(_064_));
 sky130_fd_sc_hd__mux2_1 _284_ (.A0(_043_),
    .A1(_064_),
    .S(net36),
    .X(_065_));
 sky130_fd_sc_hd__a22o_1 _285_ (.A1(_012_),
    .A2(_016_),
    .B1(_065_),
    .B2(_167_),
    .X(_066_));
 sky130_fd_sc_hd__a211oi_1 _286_ (.A1(_168_),
    .A2(_062_),
    .B1(_063_),
    .C1(_066_),
    .Y(_067_));
 sky130_fd_sc_hd__o21ai_1 _287_ (.A1(_138_),
    .A2(_148_),
    .B1(_162_),
    .Y(_068_));
 sky130_fd_sc_hd__mux2_1 _288_ (.A0(_068_),
    .A1(_061_),
    .S(_151_),
    .X(_069_));
 sky130_fd_sc_hd__a2bb2o_1 _289_ (.A1_N(_115_),
    .A2_N(_149_),
    .B1(_067_),
    .B2(_069_),
    .X(_070_));
 sky130_fd_sc_hd__or2_1 _290_ (.A(_139_),
    .B(_147_),
    .X(_071_));
 sky130_fd_sc_hd__and3b_1 _291_ (.A_N(_148_),
    .B(_162_),
    .C(_071_),
    .X(_072_));
 sky130_fd_sc_hd__o31a_1 _292_ (.A1(net11),
    .A2(net35),
    .A3(net3),
    .B1(_113_),
    .X(_073_));
 sky130_fd_sc_hd__a21o_1 _293_ (.A1(_029_),
    .A2(_062_),
    .B1(_073_),
    .X(_074_));
 sky130_fd_sc_hd__mux4_1 _294_ (.A0(net3),
    .A1(net42),
    .A2(net5),
    .A3(net41),
    .S0(net39),
    .S1(net44),
    .X(_075_));
 sky130_fd_sc_hd__a22o_1 _295_ (.A1(_012_),
    .A2(_026_),
    .B1(_075_),
    .B2(_167_),
    .X(_076_));
 sky130_fd_sc_hd__a211o_1 _296_ (.A1(_139_),
    .A2(_165_),
    .B1(_074_),
    .C1(_076_),
    .X(_077_));
 sky130_fd_sc_hd__o22a_1 _297_ (.A1(_115_),
    .A2(_138_),
    .B1(_072_),
    .B2(_077_),
    .X(_078_));
 sky130_fd_sc_hd__xor2_1 _298_ (.A(_144_),
    .B(_146_),
    .X(_079_));
 sky130_fd_sc_hd__mux2_1 _299_ (.A0(net2),
    .A1(net3),
    .S(net37),
    .X(_080_));
 sky130_fd_sc_hd__or2_1 _300_ (.A(net44),
    .B(_080_),
    .X(_081_));
 sky130_fd_sc_hd__o211a_1 _301_ (.A1(net36),
    .A2(_064_),
    .B1(_081_),
    .C1(_167_),
    .X(_082_));
 sky130_fd_sc_hd__o31a_1 _302_ (.A1(net44),
    .A2(net35),
    .A3(net2),
    .B1(_113_),
    .X(_083_));
 sky130_fd_sc_hd__a32o_1 _303_ (.A1(net36),
    .A2(_012_),
    .A3(_015_),
    .B1(_045_),
    .B2(_062_),
    .X(_084_));
 sky130_fd_sc_hd__or3_1 _304_ (.A(_082_),
    .B(_083_),
    .C(_084_),
    .X(_085_));
 sky130_fd_sc_hd__a221o_1 _305_ (.A1(_144_),
    .A2(_165_),
    .B1(_079_),
    .B2(_162_),
    .C1(_085_),
    .X(_086_));
 sky130_fd_sc_hd__o21ai_1 _306_ (.A1(_115_),
    .A2(_142_),
    .B1(_086_),
    .Y(_087_));
 sky130_fd_sc_hd__a2bb2o_1 _307_ (.A1_N(_145_),
    .A2_N(_161_),
    .B1(net17),
    .B2(_113_),
    .X(_088_));
 sky130_fd_sc_hd__o21a_1 _308_ (.A1(net39),
    .A2(net1),
    .B1(_088_),
    .X(_089_));
 sky130_fd_sc_hd__mux4_1 _309_ (.A0(net1),
    .A1(net2),
    .A2(net3),
    .A3(net42),
    .S0(net37),
    .S1(net44),
    .X(_090_));
 sky130_fd_sc_hd__and2_1 _310_ (.A(_167_),
    .B(_090_),
    .X(_091_));
 sky130_fd_sc_hd__a32o_1 _311_ (.A1(net36),
    .A2(_012_),
    .A3(_024_),
    .B1(_052_),
    .B2(_062_),
    .X(_092_));
 sky130_fd_sc_hd__or4_1 _312_ (.A(_114_),
    .B(_089_),
    .C(_091_),
    .D(_092_),
    .X(_093_));
 sky130_fd_sc_hd__o21ai_1 _313_ (.A1(_115_),
    .A2(_145_),
    .B1(_093_),
    .Y(_094_));
 sky130_fd_sc_hd__and4b_1 _314_ (.A_N(_078_),
    .B(_087_),
    .C(_094_),
    .D(net43),
    .X(_095_));
 sky130_fd_sc_hd__and3_1 _315_ (.A(_059_),
    .B(_070_),
    .C(_095_),
    .X(_096_));
 sky130_fd_sc_hd__and4b_1 _316_ (.A_N(_019_),
    .B(_036_),
    .C(_049_),
    .D(_096_),
    .X(_002_));
 sky130_fd_sc_hd__nand2_1 _317_ (.A(net33),
    .B(_094_),
    .Y(_097_));
 sky130_fd_sc_hd__o211a_1 _318_ (.A1(net50),
    .A2(net33),
    .B1(_097_),
    .C1(net43),
    .X(_003_));
 sky130_fd_sc_hd__nand2_1 _319_ (.A(net33),
    .B(_087_),
    .Y(_098_));
 sky130_fd_sc_hd__o211a_1 _320_ (.A1(net51),
    .A2(net33),
    .B1(_098_),
    .C1(net43),
    .X(_004_));
 sky130_fd_sc_hd__or2_1 _321_ (.A(net53),
    .B(net33),
    .X(_099_));
 sky130_fd_sc_hd__o211a_1 _322_ (.A1(_117_),
    .A2(_078_),
    .B1(_099_),
    .C1(net43),
    .X(_005_));
 sky130_fd_sc_hd__nand2_1 _323_ (.A(net33),
    .B(_070_),
    .Y(_100_));
 sky130_fd_sc_hd__o211a_1 _324_ (.A1(net47),
    .A2(net33),
    .B1(_100_),
    .C1(net43),
    .X(_006_));
 sky130_fd_sc_hd__nand2_1 _325_ (.A(net33),
    .B(_059_),
    .Y(_101_));
 sky130_fd_sc_hd__o211a_1 _326_ (.A1(net49),
    .A2(net33),
    .B1(_101_),
    .C1(net43),
    .X(_007_));
 sky130_fd_sc_hd__nand2_1 _327_ (.A(net34),
    .B(_049_),
    .Y(_102_));
 sky130_fd_sc_hd__o211a_1 _328_ (.A1(net46),
    .A2(net34),
    .B1(_102_),
    .C1(net43),
    .X(_008_));
 sky130_fd_sc_hd__nand2_1 _329_ (.A(net34),
    .B(_036_),
    .Y(_103_));
 sky130_fd_sc_hd__o211a_1 _330_ (.A1(net48),
    .A2(net34),
    .B1(_103_),
    .C1(net43),
    .X(_009_));
 sky130_fd_sc_hd__or2_1 _331_ (.A(net52),
    .B(net34),
    .X(_104_));
 sky130_fd_sc_hd__o211a_1 _332_ (.A1(_117_),
    .A2(_019_),
    .B1(_104_),
    .C1(net20),
    .X(_010_));
 sky130_fd_sc_hd__a22o_1 _333_ (.A1(_014_),
    .A2(_053_),
    .B1(_062_),
    .B2(_065_),
    .X(_105_));
 sky130_fd_sc_hd__a21o_1 _334_ (.A1(net38),
    .A2(net40),
    .B1(net45),
    .X(_106_));
 sky130_fd_sc_hd__o311a_1 _335_ (.A1(net36),
    .A2(_027_),
    .A3(_032_),
    .B1(_106_),
    .C1(_012_),
    .X(_107_));
 sky130_fd_sc_hd__or2_1 _336_ (.A(net36),
    .B(_080_),
    .X(_108_));
 sky130_fd_sc_hd__o211a_1 _337_ (.A1(net45),
    .A2(_145_),
    .B1(_167_),
    .C1(_108_),
    .X(_109_));
 sky130_fd_sc_hd__a21o_1 _338_ (.A1(_162_),
    .A2(_020_),
    .B1(_105_),
    .X(_110_));
 sky130_fd_sc_hd__o31a_1 _339_ (.A1(_107_),
    .A2(_109_),
    .A3(_110_),
    .B1(net20),
    .X(_011_));
 sky130_fd_sc_hd__dfxtp_1 _340_ (.CLK(clknet_1_1__leaf_clk),
    .D(_000_),
    .Q(net22));
 sky130_fd_sc_hd__dfxtp_1 _341_ (.CLK(clknet_1_1__leaf_clk),
    .D(_001_),
    .Q(net23));
 sky130_fd_sc_hd__dfxtp_1 _342_ (.CLK(clknet_1_1__leaf_clk),
    .D(_002_),
    .Q(net24));
 sky130_fd_sc_hd__dfxtp_1 _343_ (.CLK(clknet_1_0__leaf_clk),
    .D(_003_),
    .Q(net25));
 sky130_fd_sc_hd__dfxtp_1 _344_ (.CLK(clknet_1_0__leaf_clk),
    .D(_004_),
    .Q(net26));
 sky130_fd_sc_hd__dfxtp_1 _345_ (.CLK(clknet_1_0__leaf_clk),
    .D(_005_),
    .Q(net27));
 sky130_fd_sc_hd__dfxtp_1 _346_ (.CLK(clknet_1_0__leaf_clk),
    .D(_006_),
    .Q(net28));
 sky130_fd_sc_hd__dfxtp_1 _347_ (.CLK(clknet_1_0__leaf_clk),
    .D(_007_),
    .Q(net29));
 sky130_fd_sc_hd__dfxtp_1 _348_ (.CLK(clknet_1_0__leaf_clk),
    .D(_008_),
    .Q(net30));
 sky130_fd_sc_hd__dfxtp_1 _349_ (.CLK(clknet_1_1__leaf_clk),
    .D(_009_),
    .Q(net31));
 sky130_fd_sc_hd__dfxtp_1 _350_ (.CLK(clknet_1_1__leaf_clk),
    .D(_010_),
    .Q(net32));
 sky130_fd_sc_hd__dfxtp_1 _351_ (.CLK(clknet_1_1__leaf_clk),
    .D(_011_),
    .Q(net21));
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
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_14_Right_14 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_15_Right_15 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_16_Right_16 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_17_Right_17 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_18_Right_18 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_19_Right_19 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_20_Right_20 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_21_Right_21 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_22_Right_22 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_23_Right_23 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_24_Right_24 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_0_Left_25 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_1_Left_26 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_2_Left_27 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_3_Left_28 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_4_Left_29 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_5_Left_30 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_6_Left_31 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_7_Left_32 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_8_Left_33 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_9_Left_34 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_10_Left_35 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_11_Left_36 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_12_Left_37 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_13_Left_38 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_14_Left_39 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_15_Left_40 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_16_Left_41 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_17_Left_42 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_18_Left_43 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_19_Left_44 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_20_Left_45 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_21_Left_46 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_22_Left_47 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_23_Left_48 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_24_Left_49 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_50 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_51 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_52 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_53 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_54 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_55 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_56 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_57 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_58 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_59 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_60 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_61 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_62 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_63 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_64 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_65 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_66 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_67 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_68 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_69 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_70 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_71 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_72 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_73 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_74 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_75 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_76 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_77 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_78 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_79 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_80 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_81 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_82 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_83 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_84 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_85 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_86 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_87 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_88 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_89 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_15_90 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_15_91 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_92 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_93 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_94 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_17_95 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_17_96 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_97 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_98 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_99 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_19_100 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_19_101 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_102 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_103 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_104 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_21_105 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_21_106 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_107 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_108 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_109 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_23_110 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_23_111 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_112 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_113 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_114 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_115 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_116 ();
 sky130_fd_sc_hd__clkbuf_2 input1 (.A(a[0]),
    .X(net1));
 sky130_fd_sc_hd__clkbuf_2 input2 (.A(a[1]),
    .X(net2));
 sky130_fd_sc_hd__clkbuf_2 input3 (.A(a[2]),
    .X(net3));
 sky130_fd_sc_hd__buf_1 input4 (.A(a[3]),
    .X(net4));
 sky130_fd_sc_hd__clkbuf_2 input5 (.A(a[4]),
    .X(net5));
 sky130_fd_sc_hd__buf_1 input6 (.A(a[5]),
    .X(net6));
 sky130_fd_sc_hd__clkbuf_2 input7 (.A(a[6]),
    .X(net7));
 sky130_fd_sc_hd__buf_1 input8 (.A(a[7]),
    .X(net8));
 sky130_fd_sc_hd__clkbuf_1 input9 (.A(b[0]),
    .X(net9));
 sky130_fd_sc_hd__clkbuf_1 input10 (.A(b[1]),
    .X(net10));
 sky130_fd_sc_hd__clkbuf_2 input11 (.A(b[2]),
    .X(net11));
 sky130_fd_sc_hd__buf_1 input12 (.A(b[3]),
    .X(net12));
 sky130_fd_sc_hd__buf_1 input13 (.A(b[4]),
    .X(net13));
 sky130_fd_sc_hd__buf_1 input14 (.A(b[5]),
    .X(net14));
 sky130_fd_sc_hd__buf_1 input15 (.A(b[6]),
    .X(net15));
 sky130_fd_sc_hd__dlymetal6s2s_1 input16 (.A(b[7]),
    .X(net16));
 sky130_fd_sc_hd__clkbuf_2 input17 (.A(op[0]),
    .X(net17));
 sky130_fd_sc_hd__clkbuf_2 input18 (.A(op[1]),
    .X(net18));
 sky130_fd_sc_hd__buf_2 input19 (.A(op[2]),
    .X(net19));
 sky130_fd_sc_hd__buf_1 input20 (.A(rst_n),
    .X(net20));
 sky130_fd_sc_hd__buf_2 output21 (.A(net21),
    .X(flag_c));
 sky130_fd_sc_hd__buf_2 output22 (.A(net22),
    .X(flag_n));
 sky130_fd_sc_hd__buf_2 output23 (.A(net23),
    .X(flag_v));
 sky130_fd_sc_hd__buf_2 output24 (.A(net24),
    .X(flag_z));
 sky130_fd_sc_hd__buf_2 output25 (.A(net25),
    .X(result[0]));
 sky130_fd_sc_hd__buf_2 output26 (.A(net26),
    .X(result[1]));
 sky130_fd_sc_hd__buf_2 output27 (.A(net27),
    .X(result[2]));
 sky130_fd_sc_hd__buf_2 output28 (.A(net28),
    .X(result[3]));
 sky130_fd_sc_hd__buf_2 output29 (.A(net29),
    .X(result[4]));
 sky130_fd_sc_hd__buf_2 output30 (.A(net30),
    .X(result[5]));
 sky130_fd_sc_hd__buf_2 output31 (.A(net31),
    .X(result[6]));
 sky130_fd_sc_hd__buf_2 output32 (.A(net32),
    .X(result[7]));
 sky130_fd_sc_hd__buf_2 fanout33 (.A(_118_),
    .X(net33));
 sky130_fd_sc_hd__clkbuf_4 fanout34 (.A(_118_),
    .X(net34));
 sky130_fd_sc_hd__buf_2 fanout35 (.A(_112_),
    .X(net35));
 sky130_fd_sc_hd__buf_2 fanout36 (.A(_111_),
    .X(net36));
 sky130_fd_sc_hd__clkbuf_4 fanout37 (.A(net39),
    .X(net37));
 sky130_fd_sc_hd__buf_2 fanout38 (.A(net39),
    .X(net38));
 sky130_fd_sc_hd__clkbuf_2 fanout39 (.A(net9),
    .X(net39));
 sky130_fd_sc_hd__buf_2 fanout40 (.A(net8),
    .X(net40));
 sky130_fd_sc_hd__clkbuf_2 fanout41 (.A(net6),
    .X(net41));
 sky130_fd_sc_hd__clkbuf_2 fanout42 (.A(net4),
    .X(net42));
 sky130_fd_sc_hd__buf_2 fanout43 (.A(net20),
    .X(net43));
 sky130_fd_sc_hd__buf_2 fanout44 (.A(net10),
    .X(net44));
 sky130_fd_sc_hd__clkbuf_2 fanout45 (.A(net10),
    .X(net45));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_0_clk (.A(clk),
    .X(clknet_0_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_1_0__f_clk (.A(clknet_0_clk),
    .X(clknet_1_0__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_1_1__f_clk (.A(clknet_0_clk),
    .X(clknet_1_1__leaf_clk));
 sky130_fd_sc_hd__dlygate4sd3_1 hold1 (.A(net30),
    .X(net46));
 sky130_fd_sc_hd__dlygate4sd3_1 hold2 (.A(net28),
    .X(net47));
 sky130_fd_sc_hd__dlygate4sd3_1 hold3 (.A(net31),
    .X(net48));
 sky130_fd_sc_hd__dlygate4sd3_1 hold4 (.A(net29),
    .X(net49));
 sky130_fd_sc_hd__dlygate4sd3_1 hold5 (.A(net25),
    .X(net50));
 sky130_fd_sc_hd__dlygate4sd3_1 hold6 (.A(net26),
    .X(net51));
 sky130_fd_sc_hd__dlygate4sd3_1 hold7 (.A(net32),
    .X(net52));
 sky130_fd_sc_hd__dlygate4sd3_1 hold8 (.A(net27),
    .X(net53));
 sky130_ef_sc_hd__decap_12 FILLER_0_7 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_41 ();
 sky130_fd_sc_hd__decap_3 FILLER_0_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_57 ();
 sky130_fd_sc_hd__decap_6 FILLER_0_69 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_75 ();
 sky130_fd_sc_hd__decap_4 FILLER_0_79 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_97 ();
 sky130_fd_sc_hd__decap_3 FILLER_0_109 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_113 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_125 ();
 sky130_fd_sc_hd__decap_3 FILLER_0_133 ();
 sky130_fd_sc_hd__decap_3 FILLER_0_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_7 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_19 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_31 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_43 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_69 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_81 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_93 ();
 sky130_fd_sc_hd__decap_6 FILLER_1_105 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_111 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_125 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_137 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_146 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_7 ();
 sky130_fd_sc_hd__decap_8 FILLER_2_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_2_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_41 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_65 ();
 sky130_fd_sc_hd__decap_6 FILLER_2_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_2_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_97 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_109 ();
 sky130_fd_sc_hd__decap_8 FILLER_2_121 ();
 sky130_fd_sc_hd__decap_3 FILLER_2_129 ();
 sky130_fd_sc_hd__decap_6 FILLER_2_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_2_147 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_6 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_18 ();
 sky130_fd_sc_hd__decap_8 FILLER_3_39 ();
 sky130_fd_sc_hd__fill_2 FILLER_3_47 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_79 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_91 ();
 sky130_fd_sc_hd__decap_8 FILLER_3_103 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_111 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_113 ();
 sky130_fd_sc_hd__decap_4 FILLER_3_125 ();
 sky130_fd_sc_hd__decap_3 FILLER_3_145 ();
 sky130_fd_sc_hd__fill_2 FILLER_4_3 ();
 sky130_fd_sc_hd__fill_2 FILLER_4_26 ();
 sky130_fd_sc_hd__fill_2 FILLER_4_56 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_67 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_79 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_97 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_109 ();
 sky130_fd_sc_hd__decap_3 FILLER_4_141 ();
 sky130_fd_sc_hd__decap_6 FILLER_5_32 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_43 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_55 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_72 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_94 ();
 sky130_fd_sc_hd__decap_6 FILLER_5_106 ();
 sky130_fd_sc_hd__decap_6 FILLER_5_142 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_6 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_11 ();
 sky130_fd_sc_hd__fill_2 FILLER_6_26 ();
 sky130_fd_sc_hd__fill_2 FILLER_6_34 ();
 sky130_fd_sc_hd__decap_4 FILLER_6_57 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_67 ();
 sky130_fd_sc_hd__decap_8 FILLER_6_105 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_113 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_125 ();
 sky130_fd_sc_hd__decap_6 FILLER_6_134 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_3 ();
 sky130_fd_sc_hd__decap_6 FILLER_7_38 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_57 ();
 sky130_fd_sc_hd__decap_6 FILLER_7_76 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_82 ();
 sky130_fd_sc_hd__decap_3 FILLER_7_101 ();
 sky130_fd_sc_hd__fill_2 FILLER_7_125 ();
 sky130_fd_sc_hd__decap_4 FILLER_7_143 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_147 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_7 ();
 sky130_fd_sc_hd__decap_3 FILLER_8_45 ();
 sky130_fd_sc_hd__decap_8 FILLER_8_55 ();
 sky130_fd_sc_hd__decap_3 FILLER_8_63 ();
 sky130_ef_sc_hd__decap_12 FILLER_8_71 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_83 ();
 sky130_fd_sc_hd__decap_6 FILLER_8_85 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_91 ();
 sky130_ef_sc_hd__decap_12 FILLER_8_104 ();
 sky130_fd_sc_hd__decap_6 FILLER_8_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_147 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_15 ();
 sky130_fd_sc_hd__fill_2 FILLER_9_22 ();
 sky130_fd_sc_hd__decap_8 FILLER_9_36 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_44 ();
 sky130_fd_sc_hd__decap_4 FILLER_9_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_62 ();
 sky130_fd_sc_hd__decap_8 FILLER_9_74 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_82 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_99 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_111 ();
 sky130_fd_sc_hd__decap_6 FILLER_9_113 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_119 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_143 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_9 ();
 sky130_fd_sc_hd__decap_4 FILLER_10_23 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_29 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_41 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_49 ();
 sky130_fd_sc_hd__decap_4 FILLER_10_56 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_64 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_76 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_97 ();
 sky130_fd_sc_hd__decap_6 FILLER_10_109 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_115 ();
 sky130_fd_sc_hd__decap_3 FILLER_10_141 ();
 sky130_fd_sc_hd__fill_2 FILLER_11_3 ();
 sky130_fd_sc_hd__fill_2 FILLER_11_16 ();
 sky130_fd_sc_hd__decap_3 FILLER_11_40 ();
 sky130_ef_sc_hd__decap_12 FILLER_11_68 ();
 sky130_fd_sc_hd__decap_8 FILLER_11_80 ();
 sky130_fd_sc_hd__decap_8 FILLER_11_102 ();
 sky130_fd_sc_hd__fill_2 FILLER_11_110 ();
 sky130_ef_sc_hd__decap_12 FILLER_11_113 ();
 sky130_fd_sc_hd__decap_4 FILLER_11_125 ();
 sky130_fd_sc_hd__decap_3 FILLER_11_137 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_3 ();
 sky130_fd_sc_hd__decap_3 FILLER_12_25 ();
 sky130_fd_sc_hd__decap_4 FILLER_12_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_40 ();
 sky130_ef_sc_hd__decap_12 FILLER_12_55 ();
 sky130_fd_sc_hd__decap_8 FILLER_12_74 ();
 sky130_fd_sc_hd__fill_2 FILLER_12_82 ();
 sky130_fd_sc_hd__decap_8 FILLER_12_108 ();
 sky130_fd_sc_hd__decap_6 FILLER_12_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_147 ();
 sky130_fd_sc_hd__decap_4 FILLER_13_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_13_14 ();
 sky130_fd_sc_hd__decap_8 FILLER_13_22 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_30 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_38 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_44 ();
 sky130_fd_sc_hd__decap_8 FILLER_13_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_111 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_116 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_7 ();
 sky130_fd_sc_hd__decap_8 FILLER_14_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_27 ();
 sky130_fd_sc_hd__fill_2 FILLER_14_36 ();
 sky130_fd_sc_hd__decap_8 FILLER_14_51 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_59 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_81 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_109 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_121 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_3 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_15 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_27 ();
 sky130_fd_sc_hd__decap_8 FILLER_15_39 ();
 sky130_fd_sc_hd__fill_1 FILLER_15_47 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_65 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_77 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_89 ();
 sky130_fd_sc_hd__decap_8 FILLER_15_101 ();
 sky130_fd_sc_hd__decap_3 FILLER_15_109 ();
 sky130_fd_sc_hd__decap_8 FILLER_15_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_15_121 ();
 sky130_fd_sc_hd__decap_3 FILLER_15_127 ();
 sky130_fd_sc_hd__fill_1 FILLER_15_135 ();
 sky130_fd_sc_hd__decap_4 FILLER_15_144 ();
 sky130_fd_sc_hd__decap_6 FILLER_16_9 ();
 sky130_fd_sc_hd__fill_1 FILLER_16_27 ();
 sky130_fd_sc_hd__fill_1 FILLER_16_32 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_40 ();
 sky130_fd_sc_hd__fill_2 FILLER_16_82 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_97 ();
 sky130_fd_sc_hd__decap_6 FILLER_16_109 ();
 sky130_fd_sc_hd__fill_1 FILLER_16_115 ();
 sky130_fd_sc_hd__decap_3 FILLER_16_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_31 ();
 sky130_ef_sc_hd__decap_12 FILLER_17_39 ();
 sky130_fd_sc_hd__decap_4 FILLER_17_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_55 ();
 sky130_fd_sc_hd__decap_3 FILLER_17_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_68 ();
 sky130_fd_sc_hd__decap_6 FILLER_17_76 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_82 ();
 sky130_fd_sc_hd__decap_4 FILLER_17_87 ();
 sky130_ef_sc_hd__decap_12 FILLER_17_98 ();
 sky130_fd_sc_hd__fill_2 FILLER_17_110 ();
 sky130_fd_sc_hd__decap_6 FILLER_17_113 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_119 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_128 ();
 sky130_fd_sc_hd__decap_3 FILLER_17_145 ();
 sky130_fd_sc_hd__decap_8 FILLER_18_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_11 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_27 ();
 sky130_fd_sc_hd__decap_6 FILLER_18_37 ();
 sky130_fd_sc_hd__decap_6 FILLER_18_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_57 ();
 sky130_fd_sc_hd__decap_4 FILLER_18_80 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_92 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_103 ();
 sky130_fd_sc_hd__decap_6 FILLER_18_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_147 ();
 sky130_fd_sc_hd__decap_6 FILLER_19_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_19_39 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_43 ();
 sky130_fd_sc_hd__fill_2 FILLER_19_57 ();
 sky130_fd_sc_hd__fill_2 FILLER_19_64 ();
 sky130_fd_sc_hd__decap_6 FILLER_19_72 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_78 ();
 sky130_fd_sc_hd__decap_6 FILLER_19_90 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_96 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_130 ();
 sky130_fd_sc_hd__fill_2 FILLER_19_142 ();
 sky130_ef_sc_hd__decap_12 FILLER_20_6 ();
 sky130_fd_sc_hd__decap_8 FILLER_20_18 ();
 sky130_fd_sc_hd__fill_2 FILLER_20_26 ();
 sky130_fd_sc_hd__decap_8 FILLER_20_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_20_54 ();
 sky130_fd_sc_hd__fill_2 FILLER_20_67 ();
 sky130_fd_sc_hd__decap_8 FILLER_20_75 ();
 sky130_fd_sc_hd__fill_1 FILLER_20_83 ();
 sky130_fd_sc_hd__decap_3 FILLER_20_85 ();
 sky130_fd_sc_hd__decap_8 FILLER_20_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_20_121 ();
 sky130_fd_sc_hd__decap_6 FILLER_20_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_20_147 ();
 sky130_ef_sc_hd__decap_12 FILLER_21_3 ();
 sky130_ef_sc_hd__decap_12 FILLER_21_15 ();
 sky130_ef_sc_hd__decap_12 FILLER_21_27 ();
 sky130_fd_sc_hd__decap_3 FILLER_21_39 ();
 sky130_ef_sc_hd__decap_12 FILLER_21_78 ();
 sky130_fd_sc_hd__decap_6 FILLER_21_90 ();
 sky130_fd_sc_hd__decap_4 FILLER_21_108 ();
 sky130_ef_sc_hd__decap_12 FILLER_21_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_21_125 ();
 sky130_fd_sc_hd__decap_6 FILLER_21_137 ();
 sky130_fd_sc_hd__fill_1 FILLER_21_143 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_13 ();
 sky130_fd_sc_hd__decap_3 FILLER_22_25 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_29 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_41 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_47 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_55 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_61 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_65 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_97 ();
 sky130_fd_sc_hd__decap_4 FILLER_22_109 ();
 sky130_fd_sc_hd__decap_8 FILLER_22_129 ();
 sky130_fd_sc_hd__decap_3 FILLER_22_137 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_147 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_7 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_19 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_31 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_43 ();
 sky130_fd_sc_hd__fill_1 FILLER_23_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_69 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_81 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_93 ();
 sky130_fd_sc_hd__decap_6 FILLER_23_105 ();
 sky130_fd_sc_hd__fill_1 FILLER_23_111 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_23_125 ();
 sky130_fd_sc_hd__decap_6 FILLER_23_137 ();
 sky130_fd_sc_hd__fill_1 FILLER_23_143 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_11 ();
 sky130_fd_sc_hd__decap_4 FILLER_24_23 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_41 ();
 sky130_fd_sc_hd__decap_3 FILLER_24_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_69 ();
 sky130_fd_sc_hd__decap_3 FILLER_24_81 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_97 ();
 sky130_fd_sc_hd__decap_3 FILLER_24_109 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_125 ();
 sky130_fd_sc_hd__decap_3 FILLER_24_137 ();
 sky130_fd_sc_hd__decap_3 FILLER_24_141 ();
endmodule
