"""Experiment 5: CRC error detection.

Sender appends the modulo-2 remainder. Receiver divides the whole word
again. A remainder that is all zeros means no detected error.

The division matches the lab code: findXor drops the leading bit, and
mod2div pulls the next data bit down after each XOR.

Run:
  python exp5_crc.py                  # textbook cases and observation questions
  python exp5_crc.py --ask            # type a message and a key
  python exp5_crc.py --file notes.txt
  python exp5_crc.py --image photo.png
"""

from __future__ import annotations

import sys
from pathlib import Path


def find_xor(a: str, b: str) -> str:
    """XOR two equal-length strings and drop the leading bit (the quotient bit)."""
    result = ""
    for i in range(1, len(b)):
        result += "0" if a[i] == b[i] else "1"
    return result


def mod2div(dividend: str, divisor: str) -> str:
    """Modulo-2 division. The returned remainder has len(divisor) - 1 bits."""
    pick = len(divisor)
    tmp = dividend[0:pick]
    while pick < len(dividend):
        if tmp[0] == "1":
            tmp = find_xor(divisor, tmp) + dividend[pick]
        else:
            tmp = find_xor("0" * pick, tmp) + dividend[pick]
        pick += 1
    if tmp[0] == "1":
        tmp = find_xor(divisor, tmp)
    else:
        tmp = find_xor("0" * pick, tmp)
    return tmp


def encode_data(data: str, key: str) -> str:
    """Append k-1 zeros, divide, stick the remainder on the original data."""
    padded = data + "0" * (len(key) - 1)
    remainder = mod2div(padded, key)
    return data + remainder


def receiver(code: str, key: str) -> int:
    """1 if the remainder has no 1-bit, else 0."""
    remainder = mod2div(code, key)
    return 1 if "1" not in remainder else 0


def show(data: str, key: str, received: str | None = None) -> None:
    code = encode_data(data, key)
    print(f"Data:         {data}")
    print(f"Key:          {key}")
    print(f"Remainder:    {code[len(data):]}")
    print(f"Encoded data: {code}")
    word = received if received is not None else code
    print(f"Checked word: {word}")
    if receiver(word, key):
        print("Data is correct (no errors detected)")
    else:
        print("Data is incorrect (error detected)")
    print()


def file_crc(path: Path, block_bits: int, key: str) -> None:
    """CRC each block of a text or image file, then verify. Block 0 is flipped."""
    raw = path.read_bytes()
    bits = "".join(format(byte, "08b") for byte in raw)
    pad = (block_bits - len(bits) % block_bits) % block_bits
    bits += "0" * pad
    print(f"\nFile: {path}")
    print(f"Bits: {len(bits)}   block: {block_bits}   key: {key}")
    bad = 0
    blocks = len(bits) // block_bits
    for n in range(blocks):
        payload = bits[n * block_bits : (n + 1) * block_bits]
        code = encode_data(payload, key)
        checked = code
        if n == 0 and code:
            # Flip one bit so the receiver side of the exercise is visible.
            flipped = "0" if code[3] == "1" else "1"
            checked = code[:3] + flipped + code[4:]
        ok = receiver(checked, key)
        if not ok:
            bad += 1
        if n < 2:
            print(f"Block {n}: remainder {code[len(payload):]}  {'correct' if ok else 'error detected'}")
    if blocks > 2:
        print(f"... {blocks - 2} more blocks")
    print(f"Blocks with a detected error: {bad} of {blocks}")


def interactive() -> None:
    data = input("Enter data in binary format: ").strip()
    key = input("Enter key in binary format: ").strip()
    print("\nSender side")
    code = encode_data(data, key)
    print("Data:", data)
    print("Key:", key)
    print("Remainder:", code[len(data) :])
    print("Encoded data:", code)
    print("\nReceiver side")
    if receiver(code, key):
        print("Data is correct (no errors detected)")
    else:
        print("Data is incorrect (error detected)")


def main() -> None:
    print("Experiment 5: CRC")
    if "--ask" in sys.argv:
        interactive()
        return

    print("Case 1: no error")
    print("Data = 100100, key = x^3 + x^2 + 1 = 1101")
    show("100100", "1101")

    print("Case 2: error in transmission, received 100000001")
    show("100100", "1101", received="100000001")

    print("Observation 1")
    print("M = 1010001101, divisor x^5 + x^4 + x^2 + 1 = 110101")
    show("1010001101", "110101")

    print("Observation 2")
    print("Data = 10011011100, polynomial x^4 + x^2 + 1 = 10101")
    show("10011011100", "10101")

    print("Observation 3")
    print("Data = 1101101010101101, polynomial x^5 + x^2 + 1 = 100101")
    show("1101101010101101", "100101")

    args = sys.argv[1:]
    file_arg = None
    image_arg = None
    for i, arg in enumerate(args):
        if arg == "--file" and i + 1 < len(args):
            file_arg = Path(args[i + 1])
        if arg == "--image" and i + 1 < len(args):
            image_arg = Path(args[i + 1])
    sample = Path(__file__).with_name("exp2_sample.txt")
    if file_arg or sample.exists():
        file_crc(file_arg or sample, 32, "110101")
    if image_arg:
        print("\nImage as raw bytes:")
        file_crc(image_arg, 32, "110101")


if __name__ == "__main__":
    main()
