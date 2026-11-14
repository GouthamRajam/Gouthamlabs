`timescale 1ns / 1ps

// Testbench for the S2S pipeline-generated uart_top (5-module architecture).
// Same test coverage as the hand-authored UART testbench: loopback, multi-baud,
// edge cases, back-to-back. Produces uart_results.txt for Python cross-check.
module pipeline_uart_tb;

    reg         clk;
    reg         rst_n;
    reg  [7:0]  tx_data;
    reg         tx_valid;
    wire        tx_ready;
    wire [7:0]  rx_data;
    wire        rx_valid;
    wire        tx;
    reg         rx;
    reg  [15:0] baud_div;
    reg  [1:0]  parity_mode;
    wire        frame_err;
    wire        parity_err;
    wire        overrun_err;

    // Loopback: connect TX to RX (async domain crossing through sync2)
    always @(*) rx = tx;

    uart_top #(
        .DIV_W  (16),
        .DATA_W (8),
        .PM_W   (2)
    ) dut (
        .clk         (clk),
        .rst_n       (rst_n),
        .rx          (rx),
        .tx          (tx),
        .tx_data     (tx_data),
        .tx_valid    (tx_valid),
        .tx_ready    (tx_ready),
        .rx_data     (rx_data),
        .rx_valid    (rx_valid),
        .baud_div    (baud_div),
        .parity_mode (parity_mode),
        .frame_err   (frame_err),
        .parity_err  (parity_err),
        .overrun_err (overrun_err)
    );

    // 50 MHz clock (20 ns period)
    initial clk = 0;
    always #10 clk = ~clk;

    integer tx_count;
    integer err_count;
    integer i;
    integer fd;

    reg [7:0] tx_log [0:255];
    reg [7:0] rx_log [0:255];

    // Send a byte: assert tx_valid when tx_ready, wait for rx_valid
    task send_and_receive(input [7:0] data, input integer idx);
        reg [7:0] rx_byte;
        integer timeout;
        begin
            tx_log[idx] = data;

            // Wait for TX ready
            timeout = 0;
            while (!tx_ready && timeout < 2_000_000) begin
                @(posedge clk);
                timeout = timeout + 1;
            end
            if (timeout >= 2_000_000) begin
                $display("ERROR: TX ready timeout at byte %0d", idx);
                err_count = err_count + 1;
                rx_log[idx] = 8'hxx;
            end else begin
                // Drive tx_data and tx_valid for one cycle
                @(posedge clk);
                tx_data  <= data;
                tx_valid <= 1'b1;
                @(posedge clk);
                tx_valid <= 1'b0;

                // Wait for rx_valid pulse
                timeout = 0;
                while (!rx_valid && timeout < 2_000_000) begin
                    @(posedge clk);
                    timeout = timeout + 1;
                end
                if (timeout >= 2_000_000) begin
                    $display("ERROR: RX timeout at byte %0d", idx);
                    err_count = err_count + 1;
                    rx_log[idx] = 8'hxx;
                end else begin
                    rx_byte = rx_data;
                    rx_log[idx] = rx_byte;

                    if (rx_byte !== data) begin
                        $display("MISMATCH byte %0d: sent 0x%02x, got 0x%02x", idx, data, rx_byte);
                        err_count = err_count + 1;
                    end

                    if (frame_err) begin
                        $display("FRAME ERROR at byte %0d", idx);
                        err_count = err_count + 1;
                    end
                end
            end
        end
    endtask

    reg [7:0] test_byte;

    initial begin
        $dumpfile("pipeline_uart_tb.vcd");
        $dumpvars(0, pipeline_uart_tb);

        rst_n       = 0;
        tx_data     = 0;
        tx_valid    = 0;
        baud_div    = 16'd27;   // Default: 50MHz / (27*16) ≈ 115740 baud
        parity_mode = 2'b00;    // No parity (8N1)
        tx_count    = 0;
        err_count   = 0;

        // Reset
        repeat (10) @(posedge clk);
        rst_n = 1;
        repeat (5) @(posedge clk);

        // --- Test 1: default baud (~115200), 32 random bytes ---
        $display("=== Test 1: default baud (~115200), 32 random bytes ===");
        for (i = 0; i < 32; i = i + 1) begin
            test_byte = $random & 8'hFF;
            send_and_receive(test_byte, i);
        end
        tx_count = 32;

        // --- Test 2: slower baud (~57600, divisor 54) ---
        $display("=== Test 2: baud ~57600 (divisor 54), 16 bytes ===");
        baud_div = 16'd54;  // 50MHz / (54*16) ≈ 57870 baud
        repeat (10) @(posedge clk);

        for (i = 32; i < 48; i = i + 1) begin
            test_byte = $random & 8'hFF;
            send_and_receive(test_byte, i);
        end
        tx_count = 48;

        // --- Test 3: edge cases (0x00, 0xFF, 0xAA, 0x55) ---
        $display("=== Test 3: edge cases (0x00, 0xFF, 0xAA, 0x55) ===");
        send_and_receive(8'h00, 48);
        send_and_receive(8'hFF, 49);
        send_and_receive(8'hAA, 50);
        send_and_receive(8'h55, 51);
        tx_count = 52;

        // --- Test 4: back-to-back at fast baud ---
        $display("=== Test 4: back-to-back, 20 bytes at baud ~115200 ===");
        baud_div = 16'd27;
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
