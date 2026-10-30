"""Experiment 9: UDP client.

Creates a datagram socket, sends "Hello Server!" to port 8080, and
prints the reply. There is no connect() call.

Run the server first.
  python exp9_udp_client.py
Blank IP means this machine (127.0.0.1).
"""

from __future__ import annotations

import socket


def main() -> None:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_ip = input("Enter server IP address: ").strip() or "127.0.0.1"
    server_address = (server_ip, 8080)

    msg = "Hello Server!"
    client_socket.sendto(msg.encode(), server_address)
    print("Message sent to server.")

    data, addr = client_socket.recvfrom(1024)
    print("Server says:", data.decode())
    print("Reply came from:", addr)
    client_socket.close()


if __name__ == "__main__":
    main()
