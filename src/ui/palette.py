"""
PureClip Apple Liquid UI Palette
Features translucent glassmorphism styling, Light & Dark Apple themes,
tactile keycap badges, and smooth keyboard dispatch.
"""

import win32gui
import customtkinter as ctk
from typing import Callable, List
from src.core.buffer import ClipItem
from src.analytics.metrics import MetricsTracker


class LiquidPalette(ctk.CTkToplevel):
    """
    Floating, frameless palette inspired by Apple macOS Liquid & Spotlight design.
    """

    # Theme color palettes
    THEMES = {
        "dark": {
            "bg": "#13131A",
            "card_bg": "#1A1A24",
            "card_border": "#313145",
            "row_bg": "#222230",
            "row_hover": "#2B2B3D",
            "row_border": "#2E2E3E",
            "title": "#FFFFFF",
            "subtitle": "#9494A8",
            "text": "#F1F1F6",
            "keycap_bg": "#36364D",
            "keycap_text": "#C4C4DC",
            "keycap_border": "#464663",
            "badge_url": ("#1E3A5F", "#93C5FD"),
            "badge_email": ("#164E33", "#86EFAC"),
            "badge_code": ("#4A3718", "#FDE047"),
            "badge_text": ("#2D2D3D", "#CBD5E1"),
        },
        "light": {
            "bg": "#EAECEF",
            "card_bg": "#FFFFFF",
            "card_border": "#D1D5DB",
            "row_bg": "#F8FAFC",
            "row_hover": "#EDF2F7",
            "row_border": "#E2E8F0",
            "title": "#0F172A",
            "subtitle": "#64748B",
            "text": "#1E293B",
            "keycap_bg": "#E2E8F0",
            "keycap_text": "#334155",
            "keycap_border": "#CBD5E1",
            "badge_url": ("#DBEAFE", "#1E40AF"),
            "badge_email": ("#DCFCE7", "#166534"),
            "badge_code": ("#FEF3C7", "#92400E"),
            "badge_text": ("#F1F5F9", "#475569"),
        }
    }

    def __init__(
        self,
        on_select: Callable[[int], None],
        on_autofill: Callable[[], None],
        metrics: MetricsTracker,
        theme: str = "dark"
    ):
        super().__init__()

        self.on_select = on_select
        self.on_autofill = on_autofill
        self.metrics = metrics
        self.current_theme = theme

        # Window properties: Frameless, Topmost, Soft Translucency
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.attributes("-alpha", 0.95)  # Apple-like subtle glass translucency

        # Main Card (Frosted Glass Container with 1px border glow)
        self.main_card = ctk.CTkFrame(self, corner_radius=18, border_width=1)
        self.main_card.pack(fill="both", expand=True, padx=4, pady=4)

        # Header Frame
        self.header_frame = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.header_frame.pack(fill="x", padx=18, pady=(14, 8))

        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text="✦ PureClip",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
        )
        self.title_label.pack(side="left")

        self.hint_label = ctk.CTkLabel(
            self.header_frame,
            text="[1-9] Paste  •  [Tab] Form Fill  •  [T] Theme  •  [I] Insights",
            font=ctk.CTkFont(family="Segoe UI", size=11)
        )
        self.hint_label.pack(side="right")

        # Container for Clips
        self.clips_container = ctk.CTkFrame(self.main_card, fg_color="transparent")
        self.clips_container.pack(fill="both", expand=True, padx=14, pady=(2, 10))

        # Insights Panel
        self.insights_frame = None

        # Key bindings
        self.bind("<Escape>", lambda e: self.hide())
        self.bind("<Tab>", lambda e: self._handle_tab(e))
        self.bind("<t>", lambda e: self.toggle_theme())
        self.bind("<T>", lambda e: self.toggle_theme())
        self.bind("<i>", lambda e: self._toggle_insights())
        self.bind("<I>", lambda e: self._toggle_insights())

        for digit in range(1, 10):
            self.bind(str(digit), lambda e, d=digit: self._handle_digit(d))

        self._apply_theme()
        self.withdraw()

    def toggle_theme(self):
        """Switches between Apple Light Glass and Apple Dark Glass."""
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        ctk.set_appearance_mode("Light" if self.current_theme == "light" else "Dark")
        self._apply_theme()

    def _apply_theme(self):
        t = self.THEMES[self.current_theme]
        self.configure(fg_color=t["bg"])
        self.main_card.configure(
            fg_color=t["card_bg"],
            border_color=t["card_border"]
        )
        self.title_label.configure(text_color=t["title"])
        self.hint_label.configure(text_color=t["subtitle"])

    def show(self, items: List[ClipItem]):
        """Renders items and positions palette at cursor."""
        if not items:
            return

        for widget in self.clips_container.winfo_children():
            widget.destroy()

        if self.insights_frame:
            self.insights_frame.destroy()
            self.insights_frame = None

        display_items = items[:5]
        for item in display_items:
            self._render_clip_row(item)

        self.update_idletasks()
        width = 490
        height = 76 + (len(display_items) * 48)

        cursor_x, cursor_y = win32gui.GetCursorPos()
        x = cursor_x + 12
        y = cursor_y + 12

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        if x + width > screen_w:
            x = cursor_x - width - 12
        if y + height > screen_h:
            y = cursor_y - height - 12

        self.geometry(f"{width}x{height}+{max(10, x)}+{max(10, y)}")
        self.deiconify()
        self.lift()
        self.focus_force()

    def _render_clip_row(self, item: ClipItem):
        t = self.THEMES[self.current_theme]

        row = ctk.CTkFrame(
            self.clips_container,
            fg_color=t["row_bg"],
            corner_radius=12,
            border_width=1,
            border_color=t["row_border"]
        )
        row.pack(fill="x", pady=4)

        # Tactile Keycap Badge [ 1 ]
        keycap = ctk.CTkLabel(
            row,
            text=f" {item.index} ",
            font=ctk.CTkFont(family="Consolas", size=12, weight="bold"),
            fg_color=t["keycap_bg"],
            text_color=t["keycap_text"],
            corner_radius=6,
            width=28,
            height=24
        )
        keycap.pack(side="left", padx=(10, 8), pady=9)

        # Content Text
        content_lbl = ctk.CTkLabel(
            row,
            text=item.preview,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=t["text"],
            anchor="w"
        )
        content_lbl.pack(side="left", fill="x", expand=True, padx=4)

        # Category Pill Badge
        badge_key = f"badge_{item.category.lower()}"
        bg_color, fg_color = t.get(badge_key, t["badge_text"])

        badge = ctk.CTkLabel(
            row,
            text=f" {item.category} ",
            font=ctk.CTkFont(family="Segoe UI", size=10, weight="bold"),
            fg_color=bg_color,
            text_color=fg_color,
            corner_radius=8,
            height=20
        )
        badge.pack(side="right", padx=(4, 12))

        # Click support
        row.bind("<Button-1>", lambda e, idx=item.index: self._handle_digit(idx))
        content_lbl.bind("<Button-1>", lambda e, idx=item.index: self._handle_digit(idx))

    def _toggle_insights(self):
        summary = self.metrics.get_summary()
        t = self.THEMES[self.current_theme]

        for widget in self.clips_container.winfo_children():
            widget.destroy()

        self.insights_frame = ctk.CTkFrame(
            self.clips_container,
            fg_color=t["row_bg"],
            corner_radius=12,
            border_width=1,
            border_color=t["row_border"]
        )
        self.insights_frame.pack(fill="both", expand=True, pady=4)

        title = ctk.CTkLabel(
            self.insights_frame,
            text="⚡ Wispr Flow ROI Insights",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=t["title"]
        )
        title.pack(pady=(10, 6))

        stats_text = (
            f"• Estimated Time Saved: {summary['minutes_saved']} minutes\n"
            f"• App Context Switches Avoided: {summary['switches_avoided']}\n"
            f"• Tracking Links Stripped: {summary['trackers_stripped']}\n"
            f"• Form Auto-Fills Executed: {summary['form_autofills']}"
        )

        lbl = ctk.CTkLabel(
            self.insights_frame,
            text=stats_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=t["text"],
            justify="left"
        )
        lbl.pack(padx=20, pady=(4, 14))

    def _handle_digit(self, digit: int):
        self.hide()
        self.on_select(digit)

    def _handle_tab(self, event):
        self.hide()
        self.on_autofill()
        return "break"

    def hide(self):
        self.withdraw()
