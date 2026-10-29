"""Experiment 9: UDP group chat client.

Run the server first, then:
  python exp9_udp_chat_client.py
  python exp9_udp_chat_client.py 127.0.0.1 5010

Type bye to leave.
"""

from __future__ import annotations

import socket
import sys
import threading

HOST = sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 5010
SERVER = (HOST, PORT)


def receive_messages(sock: socket.socket, stop: threading.Event) -> None:
    while not stop.is_set():
        try:
            data, _ = sock.recvfrom(1024)
        except OSError:
            break
        print("\n" + data.decode(errors="replace").strip())
        print("You: ", end="", flush=True)


def main() -> None:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("=== UDP GROUP CHAT CLIENT ===")
    username = input("Enter your username to join: ").strip() or "user"
    sock.sendto(username.encode(), SERVER)
    print(f"Welcome to the room, {username}! Type 'bye' to quit.\n")

    stop = threading.Event()
    worker = threading.Thread(target=receive_messages, args=(sock, stop), daemon=True)
    worker.start()

    try:
        while True:
            message = input("You: ")
            sock.sendto(message.encode(), SERVER)
            if message.strip().lower() == "bye":
                print("Leaving chat room...")
                break
    except (KeyboardInterrupt, EOFError):
        sock.sendto(b"bye", SERVER)
        print("\nLeaving chat room...")
    finally:
        stop.set()
        sock.close()


if __name__ == "__main__":
    main()
