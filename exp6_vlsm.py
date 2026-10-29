"""Experiment 6: VLSM subnet design.

Largest network is allocated first from the given block.
Each subnet reserves two addresses: network id and broadcast.

Run: python exp6_vlsm.py
"""

from __future__ import annotations

import ipaddress


def prefix_for_hosts(hosts: int) -> int:
    if hosts < 1:
        raise ValueError("each network needs at least 1 host")
    needed = hosts + 2
    size = 1
    while size < needed:
        size *= 2
    return 32 - (size.bit_length() - 1)


def design(base: str, requirements: list[tuple[str, int]]) -> tuple[list[dict], int, str]:
    network = ipaddress.ip_network(base, strict=False)
    ordered = sorted(requirements, key=lambda item: item[1], reverse=True)
    cursor = int(network.network_address)
    end = int(network.broadcast_address)
    rows = []
    for name, hosts in ordered:
        prefix = prefix_for_hosts(hosts)
        size = 2 ** (32 - prefix)
        if cursor + size - 1 > end:
            raise ValueError(f"{name} does not fit in {network}")
        # Largest-first allocation stays aligned when the block itself is aligned.
        subnet = ipaddress.ip_network((cursor, prefix), strict=False)
        hosts_iter = subnet.hosts()
        first = next(hosts_iter)
        last = first
        for last in subnet.hosts():
            pass
        rows.append(
            {
                "name": name,
                "hosts": hosts,
                "cidr": f"{subnet.network_address}/{prefix}",
                "network": str(subnet.network_address),
                "first": str(first),
                "last": str(last),
                "broadcast": str(subnet.broadcast_address),
                "mask": str(subnet.netmask),
                "prefix": prefix,
                "size": size,
            }
        )
        cursor += size
    unused = end - cursor + 1
    return rows, unused, str(network)


def print_table(title: str, base: str, requirements: list[tuple[str, int]]) -> None:
    rows, unused, network = design(base, requirements)
    print("\n" + title)
    print(f"Address block: {network}")
    print(
        f"{'Name':<28} {'Need':>5} {'CIDR':<18} {'First host':<16} "
        f"{'Last host':<16} {'Broadcast':<16} {'Mask'}"
    )
    for row in rows:
        print(
            f"{row['name']:<28} {row['hosts']:>5} {row['cidr']:<18} {row['first']:<16} "
            f"{row['last']:<16} {row['broadcast']:<16} {row['mask']}"
        )
    print(f"Unused addresses: {unused}")


def ask_custom() -> None:
    base = input("Base block (example 192.168.1.0/24): ").strip()
    print("Enter networks as: name, hosts")
    print("Blank line finishes the list.")
    requirements = []
    while True:
        line = input("> ").strip()
        if not line:
            break
        name, hosts = line.split(",")
        requirements.append((name.strip(), int(hosts.strip())))
    if not requirements:
        print("No networks entered.")
        return
    print_table("Custom VLSM", base, requirements)


def main() -> None:
    print("Experiment 6: Variable Length Subnet Masking")
    lab = [
        ("Development LAN", 74),
        ("Production LAN", 52),
        ("Administrative LAN", 28),
        ("WAN link 1", 2),
        ("WAN link 2", 2),
        ("WAN link 3", 2),
    ]
    observation = [
        ("HR", 50),
        ("Finance", 25),
        ("IT", 12),
        ("Admin", 6),
    ]
    print_table("Lab problem: 192.168.1.0/24", "192.168.1.0/24", lab)
    print_table("Observation: 192.168.10.0/24", "192.168.10.0/24", observation)

    print("\n1. Show the two solved problems again")
    print("2. Design a custom block")
    print("3. Exit")
    try:
        choice = input("Enter: ").strip()
    except EOFError:
        return
    if choice == "2":
        ask_custom()


if __name__ == "__main__":
    main()
