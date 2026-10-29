"""Experiment 7: Wireshark and the TCP/IP layers.

This experiment is done in Wireshark, not as a compiled program.
Run this file for the capture steps, display filters, and the header
fields to point at if you are asked to explain a packet.

Run: python exp7_wireshark.py
"""

from __future__ import annotations

LAYERS = [
    (
        "Ethernet",
        "eth",
        [
            "Destination and source MAC addresses (6 bytes each)",
            "EtherType: 0x0800 IPv4, 0x0806 ARP, 0x86DD IPv6",
            "Frame length, shown in the frame header",
        ],
    ),
    (
        "Data link / ARP",
        "arp",
        [
            "Opcode 1 = request, opcode 2 = reply",
            "Sender MAC and sender IP",
            "Target MAC and target IP",
            "This is the IP-to-MAC binding",
        ],
    ),
    (
        "Network / IP",
        "ip",
        [
            "Version, header length, total length, TTL, protocol",
            "Source and destination IP addresses",
            "Identification, flags, fragment offset (fragmentation)",
            "Protocol 1 = ICMP, 6 = TCP, 17 = UDP",
        ],
    ),
    (
        "ICMP",
        "icmp",
        [
            "Type 8 / code 0 = echo request (ping)",
            "Type 0 / code 0 = echo reply",
            "Type 3 = destination unreachable",
        ],
    ),
    (
        "Transport / TCP",
        "tcp",
        [
            "Source and destination ports",
            "Sequence number and acknowledgement number",
            "Flags: SYN, ACK, FIN, RST",
            "Handshake filter: tcp.flags.syn == 1",
            "HTTP port filter: tcp.port == 80",
        ],
    ),
    (
        "UDP",
        "udp",
        [
            "Source and destination ports, length, checksum",
            "DNS uses UDP port 53: dns  or  udp.port == 53",
            "DHCP uses UDP ports 67 and 68: dhcp",
        ],
    ),
    (
        "Application",
        "http or dns or dhcp or ftp or tls",
        [
            "HTTP: request method, URL, Host, status code (http)",
            "Follow a TCP stream: right-click a packet -> Follow -> TCP Stream",
            "DNS: query name and the answer address (dns)",
            "DHCP: discover, offer, request, ack (dhcp)",
            "FTP: commands on port 21 (ftp)",
            "TLS: handshake after the TCP connection (tls)",
        ],
    ),
]

STEPS = """
Capture steps
1. Open Wireshark and start a capture on the active Wi-Fi or Ethernet interface.
2. In a browser, open http://example.com  (plain HTTP shows the request clearly).
3. In a terminal run:  ping -n 4 8.8.8.8     and     nslookup google.com
4. Stop the capture.
5. Paste one display filter at a time into the filter bar and press Enter.
6. Click a packet. In the middle pane expand Ethernet II, Internet Protocol,
   and Transmission Control Protocol (or UDP).
7. For an HTTP packet: right-click -> Follow -> TCP Stream.
   You should see the GET request and the HTTP response.
"""


def main() -> None:
    print("Experiment 7: Wireshark — TCP/IP layers")
    print(STEPS)
    print("Display filters and what to say about each layer")
    for name, filt, points in LAYERS:
        print("=" * 72)
        print(f"{name}")
        print(f"Filter: {filt}")
        for point in points:
            print(f"  - {point}")
        print()
    print("Useful extra filters")
    print("  tcp.flags.syn == 1 && tcp.flags.ack == 0    first packet of the handshake")
    print("  tcp.flags.syn == 1 && tcp.flags.ack == 1    SYN-ACK")
    print("  icmp.type == 8                              echo request")
    print("  icmp.type == 3                              destination unreachable")
    print("  http.request.method == GET                  HTTP GET only")
    print("  dns.flags.response == 0                     DNS queries")
    print("  dns.flags.response == 1                     DNS responses")


if __name__ == "__main__":
    main()
