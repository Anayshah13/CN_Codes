"""Experiment 7: Wireshark notes for the capture in the lab sheet.

This does not sniff the network. It is the commentary you give while
the capture is open: colours, filters, the handshake, and packet 56.

Run: python exp7_wireshark.py
"""

from __future__ import annotations


def main() -> None:
    print("Experiment 7: Wireshark")
    print()
    print("What Wireshark is for")
    print("  Live capture, display filters, colouring, and Follow TCP Stream.")
    print("  Green = TCP, dark blue = DNS, light blue = UDP, black = a TCP problem.")
    print()
    print("How the capture was taken")
    print("  1. Start Wireshark and click the Ethernet interface.")
    print("  2. Let packets arrive. The sheet's capture has 5893 packets")
    print("     (TCP, ARP, NTP, STP, TLS, UDP).")
    print("  3. Stop with the red square.")
    print("  4. Type a display filter and press Enter. 'tcp' kept 2456 of 2903")
    print("     packets in the filtered view (84.6%).")
    print("  5. Right-click a packet -> Follow -> TCP Stream to read one conversation.")
    print()
    print("Packet 56, an HTTP GET, 636 bytes")
    print("  Network (IP)")
    print("    source 10.120.64.42")
    print("    destination 128.119.245.12")
    print("    TTL 128")
    print("    protocol 6, which is TCP")
    print("  Transport (TCP)")
    print("    source port 55765")
    print("    destination port 80")
    print("    flags PSH, ACK (0x018)")
    print("    window 255")
    print("    payload 582 bytes")
    print("  Application (HTTP)")
    print("    GET /wireshark-labs/protected_pages/HTTPwiresharkfile5.html HTTP/1.1")
    print("    Host header and Authorization: Basic")
    print()
    print("TCP three-way handshake, from the first two frames")
    print("  The time between frame 1 and frame 2 is the connect baseline.")
    print("  Also read: window size, SACK permitted, maximum segment size,")
    print("  and the window scale option.")
    print()
    print("Filters to type")
    print("  eth     frame header and length")
    print("  arp     IP to MAC binding")
    print("  ip      header, TTL, fragmentation")
    print("  icmp    echo request (type 8) and echo reply (type 0)")
    print("  tcp     ports and handshake flags")
    print("  dhcp    discover, offer, request, ack")
    print("  ftp     port 21 commands")
    print("  http    method, host, status")


if __name__ == "__main__":
    main()
