"""
PureClip Main Application (PyQt6)
Coordinates clipboard monitoring, keyboard interception, sound feedback,
image capture, and the Apple Liquid UI modal dispatch.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.buffer import ClipBuffer, ClipItem
from src.core.pipeline import Pipeline
from src.core.clipboard import ClipboardController, play_copy_sound
from src.core.hotkey_v2 import KeyboardInterceptor
from src.analytics.metrics import MetricsTracker
from src.ui.liquid_modal import LiquidModal


class SignalBridge(QObject):
    """Bridges background keyboard events safely to the Qt GUI thread."""
    show_palette = pyqtSignal(int)


class PureClipApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        # Core State
        self.buffer = ClipBuffer(max_size=9)
        self.metrics = MetricsTracker()
        self._last_text_hash = ""
        self._last_image_hash = ""
        self._target_hwnd = None

        # Signal Bridge (thread → Qt main loop)
        self.bridge = SignalBridge()
        self.bridge.show_palette.connect(self._on_show_palette)

        # Apple Liquid Modal
        self.modal = LiquidModal(
            on_item_chosen=self._on_item_chosen,
            on_autofill_chosen=self._on_autofill_chosen
        )

        # Connect Qt clipboard listener (fires on EVERY Ctrl+C system-wide)
        self.clipboard = self.qt_app.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)

        # Low-level keyboard interceptor
        self.interceptor = KeyboardInterceptor(
            should_intercept_paste=self._should_intercept,
            on_trigger_modal=self._on_trigger_modal
        )

    def start(self):
        print("✦ PureClip is running!")
        print("• Copy anything with Ctrl+C (text, links, images).")
        print("• Copy 2+ items → Ctrl+V opens the Liquid Palette.")
        print("• Copy 1 item  → Ctrl+V pastes directly (normal behavior).")
        print("• Alt+V always opens the palette.")
        print("• Press [T] to cycle through 10 theme presets.")
        print("")

        self.interceptor.start()
        sys.exit(self.qt_app.exec())

    def _should_intercept(self) -> bool:
        """Only intercept Ctrl+V when user has copied 2+ items."""
        return len(self.buffer) >= 2

    def _on_trigger_modal(self, target_hwnd: int):
        """Called from background keyboard thread — emits signal to Qt main thread."""
        self._target_hwnd = target_hwnd
        self.bridge.show_palette.emit(target_hwnd)

    def _on_show_palette(self, target_hwnd: int):
        """Runs on Qt GUI thread to display the modal."""
        items = self.buffer.get_all()
        if not items:
            return
        self.modal.display_palette(items, target_hwnd)

    def _on_clipboard_changed(self):
        """Fired whenever the system clipboard changes (any app, any Ctrl+C)."""
        try:
            # Check for image first
            mime = self.clipboard.mimeData()

            if mime and mime.hasImage():
                image = self.clipboard.image()
                if not image.isNull():
                    # Convert QImage to bytes for storage
                    from PyQt6.QtCore import QBuffer, QIODevice
                    buf = QBuffer()
                    buf.open(QIODevice.OpenModeFlag.WriteOnly)
                    image.save(buf, "PNG")
                    img_bytes = bytes(buf.data())
                    buf.close()

                    import hashlib
                    img_hash = hashlib.md5(img_bytes[:1024]).hexdigest()
                    if img_hash != self._last_image_hash:
                        self._last_image_hash = img_hash
                        item = self.buffer.push_image(img_bytes)
                        if item:
                            self.metrics.record_copy(0)
                            play_copy_sound()
                            print(f"[PureClip] ✓ Copied #{item.index}: {item.preview}")
                    return

            # Text
            text = self.clipboard.text()
            if not text:
                return

            import hashlib
            text_hash = hashlib.md5(text.encode()).hexdigest()
            if text_hash == self._last_text_hash:
                return

            self._last_text_hash = text_hash
            _, _, trackers = Pipeline.process(text)
            item = self.buffer.push_text(text)
            if item:
                self.metrics.record_copy(trackers_count=trackers)
                play_copy_sound()
                print(f"[PureClip] ✓ Copied #{item.index}: {item.preview} ({item.category})")

        except Exception as e:
            pass

    def _on_item_chosen(self, index: int):
        """User pressed a digit key in the modal — paste the chosen item."""
        item = self.buffer.get_by_index(index)
        if not item:
            return

        target = self._target_hwnd

        if item.is_image and item.image_data:
            ClipboardController.paste_image_into_window(item.image_data, target)
        else:
            ClipboardController.paste_into_window(item.content, target)

        self.metrics.record_paste(buffer_size_at_paste=len(self.buffer))
        print(f"[PureClip] ✓ Pasted #{index} into active window.")

    def _on_autofill_chosen(self):
        """User pressed Tab — cascade-paste all text items across form fields."""
        items = [it.content for it in self.buffer.get_all() if not it.is_image]
        target = self._target_hwnd
        if items:
            ClipboardController.auto_fill_form(items, target)
            self.metrics.record_form_fill(item_count=len(items))
            print(f"[PureClip] ✓ Auto-filled {len(items)} fields.")


if __name__ == "__main__":
    app = PureClipApp()
    app.start()
