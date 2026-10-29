"""Experiment 8: TCP server. Two clients each send an integer array.

Case 1: selection-sort that client's array and send it back.
Case 2: merge both arrays, selection-sort the merge, send it to both.

Run the server first:
  python exp8_tcp_sort_server.py
Then in two other terminals:
  python exp8_tcp_sort_client.py 1
  python exp8_tcp_sort_client.py 2
"""

from __future__ import annotations

import json
import socket
import threading

HOST = "0.0.0.0"
PORT = 8000

client_arrays: dict[int, list[int]] = {}
merged_sorted: list[int] | None = None
lock = threading.Lock()
print_lock = threading.Lock()
both_received = threading.Event()


class LineReader:
    def __init__(self, sock: socket.socket) -> None:
        self.sock = sock
        self.buffer = b""

    def read_json(self):
        while b"\n" not in self.buffer:
            chunk = self.sock.recv(4096)
            if not chunk:
                return None
            self.buffer += chunk
        line, self.buffer = self.buffer.split(b"\n", 1)
        if not line:
            return None
        return json.loads(line.decode())


def send_json(sock: socket.socket, payload: dict) -> None:
    sock.sendall((json.dumps(payload) + "\n").encode())


def selection_sort(arr: list[int], name: str) -> list[int]:
    lines = [f"\n{'=' * 60}", f"SELECTION SORT: {name}", "=" * 60, f"Original Array: {arr}"]
    n = len(arr)
    for i in range(n - 1):
        min_index = i
        lines.append(f"\nPASS {i + 1}")
        lines.append(f"Starting Array: {arr}")
        lines.append(f"Assume minimum = {arr[min_index]} at index {min_index}")
        for j in range(i + 1, n):
            lines.append(f"Compare {arr[j]} with {arr[min_index]}")
            if arr[j] < arr[min_index]:
                min_index = j
                lines.append(f"New minimum found: {arr[min_index]} at index {min_index}")
        if min_index != i:
            lines.append(f"Swap {arr[i]} and {arr[min_index]}")
            arr[i], arr[min_index] = arr[min_index], arr[i]
        else:
            lines.append("No swap required.")
        lines.append(f"Array after Pass {i + 1}: {arr}")
    lines.append(f"\nFinal Sorted Array: {arr}")
    with print_lock:
        print("\n".join(lines))
    return arr


def handle_client(client_socket: socket.socket, address, client_number: int) -> None:
    global merged_sorted
    reader = LineReader(client_socket)
    try:
        array = reader.read_json()
        if not isinstance(array, list):
            print(f"Client {client_number} sent no array.")
            return
        array = [int(x) for x in array]
        print(f"\nClient {client_number} connected from {address}")
        print(f"Array received: {array}")

        with lock:
            client_arrays[client_number] = array
            if len(client_arrays) == 2:
                both_received.set()

        print(f"Client {client_number} stored. Waiting for the other client...")
        both_received.wait()

        individual = selection_sort(array.copy(), f"Client {client_number}")
        send_json(client_socket, {"case": 1, "individual_sorted": individual})

        with lock:
            if merged_sorted is None:
                merged = client_arrays[1] + client_arrays[2]
                print(f"\nClient 1 Array: {client_arrays[1]}")
                print(f"Client 2 Array: {client_arrays[2]}")
                print(f"Merged Array: {merged}")
                merged_sorted = selection_sort(merged.copy(), "MERGED ARRAY")
            result = merged_sorted

        send_json(client_socket, {"case": 2, "merged_sorted": result})
        print(f"Client {client_number} connection closed.")
    except (OSError, json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Client {client_number} error: {exc}")
    finally:
        client_socket.close()


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(2)
    print("=" * 70)
    print("TCP SORTING SERVER")
    print("=" * 70)
    print("Protocol: TCP")
    print("Algorithm: Selection Sort")
    print(f"Listening on {HOST}:{PORT}")
    print("Waiting for 2 clients...")

    threads = []
    try:
        for number in (1, 2):
            client_socket, address = server.accept()
            print(f"\nClient {number} accepted.")
            thread = threading.Thread(
                target=handle_client,
                args=(client_socket, address, number),
                daemon=True,
            )
            thread.start()
            threads.append(thread)
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.close()
        print("Server closed.")


if __name__ == "__main__":
    main()
