"""Experiment 2: Framing.

Task 1 reads a PDF, turns the text into ASCII and binary, then frames it
with character count, bit stuffing, and byte stuffing.

Task 2 frames the token stream
    A B ESC FLAG C D FLAG E ESC F
with character stuffing, bit stuffing, and PPP-style byte stuffing.

Run: python exp2_framing.py
"""

from __future__ import annotations

import math
import random
from pathlib import Path

# HDLC flag. A 0 is stuffed after five 1s so this pattern stays reserved.
FLAG_BITS = "01111110"
# Task 1 uses the word ESC as the escape token inside the text.
ESC = "ESC"
FLAG = "FLAG"


def read_pdf(filename: str) -> str:
    """Pull the text out of every page. The lab import is PyPDF2; pypdf is the same API."""
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        from pypdf import PdfReader
    reader = PdfReader(filename)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text


def text_to_ascii(text: str) -> list[int]:
    """Each character becomes its ASCII code."""
    return [ord(c) for c in text]


def ascii_to_binary(ascii_values: list[int]) -> str:
    """Each ASCII code becomes 8 bits."""
    return "".join(format(value, "08b") for value in ascii_values)


def character_count_framing(text: str) -> None:
    """Frame = count, then that many characters.

    The count is random from 2^0 to 2^16 (1 to 65536). Only the first
    three frames are printed; a PDF would otherwise flood the screen.
    """
    print("\nCharacter Count Framing (first 3 frames)")
    frames = []
    i = 0
    while i < len(text):
        count = random.randint(1, min(65536, len(text) - i))
        frames.append((count, text[i : i + count]))
        i += count
    print("Total frames:", len(frames))
    for number, (count, frame) in enumerate(frames[:3], 1):
        preview = frame[:50] + ("..." if len(frame) > 50 else "")
        print(f"\nFrame {number}")
        print("Count:", count)
        print("Data:", preview)


def bit_stuff(bits: str) -> str:
    """Insert a 0 after every run of five 1s."""
    stuffed = ""
    ones = 0
    for bit in bits:
        stuffed += bit
        if bit == "1":
            ones += 1
            if ones == 5:
                stuffed += "0"
                ones = 0
        else:
            ones = 0
    return stuffed


def pad_to_128(bits: str) -> str:
    """Pad with 1 followed by zeros until the length is a multiple of 128."""
    extra = (128 - len(bits) % 128) % 128
    if extra == 0:
        return bits
    return bits + "1" + ("0" * (extra - 1))


def bit_stuffing_frames(binary: str, size: int) -> None:
    """Fixed-length frames. Size should be a power of 2 (64, 128, 256)."""
    print("\nBit stuffing (first 3 frames)")
    prepared = pad_to_128(binary)
    stuffed = bit_stuff(prepared)
    frames = [stuffed[i : i + size] for i in range(0, len(stuffed), size)]
    print("Total frames:", len(frames))
    for number, frame in enumerate(frames[:3], 1):
        print(f"\nFrame {number}")
        print(FLAG_BITS + frame + FLAG_BITS)


def byte_stuffing(text: str) -> None:
    """Variable-length byte stuffing on the characters of the file.

    ESC is inserted at a random gap between 1 and 65536, then any ESC
    or FLAG already in the data is prefixed with another ESC.
    """
    print("\nByte stuffing (first 3 frames)")
    data = list(text)
    if data:
        interval = random.randint(1, min(65536, len(data)))
        pos = interval
        while pos < len(data):
            data.insert(pos, ESC)
            pos += interval + 1
    stuffed: list[str] = []
    for ch in data:
        if ch == ESC or ch == FLAG:
            stuffed.append(ESC)
        stuffed.append(ch)
    frame_size = 30
    frames = [stuffed[i : i + frame_size] for i in range(0, len(stuffed), frame_size)]
    print("Total frames:", len(frames))
    for number, frame in enumerate(frames[:3], 1):
        print(f"\nFrame {number}")
        print("FLAG", " ".join(frame), "FLAG")


