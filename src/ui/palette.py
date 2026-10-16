"""
PureClip Apple Liquid UI Palette
Translucent, sleek floating dispatch window inspired by macOS / iOS design.
"""

import sys
import tkinter as tk
import customtkinter as ctk
import win32gui
from typing import Callable, List, Optional
from src.core.buffer import ClipItem
from src.analytics.metrics import MetricsTracker

# Set appearance mode to modern Dark
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")


class LiquidPalette(ctk.CTkToplevel):
    """
    Floating, frameless translucent dispatch palette with tactile keycap badges.
    """

    def __init__(
        self,
        on_select: Callable[[int], None],
        on_autofill: Callable[[], None],
        metrics: MetricsTracker
    ):
        super().__init__()

        self.on_select = on_select
        self.on_autofill = on_autofill
        self.metrics = metrics

        # Window properties: Frameless, always on top
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#121217")

        # Container Frame (Apple-style frosted glass card with 1px border)
        self.main_card = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color="#16161E",
            border_width=1,
            border_color="#2A2A38"
        )
        self.main_card.pack(fill="both", expand=True, padx=4, pady=4)

        # Header
        self.header_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=16, pady=(12, 6))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="✦ PureClip",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color="#F0F0F5"
        )
        self.title_label.pack(side="left")

        self.hint_label = ctk.CTkLabel(
            self.header_frame,
            text="Press [1-9] to paste  •  [Tab] Form fill  •  [I] Insights",
            font=ctk.CTkFont(family="Segoe UI", size=11),
            text_color="#8E8E9F"
        )
        self.hint_label.pack(side="right")

        # Scrollable / List Container for Clips
        self.clips_container = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.clips_container.pack(fill="both", expand=True, padx=12, pady=6)

        # Insights Panel (initially hidden)
        self.insights_frame = None

        # Bind Keypresses directly to this window
        self.bind("<Escape>", lambda e: self.hide())
        self.bind("<Tab>", lambda e: self._handle_tab(e))
        self.bind("<i>", lambda e: self._toggle_insights())
        self.bind("<I>", lambda e: self._toggle_insights())

        for digit in range(1, 10):
            self.bind(str(digit), lambda e, d=digit: self._handle_digit(d))

        # Initially hidden offscreen
        self.withdraw()

    def show(self, items: List[ClipItem]):
        """Populates items and animates palette into view at current cursor position."""
        if not items:
            return

        # Clear previous rows
        for widget in self.clips_container.winfo_children():
            widget.destroy()

        if self.insights_frame:
            self.insights_frame.destroy()
            self.insights_frame = None

        # Populate rows (up to 5 items shown for maximum sleekness)
        display_items = items[:5]
        for item in display_items:
            self._render_clip_row(item)

        # Calculate position near cursor
        self.update_idletasks()
        width = 460
        height = 70 + (len(display_items) * 44)
        
        cursor_x, cursor_y = win32gui.GetCursorPos()
        
        # Position slightly offset from cursor
        x = cursor_x + 15
        y = cursor_y + 15

        # Check screen bounds
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        if x + width > screen_w:
            x = cursor_x - width - 15
        if y + height > screen_h:
            y = cursor_y - height - 15

        self.geometry(f"{width}x{height}+{max(10, x)}+{max(10, y)}")
        self.deiconify()
        self.lift()
        self.focus_force()

    def _render_clip_row(self, item: ClipItem):
        """Renders an individual clip with a tactile keycap and badge."""
        row = ctk.CTkFrame(
            self.clips_container,
            fg_color="#1E1E28",
            corner_radius=10,
            border_width=1,
            border_color="#2A2A38"
        )
        row.pack(fill="x", pady=3)

        # Tactile Keycap Badge [ 1 ]
        keycap = ctk.CTkLabel(
            row,
            text=f" {item.index} ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color="#2D2D3D",
            text_color="#A5A5C0",
            corner_radius=6,
            width=28,
            height=24
        )
        keycap.pack(side="left", padx=(8, 8), pady=8)

        # Content Preview
        content_lbl = ctk.CTkLabel(
            row,
            text=item.preview,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#E4E4EE",
            anchor="w"
        )
        content_lbl.pack(side="left", fill="x", expand=True, padx=4)

        # Category Pill (e.g. "URL", "Email", "Text")
        pill_color = "#3B3B4F"
        if item.category == "URL":
            pill_color = "#1E3A5F"
        elif item.category == "Email":
            pill_color = "#1F4E38"
        elif item.category == "Code":
            pill_color = "#4D381E"

        cat_badge = ctk.CTkLabel(
            row,
            text=f" {item.category} ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color=pill_color,
            text_color="#D0D0E5",
            corner_radius=8,
            height=20
        )
        cat_badge.pack(side="right", padx=(4, 10))

        # Make entire row clickable
        row.bind("<Button-1>", lambda e, idx=item.index: self._handle_digit(idx))
        content_lbl.bind("<Button-1>", lambda e, idx=item.index: self._handle_digit(idx))

    def _toggle_insights(self):
        """Shows the Wispr Flow style productivity metrics."""
        summary = self.metrics.get_summary()

        for widget in self.clips_container.winfo_children():
            widget.destroy()

        self.insights_frame = ctk.CTkFrame(self.clips_container, fg_color="#1A1A24", corner_radius=10)
        self.insights_frame.pack(fill="both", expand=True, pady=4)

        # Stat 1: Time saved
        title = ctk.CTkLabel(
            self.insights_frame,
            text="⚡ Wispr Flow ROI Insights",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color="#F5F5FA"
        )
        title.pack(pady=(8, 4))

        stats_text = (
            f"• Time Saved: {summary['minutes_saved']} minutes\n"
            f"• App Switches Avoided: {summary['switches_avoided']}\n"
            f"• Tracking Links Cleaned: {summary['trackers_stripped']}\n"
            f"• Form Auto-Fills: {summary['form_autofills']}"
        )
        
        lbl = ctk.CTkLabel(
            self.insights_frame,
            text=stats_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#C0C0D4",
            justify="left"
        )
        lbl.pack(padx=16, pady=(4, 12))

    def _handle_digit(self, digit: int):
        self.hide()
        self.on_select(digit)

    def _handle_tab(self, event):
        self.hide()
        self.on_autofill()
        return "break"

    def hide(self):
        self.withdraw()
