"""
PureClip Native Win32 Clipboard Controller
Handles reading, writing, and keystroke injection for Windows.
"""

import time
import ctypes
import win32clipboard
import win32con
from typing import Optional

# Virtual-Key codes
VK_CONTROL = 0x11
VK_V = 0x56
VK_TAB = 0x09
KEYEVENTF_KEYUP = 0x0002


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
    def paste_now(cls, text: str):
        """Sets the clipboard text and immediately injects Ctrl+V into active window."""
        if cls.set_text(text):
            # Short sleep to ensure the target app receives updated clipboard
            time.sleep(0.04)
            # Simulate Ctrl + V
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

    @classmethod
    def auto_fill_form(cls, items: list[str]):
        """
        Cascade-pastes multiple items separated by Tab:
        Paste item[0] -> Tab -> Paste item[1] -> Tab -> ...
        """
        for i, text in enumerate(items):
            cls.set_text(text)
            time.sleep(0.04)
            # Paste Ctrl + V
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, 0, 0)
            ctypes.windll.user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.01)
            ctypes.windll.user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            ctypes.windll.user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)
            
            # Send Tab if not last item
            if i < len(items) - 1:
                time.sleep(0.05)
                ctypes.windll.user32.keybd_event(VK_TAB, 0, 0, 0)
                time.sleep(0.01)
                ctypes.windll.user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)
