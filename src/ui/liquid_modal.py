"""
PureClip Apple Liquid UI Modal (PyQt6)
Ultra-sleek, hardware-accelerated frosted glass palette with Apple aesthetics,
ambient drop shadow, tactile mechanical keycaps, and zero-click keyboard focus.
"""

import sys
import time
import win32gui
from typing import Callable, List, Optional
from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QObject
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QFrame, QApplication
)
from src.core.buffer import ClipItem


class LiquidModal(QWidget):
    """
    Apple-grade translucent floating modal with tactile keycaps.
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

        # Frameless, translucent, stays on top, tool window (no taskbar item)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._init_ui()

    def _init_ui(self):
        # Outer layout with padding for the drop shadow
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)

        # Glass Container Card
        self.card = QFrame()
        self.card.setObjectName("GlassCard")
        self.card.setStyleSheet("""
            #GlassCard {
                background: rgba(18, 18, 26, 0.88);
                border: 1px solid rgba(255, 255, 255, 0.14);
                border-radius: 20px;
            }
        """)

        # Ambient Glow / Drop Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(42)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        # Card Inner Layout
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 18, 20, 18)
        self.card_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 0, 2, 4)

        self.logo_label = QLabel("✦ PureClip")
        self.logo_label.setStyleSheet("""
            color: #818CF8;
            font-size: 15px;
            font-weight: 700;
            font-family: 'Segoe UI', -apple-system, sans-serif;
            letter-spacing: 0.5px;
        """)
        header_layout.addWidget(self.logo_label)

        header_layout.addStretch()

        self.hint_label = QLabel("Tap [1-3] to paste  •  [Tab] Form fill  •  [Esc] Close")
        self.hint_label.setStyleSheet("""
            color: #94A3B8;
            font-size: 11px;
            font-family: 'Segoe UI', -apple-system, sans-serif;
        """)
        header_layout.addWidget(self.hint_label)

        self.card_layout.addLayout(header_layout)

        # Rows Container
        self.rows_container = QVBoxLayout()
        self.rows_container.setSpacing(8)
        self.card_layout.addLayout(self.rows_container)

        outer_layout.addWidget(self.card)

    def display_palette(self, items: List[ClipItem], target_hwnd: int):
        """Populates items, positions at cursor, and forces keyboard focus."""
        self.items = items[:5]
        self.target_hwnd = target_hwnd

        # Clear existing rows
        while self.rows_container.count():
            child = self.rows_container.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Render clip rows
        for item in self.items:
            self._add_row(item)

        # Adjust size and position
        self.adjustSize()
        cursor_pos = win32gui.GetCursorPos()
        x = cursor_pos[0] + 12
        y = cursor_pos[1] + 12

        screen = QApplication.primaryScreen().geometry()
        if x + self.width() > screen.width():
            x = cursor_pos[0] - self.width() - 12
        if y + self.height() > screen.height():
            y = cursor_pos[1] - self.height() - 12

        self.move(max(10, x), max(10, y))
        self.show()
        self.raise_()
        self.activateWindow()

        # Force Windows OS to focus this window immediately without mouse click
        hwnd = int(self.winId())
        win32gui.SetForegroundWindow(hwnd)

    def _add_row(self, item: ClipItem):
        row = QFrame()
        row.setObjectName(f"Row_{item.index}")
        row.setStyleSheet("""
            QFrame {
                background: rgba(30, 32, 46, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 12px;
            }
            QFrame:hover {
                background: rgba(45, 48, 70, 0.90);
                border: 1px solid rgba(129, 140, 248, 0.40);
            }
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(10, 8, 12, 8)
        row_layout.setSpacing(12)

        # Tactile Keycap
        keycap = QLabel(str(item.index))
        keycap.setFixedSize(26, 26)
        keycap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        keycap.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #3E4259, stop:1 #272A3C);
            border: 1px solid rgba(255, 255, 255, 0.22);
            border-bottom: 2px solid rgba(0, 0, 0, 0.5);
            border-radius: 6px;
            color: #FFFFFF;
            font-size: 12px;
            font-weight: 700;
            font-family: 'Consolas', monospace;
        """)
        row_layout.addWidget(keycap)

        # Text Preview
        preview_text = item.preview
        text_label = QLabel(preview_text)
        text_label.setStyleSheet("""
            color: #F8FAFC;
            font-size: 13px;
            font-family: 'Segoe UI', -apple-system, sans-serif;
            border: none;
            background: transparent;
        """)
        row_layout.addWidget(text_label, 1)

        # Category Badge
        cat_style = self._get_badge_style(item.category)
        badge = QLabel(f" {item.category} ")
        badge.setStyleSheet(cat_style)
        badge.setFixedHeight(22)
        row_layout.addWidget(badge)

        self.rows_container.addWidget(row)

    def _get_badge_style(self, category: str) -> str:
        styles = {
            "URL": "background: rgba(30, 58, 95, 0.9); color: #93C5FD; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 6px;",
            "Email": "background: rgba(22, 78, 51, 0.9); color: #86EFAC; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 6px;",
            "Code": "background: rgba(74, 55, 24, 0.9); color: #FDE047; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 6px;",
            "Text": "background: rgba(45, 45, 60, 0.8); color: #CBD5E1; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 6px;",
            "Multiline": "background: rgba(60, 45, 75, 0.8); color: #E9D5FF; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 6px;"
        }
        return styles.get(category, styles["Text"])

    def keyPressEvent(self, event):
        """Intercepts keyboard events immediately when palette is shown."""
        key = event.key()

        # Handle numeric keys [1-9]
        if Qt.Key.Key_1 <= key <= Qt.Key.Key_9:
            digit = key - Qt.Key.Key_0
            self.dismiss_and_paste(digit)
            return

        # Handle Tab (Form auto-fill)
        if key == Qt.Key.Key_Tab:
            self.dismiss_and_autofill()
            return

        # Handle Escape (Cancel)
        if key == Qt.Key.Key_Escape:
            self.hide()
            # Return focus to target
            if self.target_hwnd:
                win32gui.SetForegroundWindow(self.target_hwnd)
            return

        super().keyPressEvent(event)

    def dismiss_and_paste(self, index: int):
        """Hides the modal, restores focus to target app, and sends paste."""
        self.hide()
        target = self.target_hwnd
        # Restore focus to target window before pasting
        if target:
            try:
                win32gui.SetForegroundWindow(target)
            except Exception:
                pass
        # Execute callback after brief OS focus transition
        self.on_item_chosen(index)

    def dismiss_and_autofill(self):
        """Hides modal and executes multi-field cascade paste."""
        self.hide()
        target = self.target_hwnd
        if target:
            try:
                win32gui.SetForegroundWindow(target)
            except Exception:
                pass
        self.on_autofill_chosen()
