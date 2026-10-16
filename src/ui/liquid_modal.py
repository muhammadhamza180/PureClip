"""
PureClip Apple Liquid UI Modal (PyQt6)
Ultra-sleek, hardware-accelerated frosted glass palette with Apple aesthetics,
ambient drop shadow, tactile mechanical keycaps, zero-click keyboard focus,
and smooth draggable positioning.
"""

import sys
import time
import ctypes
import win32gui
from typing import Callable, List, Optional
from PyQt6.QtCore import Qt, QPoint
from PyQt6.QtGui import QColor, QFont, QCursor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGraphicsDropShadowEffect, QFrame, QApplication
)
from src.core.buffer import ClipItem
from src.core.clipboard import safe_set_foreground


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
        self._drag_pos = None

        # Frameless, translucent, stays on top, tool window (no taskbar clutter)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._init_ui()

    def _init_ui(self):
        # Outer layout with padding for ambient drop shadow
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(16, 16, 16, 16)

        # Glass Container Card
        self.card = QFrame()
        self.card.setObjectName("GlassCard")
        self.card.setStyleSheet("""
            #GlassCard {
                background: rgba(18, 18, 26, 0.94);
                border: 1px solid rgba(255, 255, 255, 0.16);
                border-radius: 20px;
            }
        """)

        # Ambient Glow / Soft Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(46)
        shadow.setColor(QColor(0, 0, 0, 190))
        shadow.setOffset(0, 12)
        self.card.setGraphicsEffect(shadow)

        # Card Inner Layout
        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(20, 18, 20, 18)
        self.card_layout.setSpacing(10)

        # Header Frame
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(2, 0, 2, 6)

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

        # Cleanly clear old rows
        while self.rows_container.count():
            item_widget = self.rows_container.takeAt(0)
            if item_widget.widget():
                item_widget.widget().setParent(None)
                item_widget.widget().deleteLater()

        # Render each clip row and ensure it is set visible
        for item in self.items:
            self._add_row(item)

        # Calculate exact dimensions so card never collapses
        fixed_width = 500
        calculated_height = 80 + (len(self.items) * 56) + 32  # 32 for shadow padding
        self.setFixedSize(fixed_width, calculated_height)

        # Position right near current mouse cursor using reliable QCursor
        cursor_pos = QCursor.pos()
        x = cursor_pos.x() + 15
        y = cursor_pos.y() + 15

        screen = QApplication.primaryScreen().geometry()
        if x + fixed_width > screen.width():
            x = cursor_pos.x() - fixed_width - 15
        if y + calculated_height > screen.height():
            y = cursor_pos.y() - calculated_height - 15

        self.move(max(10, x), max(10, y))
        self.show()
        self.raise_()
        self.activateWindow()
        self.setFocus()

        # Bring window to foreground in Windows OS without mouse click
        hwnd = int(self.winId())
        safe_set_foreground(hwnd)

    def _add_row(self, item: ClipItem):
        row = QFrame()
        row.setObjectName(f"Row_{item.index}")
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet("""
            QFrame {
                background: rgba(30, 32, 46, 0.78);
                border: 1px solid rgba(255, 255, 255, 0.09);
                border-radius: 12px;
            }
            QFrame:hover {
                background: rgba(45, 48, 72, 0.95);
                border: 1px solid rgba(129, 140, 248, 0.45);
            }
        """)

        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 10, 14, 10)
        row_layout.setSpacing(12)

        # Tactile 3D Keycap Badge [ 1 ]
        keycap = QLabel(str(item.index))
        keycap.setFixedSize(28, 28)
        keycap.setAlignment(Qt.AlignmentFlag.AlignCenter)
        keycap.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #424660, stop:1 #272A3C);
            border: 1px solid rgba(255, 255, 255, 0.25);
            border-bottom: 2px solid rgba(0, 0, 0, 0.6);
            border-radius: 7px;
            color: #FFFFFF;
            font-size: 13px;
            font-weight: 700;
            font-family: 'Consolas', monospace;
        """)
        row_layout.addWidget(keycap)

        # Clean Preview Text
        text_label = QLabel(item.preview)
        text_label.setStyleSheet("""
            color: #F8FAFC;
            font-size: 13px;
            font-weight: 500;
            font-family: 'Segoe UI', -apple-system, sans-serif;
            border: none;
            background: transparent;
        """)
        row_layout.addWidget(text_label, 1)

        # Category Pill Badge
        cat_style = self._get_badge_style(item.category)
        badge = QLabel(f" {item.category} ")
        badge.setStyleSheet(cat_style)
        badge.setFixedHeight(22)
        row_layout.addWidget(badge)

        # Click interaction support
        row.mousePressEvent = lambda e, idx=item.index: self.dismiss_and_paste(idx)
        text_label.mousePressEvent = lambda e, idx=item.index: self.dismiss_and_paste(idx)

        self.rows_container.addWidget(row)
        # Explicitly make sure row is visible
        row.show()

    def _get_badge_style(self, category: str) -> str:
        styles = {
            "URL": "background: rgba(30, 58, 95, 0.9); color: #93C5FD; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 7px;",
            "Email": "background: rgba(22, 78, 51, 0.9); color: #86EFAC; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 7px;",
            "Code": "background: rgba(74, 55, 24, 0.9); color: #FDE047; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 7px;",
            "Text": "background: rgba(45, 45, 60, 0.85); color: #CBD5E1; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 7px;",
            "Multiline": "background: rgba(60, 45, 75, 0.85); color: #E9D5FF; border-radius: 6px; font-size: 10px; font-weight: 600; padding: 2px 7px;"
        }
        return styles.get(category, styles["Text"])

    def mousePressEvent(self, event):
        """Allows dragging the modal anywhere on the screen."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """Performs smooth window dragging."""
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def keyPressEvent(self, event):
        """Intercepts keyboard events immediately when palette is shown."""
        txt = event.text()
        key = event.key()

        # Handle numeric keys [1-9]
        if txt in "123456789" and txt:
            self.dismiss_and_paste(int(txt))
            return

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
            if self.target_hwnd:
                safe_set_foreground(self.target_hwnd)
            return

        super().keyPressEvent(event)

    def dismiss_and_paste(self, index: int):
        """Hides the modal, restores focus to target app, and sends paste."""
        self.hide()
        target = self.target_hwnd
        if target:
            safe_set_foreground(target)
        time.sleep(0.04)
        self.on_item_chosen(index)

    def dismiss_and_autofill(self):
        """Hides modal and executes multi-field cascade paste."""
        self.hide()
        target = self.target_hwnd
        if target:
            safe_set_foreground(target)
        time.sleep(0.04)
        self.on_autofill_chosen()
