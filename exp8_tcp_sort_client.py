"""Experiment 8: TCP client.

Run the server first, then open two terminals:
  python exp8_tcp_sort_client.py 1
  python exp8_tcp_sort_client.py 2

The sheet used SERVER_IP = 10.79.163.94. The default here is 127.0.0.1
so both clients can talk to a server on this PC.
Optional: python exp8_tcp_sort_client.py 1 10.79.163.94 8000
"""

from __future__ import annotations

import json
import socket
import sys


class LineReader:
    """Read one JSON object. The server ends each reply with a newline."""

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

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print("\n" + "=" * 50)
    print(f"CLIENT {client_no}")
    print("=" * 50)
    print("Connected to Server.")

    array_input = input("\nEnter array elements separated by spaces: ")
    array = list(map(int, array_input.split()))
    print("\nArray entered:", array)
    client_socket.sendall((json.dumps(array) + "\n").encode())
    print("Array sent to Server.")

    reader = LineReader(client_socket)
    response = reader.read_json()
    print("\n" + "=" * 50)
    print("CASE 1: INDIVIDUAL SORTING")
    print("=" * 50)
    print("Sorted Array:", response["individual_sorted"])

    response = reader.read_json()
    print("\n" + "=" * 50)
    print("CASE 2: MERGE AND SORT")
    print("=" * 50)
    print("Final Merged Sorted Array:", response["merged_sorted"])

    client_socket.close()
    print("\nConnection closed.")


if __name__ == "__main__":
    main()
