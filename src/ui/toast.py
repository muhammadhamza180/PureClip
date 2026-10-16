"""
PureClip Wispr Flow Style Toast Notification
Floating micro-pill HUD that appears smoothly upon successful copy and fades out.
"""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QCursor
from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QFrame,
    QGraphicsDropShadowEffect, QApplication
)


class CopyNotificationToast(QWidget):
    """
    Sleek, Dynamic Island / Wispr Flow style animated pill notification.
    Appears near top center or cursor when text/image is copied.
    """

    def __init__(self):
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.SubWindow
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)

        self._init_ui()
        self._fade_timer = QTimer(self)
        self._fade_timer.setSingleShot(True)
        self._fade_timer.timeout.connect(self._start_fade_out)

    def _init_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        self.pill = QFrame()
        self.pill.setStyleSheet("""
            QFrame {
                background: rgba(18, 20, 30, 0.94);
                border: 1px solid rgba(129, 140, 248, 0.40);
                border-radius: 16px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(28)
        shadow.setColor(QColor(0, 0, 0, 180))
        shadow.setOffset(0, 6)
        self.pill.setGraphicsEffect(shadow)

        pill_layout = QHBoxLayout(self.pill)
        pill_layout.setContentsMargins(14, 8, 14, 8)
        pill_layout.setSpacing(8)

        # Checkmark Icon
        self.icon_label = QLabel("✓")
        self.icon_label.setStyleSheet("""
            color: #34D399;
            font-size: 13px;
            font-weight: bold;
            font-family: 'Segoe UI';
        """)
        pill_layout.addWidget(self.icon_label)

        # Copied Title
        self.title_label = QLabel("Copied")
        self.title_label.setStyleSheet("""
            color: #F8FAFC;
            font-size: 12px;
            font-weight: 600;
            font-family: 'Segoe UI';
        """)
        pill_layout.addWidget(self.title_label)

        # Item Preview Snippet
        self.snippet_label = QLabel()
        self.snippet_label.setStyleSheet("""
            color: #94A3B8;
            font-size: 11px;
            font-family: 'Segoe UI';
        """)
        pill_layout.addWidget(self.snippet_label)

        layout.addWidget(self.pill)

    def show_toast(self, text: str, count: int = 1):
        """Displays toast with preview text and starts auto-hide timer."""
        one_line = text.replace("\n", " ").strip()
        if len(one_line) > 30:
            one_line = one_line[:27] + "..."

        self.snippet_label.setText(f"• {one_line} (#{count})")
        self.adjustSize()

        # Position at top center of primary screen (Wispr Flow style)
        screen = QApplication.primaryScreen().geometry()
        x = (screen.width() - self.width()) // 2
        y = 28

        self.move(x, y)
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()

        # Auto-hide after 1.4 seconds
        self._fade_timer.stop()
        self._fade_timer.start(1400)

    def _start_fade_out(self):
        self.hide()
