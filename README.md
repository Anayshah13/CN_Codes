# CN Codes

Computer Networks lab programs (DJS23ICPC501), one runnable file per experiment.
There is no Experiment 3 PDF in this folder.

| Experiment | Topic | How to run |
|---|---|---|
| 1 | Linux networking commands | `python exp1_linux_networking_commands.py` |
| 2 | Character count, bit stuffing, byte stuffing | `python exp2_framing.py` |
| 4 | Hamming code | `python exp4_hamming.py` or `python exp4_hamming.py 1011` |
| 5 | CRC | `python exp5_crc.py` or `python exp5_crc.py --ask` |
| 6 | VLSM | `python exp6_vlsm.py` |
| 7 | Wireshark / TCP/IP layers | `python exp7_wireshark.py` (capture itself is done in Wireshark) |
| 8 | TCP sockets, selection sort | server, then two clients (below) |
| 9 | UDP group chat | server, then two or more clients (below) |
| 10 | Stop-and-Wait ARQ | `python exp10_stop_and_wait.py` and `python exp10_stop_and_wait_gui.py` |

Experiment 8, in three terminals:

```text
python exp8_tcp_sort_server.py
python exp8_tcp_sort_client.py 1
python exp8_tcp_sort_client.py 2
```

Experiment 9, server first:

```text
python exp9_udp_chat_server.py
python exp9_udp_chat_client.py
```

Type `bye` in a chat client to leave. Standard library only; no packages to install.