def observation(binary_len: int) -> None:
    """Flag overhead for frame sizes 64, 128, and 256.

    Two flags are 16 bits. Overhead % = (frames * 16) / original bits.
    """
    print("\nObservation")
    print(f"{'Frame':<10}{'No Frames':<15}{'Overhead':<15}{'Overhead %'}")
    for size in (64, 128, 256):
        frames = math.ceil(binary_len / size)
        overhead = frames * 16
        percent = (overhead / binary_len) * 100 if binary_len else 0
        print(f"{size:<10}{frames:<15}{overhead:<15}{percent:.2f}")


def task1() -> None:
    filename = input("Enter PDF filename: ").strip()
    text = read_pdf(filename)
    print("\nPDF loaded")
    print("Characters:", len(text))
    ascii_values = text_to_ascii(text)
    print("\nFirst 10 ASCII values:")
    print(ascii_values[:10])
    binary = ascii_to_binary(ascii_values)
    print("\nFirst 64 binary bits:")
    print(binary[:64])
    character_count_framing(text)
    size = int(input("\nEnter frame size (64/128/256): ").strip())
    bit_stuffing_frames(binary, size)
    byte_stuffing(text)
    observation(len(binary))


# --- Task 2: the token stream from the sheet ---

TOKENS = ["A", "B", "ESC", "FLAG", "C", "D", "FLAG", "E", "ESC", "F"]


def character_stuffing(data: list[str]) -> list[str]:
    """FLAG ... FLAG. ESC or FLAG inside the data is prefixed with ESC."""
    stuffed = [FLAG]
    for ch in data:
        if ch in (ESC, FLAG):
            stuffed.append(ESC)
        stuffed.append(ch)
    stuffed.append(FLAG)
    return stuffed


def task2_bit_stuffing(data: list[str]) -> tuple[str, str, str]:
    """ESC is byte 0x1B, FLAG is byte 0x7E. Stuff a 0 after five 1s, then add flags."""
    byte_data = []
    for ch in data:
        if ch == ESC:
            byte_data.append(0x1B)
        elif ch == FLAG:
            byte_data.append(0x7E)
        else:
            byte_data.append(ord(ch))
    binary_data = "".join(format(b, "08b") for b in byte_data)
    stuffed = bit_stuff(binary_data)
    final_frame = FLAG_BITS + stuffed + FLAG_BITS
    return binary_data, stuffed, final_frame


def task2_byte_stuffing(data: list[str]) -> list[int]:
    """PPP byte stuffing.

    Frame starts and ends with 0x7E. If a byte is 0x7E or 0x7D, send 0x7D
    and then that byte XOR 0x20.
    """
    stuffed = [0x7E]
    for ch in data:
        if ch == ESC:
            byte = 0x1B
        elif ch == FLAG:
            byte = 0x7E
        else:
            byte = ord(ch)
        if byte in (0x7E, 0x7D):
            stuffed.append(0x7D)
            stuffed.append(byte ^ 0x20)
        else:
            stuffed.append(byte)
    stuffed.append(0x7E)
    return stuffed


def task2() -> None:
    print("Data:", " ".join(TOKENS))
    char_frame = character_stuffing(TOKENS)
    print("\nCharacter stuffing:")
    print(" ".join(char_frame))
    binary, stuffed_bits, final_bits = task2_bit_stuffing(TOKENS)
    print("\nBinary data:")
    print(binary)
    print("\nBit stuffed data:")
    print(stuffed_bits)
    print("\nFinal bit frame:")
    print(final_bits)
    byte_frame = task2_byte_stuffing(TOKENS)
    print("\nByte stuffing (hex):")
    print(" ".join(f"{b:02X}" for b in byte_frame))


def main() -> None:
    print("Experiment 2")
    print("1. Task 1 — frame a PDF")
    print("2. Task 2 — A B ESC FLAG C D FLAG E ESC F")
    choice = input("Enter: ").strip()
    if choice == "2":
        task2()
    else:
        task1()


if __name__ == "__main__":
    main()
