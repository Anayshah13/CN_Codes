"""Experiment 8: TCP client for the selection-sort server.

Run the server first, then:
  python exp8_tcp_sort_client.py 1
  python exp8_tcp_sort_client.py 2

Optional: python exp8_tcp_sort_client.py 1 127.0.0.1 8000
"""

from __future__ import annotations

import json
import socket
import sys


class LineReader:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buffer = b""

    def read_json(self):
        while b"\n" not in self.buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("server closed the connection")
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b"\n", 1)
        return json.loads(line.decode())


def main() -> None:
    client_no = sys.argv[1] if len(sys.argv) > 1 else "1"
    host = sys.argv[2] if len(sys.argv) > 2 else "127.0.0.1"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 8000

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print("=" * 50)
    print(f"CLIENT {client_no}")
    print("=" * 50)
    print(f"Connected to {host}:{port}")

    raw = input("\nEnter array elements separated by spaces: ").strip()
    array = [int(part) for part in raw.split()]
    print("Array entered:", array)
    sock.sendall((json.dumps(array) + "\n").encode())
    print("Array sent to Server.")

    reader = LineReader(sock)
    case1 = reader.read_json()
    print("\n" + "=" * 50)
    print("CASE 1: INDIVIDUAL SORTING")
    print("=" * 50)
    print("Sorted Array:", case1["individual_sorted"])

    case2 = reader.read_json()
    print("\n" + "=" * 50)
    print("CASE 2: MERGE AND SORT")
    print("=" * 50)
    print("Final Merged Sorted Array:", case2["merged_sorted"])

    sock.close()
    print("\nConnection closed.")


if __name__ == "__main__":
    main()
