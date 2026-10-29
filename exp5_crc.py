"""Experiment 5: CRC error detection.

Sender appends the modulo-2 remainder. Receiver divides again.
Remainder 0 means no detected error.

Run:
  python exp5_crc.py
  python exp5_crc.py --ask
  python exp5_crc.py --file exp2_sample.txt
  python exp5_crc.py --image some.png
"""

from __future__ import annotations

import sys
from pathlib import Path


def xor_div(data: str, generator: str) -> str:
    """Modulo-2 division. Returns the remainder of length len(generator) - 1."""
    if not generator or generator[0] != "1":
        raise ValueError("generator must be a binary string starting with 1")
    if any(bit not in "01" for bit in data + generator):
        raise ValueError("data and generator must be binary")
    width = len(generator)
    register = list(data + "0" * (width - 1))
    for i in range(len(register) - width + 1):
        if register[i] != "1":
            continue
        for j in range(width):
            register[i + j] = "0" if register[i + j] == generator[j] else "1"
    return "".join(register[-(width - 1) :])


def check(received: str, generator: str) -> str:
    """Divide an already-encoded word. Do not append extra zeros."""
    width = len(generator)
    register = list(received)
    if len(register) < width:
        return received.zfill(width - 1)
    for i in range(len(register) - width + 1):
        if register[i] != "1":
            continue
        for j in range(width):
            register[i + j] = "0" if register[i + j] == generator[j] else "1"
    return "".join(register[-(width - 1) :])


def encode(message: str, generator: str) -> tuple[str, str]:
    remainder = xor_div(message, generator)
    return remainder, message + remainder


def report(message: str, generator: str, received: str | None = None) -> None:
    remainder, sent = encode(message, generator)
    print(f"Message     : {message}")
    print(f"Generator   : {generator}")
    print(f"Remainder   : {remainder}")
    print(f"Sent data   : {sent}")
    word = received if received is not None else sent
    syndrome = check(word, generator)
    print(f"Received    : {word}")
    print(f"Check rem.  : {syndrome}")
    print("Result      :", "Valid" if int(syndrome, 2) == 0 else "Invalid")


def flip(word: str, index: int) -> str:
    bits = list(word)
    bits[index] = "1" if bits[index] == "0" else "0"
    return "".join(bits)


def file_crc(path: Path, generator: str = "110101") -> None:
    raw = path.read_bytes()
    bits = "".join(format(byte, "08b") for byte in raw)
    block = 32
    padding = (block - len(bits) % block) % block
    bits += "0" * padding
    print(f"\nFile: {path}")
    print(f"Bits: {len(bits)}   block: {block}   generator: {generator}")
    bad = 0
    shown = 0
    blocks = len(bits) // block
    for n in range(blocks):
        payload = bits[n * block : (n + 1) * block]
        remainder, sent = encode(payload, generator)
        received = sent
        # Corrupt the first block so the check is visible.
        if n == 0:
            received = flip(sent, 3)
        syndrome = check(received, generator)
        ok = int(syndrome, 2) == 0
        if not ok:
            bad += 1
        if shown < 2:
            print(f"Block {n}: remainder {remainder}  check {syndrome}  {'Valid' if ok else 'Invalid'}")
            shown += 1
    if blocks > shown:
        print(f"... {blocks - shown} more blocks")
    print(f"Blocks with a detected error: {bad} of {blocks}")


def interactive() -> None:
    message = input("Enter message: ").strip()
    generator = input("Enter generator: ").strip()
    remainder, sent = encode(message, generator)
    print("Remainder:", remainder)
    print("Sent data:", sent)
    received = input("Enter received data (blank = sent data): ").strip() or sent
    syndrome = check(received, generator)
    print("Check remainder:", syndrome)
    print("Valid" if int(syndrome, 2) == 0 else "Invalid")


def main() -> None:
    print("Experiment 5: CRC")
    if "--ask" in sys.argv:
        interactive()
        return

    print("\nCase 1: no error")
    print("Data = 100100, key = x^3 + x^2 + 1 = 1101")
    report("100100", "1101")

    print("\nCase 2: error in transmission")
    report("100100", "1101", received="100000001")

    print("\nObservation 1")
    print("M = 1010001101, divisor x^5 + x^4 + x^2 + 1 = 110101")
    report("1010001101", "110101")

    print("\nObservation 2")
    print("Data = 10011011100, polynomial x^4 + x^2 + 1 = 10101")
    report("10011011100", "10101")

    print("\nObservation 3")
    print("Data = 1101101010101101, polynomial x^5 + x^2 + 1 = 100101")
    report("1101101010101101", "100101")

    file_arg = None
    image_arg = None
    args = sys.argv[1:]
    for i, arg in enumerate(args):
        if arg == "--file" and i + 1 < len(args):
            file_arg = Path(args[i + 1])
        if arg == "--image" and i + 1 < len(args):
            image_arg = Path(args[i + 1])

    sample = Path(__file__).with_name("exp2_sample.txt")
    file_crc(file_arg or sample)
    if image_arg:
        print("\nImage as raw bytes, same CRC:")
        file_crc(image_arg)


if __name__ == "__main__":
    main()
