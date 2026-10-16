"""
PureClip Native Win32 Clipboard Controller
Handles reading, writing, window focus restoration, and keystroke injection for Windows.
"""

import time
import ctypes
import win32clipboard
import win32con
from typing import Optional, List

# Virtual-Key codes
VK_CONTROL = 0x11
VK_MENU = 0x12       # Alt
VK_V = 0x56
VK_TAB = 0x09
KEYEVENTF_KEYUP = 0x0002


def safe_set_foreground(hwnd: int):
    """Safely brings a window to the foreground without raising Win32 exceptions."""
    if not hwnd:
        return
    try:
        ctypes.windll.user32.keybd_event(VK_MENU, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_MENU, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        ctypes.windll.user32.BringWindowToTop(hwnd)
    except Exception:
        pass


class ClipboardController:
    """Safely interfaces with Windows Clipboard API and keyboard simulation."""

    @staticmethod
    def get_text(retries: int = 5, delay: float = 0.02) -> Optional[str]:
        """Reads text from Windows clipboard with retry logic for locked state."""
        for _ in range(retries):
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_UNICODETEXT):
                        data = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                        return data
                    return None
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                time.sleep(delay)
        return None

    @staticmethod
    def set_text(text: str, retries: int = 5, delay: float = 0.02) -> bool:
        """Sets text in Windows clipboard with retry logic."""
        for _ in range(retries):
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
                    return True
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                time.sleep(delay)
        return False

    @classmethod
    def paste_into_window(cls, text: str, target_hwnd: Optional[int] = None):
        """
        Sets target text in clipboard, switches focus to target window,
        and simulates Ctrl+V so text appears directly in the user's active input.
        """
        cls.set_text(text)

        if target_hwnd:
            safe_set_foreground(target_hwnd)

        # Give Windows 50ms to transfer keyboard focus
        time.sleep(0.05)

        # Simulate Ctrl + V
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
        ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.02)
        ctypes.windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    @classmethod
    def auto_fill_form(cls, items: List[str], target_hwnd: Optional[int] = None):
        """
        Cascade-pastes multiple items separated by Tab:
        Paste item[0] -> Tab -> Paste item[1] -> Tab -> ...
        """
        if target_hwnd:
            safe_set_foreground(target_hwnd)

        time.sleep(0.05)

        for i, text in enumerate(items):
            cls.set_text(text)
            time.sleep(0.03)

            # Paste Ctrl + V
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.02)
            ctypes.windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            # Send Tab if not last item
            if i < len(items) - 1:
                time.sleep(0.04)
                ctypes.windll.user32.keybd_event(VK_TAB, 0, 0, 0)
                time.sleep(0.01)
                ctypes.windll.user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
                time.sleep(0.04)
