`timescale 1ns / 1ps

module uart_tb;

    reg        clk;
    reg        rst_n;
    reg  [1:0] addr;
    reg        wr_en;
    reg        rd_en;
    reg  [7:0] wr_data;
    wire [7:0] rd_data;
    wire       tx;
    reg        rx;

    // Loopback: connect TX to RX
    always @(*) rx = tx;

    s2s_uart dut (
        .clk     (clk),
        .rst_n   (rst_n),
        .addr    (addr),
        .wr_en   (wr_en),
        .rd_en   (rd_en),
        .wr_data (wr_data),
        .rd_data (rd_data),
        .tx      (tx),
        .rx      (rx)
    );

    // 50 MHz clock (20 ns period)
    initial clk = 0;
    always #10 clk = ~clk;

    integer tx_count;
    integer rx_count;
    integer err_count;
    integer i;
    integer fd;

    reg [7:0] tx_log [0:255];
    reg [7:0] rx_log [0:255];

    task write_reg(input [1:0] a, input [7:0] d);
        begin
            @(posedge clk);
            addr    <= a;
            wr_data <= d;
            wr_en   <= 1'b1;
            @(posedge clk);
            wr_en   <= 1'b0;
        end
    endtask

    task read_reg(input [1:0] a, output [7:0] d);
        begin
            @(posedge clk);
            addr  <= a;
            rd_en <= 1'b1;
            @(posedge clk);
            rd_en <= 1'b0;
            @(posedge clk);
            d = rd_data;
        end
    endtask

    task wait_tx_done;
        reg [7:0] status;
        integer timeout;
        begin
            timeout = 0;
            status = 8'd0;
            while (!(status & 8'h01) && timeout < 200000) begin
                read_reg(2'd2, status);
                timeout = timeout + 1;
            end
            if (timeout >= 200000) begin
                $display("ERROR: TX timeout");
                err_count = err_count + 1;
            end
        end
    endtask

    task wait_rx_ready;
        reg [7:0] status;
        integer timeout;
        begin
            timeout = 0;
            status = 8'd0;
            while (!(status & 8'h02) && timeout < 200000) begin
                read_reg(2'd2, status);
                timeout = timeout + 1;
            end
            if (timeout >= 200000) begin
                $display("ERROR: RX timeout");
                err_count = err_count + 1;
            end
        end
    endtask

    task send_and_receive(input [7:0] data, input integer idx);
        reg [7:0] rx_byte;
        begin
            tx_log[idx] = data;
            // Wait for TX ready
            wait_tx_done;
            // Write TX data
            write_reg(2'd0, data);
            // Wait for RX to receive
            wait_rx_ready;
            // Read RX data
            read_reg(2'd1, rx_byte);
            rx_log[idx] = rx_byte;

            if (rx_byte !== data) begin
                $display("MISMATCH byte %0d: sent 0x%02x, got 0x%02x", idx, data, rx_byte);
                err_count = err_count + 1;
            end
        end
    endtask

    reg [7:0] test_byte;

    initial begin
        $dumpfile("uart_tb.vcd");
        $dumpvars(0, uart_tb);

        rst_n   = 0;
        addr    = 0;
        wr_en   = 0;
        rd_en   = 0;
        wr_data = 0;
        tx_count = 0;
        rx_count = 0;
        err_count = 0;

        // Reset
        repeat (10) @(posedge clk);
        rst_n = 1;
        repeat (5) @(posedge clk);

        // --- Test 1: default baud (divisor 433, ~115200 @ 50 MHz) ---
        $display("=== Test 1: default baud (115200), 32 random bytes ===");
        for (i = 0; i < 32; i = i + 1) begin
            test_byte = $random & 8'hFF;
            send_and_receive(test_byte, i);
        end
        tx_count = 32;

        // --- Test 2: slower baud (divisor 867, ~57600 @ 50 MHz) ---
        $display("=== Test 2: baud 57600 (divisor 867), 16 bytes ===");
        write_reg(2'd3, 8'h63);  // low byte: 867 & 0xFF = 0x63
        write_reg(2'd3, 8'h03);  // high byte: 867 >> 8 = 0x03
        repeat (10) @(posedge clk);

        for (i = 32; i < 48; i = i + 1) begin
            test_byte = $random & 8'hFF;
            send_and_receive(test_byte, i);
        end
        tx_count = 48;

        // --- Test 3: edge cases ---
        $display("=== Test 3: edge cases (0x00, 0xFF, 0xAA, 0x55) ===");
        send_and_receive(8'h00, 48);
        send_and_receive(8'hFF, 49);
        send_and_receive(8'hAA, 50);
        send_and_receive(8'h55, 51);
        tx_count = 52;

        // --- Test 4: back-to-back at fast baud ---
        $display("=== Test 4: back-to-back, 20 bytes at baud 115200 ===");
        write_reg(2'd3, 8'hB1);  // low byte: 433 & 0xFF = 0xB1
        write_reg(2'd3, 8'h01);  // high byte: 433 >> 8 = 0x01
        repeat (10) @(posedge clk);

        for (i = 52; i < 72; i = i + 1) begin
            test_byte = $random & 8'hFF;
            send_and_receive(test_byte, i);
        end
        tx_count = 72;

        // Write results file for Python cross-check
        fd = $fopen("uart_results.txt", "w");
        for (i = 0; i < tx_count; i = i + 1) begin
            $fdisplay(fd, "%02x %02x", tx_log[i], rx_log[i]);
        end
        $fclose(fd);

        $display("");
        if (err_count == 0) begin
            $display("PASS: all %0d bytes looped back correctly", tx_count);
        end else begin
            $display("FAIL: %0d errors in %0d bytes", err_count, tx_count);
        end
        $display("");

        $finish;
    end

    // Watchdog
    initial begin
        #500_000_000;
        $display("TIMEOUT: simulation exceeded 500ms");
        $finish;
    end

endmodule
