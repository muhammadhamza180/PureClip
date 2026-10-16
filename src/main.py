"""
PureClip Main Application (PyQt6 Core)
Apple Liquid UI, Zero-Click Keyboard Dispatch, and Multi-Copy Auto-Detect.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QObject, pyqtSignal

from src.core.buffer import ClipBuffer
from src.core.pipeline import Pipeline
from src.core.clipboard import ClipboardController
from src.core.hotkey_v2 import KeyboardInterceptor
from src.analytics.metrics import MetricsTracker
from src.ui.liquid_modal import LiquidModal


class SignalBridge(QObject):
    """Bridges background keyboard hook events safely to the Qt GUI thread."""
    show_palette = pyqtSignal(int)  # passes target_hwnd


class PureClipApp:
    def __init__(self):
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setQuitOnLastWindowClosed(False)

        # Core State
        self.buffer = ClipBuffer(max_size=9)
        self.metrics = MetricsTracker()
        
        # Staged items for the current copy session
        # If user copies >= 2 items, Ctrl+V opens the picker
        # If user copies 1 item, Ctrl+V pastes directly
        self.staged_clips = []
        self._last_copied_raw = ""
        self._target_hwnd = None

        # Signal Bridge
        self.bridge = SignalBridge()
        self.bridge.show_palette.connect(self._on_show_palette_slot)

        # Apple Liquid Modal
        self.modal = LiquidModal(
            on_item_chosen=self._on_item_chosen,
            on_autofill_chosen=self._on_autofill_chosen
        )

        # Connect Native Clipboard Listener
        self.clipboard = self.qt_app.clipboard()
        self.clipboard.dataChanged.connect(self._on_clipboard_changed)

        # Low-Level Keyboard Interceptor
        self.interceptor = KeyboardInterceptor(
            should_intercept_paste=self._should_intercept_paste,
            on_trigger_modal=self._on_trigger_modal_hook
        )

    def start(self):
        """Starts listeners and main Qt event loop."""
        print("✦ PureClip Apple Liquid UI is active!")
        print("• Copy 1 item: standard Ctrl+V pastes directly.")
        print("• Copy 2+ items: Ctrl+V automatically summons the Liquid Palette.")
        print("• Press 1, 2, or 3 to paste into your active input without touching the mouse.")
        print("• Press Alt+V anytime to view your full clipboard history.")

        self.interceptor.start()
        sys.exit(self.qt_app.exec())

    def _should_intercept_paste(self) -> bool:
        """Determines if Ctrl+V should be intercepted (user staged 2+ items)."""
        return len(self.staged_clips) >= 2

    def _on_trigger_modal_hook(self, target_hwnd: int):
        """Called from background keyboard listener thread."""
        self._target_hwnd = target_hwnd
        self.bridge.show_palette.emit(target_hwnd)

    def _on_show_palette_slot(self, target_hwnd: int):
        """Runs on the Qt GUI main thread to render the palette."""
        # Use staged clips if available, else recent buffer items
        items = self.staged_clips if len(self.staged_clips) >= 2 else self.buffer.get_all()
        if not items:
            return
        self.modal.display_palette(items, target_hwnd)

    def _on_clipboard_changed(self):
        """Triggered automatically by Windows whenever ANY text is copied."""
        try:
            raw_text = self.clipboard.text()
            if not raw_text or raw_text == self._last_copied_raw:
                return

            self._last_copied_raw = raw_text
            clean_text, category, trackers = Pipeline.process(raw_text)
            if not clean_text:
                return

            # Push to permanent ring buffer
            item = self.buffer.push(raw_text)
            if item:
                # Add to current staging session
                self.staged_clips.insert(0, item)
                # Keep staged clips aligned with 1-based indexing
                for idx, it in enumerate(self.staged_clips, start=1):
                    it.index = idx

                self.metrics.record_copy(trackers_count=trackers)
                print(f"[PureClip] Staged #{len(self.staged_clips)}: {item.preview} ({item.category})")
        except Exception as e:
            pass

    def _on_item_chosen(self, index: int):
        """Called when user presses a digit [1-9] on the modal."""
        # Find item in staged clips or buffer
        selected_item = None
        for it in self.staged_clips:
            if it.index == index:
                selected_item = it
                break

        if not selected_item:
            selected_item = self.buffer.get_by_index(index)

        if selected_item:
            target = self._target_hwnd
            # Reset staged items after a successful paste
            self.staged_clips.clear()
            self.metrics.record_paste(buffer_size_at_paste=max(1, index))

            # Paste directly into the user's active window!
            ClipboardController.paste_into_window(selected_item.content, target)
            print(f"[PureClip] Pasted #{index} -> active window.")

    def _on_autofill_chosen(self):
        """Called when user presses Tab to cascade-fill form fields."""
        items = [it.content for it in self.staged_clips] if self.staged_clips else [it.content for it in self.buffer.get_all()]
        target = self._target_hwnd
        self.staged_clips.clear()
        if items:
            self.metrics.record_form_fill(item_count=len(items))
            ClipboardController.auto_fill_form(items, target)
            print(f"[PureClip] Auto-filled {len(items)} fields with Tab.")


if __name__ == "__main__":
    app = PureClipApp()
    app.start()
