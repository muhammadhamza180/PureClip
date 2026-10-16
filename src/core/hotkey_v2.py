"""
PureClip Low-Level Windows Keyboard Interceptor v2
Intercepts Ctrl+V dynamically when multiple items are staged.
Uses win32_event_filter for sub-ms keystroke suppression.
"""

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

# LLKHF_INJECTED flag (bit 4) indicates the keystroke was simulated
LLKHF_INJECTED = 0x00000010


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
        Returning False suppresses the keystroke.
        Returning True passes it through to Windows.
        """
        # ALWAYS let injected/simulated keystrokes through (our own Ctrl+V pastes)
        if hasattr(data, 'flags') and (data.flags & LLKHF_INJECTED):
            return True

        vk = data.vkCode

        # ─── Alt + V: Always open palette ───
        if (msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN) and vk == VK_V:
            is_alt = (win32api.GetAsyncKeyState(VK_MENU) & 0x8000) != 0
            if is_alt:
                target = win32gui.GetForegroundWindow()
                self._suppressing_v_release = True
                threading.Thread(target=self.on_trigger_modal, args=(target,), daemon=True).start()
                return False

        # ─── Ctrl + V: Conditionally intercept ───
        if (msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN) and vk == VK_V:
            is_ctrl = (
                (win32api.GetAsyncKeyState(VK_CONTROL) & 0x8000) != 0 or
                (win32api.GetAsyncKeyState(VK_LCONTROL) & 0x8000) != 0 or
                (win32api.GetAsyncKeyState(VK_RCONTROL) & 0x8000) != 0
            )

            if is_ctrl and self.should_intercept_paste():
                target = win32gui.GetForegroundWindow()
                self._suppressing_v_release = True
                threading.Thread(target=self.on_trigger_modal, args=(target,), daemon=True).start()
                return False

        # Suppress matching key-up
        if (msg == WM_KEYUP or msg == WM_SYSKEYUP) and vk == VK_V:
            if self._suppressing_v_release:
                self._suppressing_v_release = False
                return False

        return True
