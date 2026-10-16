"""
PureClip Main Application (PyQt6)
- Global keyboard interception: 1-9 paste instantly without clicking modal
- Wispr Flow style animated toast confirmation on copy
- Smart copy support (middle-click to copy without highlighting)
- Text and image clipboard support
- 12 Designer Modal Themes
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
from src.core.smart_copy import SmartCopyMonitor
from src.analytics.metrics import MetricsTracker
from src.ui.liquid_modal import LiquidModal
from src.ui.toast import CopyNotificationToast


class SignalBridge(QObject):
    """Bridges background thread events safely to the Qt GUI main thread."""
    show_palette = pyqtSignal(int)
    modal_key_action = pyqtSignal(str, int)
    show_copy_toast = pyqtSignal(str, int)


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

        # Signal Bridge
        self.bridge = SignalBridge()
        self.bridge.show_palette.connect(self._on_show_palette)
        self.bridge.modal_key_action.connect(self._on_modal_key_action)
        self.bridge.show_copy_toast.connect(self._on_show_copy_toast)

        # Apple Liquid Modal
        self.modal = LiquidModal(
            on_item_chosen=self._on_item_chosen,
            on_autofill_chosen=self._on_autofill_chosen
        )

        # Wispr Flow style toast notification
        self.toast = CopyNotificationToast()

        # Connect Qt clipboard listener
        self.clipboard = self.qt_app.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)

        # Low-level keyboard interceptor
        self.interceptor = KeyboardInterceptor(
            should_intercept_paste=self._should_intercept,
            is_modal_active=self._is_modal_active,
            on_trigger_modal=self._on_trigger_modal,
            on_modal_key=self._on_modal_key_thread
        )

        # Smart copy monitor (middle-click to copy)
        self.smart_copy = SmartCopyMonitor(on_copy_action=lambda: None)

    def start(self):
        print("✦ PureClip Apple Liquid UI is active!")
        print("• Copy anything with Ctrl+C (text, links, images).")
        print("• Wispr Flow style toast confirms every copy!")
        print("• Middle-click any link/text for Smart Copy.")
        print("• Copy 2+ items → Ctrl+V opens Liquid Palette.")
        print("• Press 1-9 to paste INSTANTLY (ZERO CLICKING NEEDED!).")
        print("• Press [T] to cycle 12 themes.")
        print("")

        self.interceptor.start()
        self.smart_copy.start()
        sys.exit(self.qt_app.exec())

    def _is_modal_active(self) -> bool:
        """Returns True if modal is currently shown and active."""
        return self.modal.isVisible()

    def _should_intercept(self) -> bool:
        """Only intercept Ctrl+V when user has staged 2+ items."""
        return len(self.buffer) >= 2

    def _on_trigger_modal(self, target_hwnd: int):
        self._target_hwnd = target_hwnd
        self.bridge.show_palette.emit(target_hwnd)

    def _on_modal_key_thread(self, action: str, val: int):
        """Called from global keyboard hook when modal is open."""
        self.bridge.modal_key_action.emit(action, val)

    def _on_modal_key_action(self, action: str, val: int):
        """Executes modal actions directly on GUI thread from global keypresses."""
        if not self.modal.isVisible():
            return

        if action == "digit":
            self.modal.dismiss_and_paste(val)
        elif action == "tab":
            self.modal.dismiss_and_autofill()
        elif action == "esc":
            self.modal.hide()
            if self._target_hwnd:
                from src.core.clipboard import force_foreground
                force_foreground(self._target_hwnd)
        elif action == "theme":
            self.modal.cycle_theme()

    def _on_show_palette(self, target_hwnd: int):
        items = self.buffer.get_all()
        if not items:
            return
        self.modal.display_palette(items, target_hwnd)

    def _on_show_copy_toast(self, text: str, count: int):
        self.toast.show_toast(text, count)

    def _on_clipboard_changed(self):
        """Fired whenever clipboard updates system-wide."""
        try:
            mime = self.clipboard.mimeData()

            # Image
            if mime and mime.hasImage():
                image = self.clipboard.image()
                if not image.isNull():
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
                            self.bridge.show_copy_toast.emit("[Image]", len(self.buffer))
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
                self.bridge.show_copy_toast.emit(item.preview, len(self.buffer))
                print(f"[PureClip] ✓ Copied #{item.index}: {item.preview} ({item.category})")

        except Exception as e:
            pass

    def _on_item_chosen(self, index: int):
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
        items = [it.content for it in self.buffer.get_all() if not it.is_image]
        target = self._target_hwnd
        if items:
            ClipboardController.auto_fill_form(items, target)
            self.metrics.record_form_fill(item_count=len(items))
            print(f"[PureClip] ✓ Auto-filled {len(items)} fields.")


if __name__ == "__main__":
    app = PureClipApp()
    app.start()
