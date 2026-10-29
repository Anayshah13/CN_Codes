"""Experiment 1: Linux networking commands.

Aim: Study hostname, nslookup, whois, route, arp, and ip addr.
Run: python exp1_linux_networking_commands.py
"""

from __future__ import annotations

import shutil
import subprocess
import sys

COMMANDS = [
    {
        "name": "hostname",
        "use": "Prints the name of this machine on the network.",
        "linux": ["hostname"],
        "windows": ["hostname"],
    },
    {
        "name": "nslookup",
        "use": "Asks DNS for the IP address of a domain name.",
        "linux": ["nslookup", "google.com"],
        "windows": ["nslookup", "google.com"],
    },
    {
        "name": "whois",
        "use": "Looks up registration details of a domain or IP address.",
        "linux": ["whois", "google.com"],
        "windows": ["whois", "google.com"],
    },
    {
        "name": "route",
        "use": "Shows the kernel routing table: which gateway is used for each destination.",
        "linux": ["route", "-n"],
        "windows": ["route", "print", "-4"],
    },
    {
        "name": "arp",
        "use": "Shows the ARP cache: IP address mapped to a MAC address.",
        "linux": ["arp", "-n"],
        "windows": ["arp", "-a"],
    },
    {
        "name": "ip addr",
        "use": "Shows each interface, its MAC address, and its IPv4/IPv6 addresses.",
        "linux": ["ip", "addr"],
        "windows": ["ipconfig", "/all"],
    },
]


def run(argv: list[str]) -> str:
    try:
        completed = subprocess.run(
            argv,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"(could not run {' '.join(argv)}: {exc})"
    text = (completed.stdout or "") + (completed.stderr or "")
    text = text.strip()
    return text if text else "(no output)"


def main() -> None:
    windows = sys.platform.startswith("win")
    print("Experiment 1: Linux networking commands")
    print("On a Linux lab PC, type the Linux command. This script runs that")
    print("command when it exists, and the Windows equivalent otherwise.\n")

    for item in COMMANDS:
        linux_cmd = " ".join(item["linux"])
        print("=" * 72)
        print(item["name"])
        print(item["use"])
        print(f"Linux command: {linux_cmd}")

        if not windows and shutil.which(item["linux"][0]):
            print(run(item["linux"]))
        elif windows and shutil.which(item["windows"][0]):
            fallback = " ".join(item["windows"])
            if fallback != linux_cmd:
                print(f"Windows equivalent: {fallback}")
            print(run(item["windows"]))
        elif shutil.which(item["linux"][0]):
            print(run(item["linux"]))
        else:
            print(f"'{item['linux'][0]}' is not installed on this machine.")
            print(f"On the lab Linux PC, run: {linux_cmd}")
        print()


if __name__ == "__main__":
    main()
