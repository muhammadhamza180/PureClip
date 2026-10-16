"""
PureClip Low-Level Windows Keyboard Interceptor
Intercepts Ctrl+V dynamically when multiple items are copied,
and allows standard direct paste when only 1 item is copied.
"""

import time
import threading
import win32api
import win32gui
from typing import Callable
from pynput import keyboard

# Win32 Constants
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105

VK_CONTROL = 0x11
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_MENU = 0x12       # Alt
VK_V = 0x56


class KeyboardInterceptor:
    """
    Hooks low-level Windows keyboard messages.
    Dynamically routes Ctrl+V to the Liquid Modal when multiple items are staged.
    """

    def __init__(
        self,
        should_intercept_paste: Callable[[], bool],
        on_trigger_modal: Callable[[int], None]
    ):
        self.should_intercept_paste = should_intercept_paste
        self.on_trigger_modal = on_trigger_modal
        self.listener: keyboard.Listener = None
        self._suppressing_v_release = False

    def start(self):
        """Starts the low-level Windows keyboard hook."""
        self.listener = keyboard.Listener(
            win32_event_filter=self._event_filter
        )
        self.listener.daemon = True
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()

    def _event_filter(self, msg, data):
        """
        Win32 low-level event filter.
        Returning False consumes/suppresses the keystroke.
        Returning True lets Windows pass the keystroke through.
        """
        vk = data.vkCode

        # Check if Alt + V is pressed (explicit palette trigger)
        if (msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN) and vk == VK_V:
            is_alt_down = (win32api.GetAsyncKeyState(VK_MENU) & 0x8000) != 0
            if is_alt_down:
                target_hwnd = win32gui.GetForegroundWindow()
                self._suppressing_v_release = True
                threading.Thread(target=self.on_trigger_modal, args=(target_hwnd,), daemon=True).start()
                return False

        # Check if Ctrl + V is pressed
        if (msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN) and vk == VK_V:
            is_ctrl_down = (
                (win32api.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0 or
                (win32api.GetAsyncKeyState(VK_LCONTROL) & 0x8000) != 0 or
                (win32api.GetAsyncKeyState(VK_RCONTROL) & 0x8000) != 0
            )
            
            if is_ctrl_down:
                # Ask coordinator if we should intercept (i.e. user copied >= 2 items)
                if self.should_intercept_paste():
                    target_hwnd = win32gui.GetForegroundWindow()
                    self._suppressing_v_release = True
                    # Launch modal on main thread
                    threading.Thread(target=self.on_trigger_modal, args=(target_hwnd,), daemon=True).start()
                    # Suppress Ctrl+V from reaching the text field!
                    return False

        # Suppress the corresponding key-up if we suppressed the key-down
        if (msg == WM_KEYUP or msg == WM_SYSKEYUP) and vk == VK_V:
            if self._suppressing_v_release:
                self._suppressing_v_release = False
                return False

        # Allow all other keystrokes to pass normally
        return True
