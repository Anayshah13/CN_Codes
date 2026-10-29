"""Experiment 9: UDP group chat server.

The first datagram from an address is that client's username.
Later datagrams are broadcast to every other client.
A client leaves by sending bye.

Run: python exp9_udp_chat_server.py
Then start two or more copies of exp9_udp_chat_client.py
"""

from __future__ import annotations

import socket

HOST = "0.0.0.0"
PORT = 5010


def main() -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server.bind((HOST, PORT))
    clients: dict[tuple[str, int], str] = {}

    print("=== UDP GROUP CHAT SERVER ===")
    print(f"Server is running on port {PORT}...")
    print("Press Ctrl+C to stop.")

    try:
        while True:
            data, address = server.recvfrom(1024)
            message = data.decode(errors="replace").strip()
            if not message:
                continue

            if address not in clients:
                clients[address] = message
                print(f"[JOIN] {message} {address} connected.")
                alert = f"\n*** {message} has joined the chat room! ***".encode()
                for other in clients:
                    if other != address:
                        server.sendto(alert, other)
                continue

            username = clients[address]
            if message.lower() == "bye":
                print(f"[LEAVE] {username} {address} disconnected.")
                del clients[address]
                alert = f"\n*** {username} has left the chat room. ***".encode()
                for other in clients:
                    server.sendto(alert, other)
                continue

            print(f"[{username}]: {message}")
            outgoing = f"\n[{username}]: {message}".encode()
            for other in list(clients):
                if other != address:
                    server.sendto(outgoing, other)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
