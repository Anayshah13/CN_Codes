"""Experiment 1: Linux networking commands.

The lab asks for hostname, nslookup, whois, route, arp, and ip.
On a Linux PC, type the Linux command. This script runs that command
when it exists, and the Windows equivalent otherwise, then prints
what the command is for.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

# Each row is one question from the sheet.
COMMANDS = [
    {
        "name": "hostname",
        "use": (
            "Prints the name of this computer on the network. "
            "Used to identify a machine when troubleshooting."
        ),
        "linux": ["hostname"],
        "windows": ["hostname"],
    },
    {
        "name": "nslookup",
        "use": (
            "Queries DNS. Turns a name such as google.com into IP addresses "
            "and can also do a reverse lookup."
        ),
        "linux": ["nslookup", "google.com"],
        "windows": ["nslookup", "google.com"],
    },
    {
        "name": "whois",
        "use": (
            "Reads the WHOIS record of a domain or IP: registrar, "
            "registration dates, and public contact details."
        ),
        "linux": ["whois", "google.com"],
        "windows": ["whois", "google.com"],
    },
    {
        "name": "route",
        "use": (
            "Shows the IP routing table: which gateway a packet uses "
            "for each destination. It can also add or delete routes."
        ),
        "linux": ["route", "-n"],
        "windows": ["route", "print", "-4"],
    },
    {
        "name": "arp",
        "use": (
            "Shows the ARP cache, which maps an IP address on the local "
            "LAN to a MAC address."
        ),
        "linux": ["arp", "-n"],
        "windows": ["arp", "-a"],
    },
    {
        "name": "ip",
        "use": (
            "Shows interfaces, addresses, and routes. On Linux it replaces "
            "the older ifconfig, route, and arp commands."
        ),
        "linux": ["ip", "addr"],
        "windows": ["ipconfig", "/all"],
    },
]


def run(argv: list[str]) -> str:
    """Run one command and return whatever it printed."""
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
    text = ((completed.stdout or "") + (completed.stderr or "")).strip()
    return text if text else "(no output)"


def main() -> None:
    windows = sys.platform.startswith("win")
    print("Experiment 1: Linux networking commands\n")
    for item in COMMANDS:
        linux_cmd = " ".join(item["linux"])
        print("=" * 72)
        print(item["name"])
        print(item["use"])
        print(f"Linux command: {linux_cmd}")
        if not windows and shutil.which(item["linux"][0]):
            print(run(item["linux"]))
        elif shutil.which(item["windows"][0]):
            fallback = " ".join(item["windows"])
            if fallback != linux_cmd:
                print(f"Windows equivalent: {fallback}")
            print(run(item["windows"]))
        else:
            print(f"'{item['linux'][0]}' is not installed. On the lab PC run: {linux_cmd}")
        print()


if __name__ == "__main__":
    main()
