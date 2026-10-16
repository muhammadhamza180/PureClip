"""
PureClip Main Application
The Apple-grade, lightweight smart clipboard buffer for Windows.
"""

import sys
import os

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import customtkinter as ctk
from src.core.buffer import ClipBuffer
from src.core.clipboard import ClipboardController
from src.core.hotkey import HotkeyListener
from src.core.pipeline import Pipeline
from src.analytics.metrics import MetricsTracker
from src.ui.palette import LiquidPalette


class PureClipApp:
    """Core Application Coordinator."""

    def __init__(self):
        # 1. State & Storage
        self.buffer = ClipBuffer(max_size=9)
        self.metrics = MetricsTracker()

        # 2. Pre-populate with current system clipboard if text is present
        initial_text = ClipboardController.get_text()
        if initial_text:
            self.buffer.push(initial_text)

        # 3. UI Layer (Hidden root window for event loop)
        self.root = ctk.CTk()
        self.root.withdraw()  # Root is hidden; palette is a Toplevel

        # 4. Apple Liquid UI Palette
        self.palette = LiquidPalette(
            on_select=self._on_item_selected,
            on_autofill=self._on_autofill_requested,
            metrics=self.metrics
        )

        # 5. Global Hotkey & Clipboard Monitor
        self.hotkey_listener = HotkeyListener(
            on_copy_detected=self._on_copy_detected,
            on_dispatch_trigger=self._on_dispatch_trigger
        )

    def start(self):
        """Starts background listener and launches UI event loop."""
        print("✦ PureClip is active in the background.")
        print("• Copy items naturally with [Ctrl + C].")
        print("• Tap [Alt + V] anytime to summon the Apple Liquid UI Palette.")
        print("• Press [1-9] to paste, [Tab] to auto-fill forms, [I] for insights, [Esc] to dismiss.")
        
        self.hotkey_listener.start()
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.hotkey_listener.stop()
        self.root.destroy()
        sys.exit(0)

    def _on_copy_detected(self, raw_text: str):
        """Called when a user copies text anywhere in Windows."""
        _, _, trackers = Pipeline.process(raw_text)
        item = self.buffer.push(raw_text)
        if item:
            self.metrics.record_copy(trackers_count=trackers)
            print(f"[PureClip] Captured #{item.index}: {item.preview} ({item.category})")

    def _on_dispatch_trigger(self):
        """Called when user presses Alt+V."""
        items = self.buffer.get_all()
        if not items:
            print("[PureClip] Buffer is empty. Copy something first!")
            return

        # Marshal UI execution to main Tkinter thread
        self.root.after(0, lambda: self.palette.show(items))

    def _on_item_selected(self, index: int):
        """Called when user hits a digit key (1-9) in the palette."""
        item = self.buffer.get_by_index(index)
        if item:
            buffer_len = len(self.buffer)
            # Paste into target window
            ClipboardController.paste_now(item.content)
            self.metrics.record_paste(buffer_size_at_paste=buffer_len)
            print(f"[PureClip] Dispatched item #{index} -> target application.")

    def _on_autofill_requested(self):
        """Called when user hits Tab to cascade-fill form fields."""
        items = [it.content for it in self.buffer.get_all()]
        if items:
            ClipboardController.auto_fill_form(items)
            self.metrics.record_form_fill(item_count=len(items))
            print(f"[PureClip] Form auto-filled {len(items)} fields sequentially via Tab.")


if __name__ == "__main__":
    app = PureClipApp()
    app.start()
