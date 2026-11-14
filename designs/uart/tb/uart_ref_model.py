"""Independent bit-level UART reference model (8N1).

This is NOT part of the RTL — it is the independent oracle that
decides pass/fail. The testbench compares RTL behavior against this.
"""


def encode_byte(data: int) -> list[int]:
    """Encode one byte as a list of bit values: start + 8 data (LSB first) + stop."""
    bits = [0]  # start bit
    for i in range(8):
        bits.append((data >> i) & 1)
    bits.append(1)  # stop bit
    return bits


def decode_bits(bits: list[int]) -> tuple[int, bool]:
    """Decode a 10-bit frame (start + 8 data + stop).

    Returns (byte_value, frame_ok).
    frame_ok is False if start != 0 or stop != 1.
    """
    if len(bits) != 10:
        raise ValueError(f"Expected 10 bits, got {len(bits)}")
    start = bits[0]
    stop = bits[9]
    data = 0
    for i in range(8):
        data |= (bits[1 + i] & 1) << i
    frame_ok = (start == 0) and (stop == 1)
    return data, frame_ok


def encode_stream(data_bytes: list[int]) -> list[int]:
    """Encode a sequence of bytes into a serial bit stream."""
    stream = []
    for b in data_bytes:
        stream.extend(encode_byte(b))
    return stream


def decode_stream(bit_stream: list[int], baud_ticks: int) -> list[tuple[int, bool]]:
    """Decode a serial bit stream with 16x oversampling.

    Mimics the RX: waits for falling edge (start), samples at mid-bit,
    reads 8 data bits, checks stop bit.

    Args:
        bit_stream: list of bit values, one per (baud_ticks/16) sample period
        baud_ticks: number of sample periods per bit (should be 16 for 16x)

    Returns list of (byte_value, frame_ok).
    """
    results = []
    i = 0
    n = len(bit_stream)

    while i < n:
        # Wait for falling edge (start bit)
        if bit_stream[i] == 0:
            # Sample at mid-bit of start
            mid = i + baud_ticks // 2
            if mid >= n:
                break
            if bit_stream[mid] != 0:
                # False start
                i += 1
                continue

            # Read 8 data bits at mid-bit positions
            frame_bits = [0]  # start confirmed
            valid = True
            for bit_idx in range(8):
                sample_pos = i + baud_ticks // 2 + (bit_idx + 1) * baud_ticks
                if sample_pos >= n:
                    valid = False
                    break
                frame_bits.append(bit_stream[sample_pos])

            if not valid:
                break

            # Stop bit
            stop_pos = i + baud_ticks // 2 + 9 * baud_ticks
            if stop_pos >= n:
                break
            frame_bits.append(bit_stream[stop_pos])

            byte_val, frame_ok = decode_bits(frame_bits)
            results.append((byte_val, frame_ok))

            # Advance past the stop bit
            i = i + 10 * baud_ticks
        else:
            i += 1

    return results
