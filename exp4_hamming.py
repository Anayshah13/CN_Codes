"""Experiment 4: Hamming code for single-bit error detection and correction.

Even parity. Bit positions are numbered from 1. Parity bits sit at powers of 2.
The printed codeword is position n ... position 1 (same order as the lab program).

Run:
  python exp4_hamming.py                  # short viva example, then a file demo
  python exp4_hamming.py 1011001          # encode one data block
  python exp4_hamming.py --file notes.txt # 16-bit and 32-bit frames
"""

from __future__ import annotations

import random
import sys
from pathlib import Path


def hamming_encode(data: str) -> str:
    if not data or any(bit not in "01" for bit in data):
        raise ValueError("data must be a binary string")
    m = len(data)
    r = 0
    while (1 << r) < m + r + 1:
        r += 1
    n = m + r
    code = [0] * (n + 1)  # 1-based
    j = 0
    for pos in range(1, n + 1):
        if pos & (pos - 1) == 0:
            continue
        code[pos] = int(data[j])
        j += 1
    pos = 1
    while pos <= n:
        parity = 0
        for i in range(1, n + 1):
            if i & pos:
                parity ^= code[i]
        code[pos] = parity
        pos <<= 1
    return "".join(str(code[pos]) for pos in range(n, 0, -1))


def syndrome(received: str) -> int:
    n = len(received)
    code = [0] * (n + 1)
    for pos in range(1, n + 1):
        code[pos] = int(received[n - pos])
    error_position = 0
    pos = 1
    while pos <= n:
        parity = 0
        for i in range(1, n + 1):
            if i & pos:
                parity ^= code[i]
        if parity:
            error_position += pos
        pos <<= 1
    return error_position


def correct(received: str, error_position: int) -> str:
    if error_position == 0:
        return received
    bits = list(received)
    index = len(bits) - error_position
    if index < 0 or index >= len(bits):
        return received
    bits[index] = "1" if bits[index] == "0" else "0"
    return "".join(bits)


def flip_one(codeword: str) -> tuple[str, int]:
    bits = list(codeword)
    index = random.randrange(len(bits))
    bits[index] = "1" if bits[index] == "0" else "0"
    return "".join(bits), len(bits) - index


def explain_block(data: str, force_error: bool = True) -> None:
    encoded = hamming_encode(data)
    print(f"Data        : {data}")
    print(f"Hamming code: {encoded}")
    if not force_error:
        position = syndrome(encoded)
        print(f"Syndrome    : {position} (0 means no error)")
        return
    received, flipped_pos = flip_one(encoded)
    position = syndrome(received)
    fixed = correct(received, position)
    print(f"Received    : {received}  (flipped position {flipped_pos})")
    print(f"Syndrome    : {position}")
    print(f"Corrected   : {fixed}")
    print("Match       :", "yes" if fixed == encoded else "no")


def process_file(data: bytes, frame_size: int) -> tuple[int, int, int]:
    binary = "".join(format(byte, "08b") for byte in data)
    padding = (frame_size - len(binary) % frame_size) % frame_size
    binary += "0" * padding
    total_blocks = len(binary) // frame_size
    error_blocks = max(1, total_blocks // 20)
    selected = set(random.sample(range(total_blocks), min(error_blocks, total_blocks)))
    errors = 0
    corrections = 0
    shown = 0
    for block in range(total_blocks):
        start = block * frame_size
        payload = binary[start : start + frame_size]
        encoded = hamming_encode(payload)
        received = encoded
        if block in selected:
            received, _ = flip_one(encoded)
            errors += 1
        position = syndrome(received)
        corrected = correct(received, position)
        if position != 0:
            corrections += 1
        if shown < 3:
            print(f"  block {block}: data {payload}")
            print(f"           code {encoded}")
            if received != encoded:
                print(f"           rx   {received} -> {corrected}")
            shown += 1
    if total_blocks > shown:
        print(f"  ... {total_blocks - shown} more blocks")
    return total_blocks, errors, corrections


def main() -> None:
    print("Experiment 4: Hamming code (even parity, single-bit correction)")
    args = sys.argv[1:]

    if args and args[0] == "--file":
        path = Path(args[1]) if len(args) > 1 else Path(__file__).with_name("exp2_sample.txt")
    elif args and set(args[0]) <= {"0", "1"}:
        print()
        explain_block(args[0], force_error=True)
        return
    else:
        print("\nViva example")
        explain_block("1011", force_error=True)
        path = Path(__file__).with_name("exp2_sample.txt")

    if not path.exists():
        print(f"\nFile not found: {path}")
        return

    raw = path.read_bytes()
    print(f"\nFile: {path} ({len(raw)} bytes)")
    print("About 1 in 20 blocks is given a single-bit error, then corrected.")
    results = {}
    for size in (16, 32):
        print(f"\nFrame size {size}")
        results[size] = process_file(raw, size)

    print("\nFrame Size | Total Blocks | Blocks with Error | Corrections")
    for size in (16, 32):
        total, errors, corrections = results[size]
        print(f"{size:<10} | {total:<12} | {errors:<17} | {corrections}")


if __name__ == "__main__":
    main()
