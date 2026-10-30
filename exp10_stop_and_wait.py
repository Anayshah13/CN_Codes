"""Experiment 10: Stop-and-Wait timing trace.

The sheet's table uses these durations for a successful packet:
  DATA on the wire     180
  local deliver          1
  ACK on the wire      180
  local ACK handling     1
The next DATA starts when the ACK arrives, not after the 1-unit handling.

A lost DATA or a lost ACK produces no ACK at the client. The timeout is
one data trip plus one ACK trip after the send starts, then the same
sequence number is sent again.

Default, as the task states: 20 packets, 2 data losses, 2 ACK losses.

Run:
  python exp10_stop_and_wait.py
  python exp10_stop_and_wait.py 20 3,7 5,11
"""

from __future__ import annotations

import sys

DATA_TIME = 180
ACK_TIME = 180
LOCAL = 1


def parse_ids(text: str) -> set[int]:
    text = text.strip()
    if not text or text == "-":
        return set()
    return {int(part) for part in text.split(",") if part.strip()}


def simulate(packet_count: int, data_losses: set[int], ack_losses: set[int]) -> list[dict]:
    """Each listed packet id is lost once, on its first attempt."""
    rows = []
    clock = 0
    seq = 0
    event_id = 1
    used_data: set[int] = set()
    used_ack: set[int] = set()

    def add(start, end, packet, sequence, kind, status, message, src, dst) -> None:
        nonlocal event_id
        rows.append(
            {
                "id": event_id,
                "start": start,
                "end": end,
                "packet": packet,
                "seq": sequence,
                "type": kind,
                "status": status,
                "message": message,
                "src": src,
                "dst": dst,
            }
        )
        event_id += 1

    for packet in range(1, packet_count + 1):
        delivered = False
        while not delivered:
            send_at = clock
            arrive = send_at + DATA_TIME
            add(
                send_at,
                arrive,
                packet,
                seq,
                "DATA",
                "info",
                f"Client sends DATA {packet}, Seq={seq}",
                "Client",
                "Server",
            )
            if packet in data_losses and packet not in used_data:
                used_data.add(packet)
                add(arrive, arrive, packet, seq, "DATA", "lost", f"DATA {packet} lost", "Server", "Server")
                # ACK would have arrived at send_at + DATA_TIME + ACK_TIME.
                clock = send_at + DATA_TIME + ACK_TIME
                add(clock, clock, packet, seq, "TIMEOUT", "info", "Timeout. Retransmitting.", "Client", "Client")
                continue

            add(
                arrive,
                arrive + LOCAL,
                packet,
                seq,
                "DELIVER",
                "success",
                f"Server receives DATA {packet}; delivers once",
                "Server",
                "Server",
            )
            if packet in ack_losses and packet not in used_ack:
                used_ack.add(packet)
                add(arrive, arrive + ACK_TIME, packet, seq, "ACK", "lost", f"ACK {seq} lost", "Server", "Client")
                clock = send_at + DATA_TIME + ACK_TIME
                add(clock, clock, packet, seq, "TIMEOUT", "info", "Timeout. Retransmitting.", "Client", "Client")
                continue

            add(
                arrive,
                arrive + ACK_TIME,
                packet,
                seq,
                "ACK",
                "success",
                f"ACK {seq} for DATA {packet}",
                "Server",
                "Client",
            )
            ack_at = arrive + ACK_TIME
            add(
                ack_at,
                ack_at + LOCAL,
                packet,
                seq,
                "ACK",
                "success",
                f"Client receives ACK {seq} for DATA {packet}",
                "Client",
                "Client",
            )
            clock = ack_at
            seq = 1 - seq
            delivered = True
    return rows


def print_trace(rows: list[dict]) -> None:
    header = f"{'id':<5}{'time':<8}{'end':<8}{'pkt':<6}{'seq':<5}{'type':<10}{'status':<10}{'message':<42}{'from':<8}to"
    print(header)
    for row in rows:
        print(
            f"{row['id']:<5}{row['start']:<8}{row['end']:<8}{row['packet']:<6}{row['seq']:<5}"
            f"{row['type']:<10}{row['status']:<10}{row['message']:<42}{row['src']:<8}{row['dst']}"
        )


def main() -> None:
    packet_count = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    data_losses = parse_ids(sys.argv[2]) if len(sys.argv) > 2 else {3, 8}
    ack_losses = parse_ids(sys.argv[3]) if len(sys.argv) > 3 else {5, 12}
    print("Experiment 10: Stop-and-Wait trace")
    print(f"Packets: {packet_count}   lost DATA: {sorted(data_losses) or '-'}   lost ACK: {sorted(ack_losses) or '-'}")
    print("Live sockets are exp10_stop_and_wait_server.py and exp10_stop_and_wait_client.py\n")
    print_trace(simulate(packet_count, data_losses, ack_losses))


if __name__ == "__main__":
    main()
