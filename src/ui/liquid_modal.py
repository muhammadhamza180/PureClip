"""
PureClip Apple Liquid UI Modal (PyQt6)
Features:
- AttachThreadInput focus stealing (keyboard works WITHOUT clicking)
- Resizable window with drag handles
- Multiple theme presets (selectable via [T] key)
- Image clip preview thumbnails
- Sound feedback on copy/paste
- Ambient drop shadow and frosted glass aesthetic
"""

import time
import ctypes
from typing import Callable, List
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QCursor, QPixmap, QImage
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QFrame, QApplication,
    QSizeGrip
)
from src.core.buffer import ClipItem
from src.core.clipboard import force_foreground

# ─── Theme Presets ────────────────────────────────────────────────────
THEMES = {
    "Midnight Glass": {
        "bg": "rgba(14, 14, 22, 0.94)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "row_bg": "rgba(28, 30, 44, 0.80)",
        "row_hover_bg": "rgba(48, 52, 78, 0.95)",
        "row_hover_border": "rgba(129, 140, 248, 0.50)",
        "row_border": "rgba(255, 255, 255, 0.08)",
        "title_color": "#818CF8",
        "hint_color": "#94A3B8",
        "text_color": "#F8FAFC",
        "keycap_top": "#424660", "keycap_bot": "#272A3C",
        "keycap_border": "rgba(255, 255, 255, 0.25)",
        "keycap_text": "#FFFFFF",
        "shadow_color": QColor(0, 0, 0, 200),
    },
    "Arctic Frost": {
        "bg": "rgba(240, 243, 248, 0.96)",
        "card_border": "rgba(0, 0, 0, 0.10)",
        "row_bg": "rgba(255, 255, 255, 0.90)",
        "row_hover_bg": "rgba(230, 235, 245, 1.0)",
        "row_hover_border": "rgba(99, 102, 241, 0.40)",
        "row_border": "rgba(0, 0, 0, 0.06)",
        "title_color": "#4F46E5",
        "hint_color": "#64748B",
        "text_color": "#1E293B",
        "keycap_top": "#E8ECF2", "keycap_bot": "#D1D5DB",
        "keycap_border": "rgba(0, 0, 0, 0.15)",
        "keycap_text": "#1E293B",
        "shadow_color": QColor(0, 0, 0, 80),
    },
    "Emerald Night": {
        "bg": "rgba(10, 22, 18, 0.94)",
        "card_border": "rgba(52, 211, 153, 0.20)",
        "row_bg": "rgba(20, 40, 32, 0.80)",
        "row_hover_bg": "rgba(30, 60, 48, 0.95)",
        "row_hover_border": "rgba(52, 211, 153, 0.50)",
        "row_border": "rgba(52, 211, 153, 0.10)",
        "title_color": "#34D399",
        "hint_color": "#6EE7B7",
        "text_color": "#F0FDF4",
        "keycap_top": "#1A3D2E", "keycap_bot": "#0F2A1E",
        "keycap_border": "rgba(52, 211, 153, 0.30)",
        "keycap_text": "#ECFDF5",
        "shadow_color": QColor(0, 20, 10, 180),
    },
    "Sunset Blaze": {
        "bg": "rgba(26, 12, 12, 0.94)",
        "card_border": "rgba(251, 146, 60, 0.20)",
        "row_bg": "rgba(40, 20, 16, 0.80)",
        "row_hover_bg": "rgba(60, 30, 20, 0.95)",
        "row_hover_border": "rgba(251, 146, 60, 0.50)",
        "row_border": "rgba(251, 146, 60, 0.10)",
        "title_color": "#FB923C",
        "hint_color": "#FDBA74",
        "text_color": "#FFF7ED",
        "keycap_top": "#3D2516", "keycap_bot": "#2A1A10",
        "keycap_border": "rgba(251, 146, 60, 0.30)",
        "keycap_text": "#FFF7ED",
        "shadow_color": QColor(20, 5, 0, 180),
    },
    "Royal Purple": {
        "bg": "rgba(18, 12, 28, 0.94)",
        "card_border": "rgba(168, 85, 247, 0.20)",
        "row_bg": "rgba(30, 20, 48, 0.80)",
        "row_hover_bg": "rgba(50, 35, 72, 0.95)",
        "row_hover_border": "rgba(168, 85, 247, 0.50)",
        "row_border": "rgba(168, 85, 247, 0.10)",
        "title_color": "#A855F7",
        "hint_color": "#C084FC",
        "text_color": "#FAF5FF",
        "keycap_top": "#2E1A4A", "keycap_bot": "#1A0F30",
        "keycap_border": "rgba(168, 85, 247, 0.30)",
        "keycap_text": "#F5F3FF",
        "shadow_color": QColor(10, 0, 20, 180),
    },
    "Ocean Depth": {
        "bg": "rgba(8, 16, 28, 0.94)",
        "card_border": "rgba(56, 189, 248, 0.20)",
        "row_bg": "rgba(14, 28, 48, 0.80)",
        "row_hover_bg": "rgba(20, 44, 70, 0.95)",
        "row_hover_border": "rgba(56, 189, 248, 0.50)",
        "row_border": "rgba(56, 189, 248, 0.10)",
        "title_color": "#38BDF8",
        "hint_color": "#7DD3FC",
        "text_color": "#F0F9FF",
        "keycap_top": "#0E2A42", "keycap_bot": "#091C30",
        "keycap_border": "rgba(56, 189, 248, 0.30)",
        "keycap_text": "#F0F9FF",
        "shadow_color": QColor(0, 10, 25, 180),
    },
    "Rose Gold": {
        "bg": "rgba(28, 16, 18, 0.94)",
        "card_border": "rgba(251, 113, 133, 0.20)",
        "row_bg": "rgba(44, 24, 28, 0.80)",
        "row_hover_bg": "rgba(64, 32, 40, 0.95)",
        "row_hover_border": "rgba(251, 113, 133, 0.50)",
        "row_border": "rgba(251, 113, 133, 0.10)",
        "title_color": "#FB7185",
        "hint_color": "#FDA4AF",
        "text_color": "#FFF1F2",
        "keycap_top": "#3E1E24", "keycap_bot": "#2A1218",
        "keycap_border": "rgba(251, 113, 133, 0.30)",
        "keycap_text": "#FFF1F2",
        "shadow_color": QColor(20, 5, 8, 180),
    },
    "Charcoal Minimal": {
        "bg": "rgba(32, 32, 32, 0.96)",
        "card_border": "rgba(255, 255, 255, 0.08)",
        "row_bg": "rgba(48, 48, 48, 0.80)",
        "row_hover_bg": "rgba(64, 64, 64, 0.95)",
        "row_hover_border": "rgba(255, 255, 255, 0.20)",
        "row_border": "rgba(255, 255, 255, 0.05)",
        "title_color": "#FFFFFF",
        "hint_color": "#A3A3A3",
        "text_color": "#FAFAFA",
        "keycap_top": "#525252", "keycap_bot": "#3A3A3A",
        "keycap_border": "rgba(255, 255, 255, 0.15)",
        "keycap_text": "#FFFFFF",
        "shadow_color": QColor(0, 0, 0, 160),
    },
    "Ivory Clean": {
        "bg": "rgba(255, 255, 250, 0.96)",
        "card_border": "rgba(0, 0, 0, 0.08)",
        "row_bg": "rgba(248, 248, 242, 0.90)",
        "row_hover_bg": "rgba(238, 238, 230, 1.0)",
        "row_hover_border": "rgba(0, 0, 0, 0.15)",
        "row_border": "rgba(0, 0, 0, 0.05)",
        "title_color": "#1A1A1A",
        "hint_color": "#737373",
        "text_color": "#171717",
        "keycap_top": "#E5E5E0", "keycap_bot": "#D4D4CF",
        "keycap_border": "rgba(0, 0, 0, 0.12)",
        "keycap_text": "#1A1A1A",
        "shadow_color": QColor(0, 0, 0, 50),
    },
    "Neon Cyber": {
        "bg": "rgba(8, 8, 16, 0.96)",
        "card_border": "rgba(0, 255, 170, 0.25)",
        "row_bg": "rgba(12, 14, 28, 0.85)",
        "row_hover_bg": "rgba(20, 24, 48, 0.95)",
        "row_hover_border": "rgba(0, 255, 170, 0.60)",
        "row_border": "rgba(0, 255, 170, 0.12)",
        "title_color": "#00FFAA",
        "hint_color": "#66FFD0",
        "text_color": "#E0FFF0",
        "keycap_top": "#0A1A14", "keycap_bot": "#06120E",
        "keycap_border": "rgba(0, 255, 170, 0.35)",
        "keycap_text": "#00FFAA",
        "shadow_color": QColor(0, 40, 25, 200),
    },
}

