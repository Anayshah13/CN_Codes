"""Experiment 10: Stop-and-Wait client (UDP).

Sends one message, starts a 2 second timer, and waits for ACK<seq>.
On timeout the same sequence number is sent again. The number flips
only after the matching ACK.

Run the server first:
  python exp10_stop_and_wait_client.py
"""

from __future__ import annotations

import socket

MESSAGES = ["Hello", "from", "Stop", "and", "Wait", "Protocol"]


def main() -> None:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.settimeout(2.0)
    server_address = ("localhost", 12345)
    seq_num = 0

    for message in MESSAGES:
        while True:
            packet = f"{seq_num}:{message}"
            client_socket.sendto(packet.encode(), server_address)
            print(f"Sent: {message} (Seq={seq_num})")
            try:
                data, _ = client_socket.recvfrom(1024)
                ack = data.decode()
                if ack == f"ACK{seq_num}":
                    print(f"ACK received for Seq={seq_num}\n")
                    seq_num = 1 - seq_num
                    break
            except socket.timeout:
                print("Timeout. Retransmitting...")
                continue

    client_socket.sendto(b"END", server_address)
    client_socket.close()


if __name__ == "__main__":
    main()
