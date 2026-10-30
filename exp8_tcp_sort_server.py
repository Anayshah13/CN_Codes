"""Experiment 8: TCP server.

Two clients each send an integer array.
Case 1: selection-sort that client's array and send it back.
Case 2: merge both arrays, selection-sort the merge, send it to both.

The lab server address was 10.79.163.94. This copy listens on
0.0.0.0:8000 so both clients can run on this machine at 127.0.0.1.

Run this first:
  python exp8_tcp_sort_server.py
"""

from __future__ import annotations

import json
import socket
import threading

HOST = "0.0.0.0"
PORT = 8000

# Arrays arrive on two threads. The lock is only for this shared dict.
client_arrays: dict[int, list[int]] = {}
lock = threading.Lock()
both_received = threading.Event()


class LineReader:
    """TCP does not keep message boundaries.

    The server writes one JSON object plus a newline. This reads until
    that newline, even if recv returns only part of it.
    """

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
    """Pass i puts the minimum of the unsorted tail into index i.

    Every comparison is printed so a pass can be explained out loud.
    """
    print("\n" + "=" * 60)
    print("SELECTION SORT:", name)
    print("=" * 60)
    print("Original Array:", arr)
    n = len(arr)
    for i in range(n - 1):
        min_index = i
        print("\n" + "-" * 40)
        print("PASS", i + 1)
        print("-" * 40)
        print("Starting Array:", arr)
        print("Assume minimum =", arr[min_index])
        print("Minimum index =", min_index)
        for j in range(i + 1, n):
            print("Compare", arr[j], "with", arr[min_index])
            if arr[j] < arr[min_index]:
                min_index = j
                print("New minimum found:", arr[min_index], "at index", min_index)
        if min_index != i:
            print("Swap", arr[i], "and", arr[min_index])
            arr[i], arr[min_index] = arr[min_index], arr[i]
        else:
            print("No swap required.")
        print("Array after Pass", i + 1, ":", arr)
    print("\nFinal Sorted Array:", arr)
    print("C" * 60)
    return arr


def handle_client(client_socket: socket.socket, address, client_number: int) -> None:
    reader = LineReader(client_socket)
    try:
        array = reader.read_json()
        if not isinstance(array, list):
            client_socket.close()
            return
        array = [int(x) for x in array]
        print("\nClient", client_number, "connected.")
        print("Client Address:", address)
        print("\nArray received from Client", client_number)
        print("Array:", array)

        with lock:
            client_arrays[client_number] = array
            if len(client_arrays) == 2:
                both_received.set()
        print("\nClient", client_number, "array stored.")
        print("Waiting for the other client...")
        both_received.wait()

        # Case 1. Sort a copy so the original list is still available to merge.
        print("\n\n" + "#" * 70)
        print("CASE 1: INDIVIDUAL SORTING")
        print("#" * 70)
        individual_sorted = selection_sort(array.copy(), "Client " + str(client_number))
        send_json(client_socket, {"case": 1, "individual_sorted": individual_sorted})

        # Case 2. Both threads sort the same merge. The prints interleave,
        # which is what two clients produce in the lab.
        print("\n\n" + "#" * 70)
        print("CASE 2: MERGE BOTH ARRAYS AND SORT")
        print("#" * 70)
        with lock:
            array1 = client_arrays[1]
            array2 = client_arrays[2]
            merged = array1 + array2
        print("\nClient 1 Array:", array1)
        print("Client 2 Array:", array2)
        print("\nMerged Array:")
        print(merged)
        final_sorted = selection_sort(merged.copy(), "MERGED ARRAY")
        send_json(client_socket, {"case": 2, "merged_sorted": final_sorted})
        print("\nClient", client_number, "connection closed.")
    finally:
        client_socket.close()


def main() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen(2)
    print("\n" + "=" * 70)
    print("TCP SORTING SERVER")
    print("=" * 70)
    print("Server started successfully.")
    print("Protocol: TCP")
    print("Algorithm: Selection Sort")
    print("Port:", PORT)
    print("Waiting for 2 clients...")
    print("=" * 70)

    threads = []
    client_count = 0
    while client_count < 2:
        client_socket, address = server_socket.accept()
        client_count += 1
        print("\nClient", client_count, "accepted.")
        thread = threading.Thread(
            target=handle_client,
            args=(client_socket, address, client_count),
            daemon=True,
        )
        thread.start()
        threads.append(thread)
    for thread in threads:
        thread.join()
    server_socket.close()


if __name__ == "__main__":
    main()
