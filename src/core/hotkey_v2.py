"""
PureClip Low-Level Windows Keyboard Interceptor v3
- Intercepts Ctrl+V dynamically when multiple items are staged.
- When modal is visible, GLOBALLY intercepts digits 1-9, Tab, Esc, T
  so user DOES NOT NEED TO CLICK ON THE MODAL AT ALL!
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
VK_TAB = 0x09
VK_ESCAPE = 0x1B
VK_T = 0x54

# Digit keys 1-9 on top row (0x31 - 0x39) and numpad (0x61 - 0x69)
DIGIT_MAP = {
    0x31: 1, 0x32: 2, 0x33: 3, 0x34: 4, 0x35: 5, 0x36: 6, 0x37: 7, 0x38: 8, 0x39: 9,
    0x61: 1, 0x62: 2, 0x63: 3, 0x64: 4, 0x65: 5, 0x66: 6, 0x67: 7, 0x68: 8, 0x69: 9,
}

LLKHF_INJECTED = 0x00000010


class KeyboardInterceptor:
    def __init__(
        self,
        should_intercept_paste: Callable[[], bool],
        is_modal_active: Callable[[], bool],
        on_trigger_modal: Callable[[int], None],
        on_modal_key: Callable[[str, int], None]  # action: "digit", "tab", "esc", "theme"; val: int
    ):
        self.should_intercept_paste = should_intercept_paste
        self.is_modal_active = is_modal_active
        self.on_trigger_modal = on_trigger_modal
        self.on_modal_key = on_modal_key

        self.listener: keyboard.Listener = None
        self._suppressing_v_release = False
        self._suppressed_keys = set()

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
        # ALWAYS let injected/simulated keystrokes through (our own simulated pastes)
        if hasattr(data, 'flags') and (data.flags & LLKHF_INJECTED):
            return True

        vk = data.vkCode
        is_down = (msg == WM_KEYDOWN or msg == WM_SYSKEYDOWN)
        is_up = (msg == WM_KEYUP or msg == WM_SYSKEYUP)

        # ─── 1. IF MODAL IS CURRENTLY ACTIVE / VISIBLE ───
        # Intercept 1-9, Tab, Esc, T GLOBALLY without requiring window click/focus!
        if self.is_modal_active():
            # Check digits 1-9
            if vk in DIGIT_MAP:
                if is_down:
                    digit = DIGIT_MAP[vk]
                    self._suppressed_keys.add(vk)
                    threading.Thread(target=self.on_modal_key, args=("digit", digit), daemon=True).start()
                return False

            # Check Tab
            if vk == VK_TAB:
                if is_down:
                    self._suppressed_keys.add(vk)
                    threading.Thread(target=self.on_modal_key, args=("tab", 0), daemon=True).start()
                return False

            # Check Escape
            if vk == VK_ESCAPE:
                if is_down:
                    self._suppressed_keys.add(vk)
                    threading.Thread(target=self.on_modal_key, args=("esc", 0), daemon=True).start()
                return False

            # Check T (Cycle Theme)
            if vk == VK_T:
                if is_down:
                    self._suppressed_keys.add(vk)
                    threading.Thread(target=self.on_modal_key, args=("theme", 0), daemon=True).start()
                return False

            # If user releases a key we suppressed on keydown, suppress keyup too
            if is_up and vk in self._suppressed_keys:
                self._suppressed_keys.discard(vk)
                return False

        # Clean up any leftover released keys
        if is_up and vk in self._suppressed_keys:
            self._suppressed_keys.discard(vk)

        # ─── 2. Alt + V: Always open palette ───
        if is_down and vk == VK_V:
            is_alt = (win32api.GetAsyncKeyState(VK_MENU) & 0x8000) != 0
            if is_alt:
                target = win32gui.GetForegroundWindow()
                self._suppressing_v_release = True
                threading.Thread(target=self.on_trigger_modal, args=(target,), daemon=True).start()
                return False

        # ─── 3. Ctrl + V: Conditionally intercept when 2+ items staged ───
        if is_down and vk == VK_V:
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

        # Suppress matching Ctrl+V key-up
        if is_up and vk == VK_V:
            if self._suppressing_v_release:
                self._suppressing_v_release = False
                return False

        return True
