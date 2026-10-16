"""
PureClip Smart Link & Selection Monitor
Allows click-and-drag or copy on click shortcuts without tedious full selection.
"""

import time
import ctypes
import threading
from typing import Callable
from pynput import mouse, keyboard

VK_CONTROL = 0x11
VK_C = 0x43
KEYEVENTF_KEYUP = 0x0002
user32 = ctypes.windll.user32


class SmartCopyMonitor:
    """
    Monitors mouse interactions:
    When user selects text or middle-clicks / Ctrl-clicks a link or text,
    it automatically copies it without needing manual Ctrl+C.
    """

    def __init__(self, on_copy_action: Callable[[], None]):
        self.on_copy_action = on_copy_action
        self._listener: mouse.Listener = None
        self._is_ctrl_pressed = False
        self._kb_listener: keyboard.Listener = None

    def start(self):
        # Listen for middle-click or Ctrl + left-click
        self._listener = mouse.Listener(
            on_click=self._on_click
        )
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()

    def _on_click(self, x, y, button, pressed):
        if not pressed:
            return

        # Middle mouse button click on any text/link instantly copies it
        if button == mouse.Button.middle:
            threading.Thread(target=self._trigger_copy, daemon=True).start()

    def _trigger_copy(self):
        """Simulates Ctrl+C into active window to capture selected or clicked item."""
        time.sleep(0.04)
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_C, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