THEME_NAMES = list(THEMES.keys())

BADGE_STYLES = {
    "URL":       ("rgba(30, 58, 95, 0.9)", "#93C5FD"),
    "Email":     ("rgba(22, 78, 51, 0.9)", "#86EFAC"),
    "Code":      ("rgba(74, 55, 24, 0.9)", "#FDE047"),
    "Text":      ("rgba(45, 45, 60, 0.8)", "#CBD5E1"),
    "Multiline": ("rgba(60, 45, 75, 0.8)", "#E9D5FF"),
    "Image":     ("rgba(30, 70, 90, 0.9)", "#67E8F9"),
}


class LiquidModal(QWidget):
    """
    Apple-grade translucent floating modal with:
    - AttachThreadInput keyboard focus (no clicking needed)
    - 10 theme presets (cycle with T key)
    - Image clip previews
    - Resizable and draggable
    """

    def __init__(
        self,
        on_item_chosen: Callable[[int], None],
        on_autofill_chosen: Callable[[], None]
    ):
        super().__init__()
        self.on_item_chosen = on_item_chosen
        self.on_autofill_chosen = on_autofill_chosen
        self.target_hwnd = None
        self.items: List[ClipItem] = []
        self._drag_pos = None
        self._theme_index = 0

        # Frameless, topmost, tool window
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(380, 120)

        self._init_ui()

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 14, 14, 14)

        # Glass Card Container
        self.card = QFrame()
        self.card.setObjectName("GlassCard")

        # Shadow
        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(48)
        self.shadow_effect.setOffset(0, 12)
        self.card.setGraphicsEffect(self.shadow_effect)

        # Card layout
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 16, 20, 14)
        self.card_layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 4)

        self.logo_label = QLabel("✦ PureClip")
        self.logo_label.setStyleSheet("font-size: 15px; font-weight: 700; font-family: 'Segoe UI';")
        header.addWidget(self.logo_label)

        header.addStretch()

        self.hint_label = QLabel("[1-9] Paste • [Tab] Form fill • [T] Theme • [Esc] Close")
        self.hint_label.setStyleSheet("font-size: 10px; font-family: 'Segoe UI';")
        header.addWidget(self.hint_label)

        self.card_layout.addLayout(header)

        # Rows container
        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(6)
        self.card_layout.addLayout(self.rows_container)

        # Footer with resize grip and theme name
        footer = QHBoxLayout()
        footer.setContentsMargins(2, 4, 2, 0)
        self.theme_name_label = QLabel()
        self.theme_name_label.setStyleSheet("font-size: 10px; font-family: 'Segoe UI';")
        footer.addWidget(self.theme_name_label)
        footer.addStretch()

        grip = QSizeGrip(self)
        grip.setFixedSize(14, 14)
        footer.addWidget(grip)

        self.card_layout.addLayout(footer)

        outer_layout.addWidget(self.card)

        self._apply_theme()
        self.hide()

    def _apply_theme(self):
        name = THEME_NAMES[self._theme_index]
        t = THEMES[name]

        self.card.setStyleSheet(f"""
            #GlassCard {{
                background: {t['bg']};
                border: 1px solid {t['card_border']};
                border-radius: 18px;
            }}
        """)
        self.shadow_effect.setColor(t["shadow_color"])
        self.logo_label.setStyleSheet(f"color: {t['title_color']}; font-size: 15px; font-weight: 700; font-family: 'Segoe UI';")
        self.hint_label.setStyleSheet(f"color: {t['hint_color']}; font-size: 10px; font-family: 'Segoe UI';")
        self.theme_name_label.setText(f"Theme: {name}")
        self.theme_name_label.setStyleSheet(f"color: {t['hint_color']}; font-size: 10px; font-family: 'Segoe UI';")

    def display_palette(self, items: List[ClipItem], target_hwnd: int):
        """Renders items and forces keyboard focus via AttachThreadInput."""
        self.items = items[:9]
        self.target_hwnd = target_hwnd

        # Clear old rows
        while self.rows_container.count():
            w = self.rows_container.takeAt(0)
            if w.widget():
                w.widget().setParent(None)
                w.widget().deleteLater()

        for item in self.items:
            self._add_row(item)

        # Size
        w = max(460, self.minimumWidth())
        h = 90 + (len(self.items) * 52) + 30
        self.setFixedSize(w, h)

        # Position near cursor
        pos = QCursor.pos()
        x, y = pos.x() + 15, pos.y() + 15

        screen = QApplication.primaryScreen().geometry()
        if x + w > screen.width():
            x = pos.x() - w - 15
        if y + h > screen.height():
            y = pos.y() - h - 15

        self.move(max(8, x), max(8, y))
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus(Qt.FocusReason.OtherFocusReason)

        # CRITICAL: Steal keyboard focus from Windows using AttachThreadInput
        QTimer.singleShot(20, self._force_focus)

    def _force_focus(self):
        """Executes the Win32 AttachThreadInput trick to steal keyboard input."""
        hwnd = int(self.winId())
        force_foreground(hwnd)
        self.activateWindow()
        self.setFocus(Qt.FocusReason.OtherFocusReason)

    def _add_row(self, item: ClipItem):
        t = THEMES[THEME_NAMES[self._theme_index]]

        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(f"""
            QFrame {{
                background: {t['row_bg']};
                border: 1px solid {t['row_border']};
                border-radius: 11px;
            }}
            QFrame:hover {{
                background: {t['row_hover_bg']};
                border: 1px solid {t['row_hover_border']};
            }}
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 8, 12, 8)
        row_layout.setSpacing(10)

        # Keycap
        keycap = QLabel(str(item.index))
        keycap.setFixedSize(28, 28)
        keycap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        keycap.setStyleSheet(f"""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 {t['keycap_top']}, stop:1 {t['keycap_bot']});
            border: 1px solid {t['keycap_border']};
            border-bottom: 2px solid rgba(0, 0, 0, 0.5);
            border-radius: 7px;
            color: {t['keycap_text']};
            font-size: 13px; font-weight: 700; font-family: 'Consolas';
        """)
        row_layout.addWidget(keycap)

        # Image thumbnail or text preview
        if item.is_image and item.image_data:
            thumb_label = QLabel()
            try:
                qimg = QImage()
                qimg.loadFromData(item.image_data)
                if not qimg.isNull():
                    pixmap = QPixmap.fromImage(qimg).scaled(
                        32, 32, Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    thumb_label.setPixmap(pixmap)
            except Exception:
                thumb_label.setText("🖼")
            thumb_label.setFixedSize(36, 36)
            thumb_label.setStyleSheet("border: none; background: transparent;")
            row_layout.addWidget(thumb_label)

        text_label = QLabel(item.preview)
        text_label.setStyleSheet(f"""
            color: {t['text_color']};
            font-size: 13px; font-weight: 500; font-family: 'Segoe UI';
            border: none; background: transparent;
        """)
        row_layout.addWidget(text_label, 1)

        # Badge
        bg, fg = BADGE_STYLES.get(item.category, BADGE_STYLES["Text"])
        badge = QLabel(f" {item.category} ")
        badge.setStyleSheet(f"""
            background: {bg}; color: {fg};
            border-radius: 6px; font-size: 10px; font-weight: 600;
            padding: 2px 7px;
        """)
        badge.setFixedHeight(22)
        row_layout.addWidget(badge)

        # Click support
        row.mousePressEvent = lambda e, idx=item.index: self.dismiss_and_paste(idx)
        text_label.mousePressEvent = lambda e, idx=item.index: self.dismiss_and_paste(idx)

        self.rows_container.addWidget(row)
        row.show()

    # ─── Keyboard & Mouse Events ─────────────────────────────────────

    def keyPressEvent(self, event):
        txt = event.text()
        key = event.key()

        if txt in "123456789":
            self.dismiss_and_paste(int(txt))
            return
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            self.dismiss_and_paste(key - Qt.Key.Key_0)
            return
        if key == Qt.Key.Key_Tab:
            self.dismiss_and_autofill()
            return
        if key in (Qt.Key.Key_T,):
            self._cycle_theme()
            return
        if key == Qt.Key.Key_Escape:
            self.hide()
            if self.target_hwnd:
                force_foreground(self.target_hwnd)
            return
        super().keyPressEvent(event)

    def _cycle_theme(self):
        self._theme_index = (self._theme_index + 1) % len(THEME_NAMES)
        self._apply_theme()
        # Re-render rows with new theme
        if self.items:
            saved_items = list(self.items)
            while self.rows_container.count():
                w = self.rows_container.takeAt(0)
                if w.widget():
                    w.widget().setParent(None)
                    w.widget().deleteLater()
            for item in saved_items:
                self._add_row(item)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def dismiss_and_paste(self, index: int):
        self.hide()
        target = self.target_hwnd
        if target:
            force_foreground(target)
        time.sleep(0.05)
        self.on_item_chosen(index)

    def dismiss_and_autofill(self):
        self.hide()
        target = self.target_hwnd
        if target:
            force_foreground(target)
        time.sleep(0.05)
        self.on_autofill_chosen()
