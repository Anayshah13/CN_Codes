"""Experiment 10: Stop-and-Wait server (UDP).

One frame is accepted at a time. The sequence number is only 0 or 1.
A frame whose number is the one we expect is delivered and ACKed, and
the expected number flips. Any other number is a duplicate: the previous
ACK is sent again.

Packet text is "seq:message". The client sends END when it is finished.

Run: python exp10_stop_and_wait_server.py
"""

from __future__ import annotations

import socket


def main() -> None:
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("localhost", 12345))
    print("Server is up and listening...")
    expected_seq = 0

    while True:
        data, client_address = server_socket.recvfrom(1024)
        packet = data.decode()
        if packet == "END":
            print("Transmission ended.")
            break

        seq_text, message = packet.split(":", 1)
        seq_num = int(seq_text)
        if seq_num == expected_seq:
            print(f"Received: {message} (Seq={seq_num})")
            ack = f"ACK{seq_num}"
            server_socket.sendto(ack.encode(), client_address)
            expected_seq = 1 - expected_seq
        else:
            # The frame was already accepted. Repeat the ACK the client missed.
            print("Duplicate or out of order packet. Resending ACK.")
            ack = f"ACK{1 - expected_seq}"
            server_socket.sendto(ack.encode(), client_address)

    server_socket.close()


if __name__ == "__main__":
    main()
