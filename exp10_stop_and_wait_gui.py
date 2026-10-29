"""Experiment 10: Modern Graphical User Interface (GUI) Visualizer for Stop-and-Wait ARQ.

Provides real-time interactive visualization of:
1. Sender and Receiver stations with state indicators and sequence numbers (0 / 1).
2. Live transmission channel with animated moving packets (DATA / ACK).
3. Packet loss and ACK loss simulation with visual drop effects.
4. Sender timeout countdown bar and automatic retransmission.
5. Live Space-Time Sequence Diagram (Ladder Diagram) auto-generated in real-time.
6. Statistics dashboard and color-coded event log.
7. Step-by-step stepping, pause, resume, speed control, and dynamic error injection.
"""

from __future__ import annotations
import math
import sys
import time
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional

# Import simulation logic from exp10_stop_and_wait
try:
    from exp10_stop_and_wait import simulate, Event
except ImportError:
    # Fallback definition if run standalone
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Event:
        packet_id: int
        packet_type: str
        start: float
        end: float
        status: str

    def simulate(packet_count=20, data_losses=None, ack_losses=None, timeout=2.0, data_time=0.5, ack_time=0.25):
        data_losses = set(data_losses or ())
        ack_losses = set(ack_losses or ())
        events = []
        now = 0.0
        lost_data_used = set()
        lost_ack_used = set()
        for packet_id in range(1, packet_count + 1):
            attempt = 0
            while True:
                attempt += 1
                suffix = "" if attempt == 1 else f" (retry {attempt - 1})"
                start = now
                end = start + data_time
                if packet_id in data_losses and packet_id not in lost_data_used:
                    lost_data_used.add(packet_id)
                    events.append(Event(packet_id, "DATA", start, end, "LOST" + suffix))
                    now = end + timeout
                    events.append(Event(packet_id, "TIMEOUT", end, now, f"No ACK; retransmit packet {packet_id}"))
                    continue

                events.append(Event(packet_id, "DATA", start, end, "DELIVERED" + suffix))
                ack_start = end
                ack_end = ack_start + ack_time
                if packet_id in ack_losses and packet_id not in lost_ack_used:
                    lost_ack_used.add(packet_id)
                    events.append(Event(packet_id, "ACK", ack_start, ack_end, "LOST"))
                    now = ack_end + timeout
                    events.append(Event(packet_id, "TIMEOUT", ack_end, now, f"ACK lost; retransmit packet {packet_id}"))
                    continue

                events.append(Event(packet_id, "ACK", ack_start, ack_end, "RECEIVED"))
                now = ack_end
                break
        return events


# Color Palette (Dark Theme / Cyber-Networking)
BG_MAIN = "#0b0f19"         # Very dark slate/navy
BG_PANEL = "#111827"        # Dark slate
BG_CARD = "#1f2937"         # Card background
BG_CANVAS = "#070a12"       # Pitch canvas for contrast
BORDER_COLOR = "#374151"    # Gray border
TEXT_MAIN = "#f9fafb"       # Bright white
TEXT_MUTED = "#9ca3af"      # Gray
ACCENT_BLUE = "#38bdf8"     # Sky blue for DATA
ACCENT_GREEN = "#34d399"    # Emerald for ACK
ACCENT_RED = "#f87171"      # Red for LOST
ACCENT_AMBER = "#fbbf24"    # Amber for TIMEOUT / RETRY
ACCENT_PURPLE = "#a78bfa"   # Purple accent


class StopAndWaitGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Experiment 10: Stop-and-Wait ARQ Visualizer")
        self.root.geometry("1240x820")
        self.root.minsize(1050, 720)
        self.root.configure(bg=BG_MAIN)

        # Simulation state
        self.events: list[Event] = []
        self.current_event_idx = -1
        self.is_running = False
        self.is_paused = False
        self.speed_multiplier = 1.0

        # Animation state
        self.anim_progress = 0.0
        self.current_packet_rect: Optional[int] = None
        self.current_packet_text: Optional[int] = None
        self.current_packet_subtext: Optional[int] = None
        self.particles: list[dict] = []

        # Real-time protocol metrics
        self.stat_sent = 0
        self.stat_delivered = 0
        self.stat_data_lost = 0
        self.stat_ack_lost = 0
        self.stat_timeouts = 0
        self.stat_retries = 0

        # Dynamic on-the-fly drop injection flags
        self.inject_drop_data = False
        self.inject_drop_ack = False

        # Build UI layout
        self._setup_styles()
        self._build_header()
        self._build_main_content()
        self._build_bottom_controls()

        # Load default preset into fields
        self.apply_preset("default")

        # Initial canvas setup
        self.root.after(100, self._initial_draw)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        
        style.configure("TFrame", background=BG_PANEL)
        style.configure("TLabel", background=BG_PANEL, foreground=TEXT_MAIN, font=("Segoe UI", 9))
        style.configure("TLabelframe", background=BG_PANEL, foreground=ACCENT_BLUE, bordercolor=BORDER_COLOR)
        style.configure("TLabelframe.Label", background=BG_PANEL, foreground=ACCENT_BLUE, font=("Segoe UI", 9, "bold"))
        
        # Modern Buttons
        style.configure("Accent.TButton", background="#0284c7", foreground="white", font=("Segoe UI", 9, "bold"), borderwidth=0, padding=6)
        style.map("Accent.TButton", background=[("active", "#0369a1"), ("disabled", "#334155")])

        style.configure("Action.TButton", background=BG_CARD, foreground=TEXT_MAIN, font=("Segoe UI", 9), borderwidth=1, bordercolor=BORDER_COLOR, padding=6)
        style.map("Action.TButton", background=[("active", "#374151")])

        style.configure("Danger.TButton", background="#991b1b", foreground="white", font=("Segoe UI", 8, "bold"), borderwidth=0, padding=5)
        style.map("Danger.TButton", background=[("active", "#b91c1c")])

        # Treeview (Event Log)
        style.configure("Treeview", background=BG_PANEL, foreground=TEXT_MAIN, fieldbackground=BG_PANEL,
                        rowheight=24, font=("Consolas", 9), borderwidth=0)
        style.configure("Treeview.Heading", background=BG_CARD, foreground=ACCENT_BLUE,
                        font=("Segoe UI", 9, "bold"), borderwidth=1, relief="flat")
        style.map("Treeview.Heading", background=[("active", "#374151")])
        style.map("Treeview", background=[("selected", "#1e3a8a")], foreground=[("selected", "white")])

    def _build_header(self):
        header_frame = tk.Frame(self.root, bg=BG_PANEL, height=55, highlightthickness=1, highlightbackground=BORDER_COLOR)
        header_frame.pack(fill=tk.X, padx=12, pady=(10, 6))

        # Title and badge
        title_box = tk.Frame(header_frame, bg=BG_PANEL)
        title_box.pack(side=tk.LEFT, padx=14, pady=8)

        tk.Label(title_box, text="STOP-AND-WAIT ARQ", font=("Segoe UI", 13, "bold"), fg=ACCENT_BLUE, bg=BG_PANEL).pack(side=tk.LEFT)
        tk.Label(title_box, text="VISUALIZER", font=("Segoe UI", 13, "bold"), fg="white", bg=BG_PANEL).pack(side=tk.LEFT, padx=(4, 8))
        
        badge = tk.Label(title_box, text="EXP-10 PROTOCOL LAB", font=("Segoe UI", 8, "bold"),
                         fg=ACCENT_GREEN, bg="#064e3b", padx=6, pady=2)
        badge.pack(side=tk.LEFT)

        # Quick Presets on Header
        preset_box = tk.Frame(header_frame, bg=BG_PANEL)
        preset_box.pack(side=tk.RIGHT, padx=14, pady=8)

        tk.Label(preset_box, text="Presets:", font=("Segoe UI", 9, "bold"), fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 6))
        
        btn_p1 = tk.Button(preset_box, text="Lab Default (3,14 / 7,18)", font=("Segoe UI", 8),
                           bg=BG_CARD, fg=TEXT_MAIN, activebackground="#374151", activeforeground="white",
                           relief="flat", cursor="hand2", command=lambda: self.apply_preset("default"))
        btn_p1.pack(side=tk.LEFT, padx=3)

        btn_p2 = tk.Button(preset_box, text="Clean (No Loss)", font=("Segoe UI", 8),
                           bg=BG_CARD, fg=TEXT_MAIN, activebackground="#374151", activeforeground="white",
                           relief="flat", cursor="hand2", command=lambda: self.apply_preset("clean"))
        btn_p2.pack(side=tk.LEFT, padx=3)

        btn_p3 = tk.Button(preset_box, text="Heavy Loss", font=("Segoe UI", 8),
                           bg=BG_CARD, fg=TEXT_MAIN, activebackground="#374151", activeforeground="white",
                           relief="flat", cursor="hand2", command=lambda: self.apply_preset("heavy_loss"))
        btn_p3.pack(side=tk.LEFT, padx=3)

    def _build_main_content(self):
        content_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg=BG_MAIN, bd=0, sashwidth=4, sashpad=0)
        content_paned.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        # LEFT PANE: Animation Canvas (Channel + Space-Time Ladder)
        left_frame = tk.Frame(content_paned, bg=BG_MAIN)
        content_paned.add(left_frame, minsize=650, stretch="always")

        # Upper Canvas: Animated Host Nodes & Channel
        channel_container = tk.Frame(left_frame, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        channel_container.pack(fill=tk.BOTH, expand=False, pady=(0, 6))

        # Channel header banner
        ch_banner = tk.Frame(channel_container, bg=BG_CARD, height=28)
        ch_banner.pack(fill=tk.X)
        tk.Label(ch_banner, text="TRANSMISSION CHANNEL & ENDPOINT NODES", font=("Segoe UI", 8, "bold"),
                 fg=ACCENT_BLUE, bg=BG_CARD).pack(side=tk.LEFT, padx=10, pady=4)
        
        self.status_lbl = tk.Label(ch_banner, text="Status: Ready", font=("Segoe UI", 8, "italic"),
                                   fg=TEXT_MUTED, bg=BG_CARD)
        self.status_lbl.pack(side=tk.RIGHT, padx=10)

        # Drawing Canvas for Nodes & Animated Moving Packets
        self.canvas_channel = tk.Canvas(channel_container, bg=BG_CANVAS, height=230,
                                        highlightthickness=0)
        self.canvas_channel.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        self.canvas_channel.bind("<Configure>", lambda e: self._draw_channel_background())

        # Lower Canvas: Space-Time Sequence (Ladder) Diagram
        ladder_container = tk.Frame(left_frame, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        ladder_container.pack(fill=tk.BOTH, expand=True)

        ladder_banner = tk.Frame(ladder_container, bg=BG_CARD, height=28)
        ladder_banner.pack(fill=tk.X)
        tk.Label(ladder_banner, text="SPACE-TIME SEQUENCE DIAGRAM (LADDER DIAGRAM)",
                 font=("Segoe UI", 8, "bold"), fg=ACCENT_PURPLE, bg=BG_CARD).pack(side=tk.LEFT, padx=10, pady=4)

        tk.Label(ladder_banner, text="Time flows downwards ↓", font=("Segoe UI", 8),
                 fg=TEXT_MUTED, bg=BG_CARD).pack(side=tk.RIGHT, padx=10)

        # Ladder diagram canvas with vertical scrollbar
        ladder_inner = tk.Frame(ladder_container, bg=BG_CANVAS)
        ladder_inner.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

        self.ladder_canvas = tk.Canvas(ladder_inner, bg=BG_CANVAS, highlightthickness=0)
        self.ladder_scrollbar = ttk.Scrollbar(ladder_inner, orient=tk.VERTICAL, command=self.ladder_canvas.yview)
        self.ladder_canvas.configure(yscrollcommand=self.ladder_scrollbar.set)

        self.ladder_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.ladder_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.ladder_canvas.bind("<Configure>", lambda e: self._draw_ladder_axes())

        # RIGHT PANE: Metrics & Event Log
        right_frame = tk.Frame(content_paned, bg=BG_MAIN, width=380)
        content_paned.add(right_frame, minsize=340, stretch="never")

        # Stats Cards Grid
        stats_frame = tk.LabelFrame(right_frame, text="Live Protocol Metrics", bg=BG_PANEL, fg=ACCENT_BLUE,
                                    font=("Segoe UI", 9, "bold"), padx=8, pady=8,
                                    highlightthickness=1, highlightbackground=BORDER_COLOR)
        stats_frame.pack(fill=tk.X, pady=(0, 6))

        grid = tk.Frame(stats_frame, bg=BG_PANEL)
        grid.pack(fill=tk.X)

        self.card_sent = self._create_metric_card(grid, 0, 0, "Packets Sent", "0", ACCENT_BLUE)
        self.card_delivered = self._create_metric_card(grid, 0, 1, "Delivered", "0", ACCENT_GREEN)
        self.card_data_lost = self._create_metric_card(grid, 1, 0, "DATA Lost", "0", ACCENT_RED)
        self.card_ack_lost = self._create_metric_card(grid, 1, 1, "ACK Lost", "0", ACCENT_RED)
        self.card_timeouts = self._create_metric_card(grid, 2, 0, "Timeouts", "0", ACCENT_AMBER)
        self.card_retries = self._create_metric_card(grid, 2, 1, "Retransmissions", "0", ACCENT_PURPLE)

        # Efficiency Card
        eff_box = tk.Frame(stats_frame, bg=BG_CARD, padx=8, pady=6, highlightthickness=1, highlightbackground=BORDER_COLOR)
        eff_box.pack(fill=tk.X, pady=(8, 0))
        tk.Label(eff_box, text="Channel Utilization / Efficiency:", font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD).pack(side=tk.LEFT)
        self.lbl_efficiency = tk.Label(eff_box, text="100.0%", font=("Segoe UI", 9, "bold"), fg=ACCENT_GREEN, bg=BG_CARD)
        self.lbl_efficiency.pack(side=tk.RIGHT)

        # Event Log
        log_frame = tk.LabelFrame(right_frame, text="Real-Time Event Log", bg=BG_PANEL, fg=ACCENT_BLUE,
                                  font=("Segoe UI", 9, "bold"), padx=6, pady=6,
                                  highlightthickness=1, highlightbackground=BORDER_COLOR)
        log_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("time", "pkt", "type", "status")
        self.tree_log = ttk.Treeview(log_frame, columns=columns, show="headings", selectmode="browse")
        self.tree_log.heading("time", text="Time (s)")
        self.tree_log.heading("pkt", text="Pkt#")
        self.tree_log.heading("type", text="Type")
        self.tree_log.heading("status", text="Status / Details")

        self.tree_log.column("time", width=62, anchor="center")
        self.tree_log.column("pkt", width=42, anchor="center")
        self.tree_log.column("type", width=65, anchor="center")
        self.tree_log.column("status", width=170, anchor="w")

        # Color tags in Treeview
        self.tree_log.tag_configure("DATA_OK", foreground="#38bdf8")
        self.tree_log.tag_configure("ACK_OK", foreground="#34d399")
        self.tree_log.tag_configure("LOST", foreground="#f87171")
        self.tree_log.tag_configure("TIMEOUT", foreground="#fbbf24")
        self.tree_log.tag_configure("RETRY", foreground="#c084fc")

        tree_scroll = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.tree_log.yview)
        self.tree_log.configure(yscrollcommand=tree_scroll.set)

        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_log.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def _create_metric_card(self, parent, row, col, label, value, color):
        box = tk.Frame(parent, bg=BG_CARD, padx=8, pady=5, highlightthickness=1, highlightbackground=BORDER_COLOR)
        box.grid(row=row, column=col, sticky="nsew", padx=3, pady=3)
        parent.grid_columnconfigure(col, weight=1)

        tk.Label(box, text=label, font=("Segoe UI", 8), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        val_lbl = tk.Label(box, text=value, font=("Segoe UI", 12, "bold"), fg=color, bg=BG_CARD)
        val_lbl.pack(anchor="w")
        return val_lbl

    def _build_bottom_controls(self):
        ctrl_frame = tk.Frame(self.root, bg=BG_PANEL, highlightthickness=1, highlightbackground=BORDER_COLOR)
        ctrl_frame.pack(fill=tk.X, padx=12, pady=(4, 10))

        # Row 1: Parameters Input
        params_row = tk.Frame(ctrl_frame, bg=BG_PANEL)
        params_row.pack(fill=tk.X, padx=10, pady=(6, 4))

        # Packets Count
        tk.Label(params_row, text="Total Packets:", font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 4))
        self.ent_count = tk.Entry(params_row, width=5, bg=BG_CARD, fg=TEXT_MAIN, insertbackground="white", relief="flat")
        self.ent_count.pack(side=tk.LEFT, padx=(0, 12))

        # Data Losses
        tk.Label(params_row, text="DATA Losses (IDs):", font=("Segoe UI", 8, "bold"), fg=ACCENT_BLUE, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 4))
        self.ent_data_loss = tk.Entry(params_row, width=12, bg=BG_CARD, fg=TEXT_MAIN, insertbackground="white", relief="flat")
        self.ent_data_loss.pack(side=tk.LEFT, padx=(0, 12))

        # ACK Losses
        tk.Label(params_row, text="ACK Losses (IDs):", font=("Segoe UI", 8, "bold"), fg=ACCENT_GREEN, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 4))
        self.ent_ack_loss = tk.Entry(params_row, width=12, bg=BG_CARD, fg=TEXT_MAIN, insertbackground="white", relief="flat")
        self.ent_ack_loss.pack(side=tk.LEFT, padx=(0, 12))

        # Timeout
        tk.Label(params_row, text="Timeout (s):", font=("Segoe UI", 8, "bold"), fg=ACCENT_AMBER, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 4))
        self.ent_timeout = tk.Entry(params_row, width=5, bg=BG_CARD, fg=TEXT_MAIN, insertbackground="white", relief="flat")
        self.ent_timeout.pack(side=tk.LEFT, padx=(0, 12))

        # Speed Slider
        tk.Label(params_row, text="Animation Speed:", font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 4))
        self.slider_speed = tk.Scale(params_row, from_=0.25, to=3.0, resolution=0.25, orient=tk.HORIZONTAL,
                                     bg=BG_PANEL, fg=TEXT_MAIN, highlightthickness=0, troughcolor=BG_CARD,
                                     activebackground=ACCENT_BLUE, length=120, command=self._on_speed_change)
        self.slider_speed.set(1.0)
        self.slider_speed.pack(side=tk.LEFT, padx=(0, 6))
        self.lbl_speed_val = tk.Label(params_row, text="1.0x", font=("Segoe UI", 8), fg=ACCENT_BLUE, bg=BG_PANEL)
        self.lbl_speed_val.pack(side=tk.LEFT)

        # Row 2: Action Buttons & Dynamic Injectors
        act_row = tk.Frame(ctrl_frame, bg=BG_PANEL)
        act_row.pack(fill=tk.X, padx=10, pady=(4, 8))

        self.btn_run = tk.Button(act_row, text="▶ START SIMULATION", font=("Segoe UI", 9, "bold"),
                                 bg="#0284c7", fg="white", activebackground="#0369a1", activeforeground="white",
                                 relief="flat", cursor="hand2", padx=12, pady=4, command=self.start_simulation)
        self.btn_run.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_pause = tk.Button(act_row, text="⏸ Pause", font=("Segoe UI", 9),
                                   bg=BG_CARD, fg=TEXT_MAIN, activebackground="#374151", activeforeground="white",
                                   relief="flat", cursor="hand2", padx=10, pady=4, state=tk.DISABLED, command=self.toggle_pause)
        self.btn_pause.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_step = tk.Button(act_row, text="⏭ Step Next", font=("Segoe UI", 9),
                                  bg=BG_CARD, fg=TEXT_MAIN, activebackground="#374151", activeforeground="white",
                                  relief="flat", cursor="hand2", padx=10, pady=4, command=self.step_next_event)
        self.btn_step.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_reset = tk.Button(act_row, text="↺ Reset", font=("Segoe UI", 9),
                                   bg=BG_CARD, fg=TEXT_MAIN, activebackground="#374151", activeforeground="white",
                                   relief="flat", cursor="hand2", padx=10, pady=4, command=self.reset_all)
        self.btn_reset.pack(side=tk.LEFT, padx=(0, 16))

        # Dynamic Fault Injection Buttons
        tk.Label(act_row, text="Inject Error On-The-Fly:", font=("Segoe UI", 8, "bold"), fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 6))

        self.btn_inject_data = tk.Button(act_row, text="💥 Drop Next DATA", font=("Segoe UI", 8, "bold"),
                                         bg="#7f1d1d", fg="#fca5a5", activebackground="#991b1b", activeforeground="white",
                                         relief="flat", cursor="hand2", padx=8, pady=4, command=self.inject_data_drop)
        self.btn_inject_data.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_inject_ack = tk.Button(act_row, text="💥 Drop Next ACK", font=("Segoe UI", 8, "bold"),
                                        bg="#78350f", fg="#fde68a", activebackground="#92400e", activeforeground="white",
                                        relief="flat", cursor="hand2", padx=8, pady=4, command=self.inject_ack_drop)
        self.btn_inject_ack.pack(side=tk.LEFT)

    def _on_speed_change(self, val):
        self.speed_multiplier = float(val)
        self.lbl_speed_val.config(text=f"{self.speed_multiplier:.2f}x")

    def apply_preset(self, preset_name: str):
        self.reset_all()
        if preset_name == "default":
            self.ent_count.delete(0, tk.END)
            self.ent_count.insert(0, "20")
            self.ent_data_loss.delete(0, tk.END)
            self.ent_data_loss.insert(0, "3, 14")
            self.ent_ack_loss.delete(0, tk.END)
            self.ent_ack_loss.insert(0, "7, 18")
            self.ent_timeout.delete(0, tk.END)
            self.ent_timeout.insert(0, "2.0")
        elif preset_name == "clean":
            self.ent_count.delete(0, tk.END)
            self.ent_count.insert(0, "10")
            self.ent_data_loss.delete(0, tk.END)
            self.ent_data_loss.insert(0, "0")
            self.ent_ack_loss.delete(0, tk.END)
            self.ent_ack_loss.insert(0, "0")
            self.ent_timeout.delete(0, tk.END)
            self.ent_timeout.insert(0, "2.0")
        elif preset_name == "heavy_loss":
            self.ent_count.delete(0, tk.END)
            self.ent_count.insert(0, "12")
            self.ent_data_loss.delete(0, tk.END)
            self.ent_data_loss.insert(0, "2, 5, 8")
            self.ent_ack_loss.delete(0, tk.END)
            self.ent_ack_loss.insert(0, "4, 10")
            self.ent_timeout.delete(0, tk.END)
            self.ent_timeout.insert(0, "1.8")

    def _initial_draw(self):
        self._draw_channel_background()
        self._draw_ladder_axes()

    def _draw_channel_background(self, sender_state="IDLE", receiver_state="IDLE",
                                 seq_num="0", timer_pct=0.0):
        c = self.canvas_channel
        c.delete("all")
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 100 or h < 50:
            return

        node_w = 150
        node_h = 170
        y_top = 30

        # SENDER NODE (Station A)
        x_s1 = 20
        x_s2 = x_s1 + node_w
        c.create_rectangle(x_s1, y_top, x_s2, y_top + node_h, fill=BG_CARD, outline=ACCENT_BLUE, width=2)
        c.create_rectangle(x_s1, y_top, x_s2, y_top + 28, fill="#0f2b48", outline=ACCENT_BLUE, width=1)
        c.create_text((x_s1 + x_s2) / 2, y_top + 14, text="🖥️ SENDER (A)", fill="white", font=("Segoe UI", 9, "bold"))

        # Sender state badge
        state_colors = {
            "IDLE": ("#374151", "#9ca3af"),
            "SENDING": ("#0369a1", "#38bdf8"),
            "WAITING_ACK": ("#854d0e", "#fde047"),
            "TIMEOUT": ("#991b1b", "#fca5a5"),
            "RETRANSMITTING": ("#6b21a8", "#d8b4fe"),
        }
        bg_col, fg_col = state_colors.get(sender_state, ("#374151", "#9ca3af"))
        c.create_rectangle(x_s1 + 10, y_top + 38, x_s2 - 10, y_top + 62, fill=bg_col, outline="")
        c.create_text((x_s1 + x_s2) / 2, y_top + 50, text=sender_state, fill=fg_col, font=("Segoe UI", 8, "bold"))

        # Sender Details
        c.create_text(x_s1 + 14, y_top + 80, text=f"Current Seq : {seq_num}", fill=TEXT_MAIN, font=("Segoe UI", 8), anchor="w")
        c.create_text(x_s1 + 14, y_top + 98, text="Window Size : N = 1", fill=TEXT_MUTED, font=("Segoe UI", 8), anchor="w")
        c.create_text(x_s1 + 14, y_top + 116, text="Timer Status:", fill=TEXT_MUTED, font=("Segoe UI", 8), anchor="w")

        # Timer countdown bar
        t_bar_x1 = x_s1 + 14
        t_bar_x2 = x_s2 - 14
        t_bar_y1 = y_top + 130
        t_bar_y2 = y_top + 144
        c.create_rectangle(t_bar_x1, t_bar_y1, t_bar_x2, t_bar_y2, fill="#111827", outline=BORDER_COLOR)
        if timer_pct > 0:
            fill_w = (t_bar_x2 - t_bar_x1) * min(1.0, timer_pct)
            t_col = ACCENT_RED if timer_pct >= 0.85 else (ACCENT_AMBER if timer_pct >= 0.5 else ACCENT_GREEN)
            c.create_rectangle(t_bar_x1 + 1, t_bar_y1 + 1, t_bar_x1 + fill_w, t_bar_y2 - 1, fill=t_col, outline="")
            c.create_text((t_bar_x1 + t_bar_x2) / 2, (t_bar_y1 + t_bar_y2) / 2,
                          text=f"{int(timer_pct * 100)}%", fill="white", font=("Segoe UI", 7, "bold"))
        else:
            c.create_text((t_bar_x1 + t_bar_x2) / 2, (t_bar_y1 + t_bar_y2) / 2,
                          text="OFF", fill=TEXT_MUTED, font=("Segoe UI", 7))

        # RECEIVER NODE (Station B)
        x_r2 = w - 20
        x_r1 = x_r2 - node_w
        c.create_rectangle(x_r1, y_top, x_r2, y_top + node_h, fill=BG_CARD, outline=ACCENT_GREEN, width=2)
        c.create_rectangle(x_r1, y_top, x_r2, y_top + 28, fill="#064e3b", outline=ACCENT_GREEN, width=1)
        c.create_text((x_r1 + x_r2) / 2, y_top + 14, text="🖥️ RECEIVER (B)", fill="white", font=("Segoe UI", 9, "bold"))

        rx_bg_col, rx_fg_col = state_colors.get(receiver_state, ("#374151", "#9ca3af"))
        if receiver_state == "ACCEPTED":
            rx_bg_col, rx_fg_col = ("#065f46", "#34d399")
        elif receiver_state == "DUPLICATE":
            rx_bg_col, rx_fg_col = ("#78350f", "#fde68a")
        c.create_rectangle(x_r1 + 10, y_top + 38, x_r2 - 10, y_top + 62, fill=rx_bg_col, outline="")
        c.create_text((x_r1 + x_r2) / 2, y_top + 50, text=receiver_state, fill=rx_fg_col, font=("Segoe UI", 8, "bold"))

        expected_seq = seq_num  # In Stop-and-Wait, matches
        c.create_text(x_r1 + 14, y_top + 80, text=f"Expect Seq : {expected_seq}", fill=TEXT_MAIN, font=("Segoe UI", 8), anchor="w")
        c.create_text(x_r1 + 14, y_top + 98, text=f"Delivered  : {self.stat_delivered}", fill=ACCENT_GREEN, font=("Segoe UI", 8, "bold"), anchor="w")
        c.create_text(x_r1 + 14, y_top + 116, text="Action: ACK on receive", fill=TEXT_MUTED, font=("Segoe UI", 8), anchor="w")

        # TRANSMISSION CHANNEL LANES (Middle)
        ch_x1 = x_s2 + 10
        ch_x2 = x_r1 - 10
        ch_w = ch_x2 - ch_x1
        if ch_w > 50:
            # DATA Lane (Upper wire)
            y_data = y_top + 55
            c.create_line(ch_x1, y_data, ch_x2, y_data, fill="#1e3a8a", width=3, dash=(6, 4))
            c.create_text(ch_x1 + 10, y_data - 12, text="DATA Lane (Sender ➔ Receiver)", fill=ACCENT_BLUE, font=("Segoe UI", 8, "bold"), anchor="w")
            # Direction arrows along data lane
            for step in range(1, 5):
                ax = ch_x1 + (ch_w * step / 5)
                c.create_line(ax - 5, y_data - 4, ax, y_data, ax - 5, y_data + 4, fill="#3b82f6", width=2)

            # ACK Lane (Lower wire)
            y_ack = y_top + 125
            c.create_line(ch_x1, y_ack, ch_x2, y_ack, fill="#065f46", width=3, dash=(6, 4))
            c.create_text(ch_x2 - 10, y_ack + 14, text="ACK Lane (Receiver ➔ Sender)", fill=ACCENT_GREEN, font=("Segoe UI", 8, "bold"), anchor="e")
            # Direction arrows along ack lane (pointing left)
            for step in range(1, 5):
                ax = ch_x1 + (ch_w * step / 5)
                c.create_line(ax + 5, y_ack - 4, ax, y_ack, ax + 5, y_ack + 4, fill="#10b981", width=2)

        # Draw particles if any
        self._draw_particles()

    def _draw_particles(self):
        c = self.canvas_channel
        new_particles = []
        for p in self.particles:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["life"] -= 0.1
            if p["life"] > 0:
                rad = max(1, int(p["life"] * 4))
                c.create_oval(p["x"] - rad, p["y"] - rad, p["x"] + rad, p["y"] + rad,
                              fill=p["color"], outline="")
                new_particles.append(p)
        self.particles = new_particles

    def _spawn_explosion(self, x, y, color):
        for i in range(16):
            angle = (i / 16.0) * 2 * math.pi
            spd = 2.0 + (i % 3) * 1.5
            self.particles.append({
                "x": x,
                "y": y,
                "vx": math.cos(angle) * spd,
                "vy": math.sin(angle) * spd,
                "life": 1.0,
                "color": color
            })

    def _draw_ladder_axes(self):
        c = self.ladder_canvas
        w = c.winfo_width()
        if w < 100:
            return

        # Determine canvas total height based on events count
        total_events = max(15, len(self.events) * 2 + 5)
        ladder_h = max(400, total_events * 36)
        c.configure(scrollregion=(0, 0, w, ladder_h))

        # Clear axes
        c.delete("axes")
        x_sender = 120
        x_receiver = w - 120

        # Sender Axis (Left)
        c.create_line(x_sender, 20, x_sender, ladder_h - 20, fill=ACCENT_BLUE, width=3, tags="axes")
        c.create_rectangle(x_sender - 45, 6, x_sender + 45, 26, fill=BG_CARD, outline=ACCENT_BLUE, tags="axes")
        c.create_text(x_sender, 16, text="SENDER", fill="white", font=("Segoe UI", 8, "bold"), tags="axes")

        # Receiver Axis (Right)
        c.create_line(x_receiver, 20, x_receiver, ladder_h - 20, fill=ACCENT_GREEN, width=3, tags="axes")
        c.create_rectangle(x_receiver - 45, 6, x_receiver + 45, 26, fill=BG_CARD, outline=ACCENT_GREEN, tags="axes")
        c.create_text(x_receiver, 16, text="RECEIVER", fill="white", font=("Segoe UI", 8, "bold"), tags="axes")

    def reset_all(self):
        self.is_running = False
        self.is_paused = False
        self.current_event_idx = -1
        self.events = []
        self.particles.clear()

        self.stat_sent = 0
        self.stat_delivered = 0
        self.stat_data_lost = 0
        self.stat_ack_lost = 0
        self.stat_timeouts = 0
        self.stat_retries = 0

        self._update_stat_cards()
        self.status_lbl.config(text="Status: Reset", fg=TEXT_MUTED)

        # Clear Treeview
        for row in self.tree_log.get_children():
            self.tree_log.delete(row)

        # Clear Ladder
        self.ladder_canvas.delete("all")
        self._draw_ladder_axes()

        # Reset Controls
        self.btn_run.config(state=tk.NORMAL, text="▶ START SIMULATION")
        self.btn_pause.config(state=tk.DISABLED, text="⏸ Pause")
        self.btn_step.config(state=tk.NORMAL)

        self._draw_channel_background(sender_state="IDLE", receiver_state="IDLE", seq_num="0", timer_pct=0.0)

    def _update_stat_cards(self):
        self.card_sent.config(text=str(self.stat_sent))
        self.card_delivered.config(text=str(self.stat_delivered))
        self.card_data_lost.config(text=str(self.stat_data_lost))
        self.card_ack_lost.config(text=str(self.stat_ack_lost))
        self.card_timeouts.config(text=str(self.stat_timeouts))
        self.card_retries.config(text=str(self.stat_retries))

        total_transmissions = self.stat_sent + self.stat_retries
        if total_transmissions > 0:
            eff = (self.stat_delivered / total_transmissions) * 100.0
            self.lbl_efficiency.config(text=f"{eff:.1f}%")
        else:
            self.lbl_efficiency.config(text="100.0%")

    def _parse_inputs(self):
        try:
            count = int(self.ent_count.get().strip() or "20")
            if count < 1:
                raise ValueError("Packet count must be at least 1.")
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid positive number for Packet Count.")
            return None

        # Parse Data Losses
        raw_data = self.ent_data_loss.get().strip()
        data_losses = set()
        if raw_data and raw_data != "0":
            try:
                data_losses = {int(x.strip()) for x in raw_data.split(",") if x.strip()}
            except ValueError:
                messagebox.showerror("Invalid Input", "Data loss IDs must be comma-separated integers.")
                return None

        # Parse ACK Losses
        raw_ack = self.ent_ack_loss.get().strip()
        ack_losses = set()
        if raw_ack and raw_ack != "0":
            try:
                ack_losses = {int(x.strip()) for x in raw_ack.split(",") if x.strip()}
            except ValueError:
                messagebox.showerror("Invalid Input", "ACK loss IDs must be comma-separated integers.")
                return None

        try:
            timeout = float(self.ent_timeout.get().strip() or "2.0")
            if timeout <= 0:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Invalid Input", "Timeout must be a positive number.")
            return None

        return count, data_losses, ack_losses, timeout

    def start_simulation(self):
        if self.is_running and self.is_paused:
            # Resume from pause
            self.is_paused = False
            self.btn_pause.config(text="⏸ Pause")
            self.status_lbl.config(text="Status: Running", fg=ACCENT_GREEN)
            self._animate_loop()
            return

        params = self._parse_inputs()
        if not params:
            return

        count, data_losses, ack_losses, timeout = params
        self.reset_all()

        # Generate event trace
        try:
            self.events = simulate(
                packet_count=count,
                data_losses=data_losses,
                ack_losses=ack_losses,
                timeout=timeout,
                data_time=0.5,
                ack_time=0.25
            )
        except Exception as exc:
            messagebox.showerror("Simulation Error", str(exc))
            return

        self.is_running = True
        self.is_paused = False
        self.current_event_idx = -1
        self.btn_run.config(state=tk.DISABLED)
        self.btn_pause.config(state=tk.NORMAL, text="⏸ Pause")
        self.status_lbl.config(text=f"Status: Simulating {count} packets...", fg=ACCENT_BLUE)

        # Redraw axes to fit all events
        self._draw_ladder_axes()
        self.step_next_event()

    def toggle_pause(self):
        if not self.is_running:
            return
        self.is_paused = not self.is_paused
        if self.is_paused:
            self.btn_pause.config(text="▶ Resume")
            self.status_lbl.config(text="Status: Paused", fg=ACCENT_AMBER)
        else:
            self.btn_pause.config(text="⏸ Pause")
            self.status_lbl.config(text="Status: Running", fg=ACCENT_GREEN)
            self._animate_loop()

    def inject_data_drop(self):
        self.inject_drop_data = True
        self.status_lbl.config(text="💥 Fault Injected: Next DATA packet will be dropped!", fg=ACCENT_RED)

    def inject_ack_drop(self):
        self.inject_drop_ack = True
        self.status_lbl.config(text="💥 Fault Injected: Next ACK packet will be dropped!", fg=ACCENT_AMBER)

    def step_next_event(self):
        if not self.events:
            params = self._parse_inputs()
            if not params:
                return
            count, data_losses, ack_losses, timeout = params
            self.events = simulate(count, data_losses, ack_losses, timeout)
            self._draw_ladder_axes()

        if self.current_event_idx + 1 >= len(self.events):
            self.is_running = False
            self.btn_run.config(state=tk.NORMAL, text="▶ RE-RUN")
            self.btn_pause.config(state=tk.DISABLED)
            self.status_lbl.config(text="Status: Completed all packets!", fg=ACCENT_GREEN)
            self._draw_channel_background(sender_state="IDLE", receiver_state="ACCEPTED", seq_num="0", timer_pct=0.0)
            return

        self.current_event_idx += 1
        event = self.events[self.current_event_idx]
        self._process_event(event)

    def _process_event(self, event: Event):
        # Check dynamic error injection
        is_lost = event.status.startswith("LOST")
        if self.inject_drop_data and event.packet_type == "DATA" and not is_lost:
            is_lost = True
            self.inject_drop_data = False
        if self.inject_drop_ack and event.packet_type == "ACK" and not is_lost:
            is_lost = True
            self.inject_drop_ack = False

        seq = str(event.packet_id % 2)

        # Update stats
        tag = "DATA_OK"
        if event.packet_type == "DATA":
            if "retry" in event.status:
                self.stat_retries += 1
                tag = "RETRY"
            else:
                self.stat_sent += 1
            if is_lost:
                self.stat_data_lost += 1
                tag = "LOST"
        elif event.packet_type == "ACK":
            if is_lost:
                self.stat_ack_lost += 1
                tag = "LOST"
            else:
                self.stat_delivered = max(self.stat_delivered, event.packet_id)
                tag = "ACK_OK"
        elif event.packet_type == "TIMEOUT":
            self.stat_timeouts += 1
            tag = "TIMEOUT"

        self._update_stat_cards()

        # Add row to Event Log Treeview
        item_id = self.tree_log.insert("", tk.END, values=(
            f"{event.start:.2f}s",
            f"#{event.packet_id}",
            event.packet_type,
            event.status
        ), tags=(tag,))
        self.tree_log.see(item_id)

        # Draw onto Space-Time Ladder Diagram
        self._add_ladder_event(event, self.current_event_idx, is_lost)

        # Trigger animated packet transfer
        self._start_packet_animation(event, seq, is_lost)

    def _add_ladder_event(self, event: Event, index: int, is_lost: bool):
        c = self.ladder_canvas
        w = c.winfo_width()
        x_sender = 120
        x_receiver = w - 120

        # Vertical position for this event row
        y_start = 50 + index * 42
        y_end = y_start + 32

        # Auto-scroll ladder down as events occur
        c.yview_moveto(min(1.0, (y_start - 100) / max(1, c.bbox("all")[3] if c.bbox("all") else 500)))

        seq = str(event.packet_id % 2)

        if event.packet_type == "DATA":
            if is_lost:
                x_mid = (x_sender + x_receiver) / 2
                y_mid = (y_start + y_end) / 2
                c.create_line(x_sender, y_start, x_mid, y_mid, fill=ACCENT_RED, width=2, dash=(4, 2))
                c.create_text(x_mid, y_mid, text="❌ LOST", fill=ACCENT_RED, font=("Segoe UI", 8, "bold"))
                c.create_text(x_sender + 45, y_start - 8, text=f"DATA {event.packet_id} (Seq {seq})", fill=ACCENT_BLUE, font=("Segoe UI", 7))
            else:
                retry_txt = " [RETRY]" if "retry" in event.status else ""
                c.create_line(x_sender, y_start, x_receiver, y_end, fill=ACCENT_BLUE, width=2, arrow=tk.LAST)
                c.create_text((x_sender + x_receiver) / 2, (y_start + y_end) / 2 - 8,
                              text=f"DATA {event.packet_id} (Seq {seq}){retry_txt}", fill=ACCENT_BLUE, font=("Segoe UI", 8))
                c.create_oval(x_receiver - 3, y_end - 3, x_receiver + 3, y_end + 3, fill=ACCENT_GREEN, outline="")

        elif event.packet_type == "ACK":
            if is_lost:
                x_mid = (x_receiver + x_sender) / 2
                y_mid = (y_start + y_end) / 2
                c.create_line(x_receiver, y_start, x_mid, y_mid, fill=ACCENT_RED, width=2, dash=(4, 2))
                c.create_text(x_mid, y_mid, text="❌ LOST", fill=ACCENT_RED, font=("Segoe UI", 8, "bold"))
                c.create_text(x_receiver - 45, y_start - 8, text=f"ACK {event.packet_id}", fill=ACCENT_GREEN, font=("Segoe UI", 7))
            else:
                c.create_line(x_receiver, y_start, x_sender, y_end, fill=ACCENT_GREEN, width=2, arrow=tk.LAST)
                c.create_text((x_sender + x_receiver) / 2, (y_start + y_end) / 2 - 8,
                              text=f"ACK {event.packet_id}", fill=ACCENT_GREEN, font=("Segoe UI", 8))
                c.create_oval(x_sender - 3, y_end - 3, x_sender + 3, y_end + 3, fill=ACCENT_BLUE, outline="")

        elif event.packet_type == "TIMEOUT":
            # Timeout bracket on Sender axis
            c.create_line(x_sender - 8, y_start, x_sender - 16, y_start,
                          x_sender - 16, y_end, x_sender - 8, y_end, fill=ACCENT_AMBER, width=2)
            c.create_text(x_sender - 45, (y_start + y_end) / 2,
                          text=f"⏱️ Timeout\n({event.end - event.start:.1f}s)", fill=ACCENT_AMBER, font=("Segoe UI", 7, "bold"))

    def _start_packet_animation(self, event: Event, seq: str, is_lost: bool):
        self.anim_event = event
        self.anim_seq = seq
        self.anim_lost = is_lost
        self.anim_step = 0
        self.anim_total_steps = max(10, int(28 / self.speed_multiplier))
        self._animate_loop()

    def _animate_loop(self):
        if not self.is_running or self.is_paused:
            return

        c = self.canvas_channel
        w = c.winfo_width()
        node_w = 150
        y_top = 30
        x_s2 = 20 + node_w
        x_r1 = w - 20 - node_w

        ev = self.anim_event
        is_data = (ev.packet_type == "DATA")
        is_ack = (ev.packet_type == "ACK")
        is_timeout = (ev.packet_type == "TIMEOUT")

        if is_timeout:
            # Handle timeout event animation: flash timer on sender
            progress = self.anim_step / self.anim_total_steps
            self._draw_channel_background(
                sender_state="TIMEOUT",
                receiver_state="IDLE",
                seq_num=self.anim_seq,
                timer_pct=min(1.0, progress * 1.2)
            )
            self.anim_step += 1
            if self.anim_step <= self.anim_total_steps:
                self.root.after(25, self._animate_loop)
            else:
                self.step_next_event()
            return

        # Packet flight progress: 0.0 to 1.0
        progress = self.anim_step / self.anim_total_steps

        # Check if dropped packet should stop midway
        stop_at_loss = 0.55
        if self.anim_lost and progress >= stop_at_loss:
            # Drop packet!
            if is_data:
                drop_x = x_s2 + (x_r1 - x_s2) * stop_at_loss
                drop_y = y_top + 55
            else:
                drop_x = x_r1 - (x_r1 - x_s2) * stop_at_loss
                drop_y = y_top + 125

            self._spawn_explosion(drop_x, drop_y, ACCENT_RED)
            self._draw_channel_background(
                sender_state="WAITING_ACK" if is_data else "WAITING_ACK",
                receiver_state="IDLE" if is_data else "IDLE",
                seq_num=self.anim_seq,
                timer_pct=0.6
            )
            # Draw dropped explosion badge
            c.create_rectangle(drop_x - 45, drop_y - 14, drop_x + 45, drop_y + 14,
                               fill="#7f1d1d", outline=ACCENT_RED, width=2)
            c.create_text(drop_x, drop_y, text="💥 PACKET DROPPED", fill="white", font=("Segoe UI", 7, "bold"))

            # Step after short pause
            self.root.after(int(350 / self.speed_multiplier), self.step_next_event)
            return

        # Normal flight or pre-drop flight
        if is_data:
            current_x = x_s2 + 10 + (x_r1 - x_s2 - 80) * progress
            current_y = y_top + 55
            self._draw_channel_background(
                sender_state="RETRANSMITTING" if "retry" in ev.status else "SENDING",
                receiver_state="IDLE",
                seq_num=self.anim_seq,
                timer_pct=progress * 0.4
            )
            # Draw moving DATA packet capsule
            c.create_rectangle(current_x - 38, current_y - 14, current_x + 38, current_y + 14,
                               fill="#0369a1", outline=ACCENT_BLUE, width=2)
            c.create_text(current_x, current_y - 2, text=f"DATA #{ev.packet_id}", fill="white", font=("Segoe UI", 8, "bold"))
            c.create_text(current_x, current_y + 9, text=f"Seq: {self.anim_seq}", fill=ACCENT_BLUE, font=("Segoe UI", 6))

        elif is_ack:
            current_x = (x_r1 - 10) - (x_r1 - x_s2 - 80) * progress
            current_y = y_top + 125
            self._draw_channel_background(
                sender_state="WAITING_ACK",
                receiver_state="SENDING ACK",
                seq_num=self.anim_seq,
                timer_pct=0.4 + progress * 0.3
            )
            # Draw moving ACK packet capsule
            c.create_rectangle(current_x - 30, current_y - 12, current_x + 30, current_y + 12,
                               fill="#065f46", outline=ACCENT_GREEN, width=2)
            c.create_text(current_x, current_y, text=f"ACK #{ev.packet_id}", fill="white", font=("Segoe UI", 8, "bold"))

        self.anim_step += 1
        if self.anim_step <= self.anim_total_steps:
            self.root.after(25, self._animate_loop)
        else:
            # Reached destination!
            if is_data:
                self._draw_channel_background(
                    sender_state="WAITING_ACK",
                    receiver_state="ACCEPTED",
                    seq_num=self.anim_seq,
                    timer_pct=0.5
                )
            elif is_ack:
                self._draw_channel_background(
                    sender_state="ACK RECEIVED",
                    receiver_state="IDLE",
                    seq_num=self.anim_seq,
                    timer_pct=0.0
                )
            self.root.after(int(100 / self.speed_multiplier), self.step_next_event)


def launch_gui():
    """Start the Tkinter GUI Application."""
    root = tk.Tk()
    app = StopAndWaitGUI(root)
    root.mainloop()


if __name__ == "__main__":
    launch_gui()
