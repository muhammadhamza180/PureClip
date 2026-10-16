"""
PureClip Low-Level Hotkey & Clipboard Monitor
Monitors Ctrl+C seamlessly and triggers the Liquid Palette on Alt+V.
"""

import time
import threading
from typing import Callable
from pynput import keyboard
from src.core.clipboard import ClipboardController


class HotkeyListener:
    """
    Listens for copy events and dispatch triggers globally across Windows.
    """

    def __init__(
        self,
        on_copy_detected: Callable[[str], None],
        on_dispatch_trigger: Callable[[], None]
    ):
        self.on_copy_detected = on_copy_detected
        self.on_dispatch_trigger = on_dispatch_trigger

        self._last_clipboard_text = ""
        self._current_keys = set()
        self._listener: keyboard.Listener = None
        self._running = False

    def start(self):
        """Starts the low-level keyboard listener."""
        self._running = True
        self._listener = keyboard.Listener(
            on_press=self._on_press,
            on_release=self._on_release
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        self._running = False
        if self._listener:
            self._listener.stop()

    def _on_press(self, key):
        self._current_keys.add(key)

        # Check for Alt + V (Dispatch Palette Trigger)
        is_alt = (
            keyboard.Key.alt in self._current_keys
            or keyboard.Key.alt_l in self._current_keys
            or keyboard.Key.alt_r in self._current_keys
        )

        try:
            # Check for character 'v' or 'V'
            is_v = hasattr(key, 'char') and key.char and key.char.lower() == 'v'
            is_c = hasattr(key, 'char') and key.char and key.char.lower() == 'c'
            is_ctrl = (
                keyboard.Key.ctrl in self._current_keys
                or keyboard.Key.ctrl_l in self._current_keys
                or keyboard.Key.ctrl_r in self._current_keys
            )

            # Trigger Palette on Alt + V
            if is_alt and is_v:
                self.on_dispatch_trigger()
                return

            # Detect standard copy Ctrl + C
            if is_ctrl and is_c:
                # Spawn a background thread to check clipboard after target app writes to it
                threading.Thread(target=self._poll_clipboard_after_copy, daemon=True).start()

        except Exception:
            pass

    def _on_release(self, key):
        self._current_keys.discard(key)

    def _poll_clipboard_after_copy(self):
        """Polls clipboard shortly after Ctrl+C to capture newly copied content."""
        time.sleep(0.08)  # Allow target application to populate clipboard
        text = ClipboardController.get_text()
        if text and text != self._last_clipboard_text:
            self._last_clipboard_text = text
            self.on_copy_detected(text)
