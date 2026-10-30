"""Experiment 6: VLSM for 192.168.1.0/24.

Three LANs and three WAN links. The largest network is allocated first.
Each subnet keeps two addresses for the network id and the broadcast.

The Packet Tracer drawing and the CCNA module are done in the lab.
This program prints the subnet sheet.

Run: python exp6_vlsm.py
"""

from __future__ import annotations

import ipaddress

# Hosts required, in the order the sheet names them.
# Allocation itself is largest-first, not this order.
REQUIREMENTS = [
    ("Subnet 1 Development", 74),
    ("Subnet 2 Production", 52),
    ("Subnet 3 Administration", 28),
    ("Subnet 4 WAN 1", 2),
    ("Subnet 5 WAN 2", 2),
    ("Subnet 6 WAN 3", 2),
]


def prefix_for_hosts(hosts: int) -> int:
    """Smallest prefix whose usable host count is at least `hosts`."""
    needed = hosts + 2
    size = 1
    while size < needed:
        size *= 2
    return 32 - (size.bit_length() - 1)


def design(base: str, requirements: list[tuple[str, int]]) -> list[dict]:
    network = ipaddress.ip_network(base, strict=False)
    ordered = sorted(requirements, key=lambda item: item[1], reverse=True)
    cursor = int(network.network_address)
    rows = []
    for name, hosts in ordered:
        prefix = prefix_for_hosts(hosts)
        size = 2 ** (32 - prefix)
        subnet = ipaddress.ip_network((cursor, prefix), strict=False)
        hosts_list = list(subnet.hosts())
        rows.append(
            {
                "name": name,
                "hosts": hosts,
                "cidr": f"/{prefix}",
                "network": str(subnet.network_address),
                "first": str(hosts_list[0]),
                "last": str(hosts_list[-1]),
                "broadcast": str(subnet.broadcast_address),
                "mask": str(subnet.netmask),
            }
        )
        cursor += size
    return rows


def main() -> None:
    print("Experiment 6: VLSM    block 192.168.1.0/24")
    print(
        f"{'Subnet':<28}{'Need':>6} {'CIDR':<6}{'Network':<16}"
        f"{'First':<16}{'Last':<16}{'Broadcast':<16}{'Mask'}"
    )
    for row in design("192.168.1.0/24", REQUIREMENTS):
        print(
            f"{row['name']:<28}{row['hosts']:>6} {row['cidr']:<6}{row['network']:<16}"
            f"{row['first']:<16}{row['last']:<16}{row['broadcast']:<16}{row['mask']}"
        )
    print("\nStatic routes join the three LANs across the /30 WAN links.")
    print("ping from one department to another checks that the routes work.")


if __name__ == "__main__":
    main()
