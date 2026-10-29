"""Experiment 2: Framing techniques.

Aim: Character count, bit stuffing, and byte stuffing.
Run: python exp2_framing.py
     python exp2_framing.py path\\to\\file.txt
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

FLAG = "01111110"
ESC = "10101010"


def to_binary(text: str) -> str:
    return "".join(format(ord(ch), "08b") for ch in text)


def show_preprocessing(text: str) -> str:
    print("\nPreprocessing")
    print(f"Characters: {len(text)}")
    preview = text[:80]
    print("Text:", preview + ("..." if len(text) > 80 else ""))
    ascii_codes = [ord(ch) for ch in preview]
    print("ASCII :", ascii_codes)
    binary = to_binary(text)
    print("Binary length:", len(binary), "bits")
    print("Binary preview:", binary[:64] + ("..." if len(binary) > 64 else ""))
    return binary


def character_count(text: str) -> None:
    """Each frame starts with a count of the following characters (1 to 16)."""
    i = 0
    frames = 0
    overhead_chars = 0
    print("\nCharacter-count frames  (count is the number of data characters)")
    while i < len(text):
        count = random.randint(1, min(16, len(text) - i))
        payload = text[i : i + count]
        frames += 1
        overhead_chars += 1
        print(f"Frame {frames}: [{count}] {payload!r}")
        i += count
    overhead_bits = overhead_chars * 8
    data_bits = len(text) * 8
    percent = (overhead_bits / data_bits) * 100 if data_bits else 0
    print(f"Frames: {frames}")
    print(f"Overhead: {overhead_bits} bits ({percent:.2f}%)")


def pad_to_multiple(binary: str, multiple: int = 128) -> tuple[str, int]:
    """Pad with 1 followed by zeros so the bit string length is a multiple of 128."""
    extra = (multiple - (len(binary) % multiple)) % multiple
    if extra == 0:
        return binary, 0
    pad = "1" + ("0" * (extra - 1))
    return binary + pad, extra


def stuff_bits(payload: str) -> tuple[str, int]:
    stuffed = []
    ones = 0
    extra = 0
    for bit in payload:
        stuffed.append(bit)
        if bit == "1":
            ones += 1
            if ones == 5:
                stuffed.append("0")
                extra += 1
                ones = 0
        else:
            ones = 0
    return "".join(stuffed), extra


def bit_stuffing(binary: str, frame_size: int) -> None:
    if frame_size <= 0 or (frame_size & (frame_size - 1)) != 0:
        print("Frame size must be a power of 2 (for example 8, 16, 32, 64, 128).")
        return

    prepared, pad_bits = pad_to_multiple(binary, 128)
    print(f"\nBit stuffing   flag={FLAG}   frame size={frame_size} bits")
    print(f"File padded by {pad_bits} bits so length is a multiple of 128.")

    stuffed_total = 0
    flag_bits = 0
    frame_no = 0
    for start in range(0, len(prepared), frame_size):
        payload = prepared[start : start + frame_size]
        stuffed, extra = stuff_bits(payload)
        stuffed_total += extra
        flag_bits += 16
        frame_no += 1
        print(f"Frame {frame_no}: {FLAG} {stuffed} {FLAG}   (stuffed {extra} bits)")

    overhead = stuffed_total + pad_bits + flag_bits
    percent = (overhead / len(binary)) * 100 if binary else 0
    print(f"Frames: {frame_no}")
    print(f"Overhead: {overhead} bits ({percent:.2f}%)")


def byte_stuffing(binary: str) -> None:
    bytes_ = [binary[i : i + 8] for i in range(0, len(binary), 8)]
    if bytes_ and len(bytes_[-1]) < 8:
        bytes_[-1] = bytes_[-1].ljust(8, "0")

    # Drop ESC into the stream at random gaps so stuffing is visible.
    stuffed_source = []
    inserted = 0
    index = 0
    while index < len(bytes_):
        gap = random.randint(1, min(16, len(bytes_) - index))
        stuffed_source.extend(bytes_[index : index + gap])
        index += gap
        if index < len(bytes_) and random.random() < 0.35:
            stuffed_source.append(ESC)
            inserted += 1

    print(f"\nByte stuffing   FLAG={FLAG}   ESC={ESC}")
    print(f"ESC bytes inserted at random gaps: {inserted}")

    i = 0
    frame_no = 0
    flag_count = 0
    esc_count = 0
    while i < len(stuffed_source):
        size = random.randint(1, min(8, len(stuffed_source) - i))
        chunk = stuffed_source[i : i + size]
        body = []
        frame_no += 1
        flag_count += 2
        for byte in chunk:
            if byte in (FLAG, ESC):
                body.append(ESC)
                esc_count += 1
            body.append(byte)
        print(f"Frame {frame_no}: {FLAG} {' '.join(body)} {FLAG}")
        i += size

    overhead = (flag_count + esc_count) * 8
    percent = (overhead / len(binary)) * 100 if binary else 0
    print(f"Frames: {frame_no}")
    print(f"Overhead: {overhead} bits ({percent:.2f}%)")


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).with_name("exp2_sample.txt")
    if not path.exists():
        print(f"File not found: {path}")
        return
    text = path.read_text(encoding="utf-8", errors="replace")
    if not text:
        print("File is empty.")
        return

    print("Experiment 2: Framing")
    print(f"Input file: {path}")
    binary = show_preprocessing(text)

    while True:
        print("\nMethod:")
        print("1. Character count")
        print("2. Bit stuffing")
        print("3. Byte stuffing")
        print("4. Exit")
        choice = input("Enter: ").strip()
        if choice == "1":
            character_count(text)
        elif choice == "2":
            raw = input("Enter frame size (power of 2, e.g. 64): ").strip()
            if not raw.isdigit():
                print("Enter a number.")
                continue
            bit_stuffing(binary, int(raw))
        elif choice == "3":
            byte_stuffing(binary)
        elif choice == "4":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    main()
