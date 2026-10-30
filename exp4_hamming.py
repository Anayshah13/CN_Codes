"""Experiment 4: Hamming code, even parity.

Reads a file as raw bytes, splits it into 16-bit and 32-bit blocks,
adds parity bits, flips one bit in some blocks, then corrects them.

Bit position 1 is the leftmost bit of a printed codeword, matching
code[1:] from the encoder (index 0 is position 1).

Also answers the two observation questions.

Run:
  python exp4_hamming.py
  python exp4_hamming.py some.pdf
"""

from __future__ import annotations

import random
import sys
from pathlib import Path


def required_parity_bits(m: int) -> int:
    """Smallest r such that 2^r >= m + r + 1."""
    r = 0
    while 2**r < m + r + 1:
        r += 1
    return r


def hamming_encode(data: list[int]) -> list[int]:
    """Place data on non-power-of-two positions and set even parity.

    Positions are 1-based. The returned list starts at position 1.
    """
    m = len(data)
    r = required_parity_bits(m)
    n = m + r
    code = [0] * (n + 1)  # index 0 is unused
    j = 0
    for i in range(1, n + 1):
        # Powers of two have no other bits set, so i & (i - 1) is 0 there.
        if i & (i - 1):
            code[i] = data[j]
            j += 1
    for p in range(r):
        pos = 2**p
        parity = 0
        for i in range(1, n + 1):
            if i & pos:
                parity ^= code[i]
        code[pos] = parity
    return code[1:]


def hamming_decode(received: list[int]) -> tuple[list[int], int, bool]:
    """Return data bits, syndrome, and whether a bit was flipped.

    Syndrome 0 means no error. Otherwise the syndrome is the bad position.
    """
    n = len(received)
    code = [0] + received
    syndrome = 0
    pos = 1
    while pos <= n:
        parity = 0
        for i in range(1, n + 1):
            if i & pos:
                parity ^= code[i]
        if parity:
            syndrome += pos
        pos *= 2
    corrected = False
    if syndrome != 0 and syndrome <= n:
        code[syndrome] ^= 1
        corrected = True
    data = [code[i] for i in range(1, n + 1) if i & (i - 1)]
    return data, syndrome, corrected


def bytes_to_bits(data: bytes) -> list[int]:
    """MSB of each byte first."""
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits


def bits_to_bytes(bits: list[int]) -> bytes:
    result = bytearray()
    for i in range(0, len(bits), 8):
        value = 0
        for bit in bits[i : i + 8]:
            value = (value << 1) | bit
        result.append(value)
    return bytes(result)


def split_blocks(bits: list[int], size: int) -> list[list[int]]:
    """Last block is padded with zeros so every block has `size` data bits."""
    blocks = []
    for i in range(0, len(bits), size):
        block = bits[i : i + size]
        if len(block) < size:
            block += [0] * (size - len(block))
        blocks.append(block)
    return blocks


def transmit(bits: list[int], probability: float) -> tuple[list[int], int]:
    """With the given probability, flip exactly one bit. Return its 0-based index, or -1."""
    bits = bits[:]
    if random.random() < probability:
        position = random.randrange(len(bits))
        bits[position] ^= 1
        return bits, position
    return bits, -1


def process_file(filename: str, block_size: int, error_probability: float) -> tuple:
    """Encode, damage, correct, and write the recovered bytes."""
    original = Path(filename).read_bytes()
    original_bits = bytes_to_bits(original)
    blocks = split_blocks(original_bits, block_size)
    encoded_blocks = [hamming_encode(block) for block in blocks]

    transmitted_blocks = []
    error_blocks = []
    for block_number, block in enumerate(encoded_blocks, 1):
        transmitted, error_position = transmit(block, error_probability)
        transmitted_blocks.append(transmitted)
        if error_position != -1:
            # Sheet prints the bit as a 1-based index inside the codeword.
            error_blocks.append((block_number, error_position + 1))

    decoded_bits: list[int] = []
    detected_errors = 0
    corrected_errors = 0
    for block in transmitted_blocks:
        data, syndrome, corrected = hamming_decode(block)
        if syndrome != 0:
            detected_errors += 1
        if corrected:
            corrected_errors += 1
        decoded_bits.extend(data)

    decoded_bits = decoded_bits[: len(original_bits)]
    recovered = bits_to_bytes(decoded_bits)[: len(original)]
    output_file = f"recovered_sample_{block_size}.bin"
    Path(output_file).write_bytes(recovered)
    return len(blocks), len(error_blocks), detected_errors, corrected_errors, error_blocks, output_file


def bits_of(word: str) -> list[int]:
    return [int(ch) for ch in word.strip()]


def show_word(title: str, word: str) -> None:
    """Decode one codeword. Leftmost bit is position 1."""
    received = bits_of(word)
    data, syndrome, corrected = hamming_decode(received)
    print(f"\n{title}")
    print("Received:     ", word)
    print("Syndrome:     ", syndrome, "(0 means no error)")
    if corrected:
        fixed = received[:]
        fixed[syndrome - 1] ^= 1
        print("Error position:", syndrome)
        print("Corrected:    ", "".join(map(str, fixed)))
    print("Data bits:    ", "".join(map(str, data)))


def worked_example() -> None:
    """Theory example: 7 data bits 1011001, even parity, then flip bit 6."""
    data = bits_of("1011001")
    code = hamming_encode(data)
    print("Worked example  data 1011001")
    print("Codeword (position 1 on the left):", "".join(map(str, code)))
    damaged = code[:]
    damaged[5] ^= 1  # position 6
    _data, syndrome, _corrected = hamming_decode(damaged)
    print("After flipping position 6:        ", "".join(map(str, damaged)))
    print("Syndrome (should be 6):           ", syndrome)


def observation_questions() -> None:
    print("\nObservation questions")
    show_word("Q1  7-bit code 1011010", "1011010")
    show_word("Q2  9-bit code 101100111", "101100111")


def main() -> None:
    print("Experiment 4: Hamming code")
    worked_example()
    observation_questions()

    filename = sys.argv[1] if len(sys.argv) > 1 else ""
    if not filename:
        # A short stand-in so the block table still runs without sample.pdf.
        sample = Path("hamming_sample.bin")
        sample.write_bytes(b"Hamming code sample block data for the lab.\n" * 20)
        filename = str(sample)
        print(f"\nNo file given. Using {filename}")
    error_probability = 0.1
    print(f"\nFile: {filename}    error probability: {error_probability}")
    print(f"{'Sr':<6}{'Frame':<8}{'Blocks':<12}{'With error'}")
    for serial_no, frame_size in enumerate((16, 32), 1):
        total, errors, detected, corrected, error_blocks, out = process_file(
            filename, frame_size, error_probability
        )
        print()
        print("Frame size:", frame_size)
        print("Total blocks:", total)
        print("Blocks with error:", errors)
        print("Errors detected:", detected)
        print("Errors corrected:", corrected)
        print("Recovered file:", out)
        print("First error blocks:")
        for block, bit in error_blocks[:20]:
            print(f"  Block {block} -> bit {bit}")
        print(f"{serial_no:<6}{frame_size:<8}{total:<12}{errors}")


if __name__ == "__main__":
    main()
