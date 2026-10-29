"""Experiment 10: Stop-and-Wait ARQ.

The sender transmits one data packet and waits for its ACK.
A lost data packet or a lost ACK causes a timeout and a retransmission.
Sequence numbers alternate between 0 and 1.

Run a text trace:
  python exp10_stop_and_wait.py
  python exp10_stop_and_wait.py 6 2,4 3

Arguments: packet_count  lost_data_ids  lost_ack_ids
Example above sends 6 packets, drops data 2 and 4, and drops ACK 3.

The windowed visualiser is exp10_stop_and_wait_gui.py (same simulate()).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    packet_id: int
    packet_type: str
    start: float
    end: float
    status: str

    @property
    def sequence(self) -> int:
        return (self.packet_id - 1) % 2


def simulate(
    packet_count: int = 20,
    data_losses: list[int] | None = None,
    ack_losses: list[int] | None = None,
    timeout: float = 2.0,
    data_time: float = 0.5,
    ack_time: float = 0.25,
) -> list[Event]:
    """Build a Stop-and-Wait timeline.

    Each listed packet id is lost once (first transmission only), matching
    the GUI: a data loss and an ACK loss are separate one-shot events.
    """
    if packet_count < 1:
        raise ValueError("packet_count must be at least 1")
    data_loss_set = set(data_losses or ())
    ack_loss_set = set(ack_losses or ())
    events: list[Event] = []
    now = 0.0
    used_data: set[int] = set()
    used_ack: set[int] = set()

    for packet_id in range(1, packet_count + 1):
        attempt = 0
        while True:
            attempt += 1
            note = "" if attempt == 1 else f" (retry {attempt - 1})"
            start = now
            end = start + data_time
            if packet_id in data_loss_set and packet_id not in used_data:
                used_data.add(packet_id)
                events.append(Event(packet_id, "DATA", start, end, "LOST" + note))
                now = end + timeout
                events.append(
                    Event(
                        packet_id,
                        "TIMEOUT",
                        end,
                        now,
                        f"No ACK; retransmit packet {packet_id}",
                    )
                )
                continue

            events.append(Event(packet_id, "DATA", start, end, "DELIVERED" + note))
            ack_start = end
            ack_end = ack_start + ack_time
            if packet_id in ack_loss_set and packet_id not in used_ack:
                used_ack.add(packet_id)
                events.append(Event(packet_id, "ACK", ack_start, ack_end, "LOST"))
                now = ack_end + timeout
                events.append(
                    Event(
                        packet_id,
                        "TIMEOUT",
                        ack_end,
                        now,
                        f"ACK lost; retransmit packet {packet_id}",
                    )
                )
                continue

            events.append(Event(packet_id, "ACK", ack_start, ack_end, "RECEIVED"))
            now = ack_end
            break
    return events


def parse_ids(text: str) -> list[int]:
    text = text.strip()
    if not text or text == "-":
        return []
    return [int(part) for part in text.split(",") if part.strip()]


def print_trace(events: list[Event]) -> None:
    print(f"{'Time':<14} {'Seq':<4} {'Type':<8} {'Packet':<8} Status")
    print("-" * 72)
    for event in events:
        span = f"{event.start:.2f}-{event.end:.2f}"
        seq = "-" if event.packet_type == "TIMEOUT" else str(event.sequence)
        print(f"{span:<14} {seq:<4} {event.packet_type:<8} {event.packet_id:<8} {event.status}")

    delivered = [e for e in events if e.packet_type == "DATA" and e.status.startswith("DELIVERED")]
    lost = [e for e in events if "LOST" in e.status]
    timeouts = [e for e in events if e.packet_type == "TIMEOUT"]
    print()
    print(f"Data deliveries : {len(delivered)}")
    print(f"Losses          : {len(lost)}")
    print(f"Timeouts        : {len(timeouts)}")
    if events:
        print(f"Total time      : {events[-1].end:.2f}")


def main() -> None:
    packet_count = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    data_losses = parse_ids(sys.argv[2]) if len(sys.argv) > 2 else [2]
    ack_losses = parse_ids(sys.argv[3]) if len(sys.argv) > 3 else [4]
    print("Experiment 10: Stop-and-Wait ARQ")
    print(f"Packets: {packet_count}   lost DATA: {data_losses or '-'}   lost ACK: {ack_losses or '-'}")
    print("Sender waits for ACK 0/1 before sending the next packet.\n")
    print_trace(
        simulate(
            packet_count=packet_count,
            data_losses=data_losses,
            ack_losses=ack_losses,
        )
    )
    print("\nFor the animated ladder diagram:")
    print("  python exp10_stop_and_wait_gui.py")


if __name__ == "__main__":
    main()
