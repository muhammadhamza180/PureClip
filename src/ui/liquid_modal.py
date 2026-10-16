"""
PureClip Apple Liquid UI Modal (PyQt6)
Features:
- Global key interception routing (keys 1-9 work directly without clicking!)
- 12 Designer Theme Presets (cycle via [T] key)
- Resizable window with QSizeGrip & draggable header
- Robust widget clearing that never crashes
- Image clip thumbnail previews
- Ambient drop shadow and frosted glass aesthetic
"""

import time
from typing import Callable, List
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QCursor, QPixmap, QImage
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QFrame, QApplication,
    QSizeGrip
)
from src.core.buffer import ClipItem
from src.core.clipboard import force_foreground

# ─── 12 Distinct Designer Themes ──────────────────────────────────────────
THEMES = {
    "Midnight Obsidian": {
        "bg": "rgba(14, 14, 22, 0.94)",
        "card_border": "rgba(255, 255, 255, 0.14)",
        "row_bg": "rgba(28, 30, 44, 0.82)",
        "row_hover_bg": "rgba(48, 52, 78, 0.96)",
        "row_hover_border": "rgba(129, 140, 248, 0.55)",
        "row_border": "rgba(255, 255, 255, 0.08)",
        "title_color": "#818CF8",
        "hint_color": "#94A3B8",
        "text_color": "#F8FAFC",
        "keycap_top": "#424660", "keycap_bot": "#272A3C",
        "keycap_border": "rgba(255, 255, 255, 0.25)",
        "keycap_text": "#FFFFFF",
        "shadow_color": QColor(0, 0, 0, 200),
    },
    "Arctic Pure": {
        "bg": "rgba(242, 245, 250, 0.96)",
        "card_border": "rgba(0, 0, 0, 0.12)",
        "row_bg": "rgba(255, 255, 255, 0.94)",
        "row_hover_bg": "rgba(230, 235, 245, 1.0)",
        "row_hover_border": "rgba(99, 102, 241, 0.45)",
        "row_border": "rgba(0, 0, 0, 0.07)",
        "title_color": "#4F46E5",
        "hint_color": "#64748B",
        "text_color": "#0F172A",
        "keycap_top": "#E8ECF2", "keycap_bot": "#D1D5DB",
        "keycap_border": "rgba(0, 0, 0, 0.18)",
        "keycap_text": "#0F172A",
        "shadow_color": QColor(0, 0, 0, 70),
    },
    "Emerald Glow": {
        "bg": "rgba(10, 24, 18, 0.95)",
        "card_border": "rgba(52, 211, 153, 0.25)",
        "row_bg": "rgba(18, 42, 32, 0.82)",
        "row_hover_bg": "rgba(28, 64, 48, 0.96)",
        "row_hover_border": "rgba(52, 211, 153, 0.55)",
        "row_border": "rgba(52, 211, 153, 0.12)",
        "title_color": "#34D399",
        "hint_color": "#6EE7B7",
        "text_color": "#F0FDF4",
        "keycap_top": "#1A4230", "keycap_bot": "#0F2E20",
        "keycap_border": "rgba(52, 211, 153, 0.35)",
        "keycap_text": "#ECFDF5",
        "shadow_color": QColor(0, 25, 12, 190),
    },
    "Sunset Amber": {
        "bg": "rgba(28, 14, 12, 0.95)",
        "card_border": "rgba(251, 146, 60, 0.25)",
        "row_bg": "rgba(44, 22, 18, 0.82)",
        "row_hover_bg": "rgba(66, 32, 24, 0.96)",
        "row_hover_border": "rgba(251, 146, 60, 0.55)",
        "row_border": "rgba(251, 146, 60, 0.12)",
        "title_color": "#FB923C",
        "hint_color": "#FDBA74",
        "text_color": "#FFF7ED",
        "keycap_top": "#422616", "keycap_bot": "#2B1A10",
        "keycap_border": "rgba(251, 146, 60, 0.35)",
        "keycap_text": "#FFF7ED",
        "shadow_color": QColor(25, 6, 0, 190),
    },
    "Royal Velvet": {
        "bg": "rgba(20, 12, 30, 0.95)",
        "card_border": "rgba(168, 85, 247, 0.25)",
        "row_bg": "rgba(34, 20, 52, 0.82)",
        "row_hover_bg": "rgba(54, 34, 80, 0.96)",
        "row_hover_border": "rgba(168, 85, 247, 0.55)",
        "row_border": "rgba(168, 85, 247, 0.12)",
        "title_color": "#A855F7",
        "hint_color": "#C084FC",
        "text_color": "#FAF5FF",
        "keycap_top": "#321A52", "keycap_bot": "#1E0F34",
        "keycap_border": "rgba(168, 85, 247, 0.35)",
        "keycap_text": "#F5F3FF",
        "shadow_color": QColor(15, 0, 25, 190),
    },
    "Ocean Blue": {
        "bg": "rgba(8, 18, 32, 0.95)",
        "card_border": "rgba(56, 189, 248, 0.25)",
        "row_bg": "rgba(14, 30, 52, 0.82)",
        "row_hover_bg": "rgba(22, 48, 78, 0.96)",
        "row_hover_border": "rgba(56, 189, 248, 0.55)",
        "row_border": "rgba(56, 189, 248, 0.12)",
        "title_color": "#38BDF8",
        "hint_color": "#7DD3FC",
        "text_color": "#F0F9FF",
        "keycap_top": "#0F2E4A", "keycap_bot": "#0A1F34",
        "keycap_border": "rgba(56, 189, 248, 0.35)",
        "keycap_text": "#F0F9FF",
        "shadow_color": QColor(0, 12, 28, 190),
    },
    "Rose Blush": {
        "bg": "rgba(30, 16, 20, 0.95)",
        "card_border": "rgba(251, 113, 133, 0.25)",
        "row_bg": "rgba(48, 24, 30, 0.82)",
        "row_hover_bg": "rgba(70, 34, 44, 0.96)",
        "row_hover_border": "rgba(251, 113, 133, 0.55)",
        "row_border": "rgba(251, 113, 133, 0.12)",
        "title_color": "#FB7185",
        "hint_color": "#FDA4AF",
        "text_color": "#FFF1F2",
        "keycap_top": "#441E26", "keycap_bot": "#2C121A",
        "keycap_border": "rgba(251, 113, 133, 0.35)",
        "keycap_text": "#FFF1F2",
        "shadow_color": QColor(25, 5, 10, 190),
    },
    "Charcoal Dark": {
        "bg": "rgba(26, 26, 26, 0.96)",
        "card_border": "rgba(255, 255, 255, 0.10)",
        "row_bg": "rgba(42, 42, 42, 0.82)",
        "row_hover_bg": "rgba(58, 58, 58, 0.96)",
        "row_hover_border": "rgba(255, 255, 255, 0.25)",
        "row_border": "rgba(255, 255, 255, 0.06)",
        "title_color": "#FFFFFF",
        "hint_color": "#A3A3A3",
        "text_color": "#FAFAFA",
        "keycap_top": "#4E4E4E", "keycap_bot": "#343434",
        "keycap_border": "rgba(255, 255, 255, 0.20)",
        "keycap_text": "#FFFFFF",
        "shadow_color": QColor(0, 0, 0, 170),
    },
    "Cyber Neon": {
        "bg": "rgba(8, 8, 18, 0.96)",
        "card_border": "rgba(0, 255, 170, 0.30)",
        "row_bg": "rgba(14, 16, 32, 0.85)",
        "row_hover_bg": "rgba(22, 28, 56, 0.96)",
        "row_hover_border": "rgba(0, 255, 170, 0.65)",
        "row_border": "rgba(0, 255, 170, 0.14)",
        "title_color": "#00FFAA",
        "hint_color": "#66FFD0",
        "text_color": "#E0FFF0",
        "keycap_top": "#0C2018", "keycap_bot": "#06140E",
        "keycap_border": "rgba(0, 255, 170, 0.40)",
        "keycap_text": "#00FFAA",
        "shadow_color": QColor(0, 45, 30, 210),
    },
    "Tokyo Night": {
        "bg": "rgba(18, 20, 34, 0.96)",
        "card_border": "rgba(122, 162, 247, 0.25)",
        "row_bg": "rgba(26, 30, 50, 0.82)",
        "row_hover_bg": "rgba(38, 44, 74, 0.96)",
        "row_hover_border": "rgba(122, 162, 247, 0.55)",
        "row_border": "rgba(122, 162, 247, 0.10)",
        "title_color": "#7AA2F7",
        "hint_color": "#9AA5CE",
        "text_color": "#C0CAF5",
        "keycap_top": "#2D3456", "keycap_bot": "#1C2036",
        "keycap_border": "rgba(122, 162, 247, 0.30)",
        "keycap_text": "#C0CAF5",
        "shadow_color": QColor(10, 12, 25, 190),
    },
    "Coffee Warmth": {
        "bg": "rgba(26, 20, 16, 0.96)",
        "card_border": "rgba(217, 160, 102, 0.25)",
        "row_bg": "rgba(42, 32, 26, 0.82)",
        "row_hover_bg": "rgba(60, 46, 36, 0.96)",
        "row_hover_border": "rgba(217, 160, 102, 0.55)",
        "row_border": "rgba(217, 160, 102, 0.10)",
        "title_color": "#D9A066",
        "hint_color": "#E5C29F",
        "text_color": "#F5EBE0",
        "keycap_top": "#443428", "keycap_bot": "#2C2018",
        "keycap_border": "rgba(217, 160, 102, 0.30)",
        "keycap_text": "#F5EBE0",
        "shadow_color": QColor(20, 12, 8, 190),
    },
    "Monochrome Steel": {
        "bg": "rgba(20, 22, 26, 0.96)",
        "card_border": "rgba(148, 163, 184, 0.20)",
        "row_bg": "rgba(32, 36, 44, 0.82)",
        "row_hover_bg": "rgba(46, 52, 64, 0.96)",
        "row_hover_border": "rgba(148, 163, 184, 0.50)",
        "row_border": "rgba(148, 163, 184, 0.10)",
        "title_color": "#E2E8F0",
        "hint_color": "#94A3B8",
        "text_color": "#F8FAFC",
        "keycap_top": "#384050", "keycap_bot": "#242A36",
        "keycap_border": "rgba(148, 163, 184, 0.30)",
        "keycap_text": "#F8FAFC",
        "shadow_color": QColor(5, 8, 12, 180),
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
    Apple-grade translucent floating modal.
    Keys 1-9 paste instantly without clicking!
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

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMinimumSize(420, 140)

        self._init_ui()

    def _init_ui(self):
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(14, 14, 14, 14)

        self.card = QFrame()
        self.card.setObjectName("GlassCard")

        self.shadow_effect = QGraphicsDropShadowEffect(self)
        self.shadow_effect.setBlurRadius(46)
        self.shadow_effect.setOffset(0, 10)
        self.card.setGraphicsEffect(self.shadow_effect)

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(18, 16, 18, 14)
        self.card_layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 4)

        self.logo_label = QLabel("✦ PureClip")
        self.logo_label.setStyleSheet("font-size: 15px; font-weight: 700; font-family: 'Segoe UI';")
        header.addWidget(self.logo_label)

        header.addStretch()

        self.hint_label = QLabel("[1-9] Paste  •  [Tab] Form fill  •  [T] Theme  •  [Esc] Close")
        self.hint_label.setStyleSheet("font-size: 11px; font-family: 'Segoe UI';")
        header.addWidget(self.hint_label)

        self.card_layout.addLayout(header)

        # Rows container
        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(6)
        self.card_layout.addLayout(self.rows_container)

        # Footer
        footer = QHBoxLayout()
        footer.setContentsMargins(2, 4, 2, 0)
        self.theme_name_label = QLabel()
        self.theme_name_label.setStyleSheet("font-size: 10px; font-family: 'Segoe UI';")
        footer.addWidget(self.theme_name_label)
        footer.addStretch()

        # Resizable corner grip
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
        self.hint_label.setStyleSheet(f"color: {t['hint_color']}; font-size: 11px; font-family: 'Segoe UI';")
        self.theme_name_label.setText(f"🎨 Theme: {name} ({self._theme_index + 1}/{len(THEME_NAMES)})")
        self.theme_name_label.setStyleSheet(f"color: {t['hint_color']}; font-size: 10px; font-family: 'Segoe UI';")

    def display_palette(self, items: List[ClipItem], target_hwnd: int):
        """Renders items, positions near cursor, and opens palette."""
        self.items = items[:9]
        self.target_hwnd = target_hwnd

        # Cleanly remove old row widgets without NoneType crash
        while self.rows_container.count() > 0:
            layout_item = self.rows_container.takeAt(0)
            if layout_item is not None:
                w = layout_item.widget()
                if w is not None:
                    w.setParent(None)
                    w.deleteLater()

        for item in self.items:
            self._add_row(item)

        # Geometry
        w = max(480, self.width() if self.isVisible() else 480)
        h = 92 + (len(self.items) * 54) + 28
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

        # Tactile Keycap
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
                        34, 34, Qt.AspectRatioMode.KeepAspectRatio,
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

        # Click fallback
        row.mousePressEvent = lambda e, idx=item.index: self.dismiss_and_paste(idx)
        text_label.mousePressEvent = lambda e, idx=item.index: self.dismiss_and_paste(idx)

        self.rows_container.addWidget(row)
        row.show()

    def cycle_theme(self):
        """Cycles to next theme preset."""
        self._theme_index = (self._theme_index + 1) % len(THEME_NAMES)
        self._apply_theme()
        if self.items:
            saved = list(self.items)
            while self.rows_container.count() > 0:
                item = self.rows_container.takeAt(0)
                if item and item.widget():
                    item.widget().setParent(None)
                    item.widget().deleteLater()
            for it in saved:
                self._add_row(it)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

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
        if key == Qt.Key.Key_T:
            self.cycle_theme()
            return
        if key == Qt.Key.Key_Escape:
            self.hide()
            if self.target_hwnd:
                force_foreground(self.target_hwnd)
            return
        super().keyPressEvent(event)

    def dismiss_and_paste(self, index: int):
        self.hide()
        target = self.target_hwnd
        if target:
            force_foreground(target)
        time.sleep(0.04)
        self.on_item_chosen(index)

    def dismiss_and_autofill(self):
        self.hide()
        target = self.target_hwnd
        if target:
            force_foreground(target)
        time.sleep(0.04)
        self.on_autofill_chosen()
