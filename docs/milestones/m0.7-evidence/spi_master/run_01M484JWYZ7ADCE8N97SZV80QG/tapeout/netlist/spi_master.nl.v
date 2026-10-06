module spi_master (busy,
    clk,
    cpha,
    cpol,
    cs_force,
    cs_mode,
    cs_n,
    done,
    irq,
    irq_clear,
    miso,
    mosi,
    rst_n,
    sck,
    start,
    start_err,
    word_len,
    clk_div,
    rx_data,
    tx_data);
 output busy;
 input clk;
 input cpha;
 input cpol;
 input cs_force;
 input cs_mode;
 output cs_n;
 output done;
 output irq;
 input irq_clear;
 input miso;
 output mosi;
 input rst_n;
 output sck;
 input start;
 output start_err;
 input word_len;
 input [15:0] clk_div;
 output [15:0] rx_data;
 input [15:0] tx_data;

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
 wire _170_;
 wire _171_;
 wire _172_;
 wire _173_;
 wire _174_;
 wire _175_;
 wire _176_;
 wire _177_;
 wire _178_;
 wire _179_;
 wire _180_;
 wire _181_;
 wire _182_;
 wire _183_;
 wire _184_;
 wire _185_;
 wire _186_;
 wire _187_;
 wire _188_;
 wire _189_;
 wire _190_;
 wire _191_;
 wire _192_;
 wire _193_;
 wire _194_;
 wire _195_;
 wire _196_;
 wire _197_;
 wire _198_;
 wire _199_;
 wire _200_;
 wire _201_;
 wire _202_;
 wire _203_;
 wire _204_;
 wire _205_;
 wire _206_;
 wire _207_;
 wire _208_;
 wire _209_;
 wire _210_;
 wire _211_;
 wire _212_;
 wire _213_;
 wire _214_;
 wire _215_;
 wire _216_;
 wire _217_;
 wire _218_;
 wire _219_;
 wire _220_;
 wire _221_;
 wire _222_;
 wire _223_;
 wire _224_;
 wire _225_;
 wire _226_;
 wire _227_;
 wire _228_;
 wire _229_;
 wire _230_;
 wire _231_;
 wire _232_;
 wire _233_;
 wire _234_;
 wire _235_;
 wire _236_;
 wire _237_;
 wire _238_;
 wire _239_;
 wire _240_;
 wire _241_;
 wire _242_;
 wire _243_;
 wire _244_;
 wire _245_;
 wire _246_;
 wire _247_;
 wire _248_;
 wire _249_;
 wire _250_;
 wire _251_;
 wire _252_;
 wire _253_;
 wire _254_;
 wire _255_;
 wire _256_;
 wire _257_;
 wire _258_;
 wire _259_;
 wire _260_;
 wire _261_;
 wire _262_;
 wire _263_;
 wire _264_;
 wire _265_;
 wire _266_;
 wire _267_;
 wire _268_;
 wire _269_;
 wire _270_;
 wire _271_;
 wire _272_;
 wire _273_;
 wire _274_;
 wire _275_;
 wire _276_;
 wire _277_;
 wire _278_;
 wire _279_;
 wire _280_;
 wire _281_;
 wire _282_;
 wire _283_;
 wire _284_;
 wire _285_;
 wire _286_;
 wire _287_;
 wire _288_;
 wire _289_;
 wire _290_;
 wire _291_;
 wire _292_;
 wire _293_;
 wire _294_;
 wire _295_;
 wire _296_;
 wire _297_;
 wire _298_;
 wire _299_;
 wire _300_;
 wire _301_;
 wire _302_;
 wire _303_;
 wire _304_;
 wire _305_;
 wire _306_;
 wire _307_;
 wire _308_;
 wire _309_;
 wire _310_;
 wire _311_;
 wire _312_;
 wire _313_;
 wire _314_;
 wire _315_;
 wire _316_;
 wire _317_;
 wire _318_;
 wire _319_;
 wire _320_;
 wire _321_;
 wire _322_;
 wire _323_;
 wire _324_;
 wire _325_;
 wire _326_;
 wire _327_;
 wire _328_;
 wire _329_;
 wire _330_;
 wire _331_;
 wire _332_;
 wire _333_;
 wire _334_;
 wire _335_;
 wire _336_;
 wire _337_;
 wire _338_;
 wire _339_;
 wire _340_;
 wire _341_;
 wire _342_;
 wire _343_;
 wire _344_;
 wire _345_;
 wire _346_;
 wire _347_;
 wire _348_;
 wire _349_;
 wire _350_;
 wire _351_;
 wire _352_;
 wire _353_;
 wire _354_;
 wire _355_;
 wire _356_;
 wire _357_;
 wire _358_;
 wire _359_;
 wire _360_;
 wire _361_;
 wire _362_;
 wire _363_;
 wire _364_;
 wire _365_;
 wire _366_;
 wire _367_;
 wire _368_;
 wire _369_;
 wire _370_;
 wire _371_;
 wire _372_;
 wire _373_;
 wire _374_;
 wire _375_;
 wire _376_;
 wire _377_;
 wire _378_;
 wire _379_;
 wire _380_;
 wire _381_;
 wire \edge_cnt_unused[0] ;
 wire \edge_cnt_unused[1] ;
 wire \edge_cnt_unused[2] ;
 wire \edge_cnt_unused[3] ;
 wire \edge_cnt_unused[4] ;
 wire \edge_cnt_unused[5] ;
 wire miso_s;
 wire \u_spi_clkgen.hp_cnt_q[0] ;
 wire \u_spi_clkgen.hp_cnt_q[10] ;
 wire \u_spi_clkgen.hp_cnt_q[11] ;
 wire \u_spi_clkgen.hp_cnt_q[12] ;
 wire \u_spi_clkgen.hp_cnt_q[13] ;
 wire \u_spi_clkgen.hp_cnt_q[14] ;
 wire \u_spi_clkgen.hp_cnt_q[15] ;
 wire \u_spi_clkgen.hp_cnt_q[1] ;
 wire \u_spi_clkgen.hp_cnt_q[2] ;
 wire \u_spi_clkgen.hp_cnt_q[3] ;
 wire \u_spi_clkgen.hp_cnt_q[4] ;
 wire \u_spi_clkgen.hp_cnt_q[5] ;
 wire \u_spi_clkgen.hp_cnt_q[6] ;
 wire \u_spi_clkgen.hp_cnt_q[7] ;
 wire \u_spi_clkgen.hp_cnt_q[8] ;
 wire \u_spi_clkgen.hp_cnt_q[9] ;
 wire \u_spi_clkgen.nm1_q[0] ;
 wire \u_spi_clkgen.nm1_q[10] ;
 wire \u_spi_clkgen.nm1_q[11] ;
 wire \u_spi_clkgen.nm1_q[12] ;
 wire \u_spi_clkgen.nm1_q[13] ;
 wire \u_spi_clkgen.nm1_q[14] ;
 wire \u_spi_clkgen.nm1_q[15] ;
 wire \u_spi_clkgen.nm1_q[1] ;
 wire \u_spi_clkgen.nm1_q[2] ;
 wire \u_spi_clkgen.nm1_q[3] ;
 wire \u_spi_clkgen.nm1_q[4] ;
 wire \u_spi_clkgen.nm1_q[5] ;
 wire \u_spi_clkgen.nm1_q[6] ;
 wire \u_spi_clkgen.nm1_q[7] ;
 wire \u_spi_clkgen.nm1_q[8] ;
 wire \u_spi_clkgen.nm1_q[9] ;
 wire \u_spi_clkgen.running_q ;
 wire \u_spi_clkgen.wl_q ;
 wire \u_spi_ctrl.cs_mode_q ;
 wire \u_spi_ctrl.state_q[0] ;
 wire \u_spi_ctrl.state_q[1] ;
 wire \u_spi_ctrl.state_q[2] ;
 wire \u_spi_shift.cpha_q ;
 wire \u_spi_shift.rx_sr_q[0] ;
 wire \u_spi_shift.rx_sr_q[10] ;
 wire \u_spi_shift.rx_sr_q[11] ;
 wire \u_spi_shift.rx_sr_q[12] ;
 wire \u_spi_shift.rx_sr_q[13] ;
 wire \u_spi_shift.rx_sr_q[14] ;
 wire \u_spi_shift.rx_sr_q[15] ;
 wire \u_spi_shift.rx_sr_q[1] ;
 wire \u_spi_shift.rx_sr_q[2] ;
 wire \u_spi_shift.rx_sr_q[3] ;
 wire \u_spi_shift.rx_sr_q[4] ;
 wire \u_spi_shift.rx_sr_q[5] ;
 wire \u_spi_shift.rx_sr_q[6] ;
 wire \u_spi_shift.rx_sr_q[7] ;
 wire \u_spi_shift.rx_sr_q[8] ;
 wire \u_spi_shift.rx_sr_q[9] ;
 wire \u_spi_shift.smp_d1_q ;
 wire \u_spi_shift.smp_d2_q ;
 wire \u_spi_shift.tx_sr_q[0] ;
 wire \u_spi_shift.tx_sr_q[10] ;
 wire \u_spi_shift.tx_sr_q[11] ;
 wire \u_spi_shift.tx_sr_q[12] ;
 wire \u_spi_shift.tx_sr_q[13] ;
 wire \u_spi_shift.tx_sr_q[14] ;
 wire \u_spi_shift.tx_sr_q[15] ;
 wire \u_spi_shift.tx_sr_q[1] ;
 wire \u_spi_shift.tx_sr_q[2] ;
 wire \u_spi_shift.tx_sr_q[3] ;
 wire \u_spi_shift.tx_sr_q[4] ;
 wire \u_spi_shift.tx_sr_q[5] ;
 wire \u_spi_shift.tx_sr_q[6] ;
 wire \u_spi_shift.tx_sr_q[7] ;
 wire \u_spi_shift.tx_sr_q[8] ;
 wire \u_spi_shift.tx_sr_q[9] ;
 wire \u_sync2.meta_q ;
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
 wire net46;
 wire net47;
 wire net48;
 wire net49;
 wire net50;
 wire net51;
 wire net52;
 wire net53;
 wire net54;
 wire net55;
 wire net56;
 wire net57;
 wire net58;
 wire net59;
 wire net60;
 wire net61;
 wire net62;
 wire net63;
 wire net64;
 wire net65;
 wire net66;
 wire net67;
 wire net68;
 wire net69;
 wire net70;
 wire net71;
 wire net72;
 wire net73;
 wire net74;
 wire net75;
 wire net76;
 wire net77;
 wire net78;
 wire net79;
 wire net80;
 wire net81;
 wire net82;
 wire net83;
 wire net84;
 wire net85;
 wire net86;
 wire net87;
 wire net88;
 wire net89;
 wire net90;
 wire net91;
 wire net92;
 wire net93;
 wire net94;
 wire net95;
 wire net96;
 wire net97;
 wire net98;
 wire net99;
 wire clknet_0_clk;
 wire clknet_3_0__leaf_clk;
 wire clknet_3_1__leaf_clk;
 wire clknet_3_2__leaf_clk;
 wire clknet_3_3__leaf_clk;
 wire clknet_3_4__leaf_clk;
 wire clknet_3_5__leaf_clk;
 wire clknet_3_6__leaf_clk;
 wire clknet_3_7__leaf_clk;
 wire net100;
 wire net101;
 wire net102;
 wire net103;
 wire net104;
 wire net105;
 wire net106;
 wire net107;
 wire net108;
 wire net109;
 wire net110;
 wire net111;
 wire net112;
 wire net113;
 wire net114;
 wire net115;
 wire net116;
 wire net117;
 wire net118;
 wire net119;
 wire net120;
 wire net121;
 wire net122;
 wire net123;
 wire net124;
 wire net125;
 wire net126;
 wire net127;
 wire net128;
 wire net129;
 wire net130;
 wire net131;
 wire net132;
 wire net133;
 wire net134;
 wire net135;
 wire net136;
 wire net137;
 wire net138;
 wire net139;
 wire net140;
 wire net141;
 wire net142;
 wire net143;
 wire net144;
 wire net145;
 wire net146;
 wire net147;
 wire net148;
 wire net149;
 wire net150;
 wire net151;
 wire net152;
 wire net153;
 wire net154;
 wire net155;
 wire net156;
 wire net157;
 wire net158;
 wire net159;
 wire net160;
 wire net161;
 wire net162;
 wire net163;
 wire net164;
 wire net165;
 wire net166;
 wire net167;
 wire net168;
 wire net169;
 wire net170;
 wire net171;
 wire net172;
 wire net173;
 wire net174;
 wire net175;
 wire net176;
 wire net177;
 wire net178;

 sky130_fd_sc_hd__inv_2 _382_ (.A(net17),
    .Y(_104_));
 sky130_fd_sc_hd__inv_2 _383_ (.A(\u_spi_clkgen.wl_q ),
    .Y(_105_));
 sky130_fd_sc_hd__inv_2 _384_ (.A(\u_spi_clkgen.nm1_q[14] ),
    .Y(_106_));
 sky130_fd_sc_hd__inv_2 _385_ (.A(\u_spi_clkgen.nm1_q[12] ),
    .Y(_107_));
 sky130_fd_sc_hd__inv_2 _386_ (.A(\edge_cnt_unused[0] ),
    .Y(_108_));
 sky130_fd_sc_hd__inv_2 _387_ (.A(net63),
    .Y(_109_));
 sky130_fd_sc_hd__inv_2 _388_ (.A(net9),
    .Y(_110_));
 sky130_fd_sc_hd__inv_2 _389_ (.A(net91),
    .Y(_111_));
 sky130_fd_sc_hd__inv_2 _390_ (.A(\u_spi_ctrl.state_q[2] ),
    .Y(_112_));
 sky130_fd_sc_hd__inv_2 _391_ (.A(\u_spi_ctrl.state_q[1] ),
    .Y(_113_));
 sky130_fd_sc_hd__inv_2 _392_ (.A(\u_spi_ctrl.cs_mode_q ),
    .Y(_114_));
 sky130_fd_sc_hd__inv_2 _393_ (.A(net21),
    .Y(_115_));
 sky130_fd_sc_hd__a21o_1 _394_ (.A1(_105_),
    .A2(\edge_cnt_unused[4] ),
    .B1(\edge_cnt_unused[5] ),
    .X(_116_));
 sky130_fd_sc_hd__or3_1 _395_ (.A(\edge_cnt_unused[3] ),
    .B(\edge_cnt_unused[2] ),
    .C(\edge_cnt_unused[1] ),
    .X(_117_));
 sky130_fd_sc_hd__o21a_1 _396_ (.A1(_105_),
    .A2(\edge_cnt_unused[4] ),
    .B1(\edge_cnt_unused[5] ),
    .X(_118_));
 sky130_fd_sc_hd__or3b_1 _397_ (.A(_117_),
    .B(_118_),
    .C_N(_116_),
    .X(_119_));
 sky130_fd_sc_hd__inv_2 _398_ (.A(_119_),
    .Y(_120_));
 sky130_fd_sc_hd__and2b_1 _399_ (.A_N(\u_spi_clkgen.nm1_q[13] ),
    .B(\u_spi_clkgen.hp_cnt_q[13] ),
    .X(_121_));
 sky130_fd_sc_hd__and2b_1 _400_ (.A_N(\u_spi_clkgen.nm1_q[4] ),
    .B(\u_spi_clkgen.hp_cnt_q[4] ),
    .X(_122_));
 sky130_fd_sc_hd__and2b_1 _401_ (.A_N(\u_spi_clkgen.hp_cnt_q[3] ),
    .B(\u_spi_clkgen.nm1_q[3] ),
    .X(_123_));
 sky130_fd_sc_hd__or3_1 _402_ (.A(_121_),
    .B(_122_),
    .C(_123_),
    .X(_124_));
 sky130_fd_sc_hd__and2b_1 _403_ (.A_N(\u_spi_clkgen.nm1_q[7] ),
    .B(\u_spi_clkgen.hp_cnt_q[7] ),
    .X(_125_));
 sky130_fd_sc_hd__and2b_1 _404_ (.A_N(\u_spi_clkgen.hp_cnt_q[2] ),
    .B(\u_spi_clkgen.nm1_q[2] ),
    .X(_126_));
 sky130_fd_sc_hd__and2b_1 _405_ (.A_N(\u_spi_clkgen.hp_cnt_q[7] ),
    .B(\u_spi_clkgen.nm1_q[7] ),
    .X(_127_));
 sky130_fd_sc_hd__and2b_1 _406_ (.A_N(\u_spi_clkgen.nm1_q[3] ),
    .B(\u_spi_clkgen.hp_cnt_q[3] ),
    .X(_128_));
 sky130_fd_sc_hd__or4_1 _407_ (.A(_125_),
    .B(_126_),
    .C(_127_),
    .D(_128_),
    .X(_129_));
 sky130_fd_sc_hd__xor2_1 _408_ (.A(\u_spi_clkgen.nm1_q[10] ),
    .B(\u_spi_clkgen.hp_cnt_q[10] ),
    .X(_130_));
 sky130_fd_sc_hd__and2b_1 _409_ (.A_N(\u_spi_clkgen.hp_cnt_q[4] ),
    .B(\u_spi_clkgen.nm1_q[4] ),
    .X(_131_));
 sky130_fd_sc_hd__a2111o_1 _410_ (.A1(_106_),
    .A2(\u_spi_clkgen.hp_cnt_q[14] ),
    .B1(_129_),
    .C1(_130_),
    .D1(_131_),
    .X(_132_));
 sky130_fd_sc_hd__xnor2_1 _411_ (.A(\u_spi_clkgen.nm1_q[11] ),
    .B(\u_spi_clkgen.hp_cnt_q[11] ),
    .Y(_133_));
 sky130_fd_sc_hd__xnor2_1 _412_ (.A(\u_spi_clkgen.nm1_q[6] ),
    .B(\u_spi_clkgen.hp_cnt_q[6] ),
    .Y(_134_));
 sky130_fd_sc_hd__xnor2_1 _413_ (.A(\u_spi_clkgen.nm1_q[12] ),
    .B(\u_spi_clkgen.hp_cnt_q[12] ),
    .Y(_135_));
 sky130_fd_sc_hd__and3_1 _414_ (.A(_133_),
    .B(_134_),
    .C(_135_),
    .X(_136_));
 sky130_fd_sc_hd__and2b_1 _415_ (.A_N(\u_spi_clkgen.nm1_q[9] ),
    .B(\u_spi_clkgen.hp_cnt_q[9] ),
    .X(_137_));
 sky130_fd_sc_hd__and2b_1 _416_ (.A_N(\u_spi_clkgen.hp_cnt_q[8] ),
    .B(\u_spi_clkgen.nm1_q[8] ),
    .X(_138_));
 sky130_fd_sc_hd__and2b_1 _417_ (.A_N(\u_spi_clkgen.hp_cnt_q[9] ),
    .B(\u_spi_clkgen.nm1_q[9] ),
    .X(_139_));
 sky130_fd_sc_hd__nand2b_1 _418_ (.A_N(\u_spi_clkgen.nm1_q[8] ),
    .B(\u_spi_clkgen.hp_cnt_q[8] ),
    .Y(_140_));
 sky130_fd_sc_hd__or4b_1 _419_ (.A(_137_),
    .B(_138_),
    .C(_139_),
    .D_N(_140_),
    .X(_141_));
 sky130_fd_sc_hd__xor2_1 _420_ (.A(\u_spi_clkgen.nm1_q[1] ),
    .B(\u_spi_clkgen.hp_cnt_q[1] ),
    .X(_142_));
 sky130_fd_sc_hd__and2b_1 _421_ (.A_N(\u_spi_clkgen.nm1_q[2] ),
    .B(\u_spi_clkgen.hp_cnt_q[2] ),
    .X(_143_));
 sky130_fd_sc_hd__or3b_1 _422_ (.A(_142_),
    .B(_143_),
    .C_N(\u_spi_clkgen.running_q ),
    .X(_144_));
 sky130_fd_sc_hd__and2b_1 _423_ (.A_N(\u_spi_clkgen.hp_cnt_q[5] ),
    .B(\u_spi_clkgen.nm1_q[5] ),
    .X(_145_));
 sky130_fd_sc_hd__nand2b_1 _424_ (.A_N(\u_spi_clkgen.hp_cnt_q[15] ),
    .B(\u_spi_clkgen.nm1_q[15] ),
    .Y(_146_));
 sky130_fd_sc_hd__nand2b_1 _425_ (.A_N(\u_spi_clkgen.nm1_q[5] ),
    .B(\u_spi_clkgen.hp_cnt_q[5] ),
    .Y(_147_));
 sky130_fd_sc_hd__nand2b_1 _426_ (.A_N(\u_spi_clkgen.hp_cnt_q[14] ),
    .B(\u_spi_clkgen.nm1_q[14] ),
    .Y(_148_));
 sky130_fd_sc_hd__and4b_1 _427_ (.A_N(_145_),
    .B(_146_),
    .C(_147_),
    .D(_148_),
    .X(_149_));
 sky130_fd_sc_hd__nand2b_1 _428_ (.A_N(\u_spi_clkgen.nm1_q[0] ),
    .B(\u_spi_clkgen.hp_cnt_q[0] ),
    .Y(_150_));
 sky130_fd_sc_hd__nand2b_1 _429_ (.A_N(\u_spi_clkgen.hp_cnt_q[13] ),
    .B(\u_spi_clkgen.nm1_q[13] ),
    .Y(_151_));
 sky130_fd_sc_hd__nand2b_1 _430_ (.A_N(\u_spi_clkgen.hp_cnt_q[0] ),
    .B(\u_spi_clkgen.nm1_q[0] ),
    .Y(_152_));
 sky130_fd_sc_hd__nand2b_1 _431_ (.A_N(\u_spi_clkgen.nm1_q[15] ),
    .B(\u_spi_clkgen.hp_cnt_q[15] ),
    .Y(_153_));
 sky130_fd_sc_hd__and4_1 _432_ (.A(_150_),
    .B(_151_),
    .C(_152_),
    .D(_153_),
    .X(_154_));
 sky130_fd_sc_hd__and4bb_1 _433_ (.A_N(_141_),
    .B_N(_144_),
    .C(_149_),
    .D(_154_),
    .X(_155_));
 sky130_fd_sc_hd__and4bb_1 _434_ (.A_N(_124_),
    .B_N(_132_),
    .C(_136_),
    .D(_155_),
    .X(_156_));
 sky130_fd_sc_hd__and2b_1 _435_ (.A_N(net42),
    .B(net24),
    .X(_157_));
 sky130_fd_sc_hd__nand2b_1 _436_ (.A_N(net42),
    .B(net24),
    .Y(_158_));
 sky130_fd_sc_hd__nor2_1 _437_ (.A(_122_),
    .B(_131_),
    .Y(_159_));
 sky130_fd_sc_hd__a2111oi_1 _438_ (.A1(_107_),
    .A2(\u_spi_clkgen.hp_cnt_q[12] ),
    .B1(_123_),
    .C1(_125_),
    .D1(_139_),
    .Y(_160_));
 sky130_fd_sc_hd__and4bb_1 _439_ (.A_N(_137_),
    .B_N(_143_),
    .C(_159_),
    .D(_160_),
    .X(_161_));
 sky130_fd_sc_hd__and3b_1 _440_ (.A_N(_126_),
    .B(_134_),
    .C(_140_),
    .X(_162_));
 sky130_fd_sc_hd__nor2_1 _441_ (.A(_128_),
    .B(_138_),
    .Y(_163_));
 sky130_fd_sc_hd__and4b_1 _442_ (.A_N(_127_),
    .B(_146_),
    .C(_147_),
    .D(_153_),
    .X(_164_));
 sky130_fd_sc_hd__and4_1 _443_ (.A(_151_),
    .B(_162_),
    .C(_163_),
    .D(_164_),
    .X(_165_));
 sky130_fd_sc_hd__or2_1 _444_ (.A(\u_spi_clkgen.nm1_q[14] ),
    .B(\u_spi_clkgen.hp_cnt_q[14] ),
    .X(_166_));
 sky130_fd_sc_hd__nand2_1 _445_ (.A(\u_spi_clkgen.nm1_q[14] ),
    .B(\u_spi_clkgen.hp_cnt_q[14] ),
    .Y(_167_));
 sky130_fd_sc_hd__a21oi_1 _446_ (.A1(_166_),
    .A2(_167_),
    .B1(_130_),
    .Y(_168_));
 sky130_fd_sc_hd__or3_1 _447_ (.A(_121_),
    .B(_142_),
    .C(_145_),
    .X(_169_));
 sky130_fd_sc_hd__o2111a_1 _448_ (.A1(_107_),
    .A2(\u_spi_clkgen.hp_cnt_q[12] ),
    .B1(_150_),
    .C1(_152_),
    .D1(\u_spi_clkgen.running_q ),
    .X(_170_));
 sky130_fd_sc_hd__and4b_1 _449_ (.A_N(_169_),
    .B(_133_),
    .C(_168_),
    .D(_170_),
    .X(_171_));
 sky130_fd_sc_hd__nand3_2 _450_ (.A(_161_),
    .B(_165_),
    .C(_171_),
    .Y(_172_));
 sky130_fd_sc_hd__and4_2 _451_ (.A(\edge_cnt_unused[0] ),
    .B(_161_),
    .C(_165_),
    .D(_171_),
    .X(_173_));
 sky130_fd_sc_hd__nand2_1 _452_ (.A(_120_),
    .B(_173_),
    .Y(_174_));
 sky130_fd_sc_hd__a21oi_1 _453_ (.A1(_112_),
    .A2(_113_),
    .B1(_174_),
    .Y(_175_));
 sky130_fd_sc_hd__a211o_1 _454_ (.A1(net111),
    .A2(net77),
    .B1(_175_),
    .C1(_111_),
    .X(_000_));
 sky130_fd_sc_hd__or3_1 _455_ (.A(\edge_cnt_unused[0] ),
    .B(_119_),
    .C(_172_),
    .X(_176_));
 sky130_fd_sc_hd__nor2_1 _456_ (.A(_112_),
    .B(_176_),
    .Y(_177_));
 sky130_fd_sc_hd__and2_1 _457_ (.A(net99),
    .B(_174_),
    .X(_178_));
 sky130_fd_sc_hd__o21a_1 _458_ (.A1(net148),
    .A2(_177_),
    .B1(_178_),
    .X(_001_));
 sky130_fd_sc_hd__and2_1 _459_ (.A(\u_spi_ctrl.state_q[2] ),
    .B(_176_),
    .X(_179_));
 sky130_fd_sc_hd__a31o_1 _460_ (.A1(_108_),
    .A2(_120_),
    .A3(_156_),
    .B1(_112_),
    .X(_180_));
 sky130_fd_sc_hd__nor2_1 _461_ (.A(_111_),
    .B(net75),
    .Y(_181_));
 sky130_fd_sc_hd__a22o_1 _462_ (.A1(_178_),
    .A2(_179_),
    .B1(_181_),
    .B2(net111),
    .X(_002_));
 sky130_fd_sc_hd__and2_1 _463_ (.A(net92),
    .B(net22),
    .X(_003_));
 sky130_fd_sc_hd__and2_1 _464_ (.A(net99),
    .B(net100),
    .X(_004_));
 sky130_fd_sc_hd__and4_1 _465_ (.A(_108_),
    .B(net96),
    .C(_120_),
    .D(_156_),
    .X(_006_));
 sky130_fd_sc_hd__a31o_1 _466_ (.A1(net95),
    .A2(net102),
    .A3(_115_),
    .B1(_006_),
    .X(_005_));
 sky130_fd_sc_hd__a21boi_1 _467_ (.A1(_113_),
    .A2(_180_),
    .B1_N(_174_),
    .Y(_182_));
 sky130_fd_sc_hd__o31a_1 _468_ (.A1(\u_spi_ctrl.state_q[2] ),
    .A2(\u_spi_ctrl.state_q[1] ),
    .A3(net85),
    .B1(net176),
    .X(_183_));
 sky130_fd_sc_hd__o31a_1 _469_ (.A1(_177_),
    .A2(_182_),
    .A3(_183_),
    .B1(net99),
    .X(_007_));
 sky130_fd_sc_hd__mux2_1 _470_ (.A0(net20),
    .A1(\u_spi_ctrl.cs_mode_q ),
    .S(net42),
    .X(_184_));
 sky130_fd_sc_hd__mux2_1 _471_ (.A0(net82),
    .A1(net19),
    .S(_184_),
    .X(_185_));
 sky130_fd_sc_hd__a31o_1 _472_ (.A1(net42),
    .A2(_114_),
    .A3(_176_),
    .B1(_185_),
    .X(_186_));
 sky130_fd_sc_hd__and4_1 _473_ (.A(net43),
    .B(net42),
    .C(_114_),
    .D(_176_),
    .X(_187_));
 sky130_fd_sc_hd__or3b_1 _474_ (.A(_187_),
    .B(_111_),
    .C_N(_186_),
    .X(_008_));
 sky130_fd_sc_hd__a21bo_1 _475_ (.A1(_120_),
    .A2(_173_),
    .B1_N(\u_spi_clkgen.running_q ),
    .X(_188_));
 sky130_fd_sc_hd__a21oi_1 _476_ (.A1(net76),
    .A2(_188_),
    .B1(_111_),
    .Y(_009_));
 sky130_fd_sc_hd__and3_1 _477_ (.A(net24),
    .B(net42),
    .C(net95),
    .X(_010_));
 sky130_fd_sc_hd__nor2_1 _478_ (.A(_116_),
    .B(_172_),
    .Y(_189_));
 sky130_fd_sc_hd__nor3_1 _479_ (.A(net84),
    .B(_188_),
    .C(_189_),
    .Y(_190_));
 sky130_fd_sc_hd__or3_1 _480_ (.A(_116_),
    .B(net83),
    .C(_172_),
    .X(_191_));
 sky130_fd_sc_hd__mux2_1 _481_ (.A0(_109_),
    .A1(net18),
    .S(_191_),
    .X(_192_));
 sky130_fd_sc_hd__o41a_1 _482_ (.A1(net63),
    .A2(net83),
    .A3(_188_),
    .A4(_189_),
    .B1(net92),
    .X(_193_));
 sky130_fd_sc_hd__o21a_1 _483_ (.A1(_190_),
    .A2(_192_),
    .B1(_193_),
    .X(_011_));
 sky130_fd_sc_hd__nor2_2 _484_ (.A(_111_),
    .B(net85),
    .Y(_194_));
 sky130_fd_sc_hd__o21ai_1 _485_ (.A1(\edge_cnt_unused[0] ),
    .A2(_156_),
    .B1(_194_),
    .Y(_195_));
 sky130_fd_sc_hd__nor2_1 _486_ (.A(_173_),
    .B(_195_),
    .Y(_012_));
 sky130_fd_sc_hd__and2_1 _487_ (.A(\edge_cnt_unused[1] ),
    .B(_173_),
    .X(_196_));
 sky130_fd_sc_hd__o21ai_1 _488_ (.A1(net160),
    .A2(_173_),
    .B1(_194_),
    .Y(_197_));
 sky130_fd_sc_hd__nor2_1 _489_ (.A(_196_),
    .B(_197_),
    .Y(_013_));
 sky130_fd_sc_hd__o21ai_1 _490_ (.A1(net122),
    .A2(_196_),
    .B1(_194_),
    .Y(_198_));
 sky130_fd_sc_hd__a21oi_1 _491_ (.A1(net122),
    .A2(_196_),
    .B1(_198_),
    .Y(_014_));
 sky130_fd_sc_hd__a31o_1 _492_ (.A1(\edge_cnt_unused[2] ),
    .A2(\edge_cnt_unused[1] ),
    .A3(_173_),
    .B1(\edge_cnt_unused[3] ),
    .X(_199_));
 sky130_fd_sc_hd__and4_1 _493_ (.A(\edge_cnt_unused[3] ),
    .B(\edge_cnt_unused[2] ),
    .C(\edge_cnt_unused[1] ),
    .D(_173_),
    .X(_200_));
 sky130_fd_sc_hd__and3b_1 _494_ (.A_N(_200_),
    .B(_194_),
    .C(_199_),
    .X(_015_));
 sky130_fd_sc_hd__o21ai_1 _495_ (.A1(\edge_cnt_unused[4] ),
    .A2(_200_),
    .B1(_194_),
    .Y(_201_));
 sky130_fd_sc_hd__a21oi_1 _496_ (.A1(net143),
    .A2(_200_),
    .B1(_201_),
    .Y(_016_));
 sky130_fd_sc_hd__a21o_1 _497_ (.A1(\edge_cnt_unused[4] ),
    .A2(_200_),
    .B1(\edge_cnt_unused[5] ),
    .X(_202_));
 sky130_fd_sc_hd__nand3_1 _498_ (.A(\edge_cnt_unused[5] ),
    .B(\edge_cnt_unused[4] ),
    .C(_200_),
    .Y(_203_));
 sky130_fd_sc_hd__and3_1 _499_ (.A(_194_),
    .B(_202_),
    .C(_203_),
    .X(_017_));
 sky130_fd_sc_hd__and2_1 _500_ (.A(_172_),
    .B(_194_),
    .X(_204_));
 sky130_fd_sc_hd__a21boi_1 _501_ (.A1(\u_spi_clkgen.running_q ),
    .A2(\u_spi_clkgen.hp_cnt_q[0] ),
    .B1_N(net73),
    .Y(_205_));
 sky130_fd_sc_hd__o21a_1 _502_ (.A1(\u_spi_clkgen.running_q ),
    .A2(net170),
    .B1(_205_),
    .X(_018_));
 sky130_fd_sc_hd__a21o_1 _503_ (.A1(\u_spi_clkgen.running_q ),
    .A2(\u_spi_clkgen.hp_cnt_q[0] ),
    .B1(\u_spi_clkgen.hp_cnt_q[1] ),
    .X(_206_));
 sky130_fd_sc_hd__and3_1 _504_ (.A(\u_spi_clkgen.running_q ),
    .B(\u_spi_clkgen.hp_cnt_q[1] ),
    .C(\u_spi_clkgen.hp_cnt_q[0] ),
    .X(_207_));
 sky130_fd_sc_hd__and3b_1 _505_ (.A_N(_207_),
    .B(net73),
    .C(_206_),
    .X(_019_));
 sky130_fd_sc_hd__and4_1 _506_ (.A(\u_spi_clkgen.running_q ),
    .B(\u_spi_clkgen.hp_cnt_q[2] ),
    .C(\u_spi_clkgen.hp_cnt_q[1] ),
    .D(\u_spi_clkgen.hp_cnt_q[0] ),
    .X(_208_));
 sky130_fd_sc_hd__o21ai_1 _507_ (.A1(net145),
    .A2(_207_),
    .B1(net73),
    .Y(_209_));
 sky130_fd_sc_hd__nor2_1 _508_ (.A(_208_),
    .B(_209_),
    .Y(_020_));
 sky130_fd_sc_hd__and2_1 _509_ (.A(\u_spi_clkgen.hp_cnt_q[3] ),
    .B(_208_),
    .X(_210_));
 sky130_fd_sc_hd__o21ai_1 _510_ (.A1(net164),
    .A2(_208_),
    .B1(net73),
    .Y(_211_));
 sky130_fd_sc_hd__nor2_1 _511_ (.A(_210_),
    .B(_211_),
    .Y(_021_));
 sky130_fd_sc_hd__and2_1 _512_ (.A(\u_spi_clkgen.hp_cnt_q[4] ),
    .B(\u_spi_clkgen.hp_cnt_q[3] ),
    .X(_212_));
 sky130_fd_sc_hd__a21boi_1 _513_ (.A1(\u_spi_clkgen.hp_cnt_q[4] ),
    .A2(_210_),
    .B1_N(net73),
    .Y(_213_));
 sky130_fd_sc_hd__o21a_1 _514_ (.A1(net155),
    .A2(_210_),
    .B1(_213_),
    .X(_022_));
 sky130_fd_sc_hd__and3_1 _515_ (.A(\u_spi_clkgen.hp_cnt_q[5] ),
    .B(_208_),
    .C(_212_),
    .X(_214_));
 sky130_fd_sc_hd__a21o_1 _516_ (.A1(_208_),
    .A2(_212_),
    .B1(\u_spi_clkgen.hp_cnt_q[5] ),
    .X(_215_));
 sky130_fd_sc_hd__and3b_1 _517_ (.A_N(_214_),
    .B(_215_),
    .C(net73),
    .X(_023_));
 sky130_fd_sc_hd__and4_1 _518_ (.A(\u_spi_clkgen.hp_cnt_q[6] ),
    .B(\u_spi_clkgen.hp_cnt_q[5] ),
    .C(_208_),
    .D(_212_),
    .X(_216_));
 sky130_fd_sc_hd__o21ai_1 _519_ (.A1(net159),
    .A2(_214_),
    .B1(net73),
    .Y(_217_));
 sky130_fd_sc_hd__nor2_1 _520_ (.A(_216_),
    .B(_217_),
    .Y(_024_));
 sky130_fd_sc_hd__and2_1 _521_ (.A(\u_spi_clkgen.hp_cnt_q[7] ),
    .B(_216_),
    .X(_218_));
 sky130_fd_sc_hd__o21ai_1 _522_ (.A1(net172),
    .A2(_216_),
    .B1(net73),
    .Y(_219_));
 sky130_fd_sc_hd__nor2_1 _523_ (.A(_218_),
    .B(_219_),
    .Y(_025_));
 sky130_fd_sc_hd__and3_1 _524_ (.A(\u_spi_clkgen.hp_cnt_q[8] ),
    .B(\u_spi_clkgen.hp_cnt_q[7] ),
    .C(_216_),
    .X(_220_));
 sky130_fd_sc_hd__o21ai_1 _525_ (.A1(net165),
    .A2(_218_),
    .B1(net73),
    .Y(_221_));
 sky130_fd_sc_hd__nor2_1 _526_ (.A(_220_),
    .B(_221_),
    .Y(_026_));
 sky130_fd_sc_hd__and4_2 _527_ (.A(\u_spi_clkgen.hp_cnt_q[9] ),
    .B(\u_spi_clkgen.hp_cnt_q[8] ),
    .C(\u_spi_clkgen.hp_cnt_q[7] ),
    .D(_216_),
    .X(_222_));
 sky130_fd_sc_hd__o21ai_1 _528_ (.A1(net147),
    .A2(_220_),
    .B1(net73),
    .Y(_223_));
 sky130_fd_sc_hd__nor2_1 _529_ (.A(_222_),
    .B(_223_),
    .Y(_027_));
 sky130_fd_sc_hd__o21ai_1 _530_ (.A1(\u_spi_clkgen.hp_cnt_q[10] ),
    .A2(_222_),
    .B1(net74),
    .Y(_224_));
 sky130_fd_sc_hd__a21oi_1 _531_ (.A1(net158),
    .A2(_222_),
    .B1(_224_),
    .Y(_028_));
 sky130_fd_sc_hd__a21o_1 _532_ (.A1(\u_spi_clkgen.hp_cnt_q[10] ),
    .A2(_222_),
    .B1(\u_spi_clkgen.hp_cnt_q[11] ),
    .X(_225_));
 sky130_fd_sc_hd__and3_1 _533_ (.A(\u_spi_clkgen.hp_cnt_q[11] ),
    .B(\u_spi_clkgen.hp_cnt_q[10] ),
    .C(_222_),
    .X(_226_));
 sky130_fd_sc_hd__and3b_1 _534_ (.A_N(_226_),
    .B(net74),
    .C(_225_),
    .X(_029_));
 sky130_fd_sc_hd__and4_1 _535_ (.A(\u_spi_clkgen.hp_cnt_q[12] ),
    .B(\u_spi_clkgen.hp_cnt_q[11] ),
    .C(\u_spi_clkgen.hp_cnt_q[10] ),
    .D(_222_),
    .X(_227_));
 sky130_fd_sc_hd__o21ai_1 _536_ (.A1(\u_spi_clkgen.hp_cnt_q[12] ),
    .A2(_226_),
    .B1(net74),
    .Y(_228_));
 sky130_fd_sc_hd__nor2_1 _537_ (.A(_227_),
    .B(_228_),
    .Y(_030_));
 sky130_fd_sc_hd__o21ai_1 _538_ (.A1(\u_spi_clkgen.hp_cnt_q[13] ),
    .A2(_227_),
    .B1(net74),
    .Y(_229_));
 sky130_fd_sc_hd__a21oi_1 _539_ (.A1(net131),
    .A2(_227_),
    .B1(_229_),
    .Y(_031_));
 sky130_fd_sc_hd__a21o_1 _540_ (.A1(\u_spi_clkgen.hp_cnt_q[13] ),
    .A2(_227_),
    .B1(\u_spi_clkgen.hp_cnt_q[14] ),
    .X(_230_));
 sky130_fd_sc_hd__and3_1 _541_ (.A(\u_spi_clkgen.hp_cnt_q[14] ),
    .B(\u_spi_clkgen.hp_cnt_q[13] ),
    .C(_227_),
    .X(_231_));
 sky130_fd_sc_hd__and3b_1 _542_ (.A_N(_231_),
    .B(net74),
    .C(_230_),
    .X(_032_));
 sky130_fd_sc_hd__o21ai_1 _543_ (.A1(net106),
    .A2(_231_),
    .B1(net74),
    .Y(_232_));
 sky130_fd_sc_hd__a21oi_1 _544_ (.A1(net106),
    .A2(_231_),
    .B1(_232_),
    .Y(_033_));
 sky130_fd_sc_hd__or4_1 _545_ (.A(net14),
    .B(net13),
    .C(net12),
    .D(net11),
    .X(_233_));
 sky130_fd_sc_hd__or2_1 _546_ (.A(net4),
    .B(net10),
    .X(_234_));
 sky130_fd_sc_hd__or4_2 _547_ (.A(net3),
    .B(net2),
    .C(net16),
    .D(net15),
    .X(_235_));
 sky130_fd_sc_hd__or4_1 _548_ (.A(net7),
    .B(net6),
    .C(net5),
    .D(net9),
    .X(_236_));
 sky130_fd_sc_hd__nor4_2 _549_ (.A(_233_),
    .B(_234_),
    .C(_235_),
    .D(_236_),
    .Y(_237_));
 sky130_fd_sc_hd__or3b_1 _550_ (.A(_237_),
    .B(net75),
    .C_N(net1),
    .X(_238_));
 sky130_fd_sc_hd__o211a_1 _551_ (.A1(net157),
    .A2(net82),
    .B1(_238_),
    .C1(net91),
    .X(_034_));
 sky130_fd_sc_hd__o21bai_1 _552_ (.A1(net8),
    .A2(net1),
    .B1_N(_237_),
    .Y(_239_));
 sky130_fd_sc_hd__a21o_1 _553_ (.A1(net8),
    .A2(net1),
    .B1(net75),
    .X(_240_));
 sky130_fd_sc_hd__o221a_1 _554_ (.A1(net163),
    .A2(net82),
    .B1(_239_),
    .B2(_240_),
    .C1(net91),
    .X(_035_));
 sky130_fd_sc_hd__nor2_1 _555_ (.A(_110_),
    .B(_239_),
    .Y(_241_));
 sky130_fd_sc_hd__or3_1 _556_ (.A(net9),
    .B(net8),
    .C(net1),
    .X(_242_));
 sky130_fd_sc_hd__or2_1 _557_ (.A(_237_),
    .B(_242_),
    .X(_243_));
 sky130_fd_sc_hd__nand2_1 _558_ (.A(net82),
    .B(_243_),
    .Y(_244_));
 sky130_fd_sc_hd__o221a_1 _559_ (.A1(net151),
    .A2(net82),
    .B1(_241_),
    .B2(_244_),
    .C1(net91),
    .X(_036_));
 sky130_fd_sc_hd__or2_1 _560_ (.A(net10),
    .B(_243_),
    .X(_245_));
 sky130_fd_sc_hd__inv_2 _561_ (.A(_245_),
    .Y(_246_));
 sky130_fd_sc_hd__a21o_1 _562_ (.A1(net10),
    .A2(_243_),
    .B1(net75),
    .X(_247_));
 sky130_fd_sc_hd__o221a_1 _563_ (.A1(net152),
    .A2(net82),
    .B1(_246_),
    .B2(_247_),
    .C1(net91),
    .X(_037_));
 sky130_fd_sc_hd__nor2_1 _564_ (.A(net11),
    .B(_245_),
    .Y(_248_));
 sky130_fd_sc_hd__a21o_1 _565_ (.A1(net11),
    .A2(_245_),
    .B1(net75),
    .X(_249_));
 sky130_fd_sc_hd__o221a_1 _566_ (.A1(net156),
    .A2(net82),
    .B1(_248_),
    .B2(_249_),
    .C1(net91),
    .X(_038_));
 sky130_fd_sc_hd__o21a_1 _567_ (.A1(net11),
    .A2(_245_),
    .B1(net12),
    .X(_250_));
 sky130_fd_sc_hd__or3_1 _568_ (.A(net12),
    .B(net11),
    .C(_245_),
    .X(_251_));
 sky130_fd_sc_hd__nand2_1 _569_ (.A(net82),
    .B(_251_),
    .Y(_252_));
 sky130_fd_sc_hd__o221a_1 _570_ (.A1(net149),
    .A2(net82),
    .B1(_250_),
    .B2(_252_),
    .C1(net94),
    .X(_039_));
 sky130_fd_sc_hd__and2_1 _571_ (.A(net13),
    .B(_251_),
    .X(_253_));
 sky130_fd_sc_hd__o21ai_1 _572_ (.A1(net13),
    .A2(_251_),
    .B1(net80),
    .Y(_254_));
 sky130_fd_sc_hd__o221a_1 _573_ (.A1(net154),
    .A2(net80),
    .B1(_253_),
    .B2(_254_),
    .C1(net94),
    .X(_040_));
 sky130_fd_sc_hd__o21a_1 _574_ (.A1(net13),
    .A2(_251_),
    .B1(net14),
    .X(_255_));
 sky130_fd_sc_hd__or4_4 _575_ (.A(net10),
    .B(_233_),
    .C(_237_),
    .D(_242_),
    .X(_256_));
 sky130_fd_sc_hd__nand2_1 _576_ (.A(net80),
    .B(_256_),
    .Y(_257_));
 sky130_fd_sc_hd__o221a_1 _577_ (.A1(net144),
    .A2(net80),
    .B1(_255_),
    .B2(_257_),
    .C1(net94),
    .X(_041_));
 sky130_fd_sc_hd__nor2_1 _578_ (.A(net15),
    .B(_256_),
    .Y(_258_));
 sky130_fd_sc_hd__a21o_1 _579_ (.A1(net15),
    .A2(_256_),
    .B1(net75),
    .X(_259_));
 sky130_fd_sc_hd__o221a_1 _580_ (.A1(net146),
    .A2(net80),
    .B1(_258_),
    .B2(_259_),
    .C1(net96),
    .X(_042_));
 sky130_fd_sc_hd__or3_1 _581_ (.A(net16),
    .B(net15),
    .C(_256_),
    .X(_260_));
 sky130_fd_sc_hd__o21a_1 _582_ (.A1(net15),
    .A2(_256_),
    .B1(net16),
    .X(_261_));
 sky130_fd_sc_hd__nand2_1 _583_ (.A(net81),
    .B(_260_),
    .Y(_262_));
 sky130_fd_sc_hd__o221a_1 _584_ (.A1(net150),
    .A2(net81),
    .B1(_261_),
    .B2(_262_),
    .C1(net96),
    .X(_043_));
 sky130_fd_sc_hd__o21ai_1 _585_ (.A1(net2),
    .A2(_260_),
    .B1(net81),
    .Y(_263_));
 sky130_fd_sc_hd__a21o_1 _586_ (.A1(net2),
    .A2(_260_),
    .B1(_263_),
    .X(_264_));
 sky130_fd_sc_hd__o211a_1 _587_ (.A1(net138),
    .A2(net80),
    .B1(_264_),
    .C1(net95),
    .X(_044_));
 sky130_fd_sc_hd__o21a_1 _588_ (.A1(net2),
    .A2(_260_),
    .B1(net3),
    .X(_265_));
 sky130_fd_sc_hd__o21ai_1 _589_ (.A1(_235_),
    .A2(_256_),
    .B1(net80),
    .Y(_266_));
 sky130_fd_sc_hd__o221a_1 _590_ (.A1(net153),
    .A2(net80),
    .B1(_265_),
    .B2(_266_),
    .C1(net96),
    .X(_045_));
 sky130_fd_sc_hd__o21a_1 _591_ (.A1(_235_),
    .A2(_256_),
    .B1(net4),
    .X(_267_));
 sky130_fd_sc_hd__or3_1 _592_ (.A(net4),
    .B(_235_),
    .C(_256_),
    .X(_268_));
 sky130_fd_sc_hd__or3b_1 _593_ (.A(net79),
    .B(_267_),
    .C_N(_268_),
    .X(_269_));
 sky130_fd_sc_hd__o211a_1 _594_ (.A1(net171),
    .A2(net80),
    .B1(_269_),
    .C1(net96),
    .X(_046_));
 sky130_fd_sc_hd__a21oi_1 _595_ (.A1(net5),
    .A2(_268_),
    .B1(net79),
    .Y(_270_));
 sky130_fd_sc_hd__or2_1 _596_ (.A(net5),
    .B(_268_),
    .X(_271_));
 sky130_fd_sc_hd__nand2_1 _597_ (.A(_270_),
    .B(_271_),
    .Y(_272_));
 sky130_fd_sc_hd__o211a_1 _598_ (.A1(net142),
    .A2(net80),
    .B1(_272_),
    .C1(net96),
    .X(_047_));
 sky130_fd_sc_hd__nand2_1 _599_ (.A(net6),
    .B(_271_),
    .Y(_273_));
 sky130_fd_sc_hd__or2_1 _600_ (.A(net6),
    .B(_271_),
    .X(_274_));
 sky130_fd_sc_hd__a21o_1 _601_ (.A1(_106_),
    .A2(net79),
    .B1(_111_),
    .X(_275_));
 sky130_fd_sc_hd__a31oi_1 _602_ (.A1(net81),
    .A2(_273_),
    .A3(_274_),
    .B1(_275_),
    .Y(_048_));
 sky130_fd_sc_hd__a32o_1 _603_ (.A1(net7),
    .A2(_181_),
    .A3(_274_),
    .B1(_194_),
    .B2(net101),
    .X(_049_));
 sky130_fd_sc_hd__and2_1 _604_ (.A(net99),
    .B(net103),
    .X(_050_));
 sky130_fd_sc_hd__xnor2_1 _605_ (.A(\u_spi_shift.cpha_q ),
    .B(\edge_cnt_unused[0] ),
    .Y(_276_));
 sky130_fd_sc_hd__and4bb_1 _606_ (.A_N(_111_),
    .B_N(_116_),
    .C(_156_),
    .D(_276_),
    .X(_051_));
 sky130_fd_sc_hd__and2_1 _607_ (.A(net91),
    .B(_184_),
    .X(_052_));
 sky130_fd_sc_hd__or4b_2 _608_ (.A(\edge_cnt_unused[0] ),
    .B(_119_),
    .C(net85),
    .D_N(_156_),
    .X(_277_));
 sky130_fd_sc_hd__and4bb_1 _609_ (.A_N(_119_),
    .B_N(_172_),
    .C(net77),
    .D(_108_),
    .X(_278_));
 sky130_fd_sc_hd__or2_1 _610_ (.A(net161),
    .B(net69),
    .X(_279_));
 sky130_fd_sc_hd__o211a_1 _611_ (.A1(\u_spi_shift.rx_sr_q[0] ),
    .A2(net71),
    .B1(_279_),
    .C1(net95),
    .X(_053_));
 sky130_fd_sc_hd__or2_1 _612_ (.A(net54),
    .B(net69),
    .X(_280_));
 sky130_fd_sc_hd__o211a_1 _613_ (.A1(net136),
    .A2(net71),
    .B1(_280_),
    .C1(net95),
    .X(_054_));
 sky130_fd_sc_hd__or2_1 _614_ (.A(net55),
    .B(net69),
    .X(_281_));
 sky130_fd_sc_hd__o211a_1 _615_ (.A1(net140),
    .A2(net71),
    .B1(_281_),
    .C1(net95),
    .X(_055_));
 sky130_fd_sc_hd__or2_1 _616_ (.A(net56),
    .B(net69),
    .X(_282_));
 sky130_fd_sc_hd__o211a_1 _617_ (.A1(net132),
    .A2(net71),
    .B1(_282_),
    .C1(net95),
    .X(_056_));
 sky130_fd_sc_hd__or2_1 _618_ (.A(net57),
    .B(net69),
    .X(_283_));
 sky130_fd_sc_hd__o211a_1 _619_ (.A1(net129),
    .A2(net71),
    .B1(_283_),
    .C1(net95),
    .X(_057_));
 sky130_fd_sc_hd__or2_1 _620_ (.A(net58),
    .B(net69),
    .X(_284_));
 sky130_fd_sc_hd__o211a_1 _621_ (.A1(net127),
    .A2(net71),
    .B1(_284_),
    .C1(net95),
    .X(_058_));
 sky130_fd_sc_hd__or2_1 _622_ (.A(net59),
    .B(net69),
    .X(_285_));
 sky130_fd_sc_hd__o211a_1 _623_ (.A1(net134),
    .A2(net71),
    .B1(_285_),
    .C1(net97),
    .X(_059_));
 sky130_fd_sc_hd__or2_1 _624_ (.A(net60),
    .B(net69),
    .X(_286_));
 sky130_fd_sc_hd__o211a_1 _625_ (.A1(net125),
    .A2(net71),
    .B1(_286_),
    .C1(net97),
    .X(_060_));
 sky130_fd_sc_hd__and2_1 _626_ (.A(net169),
    .B(net71),
    .X(_287_));
 sky130_fd_sc_hd__and3_1 _627_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[8] ),
    .C(net70),
    .X(_288_));
 sky130_fd_sc_hd__o21a_1 _628_ (.A1(_287_),
    .A2(_288_),
    .B1(net97),
    .X(_061_));
 sky130_fd_sc_hd__and2_1 _629_ (.A(net62),
    .B(net72),
    .X(_289_));
 sky130_fd_sc_hd__and3_1 _630_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[9] ),
    .C(net69),
    .X(_290_));
 sky130_fd_sc_hd__o21a_1 _631_ (.A1(_289_),
    .A2(_290_),
    .B1(net97),
    .X(_062_));
 sky130_fd_sc_hd__and2_1 _632_ (.A(net175),
    .B(net72),
    .X(_291_));
 sky130_fd_sc_hd__and3_1 _633_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[10] ),
    .C(net69),
    .X(_292_));
 sky130_fd_sc_hd__o21a_1 _634_ (.A1(_291_),
    .A2(_292_),
    .B1(net97),
    .X(_063_));
 sky130_fd_sc_hd__and2_1 _635_ (.A(net168),
    .B(net72),
    .X(_293_));
 sky130_fd_sc_hd__and3_1 _636_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[11] ),
    .C(net70),
    .X(_294_));
 sky130_fd_sc_hd__o21a_1 _637_ (.A1(_293_),
    .A2(_294_),
    .B1(net98),
    .X(_064_));
 sky130_fd_sc_hd__and2_1 _638_ (.A(net50),
    .B(net72),
    .X(_295_));
 sky130_fd_sc_hd__and3_1 _639_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[12] ),
    .C(net70),
    .X(_296_));
 sky130_fd_sc_hd__o21a_1 _640_ (.A1(_295_),
    .A2(_296_),
    .B1(net98),
    .X(_065_));
 sky130_fd_sc_hd__and2_1 _641_ (.A(net51),
    .B(net72),
    .X(_297_));
 sky130_fd_sc_hd__and3_1 _642_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[13] ),
    .C(net70),
    .X(_298_));
 sky130_fd_sc_hd__o21a_1 _643_ (.A1(_297_),
    .A2(_298_),
    .B1(net98),
    .X(_066_));
 sky130_fd_sc_hd__and2_1 _644_ (.A(net174),
    .B(net72),
    .X(_299_));
 sky130_fd_sc_hd__and3_1 _645_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[14] ),
    .C(net70),
    .X(_300_));
 sky130_fd_sc_hd__o21a_1 _646_ (.A1(_299_),
    .A2(_300_),
    .B1(net98),
    .X(_067_));
 sky130_fd_sc_hd__and2_1 _647_ (.A(net173),
    .B(net72),
    .X(_301_));
 sky130_fd_sc_hd__and3_1 _648_ (.A(\u_spi_clkgen.wl_q ),
    .B(\u_spi_shift.rx_sr_q[15] ),
    .C(net70),
    .X(_302_));
 sky130_fd_sc_hd__o21a_1 _649_ (.A1(_301_),
    .A2(_302_),
    .B1(net98),
    .X(_068_));
 sky130_fd_sc_hd__mux2_1 _650_ (.A0(\u_spi_shift.rx_sr_q[0] ),
    .A1(miso_s),
    .S(net87),
    .X(_303_));
 sky130_fd_sc_hd__and3_1 _651_ (.A(net99),
    .B(net77),
    .C(_303_),
    .X(_069_));
 sky130_fd_sc_hd__mux2_1 _652_ (.A0(\u_spi_shift.rx_sr_q[1] ),
    .A1(\u_spi_shift.rx_sr_q[0] ),
    .S(net86),
    .X(_304_));
 sky130_fd_sc_hd__and3_1 _653_ (.A(net95),
    .B(net75),
    .C(_304_),
    .X(_070_));
 sky130_fd_sc_hd__mux2_1 _654_ (.A0(\u_spi_shift.rx_sr_q[2] ),
    .A1(\u_spi_shift.rx_sr_q[1] ),
    .S(net86),
    .X(_305_));
 sky130_fd_sc_hd__and3_1 _655_ (.A(net23),
    .B(net75),
    .C(_305_),
    .X(_071_));
 sky130_fd_sc_hd__mux2_1 _656_ (.A0(\u_spi_shift.rx_sr_q[3] ),
    .A1(\u_spi_shift.rx_sr_q[2] ),
    .S(net86),
    .X(_306_));
 sky130_fd_sc_hd__and3_1 _657_ (.A(net96),
    .B(net75),
    .C(_306_),
    .X(_072_));
 sky130_fd_sc_hd__mux2_1 _658_ (.A0(\u_spi_shift.rx_sr_q[4] ),
    .A1(\u_spi_shift.rx_sr_q[3] ),
    .S(net86),
    .X(_307_));
 sky130_fd_sc_hd__and3_1 _659_ (.A(net96),
    .B(net75),
    .C(_307_),
    .X(_073_));
 sky130_fd_sc_hd__mux2_1 _660_ (.A0(\u_spi_shift.rx_sr_q[5] ),
    .A1(\u_spi_shift.rx_sr_q[4] ),
    .S(net86),
    .X(_308_));
 sky130_fd_sc_hd__and3_1 _661_ (.A(net96),
    .B(net79),
    .C(_308_),
    .X(_074_));
 sky130_fd_sc_hd__mux2_1 _662_ (.A0(\u_spi_shift.rx_sr_q[6] ),
    .A1(\u_spi_shift.rx_sr_q[5] ),
    .S(net86),
    .X(_309_));
 sky130_fd_sc_hd__and3_1 _663_ (.A(net97),
    .B(net77),
    .C(_309_),
    .X(_075_));
 sky130_fd_sc_hd__mux2_1 _664_ (.A0(\u_spi_shift.rx_sr_q[7] ),
    .A1(\u_spi_shift.rx_sr_q[6] ),
    .S(net86),
    .X(_310_));
 sky130_fd_sc_hd__and3_1 _665_ (.A(net97),
    .B(net77),
    .C(_310_),
    .X(_076_));
 sky130_fd_sc_hd__mux2_1 _666_ (.A0(\u_spi_shift.rx_sr_q[8] ),
    .A1(\u_spi_shift.rx_sr_q[7] ),
    .S(net86),
    .X(_311_));
 sky130_fd_sc_hd__and3_1 _667_ (.A(net97),
    .B(net77),
    .C(_311_),
    .X(_077_));
 sky130_fd_sc_hd__mux2_1 _668_ (.A0(\u_spi_shift.rx_sr_q[9] ),
    .A1(\u_spi_shift.rx_sr_q[8] ),
    .S(net86),
    .X(_312_));
 sky130_fd_sc_hd__and3_1 _669_ (.A(net97),
    .B(net77),
    .C(_312_),
    .X(_078_));
 sky130_fd_sc_hd__mux2_1 _670_ (.A0(\u_spi_shift.rx_sr_q[10] ),
    .A1(\u_spi_shift.rx_sr_q[9] ),
    .S(net86),
    .X(_313_));
 sky130_fd_sc_hd__and3_1 _671_ (.A(net97),
    .B(net77),
    .C(_313_),
    .X(_079_));
 sky130_fd_sc_hd__mux2_1 _672_ (.A0(\u_spi_shift.rx_sr_q[11] ),
    .A1(\u_spi_shift.rx_sr_q[10] ),
    .S(net87),
    .X(_314_));
 sky130_fd_sc_hd__and3_1 _673_ (.A(net98),
    .B(net77),
    .C(_314_),
    .X(_080_));
 sky130_fd_sc_hd__mux2_1 _674_ (.A0(\u_spi_shift.rx_sr_q[12] ),
    .A1(\u_spi_shift.rx_sr_q[11] ),
    .S(net87),
    .X(_315_));
 sky130_fd_sc_hd__and3_1 _675_ (.A(net98),
    .B(net77),
    .C(_315_),
    .X(_081_));
 sky130_fd_sc_hd__mux2_1 _676_ (.A0(\u_spi_shift.rx_sr_q[13] ),
    .A1(\u_spi_shift.rx_sr_q[12] ),
    .S(net87),
    .X(_316_));
 sky130_fd_sc_hd__and3_1 _677_ (.A(net98),
    .B(net78),
    .C(_316_),
    .X(_082_));
 sky130_fd_sc_hd__mux2_1 _678_ (.A0(\u_spi_shift.rx_sr_q[14] ),
    .A1(\u_spi_shift.rx_sr_q[13] ),
    .S(net87),
    .X(_317_));
 sky130_fd_sc_hd__and3_1 _679_ (.A(net98),
    .B(net78),
    .C(_317_),
    .X(_083_));
 sky130_fd_sc_hd__mux2_1 _680_ (.A0(\u_spi_shift.rx_sr_q[15] ),
    .A1(\u_spi_shift.rx_sr_q[14] ),
    .S(net87),
    .X(_318_));
 sky130_fd_sc_hd__and3_1 _681_ (.A(net98),
    .B(net78),
    .C(_318_),
    .X(_084_));
 sky130_fd_sc_hd__or3_1 _682_ (.A(_116_),
    .B(_172_),
    .C(_276_),
    .X(_319_));
 sky130_fd_sc_hd__mux2_1 _683_ (.A0(\u_spi_shift.tx_sr_q[15] ),
    .A1(net46),
    .S(_319_),
    .X(_320_));
 sky130_fd_sc_hd__mux2_1 _684_ (.A0(net38),
    .A1(net31),
    .S(net90),
    .X(_321_));
 sky130_fd_sc_hd__a31o_1 _685_ (.A1(_104_),
    .A2(net93),
    .A3(_321_),
    .B1(_194_),
    .X(_322_));
 sky130_fd_sc_hd__o211a_1 _686_ (.A1(net84),
    .A2(_320_),
    .B1(_322_),
    .C1(net71),
    .X(_085_));
 sky130_fd_sc_hd__nor2_2 _687_ (.A(_104_),
    .B(net76),
    .Y(_323_));
 sky130_fd_sc_hd__nand2_2 _688_ (.A(net17),
    .B(net84),
    .Y(_324_));
 sky130_fd_sc_hd__o31a_1 _689_ (.A1(_116_),
    .A2(_172_),
    .A3(_276_),
    .B1(net76),
    .X(_325_));
 sky130_fd_sc_hd__nand2_1 _690_ (.A(net78),
    .B(_319_),
    .Y(_326_));
 sky130_fd_sc_hd__a32o_1 _691_ (.A1(net88),
    .A2(net25),
    .A3(_323_),
    .B1(net67),
    .B2(net166),
    .X(_327_));
 sky130_fd_sc_hd__and2_1 _692_ (.A(net92),
    .B(_327_),
    .X(_086_));
 sky130_fd_sc_hd__nor2_2 _693_ (.A(net17),
    .B(net76),
    .Y(_328_));
 sky130_fd_sc_hd__nand2_4 _694_ (.A(_104_),
    .B(net84),
    .Y(_329_));
 sky130_fd_sc_hd__a21o_1 _695_ (.A1(net88),
    .A2(net25),
    .B1(_329_),
    .X(_330_));
 sky130_fd_sc_hd__or2_1 _696_ (.A(\u_spi_shift.tx_sr_q[0] ),
    .B(net84),
    .X(_331_));
 sky130_fd_sc_hd__a21o_1 _697_ (.A1(net88),
    .A2(net32),
    .B1(_324_),
    .X(_332_));
 sky130_fd_sc_hd__a31o_1 _698_ (.A1(_330_),
    .A2(_331_),
    .A3(_332_),
    .B1(net67),
    .X(_333_));
 sky130_fd_sc_hd__o211a_1 _699_ (.A1(net104),
    .A2(net65),
    .B1(_333_),
    .C1(net92),
    .X(_087_));
 sky130_fd_sc_hd__a21o_1 _700_ (.A1(net88),
    .A2(net33),
    .B1(_324_),
    .X(_334_));
 sky130_fd_sc_hd__or2_1 _701_ (.A(\u_spi_shift.tx_sr_q[1] ),
    .B(net83),
    .X(_335_));
 sky130_fd_sc_hd__a21o_1 _702_ (.A1(net88),
    .A2(net32),
    .B1(_329_),
    .X(_336_));
 sky130_fd_sc_hd__a31o_1 _703_ (.A1(_334_),
    .A2(_335_),
    .A3(_336_),
    .B1(net67),
    .X(_337_));
 sky130_fd_sc_hd__o211a_1 _704_ (.A1(net110),
    .A2(net65),
    .B1(_337_),
    .C1(net91),
    .X(_088_));
 sky130_fd_sc_hd__a21o_1 _705_ (.A1(net88),
    .A2(net33),
    .B1(_329_),
    .X(_338_));
 sky130_fd_sc_hd__or2_1 _706_ (.A(\u_spi_shift.tx_sr_q[2] ),
    .B(net83),
    .X(_339_));
 sky130_fd_sc_hd__a21o_1 _707_ (.A1(net88),
    .A2(net34),
    .B1(_324_),
    .X(_340_));
 sky130_fd_sc_hd__a31o_1 _708_ (.A1(_338_),
    .A2(_339_),
    .A3(_340_),
    .B1(net67),
    .X(_341_));
 sky130_fd_sc_hd__o211a_1 _709_ (.A1(net109),
    .A2(net65),
    .B1(_341_),
    .C1(net91),
    .X(_089_));
 sky130_fd_sc_hd__a21o_1 _710_ (.A1(net88),
    .A2(net35),
    .B1(_324_),
    .X(_342_));
 sky130_fd_sc_hd__or2_1 _711_ (.A(\u_spi_shift.tx_sr_q[3] ),
    .B(net83),
    .X(_343_));
 sky130_fd_sc_hd__a21o_1 _712_ (.A1(net88),
    .A2(net34),
    .B1(_329_),
    .X(_344_));
 sky130_fd_sc_hd__a31o_1 _713_ (.A1(_342_),
    .A2(_343_),
    .A3(_344_),
    .B1(net67),
    .X(_345_));
 sky130_fd_sc_hd__o211a_1 _714_ (.A1(net107),
    .A2(net65),
    .B1(_345_),
    .C1(net91),
    .X(_090_));
 sky130_fd_sc_hd__a21o_1 _715_ (.A1(net89),
    .A2(net35),
    .B1(_329_),
    .X(_346_));
 sky130_fd_sc_hd__or2_1 _716_ (.A(\u_spi_shift.tx_sr_q[4] ),
    .B(net83),
    .X(_347_));
 sky130_fd_sc_hd__a21o_1 _717_ (.A1(net89),
    .A2(net36),
    .B1(_324_),
    .X(_348_));
 sky130_fd_sc_hd__a31o_1 _718_ (.A1(_346_),
    .A2(_347_),
    .A3(_348_),
    .B1(net67),
    .X(_349_));
 sky130_fd_sc_hd__o211a_1 _719_ (.A1(net105),
    .A2(net65),
    .B1(_349_),
    .C1(net93),
    .X(_091_));
 sky130_fd_sc_hd__a21o_1 _720_ (.A1(net89),
    .A2(net37),
    .B1(_324_),
    .X(_350_));
 sky130_fd_sc_hd__or2_1 _721_ (.A(\u_spi_shift.tx_sr_q[5] ),
    .B(net83),
    .X(_351_));
 sky130_fd_sc_hd__a21o_1 _722_ (.A1(net89),
    .A2(net36),
    .B1(_329_),
    .X(_352_));
 sky130_fd_sc_hd__a31o_1 _723_ (.A1(_350_),
    .A2(_351_),
    .A3(_352_),
    .B1(net67),
    .X(_353_));
 sky130_fd_sc_hd__o211a_1 _724_ (.A1(net108),
    .A2(net65),
    .B1(_353_),
    .C1(net93),
    .X(_092_));
 sky130_fd_sc_hd__a21o_1 _725_ (.A1(net89),
    .A2(net37),
    .B1(_329_),
    .X(_354_));
 sky130_fd_sc_hd__or2_1 _726_ (.A(\u_spi_shift.tx_sr_q[6] ),
    .B(net83),
    .X(_355_));
 sky130_fd_sc_hd__a21o_1 _727_ (.A1(net88),
    .A2(net38),
    .B1(_324_),
    .X(_356_));
 sky130_fd_sc_hd__a31o_1 _728_ (.A1(_354_),
    .A2(_355_),
    .A3(_356_),
    .B1(net67),
    .X(_357_));
 sky130_fd_sc_hd__o211a_1 _729_ (.A1(net117),
    .A2(net65),
    .B1(_357_),
    .C1(net92),
    .X(_093_));
 sky130_fd_sc_hd__mux2_1 _730_ (.A0(net25),
    .A1(net39),
    .S(net90),
    .X(_358_));
 sky130_fd_sc_hd__a21o_1 _731_ (.A1(net89),
    .A2(net38),
    .B1(_329_),
    .X(_359_));
 sky130_fd_sc_hd__o221a_1 _732_ (.A1(\u_spi_shift.tx_sr_q[7] ),
    .A2(net83),
    .B1(_324_),
    .B2(_358_),
    .C1(_359_),
    .X(_360_));
 sky130_fd_sc_hd__or2_1 _733_ (.A(net68),
    .B(_360_),
    .X(_361_));
 sky130_fd_sc_hd__o211a_1 _734_ (.A1(net115),
    .A2(net66),
    .B1(_361_),
    .C1(net93),
    .X(_094_));
 sky130_fd_sc_hd__mux2_1 _735_ (.A0(net32),
    .A1(net40),
    .S(net90),
    .X(_362_));
 sky130_fd_sc_hd__a22o_1 _736_ (.A1(_328_),
    .A2(_358_),
    .B1(_362_),
    .B2(_323_),
    .X(_363_));
 sky130_fd_sc_hd__a211o_1 _737_ (.A1(\u_spi_shift.tx_sr_q[8] ),
    .A2(net76),
    .B1(net67),
    .C1(_363_),
    .X(_364_));
 sky130_fd_sc_hd__o211a_1 _738_ (.A1(net123),
    .A2(net66),
    .B1(_364_),
    .C1(net92),
    .X(_095_));
 sky130_fd_sc_hd__mux2_1 _739_ (.A0(net33),
    .A1(net26),
    .S(net90),
    .X(_365_));
 sky130_fd_sc_hd__a22o_1 _740_ (.A1(_328_),
    .A2(_362_),
    .B1(_365_),
    .B2(_323_),
    .X(_366_));
 sky130_fd_sc_hd__a211o_1 _741_ (.A1(net178),
    .A2(net76),
    .B1(net68),
    .C1(_366_),
    .X(_367_));
 sky130_fd_sc_hd__o211a_1 _742_ (.A1(net116),
    .A2(net66),
    .B1(_367_),
    .C1(net92),
    .X(_096_));
 sky130_fd_sc_hd__mux2_1 _743_ (.A0(net34),
    .A1(net27),
    .S(net90),
    .X(_368_));
 sky130_fd_sc_hd__a22o_1 _744_ (.A1(\u_spi_shift.tx_sr_q[10] ),
    .A2(net76),
    .B1(_328_),
    .B2(_365_),
    .X(_369_));
 sky130_fd_sc_hd__a211o_1 _745_ (.A1(_323_),
    .A2(_368_),
    .B1(_369_),
    .C1(net68),
    .X(_370_));
 sky130_fd_sc_hd__o211a_1 _746_ (.A1(net113),
    .A2(net65),
    .B1(_370_),
    .C1(net92),
    .X(_097_));
 sky130_fd_sc_hd__mux2_1 _747_ (.A0(net35),
    .A1(net28),
    .S(net90),
    .X(_371_));
 sky130_fd_sc_hd__a22o_1 _748_ (.A1(\u_spi_shift.tx_sr_q[11] ),
    .A2(net76),
    .B1(_328_),
    .B2(_368_),
    .X(_372_));
 sky130_fd_sc_hd__a211o_1 _749_ (.A1(_323_),
    .A2(_371_),
    .B1(_372_),
    .C1(net68),
    .X(_373_));
 sky130_fd_sc_hd__o211a_1 _750_ (.A1(net114),
    .A2(net65),
    .B1(_373_),
    .C1(net92),
    .X(_098_));
 sky130_fd_sc_hd__mux2_1 _751_ (.A0(net36),
    .A1(net29),
    .S(net90),
    .X(_374_));
 sky130_fd_sc_hd__a22o_1 _752_ (.A1(_328_),
    .A2(_371_),
    .B1(_374_),
    .B2(_323_),
    .X(_375_));
 sky130_fd_sc_hd__a211o_1 _753_ (.A1(\u_spi_shift.tx_sr_q[12] ),
    .A2(net76),
    .B1(net68),
    .C1(_375_),
    .X(_376_));
 sky130_fd_sc_hd__o211a_1 _754_ (.A1(net118),
    .A2(net66),
    .B1(_376_),
    .C1(net92),
    .X(_099_));
 sky130_fd_sc_hd__mux2_1 _755_ (.A0(net37),
    .A1(net30),
    .S(net90),
    .X(_377_));
 sky130_fd_sc_hd__a22o_1 _756_ (.A1(_328_),
    .A2(_374_),
    .B1(_377_),
    .B2(_323_),
    .X(_378_));
 sky130_fd_sc_hd__a211o_1 _757_ (.A1(\u_spi_shift.tx_sr_q[13] ),
    .A2(net78),
    .B1(net67),
    .C1(_378_),
    .X(_379_));
 sky130_fd_sc_hd__o211a_1 _758_ (.A1(net120),
    .A2(net65),
    .B1(_379_),
    .C1(net93),
    .X(_100_));
 sky130_fd_sc_hd__a22o_1 _759_ (.A1(_321_),
    .A2(_323_),
    .B1(_328_),
    .B2(_377_),
    .X(_380_));
 sky130_fd_sc_hd__a211o_1 _760_ (.A1(net177),
    .A2(net76),
    .B1(net68),
    .C1(_380_),
    .X(_381_));
 sky130_fd_sc_hd__o211a_1 _761_ (.A1(net112),
    .A2(net66),
    .B1(_381_),
    .C1(net93),
    .X(_101_));
 sky130_fd_sc_hd__a22o_1 _762_ (.A1(net41),
    .A2(_181_),
    .B1(_194_),
    .B2(net167),
    .X(_102_));
 sky130_fd_sc_hd__o211a_1 _763_ (.A1(net139),
    .A2(net83),
    .B1(_329_),
    .C1(net93),
    .X(_103_));
 sky130_fd_sc_hd__dfxtp_1 _764_ (.CLK(clknet_3_2__leaf_clk),
    .D(_003_),
    .Q(\u_sync2.meta_q ));
 sky130_fd_sc_hd__dfxtp_1 _765_ (.CLK(clknet_3_6__leaf_clk),
    .D(_004_),
    .Q(\u_spi_shift.smp_d2_q ));
 sky130_fd_sc_hd__dfxtp_1 _766_ (.CLK(clknet_3_6__leaf_clk),
    .D(_000_),
    .Q(\u_spi_ctrl.state_q[0] ));
 sky130_fd_sc_hd__dfxtp_1 _767_ (.CLK(clknet_3_7__leaf_clk),
    .D(_001_),
    .Q(\u_spi_ctrl.state_q[1] ));
 sky130_fd_sc_hd__dfxtp_1 _768_ (.CLK(clknet_3_5__leaf_clk),
    .D(_005_),
    .Q(net45));
 sky130_fd_sc_hd__dfxtp_1 _769_ (.CLK(clknet_3_5__leaf_clk),
    .D(_006_),
    .Q(net44));
 sky130_fd_sc_hd__dfxtp_2 _770_ (.CLK(clknet_3_4__leaf_clk),
    .D(_007_),
    .Q(net42));
 sky130_fd_sc_hd__dfxtp_1 _771_ (.CLK(clknet_3_1__leaf_clk),
    .D(_008_),
    .Q(net43));
 sky130_fd_sc_hd__dfxtp_1 _772_ (.CLK(clknet_3_3__leaf_clk),
    .D(_009_),
    .Q(\u_spi_clkgen.running_q ));
 sky130_fd_sc_hd__dfxtp_1 _773_ (.CLK(clknet_3_6__leaf_clk),
    .D(_002_),
    .Q(\u_spi_ctrl.state_q[2] ));
 sky130_fd_sc_hd__dfxtp_1 _774_ (.CLK(clknet_3_5__leaf_clk),
    .D(_010_),
    .Q(net64));
 sky130_fd_sc_hd__dfxtp_1 _775_ (.CLK(clknet_3_3__leaf_clk),
    .D(_011_),
    .Q(net63));
 sky130_fd_sc_hd__dfxtp_1 _776_ (.CLK(clknet_3_3__leaf_clk),
    .D(_012_),
    .Q(\edge_cnt_unused[0] ));
 sky130_fd_sc_hd__dfxtp_1 _777_ (.CLK(clknet_3_6__leaf_clk),
    .D(_013_),
    .Q(\edge_cnt_unused[1] ));
 sky130_fd_sc_hd__dfxtp_1 _778_ (.CLK(clknet_3_3__leaf_clk),
    .D(_014_),
    .Q(\edge_cnt_unused[2] ));
 sky130_fd_sc_hd__dfxtp_1 _779_ (.CLK(clknet_3_3__leaf_clk),
    .D(_015_),
    .Q(\edge_cnt_unused[3] ));
 sky130_fd_sc_hd__dfxtp_1 _780_ (.CLK(clknet_3_6__leaf_clk),
    .D(_016_),
    .Q(\edge_cnt_unused[4] ));
 sky130_fd_sc_hd__dfxtp_1 _781_ (.CLK(clknet_3_6__leaf_clk),
    .D(_017_),
    .Q(\edge_cnt_unused[5] ));
 sky130_fd_sc_hd__dfxtp_1 _782_ (.CLK(clknet_3_1__leaf_clk),
    .D(_018_),
    .Q(\u_spi_clkgen.hp_cnt_q[0] ));
 sky130_fd_sc_hd__dfxtp_1 _783_ (.CLK(clknet_3_0__leaf_clk),
    .D(_019_),
    .Q(\u_spi_clkgen.hp_cnt_q[1] ));
 sky130_fd_sc_hd__dfxtp_1 _784_ (.CLK(clknet_3_0__leaf_clk),
    .D(_020_),
    .Q(\u_spi_clkgen.hp_cnt_q[2] ));
 sky130_fd_sc_hd__dfxtp_1 _785_ (.CLK(clknet_3_0__leaf_clk),
    .D(_021_),
    .Q(\u_spi_clkgen.hp_cnt_q[3] ));
 sky130_fd_sc_hd__dfxtp_1 _786_ (.CLK(clknet_3_0__leaf_clk),
    .D(_022_),
    .Q(\u_spi_clkgen.hp_cnt_q[4] ));
 sky130_fd_sc_hd__dfxtp_1 _787_ (.CLK(clknet_3_1__leaf_clk),
    .D(_023_),
    .Q(\u_spi_clkgen.hp_cnt_q[5] ));
 sky130_fd_sc_hd__dfxtp_1 _788_ (.CLK(clknet_3_1__leaf_clk),
    .D(_024_),
    .Q(\u_spi_clkgen.hp_cnt_q[6] ));
 sky130_fd_sc_hd__dfxtp_1 _789_ (.CLK(clknet_3_1__leaf_clk),
    .D(_025_),
    .Q(\u_spi_clkgen.hp_cnt_q[7] ));
 sky130_fd_sc_hd__dfxtp_1 _790_ (.CLK(clknet_3_1__leaf_clk),
    .D(_026_),
    .Q(\u_spi_clkgen.hp_cnt_q[8] ));
 sky130_fd_sc_hd__dfxtp_1 _791_ (.CLK(clknet_3_1__leaf_clk),
    .D(_027_),
    .Q(\u_spi_clkgen.hp_cnt_q[9] ));
 sky130_fd_sc_hd__dfxtp_1 _792_ (.CLK(clknet_3_5__leaf_clk),
    .D(_028_),
    .Q(\u_spi_clkgen.hp_cnt_q[10] ));
 sky130_fd_sc_hd__dfxtp_1 _793_ (.CLK(clknet_3_5__leaf_clk),
    .D(_029_),
    .Q(\u_spi_clkgen.hp_cnt_q[11] ));
 sky130_fd_sc_hd__dfxtp_1 _794_ (.CLK(clknet_3_4__leaf_clk),
    .D(_030_),
    .Q(\u_spi_clkgen.hp_cnt_q[12] ));
 sky130_fd_sc_hd__dfxtp_1 _795_ (.CLK(clknet_3_4__leaf_clk),
    .D(_031_),
    .Q(\u_spi_clkgen.hp_cnt_q[13] ));
 sky130_fd_sc_hd__dfxtp_1 _796_ (.CLK(clknet_3_4__leaf_clk),
    .D(_032_),
    .Q(\u_spi_clkgen.hp_cnt_q[14] ));
 sky130_fd_sc_hd__dfxtp_1 _797_ (.CLK(clknet_3_4__leaf_clk),
    .D(_033_),
    .Q(\u_spi_clkgen.hp_cnt_q[15] ));
 sky130_fd_sc_hd__dfxtp_1 _798_ (.CLK(clknet_3_0__leaf_clk),
    .D(_034_),
    .Q(\u_spi_clkgen.nm1_q[0] ));
 sky130_fd_sc_hd__dfxtp_1 _799_ (.CLK(clknet_3_0__leaf_clk),
    .D(_035_),
    .Q(\u_spi_clkgen.nm1_q[1] ));
 sky130_fd_sc_hd__dfxtp_1 _800_ (.CLK(clknet_3_0__leaf_clk),
    .D(_036_),
    .Q(\u_spi_clkgen.nm1_q[2] ));
 sky130_fd_sc_hd__dfxtp_1 _801_ (.CLK(clknet_3_1__leaf_clk),
    .D(_037_),
    .Q(\u_spi_clkgen.nm1_q[3] ));
 sky130_fd_sc_hd__dfxtp_1 _802_ (.CLK(clknet_3_1__leaf_clk),
    .D(_038_),
    .Q(\u_spi_clkgen.nm1_q[4] ));
 sky130_fd_sc_hd__dfxtp_1 _803_ (.CLK(clknet_3_1__leaf_clk),
    .D(_039_),
    .Q(\u_spi_clkgen.nm1_q[5] ));
 sky130_fd_sc_hd__dfxtp_1 _804_ (.CLK(clknet_3_1__leaf_clk),
    .D(_040_),
    .Q(\u_spi_clkgen.nm1_q[6] ));
 sky130_fd_sc_hd__dfxtp_1 _805_ (.CLK(clknet_3_1__leaf_clk),
    .D(_041_),
    .Q(\u_spi_clkgen.nm1_q[7] ));
 sky130_fd_sc_hd__dfxtp_1 _806_ (.CLK(clknet_3_4__leaf_clk),
    .D(_042_),
    .Q(\u_spi_clkgen.nm1_q[8] ));
 sky130_fd_sc_hd__dfxtp_1 _807_ (.CLK(clknet_3_4__leaf_clk),
    .D(_043_),
    .Q(\u_spi_clkgen.nm1_q[9] ));
 sky130_fd_sc_hd__dfxtp_1 _808_ (.CLK(clknet_3_4__leaf_clk),
    .D(_044_),
    .Q(\u_spi_clkgen.nm1_q[10] ));
 sky130_fd_sc_hd__dfxtp_1 _809_ (.CLK(clknet_3_4__leaf_clk),
    .D(_045_),
    .Q(\u_spi_clkgen.nm1_q[11] ));
 sky130_fd_sc_hd__dfxtp_1 _810_ (.CLK(clknet_3_4__leaf_clk),
    .D(_046_),
    .Q(\u_spi_clkgen.nm1_q[12] ));
 sky130_fd_sc_hd__dfxtp_1 _811_ (.CLK(clknet_3_4__leaf_clk),
    .D(_047_),
    .Q(\u_spi_clkgen.nm1_q[13] ));
 sky130_fd_sc_hd__dfxtp_1 _812_ (.CLK(clknet_3_4__leaf_clk),
    .D(_048_),
    .Q(\u_spi_clkgen.nm1_q[14] ));
 sky130_fd_sc_hd__dfxtp_1 _813_ (.CLK(clknet_3_4__leaf_clk),
    .D(_049_),
    .Q(\u_spi_clkgen.nm1_q[15] ));
 sky130_fd_sc_hd__dfxtp_1 _814_ (.CLK(clknet_3_6__leaf_clk),
    .D(_050_),
    .Q(miso_s));
 sky130_fd_sc_hd__dfxtp_1 _815_ (.CLK(clknet_3_6__leaf_clk),
    .D(_051_),
    .Q(\u_spi_shift.smp_d1_q ));
 sky130_fd_sc_hd__dfxtp_1 _816_ (.CLK(clknet_3_0__leaf_clk),
    .D(_052_),
    .Q(\u_spi_ctrl.cs_mode_q ));
 sky130_fd_sc_hd__dfxtp_1 _817_ (.CLK(clknet_3_5__leaf_clk),
    .D(net162),
    .Q(net47));
 sky130_fd_sc_hd__dfxtp_1 _818_ (.CLK(clknet_3_5__leaf_clk),
    .D(net137),
    .Q(net54));
 sky130_fd_sc_hd__dfxtp_1 _819_ (.CLK(clknet_3_5__leaf_clk),
    .D(net141),
    .Q(net55));
 sky130_fd_sc_hd__dfxtp_1 _820_ (.CLK(clknet_3_5__leaf_clk),
    .D(net133),
    .Q(net56));
 sky130_fd_sc_hd__dfxtp_1 _821_ (.CLK(clknet_3_5__leaf_clk),
    .D(net130),
    .Q(net57));
 sky130_fd_sc_hd__dfxtp_1 _822_ (.CLK(clknet_3_5__leaf_clk),
    .D(net128),
    .Q(net58));
 sky130_fd_sc_hd__dfxtp_1 _823_ (.CLK(clknet_3_5__leaf_clk),
    .D(net135),
    .Q(net59));
 sky130_fd_sc_hd__dfxtp_1 _824_ (.CLK(clknet_3_7__leaf_clk),
    .D(net126),
    .Q(net60));
 sky130_fd_sc_hd__dfxtp_1 _825_ (.CLK(clknet_3_7__leaf_clk),
    .D(_061_),
    .Q(net61));
 sky130_fd_sc_hd__dfxtp_1 _826_ (.CLK(clknet_3_7__leaf_clk),
    .D(_062_),
    .Q(net62));
 sky130_fd_sc_hd__dfxtp_1 _827_ (.CLK(clknet_3_7__leaf_clk),
    .D(_063_),
    .Q(net48));
 sky130_fd_sc_hd__dfxtp_1 _828_ (.CLK(clknet_3_7__leaf_clk),
    .D(_064_),
    .Q(net49));
 sky130_fd_sc_hd__dfxtp_1 _829_ (.CLK(clknet_3_7__leaf_clk),
    .D(_065_),
    .Q(net50));
 sky130_fd_sc_hd__dfxtp_1 _830_ (.CLK(clknet_3_7__leaf_clk),
    .D(_066_),
    .Q(net51));
 sky130_fd_sc_hd__dfxtp_1 _831_ (.CLK(clknet_3_7__leaf_clk),
    .D(_067_),
    .Q(net52));
 sky130_fd_sc_hd__dfxtp_1 _832_ (.CLK(clknet_3_7__leaf_clk),
    .D(_068_),
    .Q(net53));
 sky130_fd_sc_hd__dfxtp_1 _833_ (.CLK(clknet_3_6__leaf_clk),
    .D(_069_),
    .Q(\u_spi_shift.rx_sr_q[0] ));
 sky130_fd_sc_hd__dfxtp_1 _834_ (.CLK(clknet_3_5__leaf_clk),
    .D(_070_),
    .Q(\u_spi_shift.rx_sr_q[1] ));
 sky130_fd_sc_hd__dfxtp_1 _835_ (.CLK(clknet_3_5__leaf_clk),
    .D(_071_),
    .Q(\u_spi_shift.rx_sr_q[2] ));
 sky130_fd_sc_hd__dfxtp_1 _836_ (.CLK(clknet_3_5__leaf_clk),
    .D(_072_),
    .Q(\u_spi_shift.rx_sr_q[3] ));
 sky130_fd_sc_hd__dfxtp_1 _837_ (.CLK(clknet_3_5__leaf_clk),
    .D(_073_),
    .Q(\u_spi_shift.rx_sr_q[4] ));
 sky130_fd_sc_hd__dfxtp_1 _838_ (.CLK(clknet_3_5__leaf_clk),
    .D(_074_),
    .Q(\u_spi_shift.rx_sr_q[5] ));
 sky130_fd_sc_hd__dfxtp_1 _839_ (.CLK(clknet_3_7__leaf_clk),
    .D(_075_),
    .Q(\u_spi_shift.rx_sr_q[6] ));
 sky130_fd_sc_hd__dfxtp_1 _840_ (.CLK(clknet_3_7__leaf_clk),
    .D(_076_),
    .Q(\u_spi_shift.rx_sr_q[7] ));
 sky130_fd_sc_hd__dfxtp_1 _841_ (.CLK(clknet_3_7__leaf_clk),
    .D(_077_),
    .Q(\u_spi_shift.rx_sr_q[8] ));
 sky130_fd_sc_hd__dfxtp_1 _842_ (.CLK(clknet_3_6__leaf_clk),
    .D(_078_),
    .Q(\u_spi_shift.rx_sr_q[9] ));
 sky130_fd_sc_hd__dfxtp_1 _843_ (.CLK(clknet_3_7__leaf_clk),
    .D(_079_),
    .Q(\u_spi_shift.rx_sr_q[10] ));
 sky130_fd_sc_hd__dfxtp_1 _844_ (.CLK(clknet_3_7__leaf_clk),
    .D(_080_),
    .Q(\u_spi_shift.rx_sr_q[11] ));
 sky130_fd_sc_hd__dfxtp_1 _845_ (.CLK(clknet_3_6__leaf_clk),
    .D(_081_),
    .Q(\u_spi_shift.rx_sr_q[12] ));
 sky130_fd_sc_hd__dfxtp_1 _846_ (.CLK(clknet_3_6__leaf_clk),
    .D(_082_),
    .Q(\u_spi_shift.rx_sr_q[13] ));
 sky130_fd_sc_hd__dfxtp_1 _847_ (.CLK(clknet_3_7__leaf_clk),
    .D(_083_),
    .Q(\u_spi_shift.rx_sr_q[14] ));
 sky130_fd_sc_hd__dfxtp_1 _848_ (.CLK(clknet_3_7__leaf_clk),
    .D(_084_),
    .Q(\u_spi_shift.rx_sr_q[15] ));
 sky130_fd_sc_hd__dfxtp_1 _849_ (.CLK(clknet_3_3__leaf_clk),
    .D(_085_),
    .Q(net46));
 sky130_fd_sc_hd__dfxtp_1 _850_ (.CLK(clknet_3_2__leaf_clk),
    .D(_086_),
    .Q(\u_spi_shift.tx_sr_q[0] ));
 sky130_fd_sc_hd__dfxtp_1 _851_ (.CLK(clknet_3_2__leaf_clk),
    .D(_087_),
    .Q(\u_spi_shift.tx_sr_q[1] ));
 sky130_fd_sc_hd__dfxtp_1 _852_ (.CLK(clknet_3_0__leaf_clk),
    .D(_088_),
    .Q(\u_spi_shift.tx_sr_q[2] ));
 sky130_fd_sc_hd__dfxtp_1 _853_ (.CLK(clknet_3_0__leaf_clk),
    .D(_089_),
    .Q(\u_spi_shift.tx_sr_q[3] ));
 sky130_fd_sc_hd__dfxtp_1 _854_ (.CLK(clknet_3_0__leaf_clk),
    .D(_090_),
    .Q(\u_spi_shift.tx_sr_q[4] ));
 sky130_fd_sc_hd__dfxtp_1 _855_ (.CLK(clknet_3_3__leaf_clk),
    .D(_091_),
    .Q(\u_spi_shift.tx_sr_q[5] ));
 sky130_fd_sc_hd__dfxtp_1 _856_ (.CLK(clknet_3_3__leaf_clk),
    .D(_092_),
    .Q(\u_spi_shift.tx_sr_q[6] ));
 sky130_fd_sc_hd__dfxtp_1 _857_ (.CLK(clknet_3_3__leaf_clk),
    .D(_093_),
    .Q(\u_spi_shift.tx_sr_q[7] ));
 sky130_fd_sc_hd__dfxtp_1 _858_ (.CLK(clknet_3_2__leaf_clk),
    .D(_094_),
    .Q(\u_spi_shift.tx_sr_q[8] ));
 sky130_fd_sc_hd__dfxtp_1 _859_ (.CLK(clknet_3_2__leaf_clk),
    .D(net124),
    .Q(\u_spi_shift.tx_sr_q[9] ));
 sky130_fd_sc_hd__dfxtp_1 _860_ (.CLK(clknet_3_2__leaf_clk),
    .D(_096_),
    .Q(\u_spi_shift.tx_sr_q[10] ));
 sky130_fd_sc_hd__dfxtp_1 _861_ (.CLK(clknet_3_2__leaf_clk),
    .D(_097_),
    .Q(\u_spi_shift.tx_sr_q[11] ));
 sky130_fd_sc_hd__dfxtp_1 _862_ (.CLK(clknet_3_2__leaf_clk),
    .D(_098_),
    .Q(\u_spi_shift.tx_sr_q[12] ));
 sky130_fd_sc_hd__dfxtp_1 _863_ (.CLK(clknet_3_2__leaf_clk),
    .D(net119),
    .Q(\u_spi_shift.tx_sr_q[13] ));
 sky130_fd_sc_hd__dfxtp_1 _864_ (.CLK(clknet_3_2__leaf_clk),
    .D(net121),
    .Q(\u_spi_shift.tx_sr_q[14] ));
 sky130_fd_sc_hd__dfxtp_1 _865_ (.CLK(clknet_3_2__leaf_clk),
    .D(_101_),
    .Q(\u_spi_shift.tx_sr_q[15] ));
 sky130_fd_sc_hd__dfxtp_2 _866_ (.CLK(clknet_3_6__leaf_clk),
    .D(_102_),
    .Q(\u_spi_clkgen.wl_q ));
 sky130_fd_sc_hd__dfxtp_1 _867_ (.CLK(clknet_3_3__leaf_clk),
    .D(_103_),
    .Q(\u_spi_shift.cpha_q ));
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
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_25_Right_25 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_26_Right_26 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_27_Right_27 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_28_Right_28 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_29_Right_29 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_30_Right_30 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_31_Right_31 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_32_Right_32 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_33_Right_33 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_34_Right_34 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_35_Right_35 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_36_Right_36 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_37_Right_37 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_38_Right_38 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_39_Right_39 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_0_Left_40 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_1_Left_41 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_2_Left_42 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_3_Left_43 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_4_Left_44 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_5_Left_45 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_6_Left_46 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_7_Left_47 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_8_Left_48 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_9_Left_49 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_10_Left_50 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_11_Left_51 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_12_Left_52 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_13_Left_53 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_14_Left_54 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_15_Left_55 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_16_Left_56 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_17_Left_57 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_18_Left_58 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_19_Left_59 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_20_Left_60 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_21_Left_61 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_22_Left_62 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_23_Left_63 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_24_Left_64 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_25_Left_65 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_26_Left_66 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_27_Left_67 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_28_Left_68 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_29_Left_69 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_30_Left_70 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_31_Left_71 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_32_Left_72 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_33_Left_73 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_34_Left_74 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_35_Left_75 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_36_Left_76 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_37_Left_77 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_38_Left_78 ();
 sky130_fd_sc_hd__decap_3 PHY_EDGE_ROW_39_Left_79 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_80 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_81 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_82 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_83 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_84 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_85 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_86 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_0_87 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_88 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_89 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_90 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_1_91 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_92 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_93 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_94 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_2_95 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_96 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_97 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_98 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_3_99 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_100 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_101 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_102 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_4_103 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_104 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_105 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_106 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_5_107 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_108 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_109 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_110 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_6_111 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_112 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_113 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_114 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_7_115 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_116 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_117 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_118 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_8_119 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_120 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_121 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_122 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_9_123 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_124 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_125 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_126 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_10_127 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_128 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_129 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_130 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_11_131 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_132 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_133 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_134 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_12_135 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_136 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_137 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_138 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_13_139 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_140 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_141 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_142 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_14_143 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_15_144 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_15_145 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_15_146 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_15_147 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_148 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_149 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_150 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_16_151 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_17_152 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_17_153 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_17_154 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_17_155 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_156 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_157 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_158 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_18_159 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_19_160 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_19_161 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_19_162 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_19_163 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_164 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_165 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_166 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_20_167 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_21_168 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_21_169 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_21_170 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_21_171 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_172 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_173 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_174 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_22_175 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_23_176 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_23_177 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_23_178 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_23_179 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_180 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_181 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_182 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_24_183 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_25_184 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_25_185 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_25_186 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_25_187 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_26_188 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_26_189 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_26_190 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_26_191 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_27_192 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_27_193 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_27_194 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_27_195 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_28_196 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_28_197 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_28_198 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_28_199 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_29_200 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_29_201 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_29_202 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_29_203 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_30_204 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_30_205 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_30_206 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_30_207 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_31_208 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_31_209 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_31_210 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_31_211 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_32_212 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_32_213 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_32_214 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_32_215 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_33_216 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_33_217 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_33_218 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_33_219 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_34_220 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_34_221 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_34_222 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_34_223 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_35_224 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_35_225 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_35_226 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_35_227 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_36_228 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_36_229 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_36_230 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_36_231 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_37_232 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_37_233 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_37_234 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_37_235 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_38_236 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_38_237 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_38_238 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_38_239 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_240 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_241 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_242 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_243 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_244 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_245 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_246 ();
 sky130_fd_sc_hd__tapvpwrvgnd_1 TAP_TAPCELL_ROW_39_247 ();
 sky130_fd_sc_hd__buf_1 input1 (.A(clk_div[0]),
    .X(net1));
 sky130_fd_sc_hd__buf_1 input2 (.A(clk_div[10]),
    .X(net2));
 sky130_fd_sc_hd__clkbuf_1 input3 (.A(clk_div[11]),
    .X(net3));
 sky130_fd_sc_hd__buf_1 input4 (.A(clk_div[12]),
    .X(net4));
 sky130_fd_sc_hd__buf_1 input5 (.A(clk_div[13]),
    .X(net5));
 sky130_fd_sc_hd__buf_1 input6 (.A(clk_div[14]),
    .X(net6));
 sky130_fd_sc_hd__buf_1 input7 (.A(clk_div[15]),
    .X(net7));
 sky130_fd_sc_hd__buf_1 input8 (.A(clk_div[1]),
    .X(net8));
 sky130_fd_sc_hd__buf_1 input9 (.A(clk_div[2]),
    .X(net9));
 sky130_fd_sc_hd__buf_1 input10 (.A(clk_div[3]),
    .X(net10));
 sky130_fd_sc_hd__clkbuf_1 input11 (.A(clk_div[4]),
    .X(net11));
 sky130_fd_sc_hd__clkbuf_1 input12 (.A(clk_div[5]),
    .X(net12));
 sky130_fd_sc_hd__buf_1 input13 (.A(clk_div[6]),
    .X(net13));
 sky130_fd_sc_hd__clkbuf_1 input14 (.A(clk_div[7]),
    .X(net14));
 sky130_fd_sc_hd__clkbuf_1 input15 (.A(clk_div[8]),
    .X(net15));
 sky130_fd_sc_hd__clkbuf_1 input16 (.A(clk_div[9]),
    .X(net16));
 sky130_fd_sc_hd__clkbuf_2 input17 (.A(cpha),
    .X(net17));
 sky130_fd_sc_hd__buf_1 input18 (.A(cpol),
    .X(net18));
 sky130_fd_sc_hd__clkbuf_1 input19 (.A(cs_force),
    .X(net19));
 sky130_fd_sc_hd__clkbuf_1 input20 (.A(cs_mode),
    .X(net20));
 sky130_fd_sc_hd__clkbuf_1 input21 (.A(irq_clear),
    .X(net21));
 sky130_fd_sc_hd__clkbuf_1 input22 (.A(miso),
    .X(net22));
 sky130_fd_sc_hd__clkbuf_2 input23 (.A(rst_n),
    .X(net23));
 sky130_fd_sc_hd__buf_1 input24 (.A(start),
    .X(net24));
 sky130_fd_sc_hd__buf_1 input25 (.A(tx_data[0]),
    .X(net25));
 sky130_fd_sc_hd__clkbuf_1 input26 (.A(tx_data[10]),
    .X(net26));
 sky130_fd_sc_hd__clkbuf_1 input27 (.A(tx_data[11]),
    .X(net27));
 sky130_fd_sc_hd__clkbuf_1 input28 (.A(tx_data[12]),
    .X(net28));
 sky130_fd_sc_hd__clkbuf_1 input29 (.A(tx_data[13]),
    .X(net29));
 sky130_fd_sc_hd__clkbuf_1 input30 (.A(tx_data[14]),
    .X(net30));
 sky130_fd_sc_hd__clkbuf_1 input31 (.A(tx_data[15]),
    .X(net31));
 sky130_fd_sc_hd__buf_1 input32 (.A(tx_data[1]),
    .X(net32));
 sky130_fd_sc_hd__buf_1 input33 (.A(tx_data[2]),
    .X(net33));
 sky130_fd_sc_hd__buf_1 input34 (.A(tx_data[3]),
    .X(net34));
 sky130_fd_sc_hd__buf_1 input35 (.A(tx_data[4]),
    .X(net35));
 sky130_fd_sc_hd__buf_1 input36 (.A(tx_data[5]),
    .X(net36));
 sky130_fd_sc_hd__buf_1 input37 (.A(tx_data[6]),
    .X(net37));
 sky130_fd_sc_hd__buf_1 input38 (.A(tx_data[7]),
    .X(net38));
 sky130_fd_sc_hd__clkbuf_1 input39 (.A(tx_data[8]),
    .X(net39));
 sky130_fd_sc_hd__clkbuf_1 input40 (.A(tx_data[9]),
    .X(net40));
 sky130_fd_sc_hd__buf_1 input41 (.A(word_len),
    .X(net41));
 sky130_fd_sc_hd__buf_2 output42 (.A(net42),
    .X(busy));
 sky130_fd_sc_hd__buf_2 output43 (.A(net43),
    .X(cs_n));
 sky130_fd_sc_hd__buf_2 output44 (.A(net44),
    .X(done));
 sky130_fd_sc_hd__buf_2 output45 (.A(net45),
    .X(irq));
 sky130_fd_sc_hd__buf_2 output46 (.A(net46),
    .X(mosi));
 sky130_fd_sc_hd__buf_2 output47 (.A(net47),
    .X(rx_data[0]));
 sky130_fd_sc_hd__buf_2 output48 (.A(net48),
    .X(rx_data[10]));
 sky130_fd_sc_hd__buf_2 output49 (.A(net49),
    .X(rx_data[11]));
 sky130_fd_sc_hd__buf_2 output50 (.A(net50),
    .X(rx_data[12]));
 sky130_fd_sc_hd__buf_2 output51 (.A(net51),
    .X(rx_data[13]));
 sky130_fd_sc_hd__buf_2 output52 (.A(net52),
    .X(rx_data[14]));
 sky130_fd_sc_hd__buf_2 output53 (.A(net53),
    .X(rx_data[15]));
 sky130_fd_sc_hd__buf_2 output54 (.A(net54),
    .X(rx_data[1]));
 sky130_fd_sc_hd__buf_2 output55 (.A(net55),
    .X(rx_data[2]));
 sky130_fd_sc_hd__buf_2 output56 (.A(net56),
    .X(rx_data[3]));
 sky130_fd_sc_hd__buf_2 output57 (.A(net57),
    .X(rx_data[4]));
 sky130_fd_sc_hd__buf_2 output58 (.A(net58),
    .X(rx_data[5]));
 sky130_fd_sc_hd__buf_2 output59 (.A(net59),
    .X(rx_data[6]));
 sky130_fd_sc_hd__buf_2 output60 (.A(net60),
    .X(rx_data[7]));
 sky130_fd_sc_hd__buf_2 output61 (.A(net61),
    .X(rx_data[8]));
 sky130_fd_sc_hd__buf_2 output62 (.A(net62),
    .X(rx_data[9]));
 sky130_fd_sc_hd__buf_2 output63 (.A(net63),
    .X(sck));
 sky130_fd_sc_hd__buf_2 output64 (.A(net64),
    .X(start_err));
 sky130_fd_sc_hd__buf_2 fanout65 (.A(_326_),
    .X(net65));
 sky130_fd_sc_hd__dlymetal6s2s_1 fanout66 (.A(_326_),
    .X(net66));
 sky130_fd_sc_hd__buf_2 fanout67 (.A(_325_),
    .X(net67));
 sky130_fd_sc_hd__clkbuf_2 fanout68 (.A(_325_),
    .X(net68));
 sky130_fd_sc_hd__clkbuf_2 fanout69 (.A(_278_),
    .X(net69));
 sky130_fd_sc_hd__buf_1 fanout70 (.A(_278_),
    .X(net70));
 sky130_fd_sc_hd__buf_2 fanout71 (.A(_277_),
    .X(net71));
 sky130_fd_sc_hd__buf_1 fanout72 (.A(_277_),
    .X(net72));
 sky130_fd_sc_hd__clkbuf_2 fanout73 (.A(_204_),
    .X(net73));
 sky130_fd_sc_hd__buf_1 fanout74 (.A(_204_),
    .X(net74));
 sky130_fd_sc_hd__buf_2 fanout75 (.A(net79),
    .X(net75));
 sky130_fd_sc_hd__clkbuf_4 fanout76 (.A(net78),
    .X(net76));
 sky130_fd_sc_hd__clkbuf_2 fanout77 (.A(net78),
    .X(net77));
 sky130_fd_sc_hd__clkbuf_2 fanout78 (.A(net79),
    .X(net78));
 sky130_fd_sc_hd__clkbuf_2 fanout79 (.A(_158_),
    .X(net79));
 sky130_fd_sc_hd__buf_2 fanout80 (.A(net81),
    .X(net80));
 sky130_fd_sc_hd__buf_1 fanout81 (.A(net82),
    .X(net81));
 sky130_fd_sc_hd__buf_2 fanout82 (.A(_157_),
    .X(net82));
 sky130_fd_sc_hd__clkbuf_2 fanout83 (.A(net85),
    .X(net83));
 sky130_fd_sc_hd__clkbuf_2 fanout84 (.A(net85),
    .X(net84));
 sky130_fd_sc_hd__clkbuf_2 fanout85 (.A(_157_),
    .X(net85));
 sky130_fd_sc_hd__clkbuf_4 fanout86 (.A(\u_spi_shift.smp_d2_q ),
    .X(net86));
 sky130_fd_sc_hd__clkbuf_2 fanout87 (.A(\u_spi_shift.smp_d2_q ),
    .X(net87));
 sky130_fd_sc_hd__buf_2 fanout88 (.A(net89),
    .X(net88));
 sky130_fd_sc_hd__clkbuf_2 fanout89 (.A(net90),
    .X(net89));
 sky130_fd_sc_hd__buf_2 fanout90 (.A(net41),
    .X(net90));
 sky130_fd_sc_hd__buf_2 fanout91 (.A(net94),
    .X(net91));
 sky130_fd_sc_hd__buf_2 fanout92 (.A(net94),
    .X(net92));
 sky130_fd_sc_hd__clkbuf_2 fanout93 (.A(net94),
    .X(net93));
 sky130_fd_sc_hd__clkbuf_2 fanout94 (.A(net23),
    .X(net94));
 sky130_fd_sc_hd__buf_2 fanout95 (.A(net96),
    .X(net95));
 sky130_fd_sc_hd__buf_2 fanout96 (.A(net23),
    .X(net96));
 sky130_fd_sc_hd__clkbuf_2 fanout97 (.A(net99),
    .X(net97));
 sky130_fd_sc_hd__clkbuf_2 fanout98 (.A(net99),
    .X(net98));
 sky130_fd_sc_hd__clkbuf_2 fanout99 (.A(net23),
    .X(net99));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_0_clk (.A(clk),
    .X(clknet_0_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_0__f_clk (.A(clknet_0_clk),
    .X(clknet_3_0__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_1__f_clk (.A(clknet_0_clk),
    .X(clknet_3_1__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_2__f_clk (.A(clknet_0_clk),
    .X(clknet_3_2__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_3__f_clk (.A(clknet_0_clk),
    .X(clknet_3_3__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_4__f_clk (.A(clknet_0_clk),
    .X(clknet_3_4__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_5__f_clk (.A(clknet_0_clk),
    .X(clknet_3_5__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_6__f_clk (.A(clknet_0_clk),
    .X(clknet_3_6__leaf_clk));
 sky130_fd_sc_hd__clkbuf_16 clkbuf_3_7__f_clk (.A(clknet_0_clk),
    .X(clknet_3_7__leaf_clk));
 sky130_fd_sc_hd__clkinv_4 clkload0 (.A(clknet_3_0__leaf_clk));
 sky130_fd_sc_hd__clkinvlp_4 clkload1 (.A(clknet_3_1__leaf_clk));
 sky130_fd_sc_hd__clkinv_4 clkload2 (.A(clknet_3_2__leaf_clk));
 sky130_fd_sc_hd__inv_6 clkload3 (.A(clknet_3_3__leaf_clk));
 sky130_fd_sc_hd__bufinv_16 clkload4 (.A(clknet_3_4__leaf_clk));
 sky130_fd_sc_hd__bufinv_16 clkload5 (.A(clknet_3_6__leaf_clk));
 sky130_fd_sc_hd__dlygate4sd3_1 hold1 (.A(\u_spi_shift.smp_d1_q ),
    .X(net100));
 sky130_fd_sc_hd__dlygate4sd3_1 hold2 (.A(\u_spi_clkgen.nm1_q[15] ),
    .X(net101));
 sky130_fd_sc_hd__dlygate4sd3_1 hold3 (.A(net45),
    .X(net102));
 sky130_fd_sc_hd__dlygate4sd3_1 hold4 (.A(\u_sync2.meta_q ),
    .X(net103));
 sky130_fd_sc_hd__dlygate4sd3_1 hold5 (.A(\u_spi_shift.tx_sr_q[1] ),
    .X(net104));
 sky130_fd_sc_hd__dlygate4sd3_1 hold6 (.A(\u_spi_shift.tx_sr_q[5] ),
    .X(net105));
 sky130_fd_sc_hd__dlygate4sd3_1 hold7 (.A(\u_spi_clkgen.hp_cnt_q[15] ),
    .X(net106));
 sky130_fd_sc_hd__dlygate4sd3_1 hold8 (.A(\u_spi_shift.tx_sr_q[4] ),
    .X(net107));
 sky130_fd_sc_hd__dlygate4sd3_1 hold9 (.A(\u_spi_shift.tx_sr_q[6] ),
    .X(net108));
 sky130_fd_sc_hd__dlygate4sd3_1 hold10 (.A(\u_spi_shift.tx_sr_q[3] ),
    .X(net109));
 sky130_fd_sc_hd__dlygate4sd3_1 hold11 (.A(\u_spi_shift.tx_sr_q[2] ),
    .X(net110));
 sky130_fd_sc_hd__dlygate4sd3_1 hold12 (.A(\u_spi_ctrl.state_q[0] ),
    .X(net111));
 sky130_fd_sc_hd__dlygate4sd3_1 hold13 (.A(\u_spi_shift.tx_sr_q[15] ),
    .X(net112));
 sky130_fd_sc_hd__dlygate4sd3_1 hold14 (.A(\u_spi_shift.tx_sr_q[11] ),
    .X(net113));
 sky130_fd_sc_hd__dlygate4sd3_1 hold15 (.A(\u_spi_shift.tx_sr_q[12] ),
    .X(net114));
 sky130_fd_sc_hd__dlygate4sd3_1 hold16 (.A(\u_spi_shift.tx_sr_q[8] ),
    .X(net115));
 sky130_fd_sc_hd__dlygate4sd3_1 hold17 (.A(\u_spi_shift.tx_sr_q[10] ),
    .X(net116));
 sky130_fd_sc_hd__dlygate4sd3_1 hold18 (.A(\u_spi_shift.tx_sr_q[7] ),
    .X(net117));
 sky130_fd_sc_hd__dlygate4sd3_1 hold19 (.A(\u_spi_shift.tx_sr_q[13] ),
    .X(net118));
 sky130_fd_sc_hd__dlygate4sd3_1 hold20 (.A(_099_),
    .X(net119));
 sky130_fd_sc_hd__dlygate4sd3_1 hold21 (.A(\u_spi_shift.tx_sr_q[14] ),
    .X(net120));
 sky130_fd_sc_hd__dlygate4sd3_1 hold22 (.A(_100_),
    .X(net121));
 sky130_fd_sc_hd__dlygate4sd3_1 hold23 (.A(\edge_cnt_unused[2] ),
    .X(net122));
 sky130_fd_sc_hd__dlygate4sd3_1 hold24 (.A(\u_spi_shift.tx_sr_q[9] ),
    .X(net123));
 sky130_fd_sc_hd__dlygate4sd3_1 hold25 (.A(_095_),
    .X(net124));
 sky130_fd_sc_hd__dlygate4sd3_1 hold26 (.A(\u_spi_shift.rx_sr_q[7] ),
    .X(net125));
 sky130_fd_sc_hd__dlygate4sd3_1 hold27 (.A(_060_),
    .X(net126));
 sky130_fd_sc_hd__dlygate4sd3_1 hold28 (.A(\u_spi_shift.rx_sr_q[5] ),
    .X(net127));
 sky130_fd_sc_hd__dlygate4sd3_1 hold29 (.A(_058_),
    .X(net128));
 sky130_fd_sc_hd__dlygate4sd3_1 hold30 (.A(\u_spi_shift.rx_sr_q[4] ),
    .X(net129));
 sky130_fd_sc_hd__dlygate4sd3_1 hold31 (.A(_057_),
    .X(net130));
 sky130_fd_sc_hd__dlygate4sd3_1 hold32 (.A(\u_spi_clkgen.hp_cnt_q[13] ),
    .X(net131));
 sky130_fd_sc_hd__dlygate4sd3_1 hold33 (.A(\u_spi_shift.rx_sr_q[3] ),
    .X(net132));
 sky130_fd_sc_hd__dlygate4sd3_1 hold34 (.A(_056_),
    .X(net133));
 sky130_fd_sc_hd__dlygate4sd3_1 hold35 (.A(\u_spi_shift.rx_sr_q[6] ),
    .X(net134));
 sky130_fd_sc_hd__dlygate4sd3_1 hold36 (.A(_059_),
    .X(net135));
 sky130_fd_sc_hd__dlygate4sd3_1 hold37 (.A(\u_spi_shift.rx_sr_q[1] ),
    .X(net136));
 sky130_fd_sc_hd__dlygate4sd3_1 hold38 (.A(_054_),
    .X(net137));
 sky130_fd_sc_hd__dlygate4sd3_1 hold39 (.A(\u_spi_clkgen.nm1_q[10] ),
    .X(net138));
 sky130_fd_sc_hd__dlygate4sd3_1 hold40 (.A(\u_spi_shift.cpha_q ),
    .X(net139));
 sky130_fd_sc_hd__dlygate4sd3_1 hold41 (.A(\u_spi_shift.rx_sr_q[2] ),
    .X(net140));
 sky130_fd_sc_hd__dlygate4sd3_1 hold42 (.A(_055_),
    .X(net141));
 sky130_fd_sc_hd__dlygate4sd3_1 hold43 (.A(\u_spi_clkgen.nm1_q[13] ),
    .X(net142));
 sky130_fd_sc_hd__dlygate4sd3_1 hold44 (.A(\edge_cnt_unused[4] ),
    .X(net143));
 sky130_fd_sc_hd__dlygate4sd3_1 hold45 (.A(\u_spi_clkgen.nm1_q[7] ),
    .X(net144));
 sky130_fd_sc_hd__dlygate4sd3_1 hold46 (.A(\u_spi_clkgen.hp_cnt_q[2] ),
    .X(net145));
 sky130_fd_sc_hd__dlygate4sd3_1 hold47 (.A(\u_spi_clkgen.nm1_q[8] ),
    .X(net146));
 sky130_fd_sc_hd__dlygate4sd3_1 hold48 (.A(\u_spi_clkgen.hp_cnt_q[9] ),
    .X(net147));
 sky130_fd_sc_hd__dlygate4sd3_1 hold49 (.A(\u_spi_ctrl.state_q[1] ),
    .X(net148));
 sky130_fd_sc_hd__dlygate4sd3_1 hold50 (.A(\u_spi_clkgen.nm1_q[5] ),
    .X(net149));
 sky130_fd_sc_hd__dlygate4sd3_1 hold51 (.A(\u_spi_clkgen.nm1_q[9] ),
    .X(net150));
 sky130_fd_sc_hd__dlygate4sd3_1 hold52 (.A(\u_spi_clkgen.nm1_q[2] ),
    .X(net151));
 sky130_fd_sc_hd__dlygate4sd3_1 hold53 (.A(\u_spi_clkgen.nm1_q[3] ),
    .X(net152));
 sky130_fd_sc_hd__dlygate4sd3_1 hold54 (.A(\u_spi_clkgen.nm1_q[11] ),
    .X(net153));
 sky130_fd_sc_hd__dlygate4sd3_1 hold55 (.A(\u_spi_clkgen.nm1_q[6] ),
    .X(net154));
 sky130_fd_sc_hd__dlygate4sd3_1 hold56 (.A(\u_spi_clkgen.hp_cnt_q[4] ),
    .X(net155));
 sky130_fd_sc_hd__dlygate4sd3_1 hold57 (.A(\u_spi_clkgen.nm1_q[4] ),
    .X(net156));
 sky130_fd_sc_hd__dlygate4sd3_1 hold58 (.A(\u_spi_clkgen.nm1_q[0] ),
    .X(net157));
 sky130_fd_sc_hd__dlygate4sd3_1 hold59 (.A(\u_spi_clkgen.hp_cnt_q[10] ),
    .X(net158));
 sky130_fd_sc_hd__dlygate4sd3_1 hold60 (.A(\u_spi_clkgen.hp_cnt_q[6] ),
    .X(net159));
 sky130_fd_sc_hd__dlygate4sd3_1 hold61 (.A(\edge_cnt_unused[1] ),
    .X(net160));
 sky130_fd_sc_hd__dlygate4sd3_1 hold62 (.A(net47),
    .X(net161));
 sky130_fd_sc_hd__dlygate4sd3_1 hold63 (.A(_053_),
    .X(net162));
 sky130_fd_sc_hd__dlygate4sd3_1 hold64 (.A(\u_spi_clkgen.nm1_q[1] ),
    .X(net163));
 sky130_fd_sc_hd__dlygate4sd3_1 hold65 (.A(\u_spi_clkgen.hp_cnt_q[3] ),
    .X(net164));
 sky130_fd_sc_hd__dlygate4sd3_1 hold66 (.A(\u_spi_clkgen.hp_cnt_q[8] ),
    .X(net165));
 sky130_fd_sc_hd__dlygate4sd3_1 hold67 (.A(\u_spi_shift.tx_sr_q[0] ),
    .X(net166));
 sky130_fd_sc_hd__dlygate4sd3_1 hold68 (.A(\u_spi_clkgen.wl_q ),
    .X(net167));
 sky130_fd_sc_hd__dlygate4sd3_1 hold69 (.A(net49),
    .X(net168));
 sky130_fd_sc_hd__dlygate4sd3_1 hold70 (.A(net61),
    .X(net169));
 sky130_fd_sc_hd__dlygate4sd3_1 hold71 (.A(\u_spi_clkgen.hp_cnt_q[0] ),
    .X(net170));
 sky130_fd_sc_hd__dlygate4sd3_1 hold72 (.A(\u_spi_clkgen.nm1_q[12] ),
    .X(net171));
 sky130_fd_sc_hd__dlygate4sd3_1 hold73 (.A(\u_spi_clkgen.hp_cnt_q[7] ),
    .X(net172));
 sky130_fd_sc_hd__dlygate4sd3_1 hold74 (.A(net53),
    .X(net173));
 sky130_fd_sc_hd__dlygate4sd3_1 hold75 (.A(net52),
    .X(net174));
 sky130_fd_sc_hd__dlygate4sd3_1 hold76 (.A(net48),
    .X(net175));
 sky130_fd_sc_hd__dlygate4sd3_1 hold77 (.A(\u_spi_ctrl.state_q[0] ),
    .X(net176));
 sky130_fd_sc_hd__dlygate4sd3_1 hold78 (.A(\u_spi_shift.tx_sr_q[14] ),
    .X(net177));
 sky130_fd_sc_hd__dlygate4sd3_1 hold79 (.A(\u_spi_shift.tx_sr_q[9] ),
    .X(net178));
 sky130_fd_sc_hd__decap_8 FILLER_0_6 ();
 sky130_fd_sc_hd__decap_3 FILLER_0_14 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_20 ();
 sky130_fd_sc_hd__decap_4 FILLER_0_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_36 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_48 ();
 sky130_fd_sc_hd__decap_4 FILLER_0_52 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_57 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_68 ();
 sky130_fd_sc_hd__fill_2 FILLER_0_76 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_83 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_88 ();
 sky130_fd_sc_hd__decap_4 FILLER_0_93 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_100 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_116 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_128 ();
 sky130_fd_sc_hd__decap_8 FILLER_0_132 ();
 sky130_fd_sc_hd__decap_4 FILLER_0_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_148 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_160 ();
 sky130_fd_sc_hd__fill_2 FILLER_0_175 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_180 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_192 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_197 ();
 sky130_ef_sc_hd__decap_12 FILLER_0_212 ();
 sky130_fd_sc_hd__decap_6 FILLER_0_228 ();
 sky130_fd_sc_hd__fill_1 FILLER_0_234 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_3 ();
 sky130_fd_sc_hd__decap_8 FILLER_1_15 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_39 ();
 sky130_fd_sc_hd__decap_6 FILLER_1_45 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_55 ();
 sky130_fd_sc_hd__decap_4 FILLER_1_57 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_70 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_78 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_84 ();
 sky130_fd_sc_hd__decap_3 FILLER_1_98 ();
 sky130_fd_sc_hd__fill_2 FILLER_1_110 ();
 sky130_fd_sc_hd__decap_4 FILLER_1_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_1_132 ();
 sky130_fd_sc_hd__decap_6 FILLER_1_141 ();
 sky130_fd_sc_hd__decap_3 FILLER_1_159 ();
 sky130_fd_sc_hd__decap_4 FILLER_1_169 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_173 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_182 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_194 ();
 sky130_ef_sc_hd__decap_12 FILLER_1_206 ();
 sky130_fd_sc_hd__decap_6 FILLER_1_218 ();
 sky130_fd_sc_hd__decap_8 FILLER_1_225 ();
 sky130_fd_sc_hd__fill_1 FILLER_1_233 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_3 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_85 ();
 sky130_fd_sc_hd__fill_1 FILLER_2_115 ();
 sky130_fd_sc_hd__fill_1 FILLER_2_139 ();
 sky130_fd_sc_hd__fill_2 FILLER_2_157 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_184 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_197 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_209 ();
 sky130_ef_sc_hd__decap_12 FILLER_2_221 ();
 sky130_fd_sc_hd__decap_4 FILLER_2_233 ();
 sky130_fd_sc_hd__fill_1 FILLER_2_237 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_3 ();
 sky130_fd_sc_hd__decap_3 FILLER_3_15 ();
 sky130_fd_sc_hd__fill_2 FILLER_3_45 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_71 ();
 sky130_fd_sc_hd__decap_3 FILLER_3_84 ();
 sky130_fd_sc_hd__decap_4 FILLER_3_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_133 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_145 ();
 sky130_fd_sc_hd__decap_6 FILLER_3_158 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_188 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_200 ();
 sky130_ef_sc_hd__decap_12 FILLER_3_212 ();
 sky130_fd_sc_hd__decap_8 FILLER_3_225 ();
 sky130_fd_sc_hd__fill_1 FILLER_3_233 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_7 ();
 sky130_fd_sc_hd__decap_8 FILLER_4_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_27 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_33 ();
 sky130_fd_sc_hd__fill_2 FILLER_4_45 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_63 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_67 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_85 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_89 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_98 ();
 sky130_fd_sc_hd__fill_2 FILLER_4_118 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_132 ();
 sky130_fd_sc_hd__decap_6 FILLER_4_141 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_163 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_167 ();
 sky130_fd_sc_hd__decap_4 FILLER_4_192 ();
 sky130_ef_sc_hd__decap_12 FILLER_4_197 ();
 sky130_fd_sc_hd__decap_3 FILLER_4_209 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_220 ();
 sky130_fd_sc_hd__fill_1 FILLER_4_237 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_6 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_18 ();
 sky130_fd_sc_hd__decap_4 FILLER_5_30 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_34 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_44 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_57 ();
 sky130_fd_sc_hd__decap_8 FILLER_5_69 ();
 sky130_fd_sc_hd__fill_2 FILLER_5_77 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_87 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_99 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_111 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_113 ();
 sky130_fd_sc_hd__decap_4 FILLER_5_125 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_129 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_138 ();
 sky130_fd_sc_hd__decap_8 FILLER_5_158 ();
 sky130_fd_sc_hd__fill_2 FILLER_5_166 ();
 sky130_ef_sc_hd__decap_12 FILLER_5_175 ();
 sky130_fd_sc_hd__decap_6 FILLER_5_187 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_193 ();
 sky130_fd_sc_hd__fill_2 FILLER_5_199 ();
 sky130_fd_sc_hd__decap_4 FILLER_5_225 ();
 sky130_fd_sc_hd__fill_1 FILLER_5_229 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_3 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_15 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_27 ();
 sky130_fd_sc_hd__decap_6 FILLER_6_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_59 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_71 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_85 ();
 sky130_fd_sc_hd__decap_4 FILLER_6_97 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_117 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_129 ();
 sky130_ef_sc_hd__decap_12 FILLER_6_150 ();
 sky130_fd_sc_hd__decap_6 FILLER_6_162 ();
 sky130_fd_sc_hd__fill_1 FILLER_6_168 ();
 sky130_fd_sc_hd__decap_8 FILLER_6_176 ();
 sky130_fd_sc_hd__decap_4 FILLER_6_192 ();
 sky130_fd_sc_hd__decap_6 FILLER_6_197 ();
 sky130_fd_sc_hd__decap_3 FILLER_6_235 ();
 sky130_fd_sc_hd__decap_3 FILLER_7_6 ();
 sky130_fd_sc_hd__decap_3 FILLER_7_12 ();
 sky130_ef_sc_hd__decap_12 FILLER_7_39 ();
 sky130_fd_sc_hd__decap_4 FILLER_7_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_55 ();
 sky130_fd_sc_hd__decap_6 FILLER_7_89 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_95 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_127 ();
 sky130_ef_sc_hd__decap_12 FILLER_7_147 ();
 sky130_fd_sc_hd__decap_8 FILLER_7_159 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_167 ();
 sky130_fd_sc_hd__decap_4 FILLER_7_176 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_223 ();
 sky130_fd_sc_hd__fill_1 FILLER_7_233 ();
 sky130_ef_sc_hd__decap_12 FILLER_8_6 ();
 sky130_fd_sc_hd__decap_8 FILLER_8_18 ();
 sky130_fd_sc_hd__fill_2 FILLER_8_26 ();
 sky130_fd_sc_hd__decap_4 FILLER_8_37 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_78 ();
 sky130_ef_sc_hd__decap_12 FILLER_8_119 ();
 sky130_fd_sc_hd__decap_4 FILLER_8_131 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_144 ();
 sky130_fd_sc_hd__decap_4 FILLER_8_161 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_165 ();
 sky130_fd_sc_hd__decap_3 FILLER_8_178 ();
 sky130_fd_sc_hd__decap_8 FILLER_8_188 ();
 sky130_fd_sc_hd__decap_4 FILLER_8_205 ();
 sky130_fd_sc_hd__fill_1 FILLER_8_209 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_3 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_15 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_27 ();
 sky130_fd_sc_hd__decap_6 FILLER_9_39 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_45 ();
 sky130_fd_sc_hd__fill_2 FILLER_9_54 ();
 sky130_fd_sc_hd__decap_4 FILLER_9_64 ();
 sky130_fd_sc_hd__decap_8 FILLER_9_95 ();
 sky130_fd_sc_hd__decap_4 FILLER_9_108 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_113 ();
 sky130_fd_sc_hd__decap_8 FILLER_9_132 ();
 sky130_fd_sc_hd__decap_3 FILLER_9_140 ();
 sky130_fd_sc_hd__decap_3 FILLER_9_151 ();
 sky130_fd_sc_hd__decap_3 FILLER_9_162 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_185 ();
 sky130_ef_sc_hd__decap_12 FILLER_9_197 ();
 sky130_fd_sc_hd__decap_6 FILLER_9_209 ();
 sky130_fd_sc_hd__fill_1 FILLER_9_215 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_7 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_27 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_42 ();
 sky130_fd_sc_hd__decap_4 FILLER_10_48 ();
 sky130_fd_sc_hd__decap_3 FILLER_10_64 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_73 ();
 sky130_fd_sc_hd__decap_3 FILLER_10_81 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_85 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_97 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_10_121 ();
 sky130_fd_sc_hd__decap_8 FILLER_10_132 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_10_153 ();
 sky130_fd_sc_hd__decap_6 FILLER_10_189 ();
 sky130_fd_sc_hd__fill_1 FILLER_10_195 ();
 sky130_fd_sc_hd__decap_6 FILLER_10_206 ();
 sky130_fd_sc_hd__fill_2 FILLER_10_236 ();
 sky130_fd_sc_hd__decap_8 FILLER_11_6 ();
 sky130_fd_sc_hd__decap_3 FILLER_11_14 ();
 sky130_fd_sc_hd__decap_4 FILLER_11_44 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_11_79 ();
 sky130_fd_sc_hd__decap_4 FILLER_11_91 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_95 ();
 sky130_ef_sc_hd__decap_12 FILLER_11_121 ();
 sky130_fd_sc_hd__decap_8 FILLER_11_133 ();
 sky130_ef_sc_hd__decap_12 FILLER_11_152 ();
 sky130_fd_sc_hd__decap_4 FILLER_11_209 ();
 sky130_fd_sc_hd__fill_1 FILLER_11_213 ();
 sky130_fd_sc_hd__fill_2 FILLER_11_222 ();
 sky130_ef_sc_hd__decap_12 FILLER_12_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_12_18 ();
 sky130_fd_sc_hd__fill_2 FILLER_12_56 ();
 sky130_ef_sc_hd__decap_12 FILLER_12_64 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_76 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_83 ();
 sky130_fd_sc_hd__decap_8 FILLER_12_91 ();
 sky130_fd_sc_hd__decap_3 FILLER_12_99 ();
 sky130_fd_sc_hd__decap_8 FILLER_12_120 ();
 sky130_fd_sc_hd__decap_3 FILLER_12_128 ();
 sky130_fd_sc_hd__decap_6 FILLER_12_157 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_163 ();
 sky130_fd_sc_hd__fill_2 FILLER_12_180 ();
 sky130_fd_sc_hd__fill_1 FILLER_12_233 ();
 sky130_fd_sc_hd__fill_2 FILLER_13_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_13_22 ();
 sky130_fd_sc_hd__decap_4 FILLER_13_52 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_64 ();
 sky130_fd_sc_hd__decap_6 FILLER_13_76 ();
 sky130_fd_sc_hd__decap_8 FILLER_13_93 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_101 ();
 sky130_fd_sc_hd__decap_3 FILLER_13_109 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_118 ();
 sky130_ef_sc_hd__decap_12 FILLER_13_129 ();
 sky130_fd_sc_hd__decap_3 FILLER_13_141 ();
 sky130_fd_sc_hd__decap_3 FILLER_13_147 ();
 sky130_fd_sc_hd__decap_6 FILLER_13_161 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_167 ();
 sky130_fd_sc_hd__fill_2 FILLER_13_173 ();
 sky130_fd_sc_hd__decap_8 FILLER_13_183 ();
 sky130_fd_sc_hd__fill_2 FILLER_13_191 ();
 sky130_fd_sc_hd__decap_4 FILLER_13_206 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_210 ();
 sky130_fd_sc_hd__fill_1 FILLER_13_233 ();
 sky130_fd_sc_hd__fill_2 FILLER_14_3 ();
 sky130_fd_sc_hd__decap_6 FILLER_14_21 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_27 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_29 ();
 sky130_fd_sc_hd__decap_8 FILLER_14_42 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_50 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_60 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_72 ();
 sky130_fd_sc_hd__decap_8 FILLER_14_90 ();
 sky130_fd_sc_hd__fill_1 FILLER_14_98 ();
 sky130_fd_sc_hd__decap_3 FILLER_14_133 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_154 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_177 ();
 sky130_fd_sc_hd__fill_2 FILLER_14_189 ();
 sky130_ef_sc_hd__decap_12 FILLER_14_206 ();
 sky130_fd_sc_hd__fill_2 FILLER_14_218 ();
 sky130_fd_sc_hd__fill_2 FILLER_14_236 ();
 sky130_fd_sc_hd__decap_4 FILLER_15_3 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_16 ();
 sky130_fd_sc_hd__decap_6 FILLER_15_28 ();
 sky130_fd_sc_hd__fill_2 FILLER_15_54 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_69 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_86 ();
 sky130_fd_sc_hd__decap_6 FILLER_15_98 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_121 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_133 ();
 sky130_ef_sc_hd__decap_12 FILLER_15_145 ();
 sky130_fd_sc_hd__decap_4 FILLER_15_157 ();
 sky130_fd_sc_hd__decap_4 FILLER_15_185 ();
 sky130_fd_sc_hd__fill_1 FILLER_15_189 ();
 sky130_fd_sc_hd__decap_4 FILLER_15_206 ();
 sky130_fd_sc_hd__fill_1 FILLER_15_210 ();
 sky130_fd_sc_hd__fill_1 FILLER_15_233 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_6 ();
 sky130_fd_sc_hd__decap_8 FILLER_16_18 ();
 sky130_fd_sc_hd__fill_2 FILLER_16_26 ();
 sky130_fd_sc_hd__decap_8 FILLER_16_32 ();
 sky130_fd_sc_hd__fill_2 FILLER_16_40 ();
 sky130_fd_sc_hd__decap_4 FILLER_16_66 ();
 sky130_fd_sc_hd__decap_8 FILLER_16_76 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_97 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_116 ();
 sky130_fd_sc_hd__decap_4 FILLER_16_128 ();
 sky130_fd_sc_hd__fill_1 FILLER_16_132 ();
 sky130_fd_sc_hd__fill_2 FILLER_16_138 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_146 ();
 sky130_fd_sc_hd__decap_4 FILLER_16_158 ();
 sky130_fd_sc_hd__decap_4 FILLER_16_170 ();
 sky130_ef_sc_hd__decap_12 FILLER_16_182 ();
 sky130_fd_sc_hd__fill_2 FILLER_16_194 ();
 sky130_fd_sc_hd__decap_4 FILLER_16_206 ();
 sky130_fd_sc_hd__fill_1 FILLER_16_210 ();
 sky130_fd_sc_hd__decap_3 FILLER_16_235 ();
 sky130_fd_sc_hd__decap_3 FILLER_17_6 ();
 sky130_fd_sc_hd__decap_3 FILLER_17_17 ();
 sky130_fd_sc_hd__fill_2 FILLER_17_41 ();
 sky130_fd_sc_hd__decap_6 FILLER_17_50 ();
 sky130_fd_sc_hd__decap_8 FILLER_17_103 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_111 ();
 sky130_ef_sc_hd__decap_12 FILLER_17_113 ();
 sky130_fd_sc_hd__decap_4 FILLER_17_125 ();
 sky130_fd_sc_hd__fill_1 FILLER_17_129 ();
 sky130_fd_sc_hd__decap_8 FILLER_17_154 ();
 sky130_fd_sc_hd__decap_3 FILLER_17_162 ();
 sky130_fd_sc_hd__decap_8 FILLER_17_206 ();
 sky130_fd_sc_hd__fill_2 FILLER_17_214 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_19 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_18_43 ();
 sky130_ef_sc_hd__decap_12 FILLER_18_55 ();
 sky130_fd_sc_hd__fill_2 FILLER_18_67 ();
 sky130_fd_sc_hd__fill_2 FILLER_18_75 ();
 sky130_fd_sc_hd__decap_4 FILLER_18_106 ();
 sky130_ef_sc_hd__decap_12 FILLER_18_126 ();
 sky130_fd_sc_hd__fill_2 FILLER_18_138 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_141 ();
 sky130_fd_sc_hd__decap_3 FILLER_18_153 ();
 sky130_ef_sc_hd__decap_12 FILLER_18_173 ();
 sky130_fd_sc_hd__decap_4 FILLER_18_185 ();
 sky130_fd_sc_hd__fill_2 FILLER_18_194 ();
 sky130_fd_sc_hd__decap_4 FILLER_18_206 ();
 sky130_fd_sc_hd__fill_1 FILLER_18_210 ();
 sky130_fd_sc_hd__decap_3 FILLER_18_235 ();
 sky130_fd_sc_hd__decap_8 FILLER_19_6 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_14 ();
 sky130_fd_sc_hd__decap_8 FILLER_19_48 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_69 ();
 sky130_fd_sc_hd__decap_4 FILLER_19_81 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_85 ();
 sky130_fd_sc_hd__decap_6 FILLER_19_93 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_99 ();
 sky130_fd_sc_hd__decap_8 FILLER_19_103 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_111 ();
 sky130_fd_sc_hd__fill_2 FILLER_19_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_142 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_154 ();
 sky130_fd_sc_hd__fill_2 FILLER_19_166 ();
 sky130_ef_sc_hd__decap_12 FILLER_19_169 ();
 sky130_fd_sc_hd__decap_6 FILLER_19_181 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_187 ();
 sky130_fd_sc_hd__decap_6 FILLER_19_204 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_210 ();
 sky130_fd_sc_hd__fill_1 FILLER_19_223 ();
 sky130_fd_sc_hd__decap_6 FILLER_20_6 ();
 sky130_fd_sc_hd__fill_1 FILLER_20_12 ();
 sky130_fd_sc_hd__decap_3 FILLER_20_25 ();
 sky130_fd_sc_hd__fill_1 FILLER_20_33 ();
 sky130_ef_sc_hd__decap_12 FILLER_20_70 ();
 sky130_fd_sc_hd__fill_2 FILLER_20_82 ();
 sky130_ef_sc_hd__decap_12 FILLER_20_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_20_97 ();
 sky130_fd_sc_hd__decap_6 FILLER_20_134 ();
 sky130_fd_sc_hd__decap_8 FILLER_20_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_20_149 ();
 sky130_fd_sc_hd__decap_6 FILLER_20_163 ();
 sky130_ef_sc_hd__decap_12 FILLER_20_172 ();
 sky130_fd_sc_hd__decap_6 FILLER_20_184 ();
 sky130_fd_sc_hd__fill_2 FILLER_20_194 ();
 sky130_fd_sc_hd__decap_6 FILLER_20_206 ();
 sky130_fd_sc_hd__fill_2 FILLER_20_220 ();
 sky130_fd_sc_hd__decap_4 FILLER_21_3 ();
 sky130_fd_sc_hd__decap_6 FILLER_21_30 ();
 sky130_fd_sc_hd__fill_1 FILLER_21_55 ();
 sky130_fd_sc_hd__decap_3 FILLER_21_57 ();
 sky130_fd_sc_hd__decap_6 FILLER_21_80 ();
 sky130_fd_sc_hd__fill_1 FILLER_21_86 ();
 sky130_fd_sc_hd__fill_1 FILLER_21_103 ();
 sky130_fd_sc_hd__decap_6 FILLER_21_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_21_122 ();
 sky130_fd_sc_hd__decap_6 FILLER_21_128 ();
 sky130_fd_sc_hd__fill_1 FILLER_21_144 ();
 sky130_fd_sc_hd__fill_1 FILLER_21_177 ();
 sky130_fd_sc_hd__decap_4 FILLER_21_203 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_6 ();
 sky130_fd_sc_hd__decap_3 FILLER_22_25 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_29 ();
 sky130_fd_sc_hd__decap_3 FILLER_22_53 ();
 sky130_fd_sc_hd__fill_2 FILLER_22_64 ();
 sky130_fd_sc_hd__fill_2 FILLER_22_82 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_85 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_91 ();
 sky130_fd_sc_hd__decap_3 FILLER_22_102 ();
 sky130_fd_sc_hd__decap_6 FILLER_22_108 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_114 ();
 sky130_ef_sc_hd__decap_12 FILLER_22_123 ();
 sky130_fd_sc_hd__decap_4 FILLER_22_135 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_139 ();
 sky130_fd_sc_hd__fill_2 FILLER_22_148 ();
 sky130_fd_sc_hd__fill_2 FILLER_22_194 ();
 sky130_fd_sc_hd__decap_3 FILLER_22_206 ();
 sky130_fd_sc_hd__fill_1 FILLER_22_233 ();
 sky130_fd_sc_hd__fill_2 FILLER_23_6 ();
 sky130_fd_sc_hd__decap_8 FILLER_23_36 ();
 sky130_fd_sc_hd__fill_1 FILLER_23_44 ();
 sky130_fd_sc_hd__fill_1 FILLER_23_51 ();
 sky130_fd_sc_hd__decap_3 FILLER_23_57 ();
 sky130_fd_sc_hd__fill_2 FILLER_23_73 ();
 sky130_fd_sc_hd__fill_2 FILLER_23_106 ();
 sky130_fd_sc_hd__fill_2 FILLER_23_129 ();
 sky130_fd_sc_hd__fill_2 FILLER_23_147 ();
 sky130_fd_sc_hd__decap_3 FILLER_23_165 ();
 sky130_fd_sc_hd__decap_8 FILLER_23_173 ();
 sky130_fd_sc_hd__decap_3 FILLER_23_181 ();
 sky130_fd_sc_hd__decap_8 FILLER_23_225 ();
 sky130_fd_sc_hd__fill_1 FILLER_23_233 ();
 sky130_fd_sc_hd__decap_6 FILLER_24_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_9 ();
 sky130_fd_sc_hd__decap_4 FILLER_24_23 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_29 ();
 sky130_fd_sc_hd__decap_3 FILLER_24_41 ();
 sky130_fd_sc_hd__decap_4 FILLER_24_75 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_97 ();
 sky130_fd_sc_hd__decap_4 FILLER_24_109 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_124 ();
 sky130_fd_sc_hd__decap_4 FILLER_24_136 ();
 sky130_fd_sc_hd__decap_6 FILLER_24_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_151 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_163 ();
 sky130_fd_sc_hd__decap_6 FILLER_24_175 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_181 ();
 sky130_fd_sc_hd__decap_8 FILLER_24_187 ();
 sky130_fd_sc_hd__fill_1 FILLER_24_195 ();
 sky130_ef_sc_hd__decap_12 FILLER_24_210 ();
 sky130_fd_sc_hd__decap_6 FILLER_25_6 ();
 sky130_fd_sc_hd__fill_1 FILLER_25_23 ();
 sky130_ef_sc_hd__decap_12 FILLER_25_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_25_55 ();
 sky130_fd_sc_hd__decap_8 FILLER_25_69 ();
 sky130_fd_sc_hd__decap_3 FILLER_25_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_25_84 ();
 sky130_fd_sc_hd__decap_6 FILLER_25_106 ();
 sky130_fd_sc_hd__decap_8 FILLER_25_113 ();
 sky130_fd_sc_hd__decap_3 FILLER_25_121 ();
 sky130_fd_sc_hd__decap_4 FILLER_25_140 ();
 sky130_fd_sc_hd__fill_1 FILLER_25_156 ();
 sky130_fd_sc_hd__decap_3 FILLER_25_165 ();
 sky130_ef_sc_hd__decap_12 FILLER_25_169 ();
 sky130_fd_sc_hd__decap_8 FILLER_25_197 ();
 sky130_ef_sc_hd__decap_12 FILLER_25_210 ();
 sky130_fd_sc_hd__fill_2 FILLER_25_222 ();
 sky130_fd_sc_hd__decap_4 FILLER_25_225 ();
 sky130_fd_sc_hd__fill_1 FILLER_25_229 ();
 sky130_fd_sc_hd__fill_1 FILLER_26_6 ();
 sky130_fd_sc_hd__decap_8 FILLER_26_29 ();
 sky130_fd_sc_hd__decap_3 FILLER_26_37 ();
 sky130_fd_sc_hd__decap_3 FILLER_26_46 ();
 sky130_fd_sc_hd__fill_2 FILLER_26_82 ();
 sky130_fd_sc_hd__fill_1 FILLER_26_92 ();
 sky130_ef_sc_hd__decap_12 FILLER_26_110 ();
 sky130_ef_sc_hd__decap_12 FILLER_26_122 ();
 sky130_fd_sc_hd__decap_4 FILLER_26_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_26_186 ();
 sky130_ef_sc_hd__decap_12 FILLER_26_197 ();
 sky130_fd_sc_hd__fill_2 FILLER_26_218 ();
 sky130_fd_sc_hd__fill_2 FILLER_26_223 ();
 sky130_fd_sc_hd__fill_2 FILLER_26_236 ();
 sky130_fd_sc_hd__decap_3 FILLER_27_3 ();
 sky130_fd_sc_hd__fill_1 FILLER_27_15 ();
 sky130_fd_sc_hd__decap_8 FILLER_27_24 ();
 sky130_fd_sc_hd__decap_3 FILLER_27_32 ();
 sky130_fd_sc_hd__decap_6 FILLER_27_50 ();
 sky130_fd_sc_hd__decap_8 FILLER_27_57 ();
 sky130_fd_sc_hd__fill_2 FILLER_27_65 ();
 sky130_fd_sc_hd__decap_8 FILLER_27_103 ();
 sky130_fd_sc_hd__fill_1 FILLER_27_111 ();
 sky130_fd_sc_hd__decap_4 FILLER_27_136 ();
 sky130_fd_sc_hd__fill_1 FILLER_27_140 ();
 sky130_fd_sc_hd__decap_8 FILLER_27_160 ();
 sky130_fd_sc_hd__decap_8 FILLER_27_169 ();
 sky130_fd_sc_hd__fill_2 FILLER_27_199 ();
 sky130_fd_sc_hd__fill_2 FILLER_27_206 ();
 sky130_fd_sc_hd__decap_4 FILLER_28_23 ();
 sky130_fd_sc_hd__fill_1 FILLER_28_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_28_37 ();
 sky130_ef_sc_hd__decap_12 FILLER_28_65 ();
 sky130_fd_sc_hd__decap_6 FILLER_28_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_28_83 ();
 sky130_fd_sc_hd__decap_4 FILLER_28_98 ();
 sky130_fd_sc_hd__decap_8 FILLER_28_128 ();
 sky130_fd_sc_hd__fill_1 FILLER_28_141 ();
 sky130_fd_sc_hd__decap_4 FILLER_28_148 ();
 sky130_fd_sc_hd__fill_1 FILLER_28_152 ();
 sky130_fd_sc_hd__fill_2 FILLER_28_177 ();
 sky130_fd_sc_hd__decap_6 FILLER_28_189 ();
 sky130_fd_sc_hd__fill_1 FILLER_28_195 ();
 sky130_fd_sc_hd__decap_4 FILLER_28_211 ();
 sky130_fd_sc_hd__fill_1 FILLER_28_237 ();
 sky130_ef_sc_hd__decap_12 FILLER_29_6 ();
 sky130_ef_sc_hd__decap_12 FILLER_29_18 ();
 sky130_fd_sc_hd__fill_2 FILLER_29_30 ();
 sky130_fd_sc_hd__decap_4 FILLER_29_44 ();
 sky130_ef_sc_hd__decap_12 FILLER_29_65 ();
 sky130_fd_sc_hd__decap_6 FILLER_29_77 ();
 sky130_fd_sc_hd__fill_1 FILLER_29_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_29_92 ();
 sky130_fd_sc_hd__decap_8 FILLER_29_104 ();
 sky130_fd_sc_hd__decap_8 FILLER_29_113 ();
 sky130_fd_sc_hd__fill_2 FILLER_29_121 ();
 sky130_fd_sc_hd__fill_1 FILLER_29_183 ();
 sky130_ef_sc_hd__decap_12 FILLER_29_200 ();
 sky130_fd_sc_hd__decap_8 FILLER_29_212 ();
 sky130_fd_sc_hd__decap_3 FILLER_30_3 ();
 sky130_fd_sc_hd__decap_6 FILLER_30_15 ();
 sky130_fd_sc_hd__decap_4 FILLER_30_44 ();
 sky130_fd_sc_hd__decap_4 FILLER_30_72 ();
 sky130_fd_sc_hd__fill_1 FILLER_30_76 ();
 sky130_ef_sc_hd__decap_12 FILLER_30_97 ();
 sky130_fd_sc_hd__decap_3 FILLER_30_109 ();
 sky130_fd_sc_hd__decap_8 FILLER_30_129 ();
 sky130_fd_sc_hd__decap_3 FILLER_30_137 ();
 sky130_fd_sc_hd__fill_2 FILLER_30_159 ();
 sky130_fd_sc_hd__decap_8 FILLER_30_177 ();
 sky130_fd_sc_hd__fill_1 FILLER_30_185 ();
 sky130_fd_sc_hd__decap_6 FILLER_30_190 ();
 sky130_fd_sc_hd__fill_2 FILLER_30_232 ();
 sky130_fd_sc_hd__decap_3 FILLER_31_38 ();
 sky130_fd_sc_hd__decap_3 FILLER_31_101 ();
 sky130_ef_sc_hd__decap_12 FILLER_31_132 ();
 sky130_ef_sc_hd__decap_12 FILLER_31_144 ();
 sky130_ef_sc_hd__decap_12 FILLER_31_156 ();
 sky130_fd_sc_hd__fill_1 FILLER_31_169 ();
 sky130_fd_sc_hd__decap_6 FILLER_31_174 ();
 sky130_fd_sc_hd__decap_6 FILLER_31_201 ();
 sky130_fd_sc_hd__decap_6 FILLER_31_218 ();
 sky130_ef_sc_hd__decap_12 FILLER_32_15 ();
 sky130_fd_sc_hd__fill_1 FILLER_32_27 ();
 sky130_ef_sc_hd__decap_12 FILLER_32_37 ();
 sky130_fd_sc_hd__decap_4 FILLER_32_80 ();
 sky130_fd_sc_hd__decap_8 FILLER_32_99 ();
 sky130_fd_sc_hd__fill_2 FILLER_32_107 ();
 sky130_ef_sc_hd__decap_12 FILLER_32_125 ();
 sky130_fd_sc_hd__decap_3 FILLER_32_137 ();
 sky130_ef_sc_hd__decap_12 FILLER_32_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_32_153 ();
 sky130_fd_sc_hd__decap_8 FILLER_32_165 ();
 sky130_fd_sc_hd__decap_3 FILLER_32_173 ();
 sky130_fd_sc_hd__decap_4 FILLER_32_181 ();
 sky130_fd_sc_hd__fill_1 FILLER_32_185 ();
 sky130_fd_sc_hd__fill_1 FILLER_32_195 ();
 sky130_fd_sc_hd__decap_8 FILLER_32_197 ();
 sky130_fd_sc_hd__fill_1 FILLER_32_205 ();
 sky130_fd_sc_hd__decap_3 FILLER_33_3 ();
 sky130_fd_sc_hd__decap_4 FILLER_33_15 ();
 sky130_fd_sc_hd__fill_1 FILLER_33_26 ();
 sky130_fd_sc_hd__decap_8 FILLER_33_41 ();
 sky130_fd_sc_hd__decap_4 FILLER_33_57 ();
 sky130_fd_sc_hd__fill_1 FILLER_33_61 ();
 sky130_ef_sc_hd__decap_12 FILLER_33_94 ();
 sky130_fd_sc_hd__decap_6 FILLER_33_106 ();
 sky130_fd_sc_hd__fill_2 FILLER_33_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_33_123 ();
 sky130_ef_sc_hd__decap_12 FILLER_33_135 ();
 sky130_fd_sc_hd__fill_2 FILLER_33_147 ();
 sky130_fd_sc_hd__decap_3 FILLER_33_165 ();
 sky130_fd_sc_hd__decap_4 FILLER_33_169 ();
 sky130_fd_sc_hd__fill_1 FILLER_33_173 ();
 sky130_fd_sc_hd__decap_8 FILLER_33_190 ();
 sky130_ef_sc_hd__decap_12 FILLER_33_203 ();
 sky130_fd_sc_hd__decap_8 FILLER_33_215 ();
 sky130_fd_sc_hd__fill_1 FILLER_33_223 ();
 sky130_fd_sc_hd__decap_3 FILLER_33_235 ();
 sky130_fd_sc_hd__decap_4 FILLER_34_24 ();
 sky130_fd_sc_hd__decap_4 FILLER_34_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_34_33 ();
 sky130_fd_sc_hd__decap_4 FILLER_34_80 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_93 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_105 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_117 ();
 sky130_fd_sc_hd__decap_8 FILLER_34_129 ();
 sky130_fd_sc_hd__decap_3 FILLER_34_137 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_153 ();
 sky130_fd_sc_hd__decap_8 FILLER_34_165 ();
 sky130_fd_sc_hd__fill_2 FILLER_34_173 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_180 ();
 sky130_fd_sc_hd__decap_4 FILLER_34_192 ();
 sky130_ef_sc_hd__decap_12 FILLER_34_197 ();
 sky130_fd_sc_hd__decap_6 FILLER_34_209 ();
 sky130_fd_sc_hd__fill_1 FILLER_34_237 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_6 ();
 sky130_fd_sc_hd__decap_4 FILLER_35_18 ();
 sky130_fd_sc_hd__fill_1 FILLER_35_22 ();
 sky130_fd_sc_hd__decap_3 FILLER_35_30 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_97 ();
 sky130_fd_sc_hd__decap_3 FILLER_35_109 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_125 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_137 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_149 ();
 sky130_fd_sc_hd__decap_6 FILLER_35_161 ();
 sky130_fd_sc_hd__fill_1 FILLER_35_167 ();
 sky130_fd_sc_hd__decap_4 FILLER_35_169 ();
 sky130_fd_sc_hd__fill_1 FILLER_35_173 ();
 sky130_fd_sc_hd__decap_4 FILLER_35_199 ();
 sky130_ef_sc_hd__decap_12 FILLER_35_208 ();
 sky130_fd_sc_hd__decap_4 FILLER_35_220 ();
 sky130_fd_sc_hd__decap_4 FILLER_35_225 ();
 sky130_fd_sc_hd__fill_1 FILLER_35_229 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_3 ();
 sky130_fd_sc_hd__decap_4 FILLER_36_23 ();
 sky130_fd_sc_hd__fill_1 FILLER_36_27 ();
 sky130_fd_sc_hd__decap_4 FILLER_36_29 ();
 sky130_fd_sc_hd__fill_1 FILLER_36_33 ();
 sky130_fd_sc_hd__decap_4 FILLER_36_50 ();
 sky130_fd_sc_hd__fill_1 FILLER_36_54 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_71 ();
 sky130_fd_sc_hd__fill_1 FILLER_36_83 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_97 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_109 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_121 ();
 sky130_fd_sc_hd__decap_6 FILLER_36_133 ();
 sky130_fd_sc_hd__fill_1 FILLER_36_139 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_146 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_158 ();
 sky130_ef_sc_hd__decap_12 FILLER_36_170 ();
 sky130_fd_sc_hd__decap_8 FILLER_36_182 ();
 sky130_fd_sc_hd__fill_1 FILLER_36_195 ();
 sky130_fd_sc_hd__fill_2 FILLER_36_216 ();
 sky130_fd_sc_hd__decap_4 FILLER_37_6 ();
 sky130_fd_sc_hd__decap_8 FILLER_37_34 ();
 sky130_fd_sc_hd__fill_1 FILLER_37_42 ();
 sky130_fd_sc_hd__decap_4 FILLER_37_51 ();
 sky130_fd_sc_hd__fill_1 FILLER_37_55 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_69 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_81 ();
 sky130_fd_sc_hd__fill_1 FILLER_37_93 ();
 sky130_fd_sc_hd__decap_8 FILLER_37_102 ();
 sky130_fd_sc_hd__fill_2 FILLER_37_110 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_125 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_137 ();
 sky130_ef_sc_hd__decap_12 FILLER_37_149 ();
 sky130_fd_sc_hd__decap_6 FILLER_37_161 ();
 sky130_fd_sc_hd__fill_1 FILLER_37_167 ();
 sky130_fd_sc_hd__decap_8 FILLER_37_169 ();
 sky130_fd_sc_hd__fill_2 FILLER_37_177 ();
 sky130_fd_sc_hd__fill_1 FILLER_37_216 ();
 sky130_fd_sc_hd__fill_1 FILLER_37_223 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_6 ();
 sky130_fd_sc_hd__decap_3 FILLER_38_18 ();
 sky130_fd_sc_hd__fill_2 FILLER_38_26 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_45 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_69 ();
 sky130_fd_sc_hd__decap_3 FILLER_38_81 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_97 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_109 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_121 ();
 sky130_fd_sc_hd__decap_6 FILLER_38_133 ();
 sky130_fd_sc_hd__fill_1 FILLER_38_139 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_141 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_153 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_165 ();
 sky130_ef_sc_hd__decap_12 FILLER_38_177 ();
 sky130_fd_sc_hd__decap_6 FILLER_38_189 ();
 sky130_fd_sc_hd__fill_1 FILLER_38_195 ();
 sky130_fd_sc_hd__decap_8 FILLER_38_206 ();
 sky130_fd_sc_hd__fill_1 FILLER_38_214 ();
 sky130_fd_sc_hd__fill_1 FILLER_38_237 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_3 ();
 sky130_fd_sc_hd__decap_6 FILLER_39_15 ();
 sky130_fd_sc_hd__fill_1 FILLER_39_21 ();
 sky130_fd_sc_hd__decap_3 FILLER_39_25 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_29 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_41 ();
 sky130_fd_sc_hd__decap_3 FILLER_39_53 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_57 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_69 ();
 sky130_fd_sc_hd__decap_3 FILLER_39_81 ();
 sky130_fd_sc_hd__decap_3 FILLER_39_85 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_92 ();
 sky130_fd_sc_hd__decap_8 FILLER_39_104 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_113 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_125 ();
 sky130_fd_sc_hd__decap_3 FILLER_39_137 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_141 ();
 sky130_fd_sc_hd__fill_1 FILLER_39_153 ();
 sky130_fd_sc_hd__decap_8 FILLER_39_158 ();
 sky130_fd_sc_hd__fill_2 FILLER_39_166 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_169 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_181 ();
 sky130_fd_sc_hd__decap_3 FILLER_39_193 ();
 sky130_ef_sc_hd__decap_12 FILLER_39_197 ();
 sky130_fd_sc_hd__decap_6 FILLER_39_209 ();
 sky130_fd_sc_hd__fill_1 FILLER_39_215 ();
endmodule
