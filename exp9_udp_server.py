"""Experiment 9: UDP server.

UDP does not connect. socket() creates the socket, bind() chooses the
port, recvfrom() reads one datagram and the sender's address, and
sendto() replies to that address.

The sheet's listing forgot the bind and unpacked recvfrom into one
variable. Both are fixed here. Port is 8080, as in the sheet.

Run: python exp9_udp_server.py
Then: python exp9_udp_client.py
"""

from __future__ import annotations

import socket


def main() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("UDP socket created.")
    server_socket.bind(("0.0.0.0", 8080))
    print("Socket bound to port 8080.")

    # recvfrom returns (bytes, (ip, port)). The port is how we reply.
    data, client_addr = server_socket.recvfrom(1024)
    print("Received from client:", data.decode())

    response = "Hello from server!"
    server_socket.sendto(response.encode(), client_addr)
    print("Response sent to client:", client_addr)
    server_socket.close()


if __name__ == "__main__":
    main()
