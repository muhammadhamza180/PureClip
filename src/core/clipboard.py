"""
PureClip Native Win32 Clipboard Controller
Handles reading/writing text & images, window focus stealing via
AttachThreadInput, keystroke injection, and sound feedback.
"""

import time
import ctypes
import ctypes.wintypes as wintypes
import winsound
import threading
import win32clipboard
import win32con
from typing import Optional, List
from io import BytesIO

# Win32 APIs
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# Virtual-Key codes
VK_CONTROL = 0x11
VK_MENU = 0x12  # Alt
VK_V = 0x56
VK_TAB = 0x09
KEYEVENTF_KEYUP = 0x0002
SW_SHOW = 5


def force_foreground(hwnd: int):
    """
    Reliably steals foreground focus on Windows using the AttachThreadInput trick.
    This is the definitive solution to the SetForegroundWindow restriction.
    """
    if not hwnd:
        return

    try:
        # Get the thread of the current foreground window
        fg_hwnd = user32.GetForegroundWindow()
        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, None)
        our_thread = kernel32.GetCurrentThreadId()

        if fg_thread != our_thread:
            # Attach our thread's input processing to the foreground thread
            user32.AttachThreadInput(our_thread, fg_thread, True)

        # Now we are authorized to steal foreground
        user32.ShowWindow(hwnd, SW_SHOW)
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
        user32.SetFocus(hwnd)

        if fg_thread != our_thread:
            # Detach after we have stolen focus
            user32.AttachThreadInput(our_thread, fg_thread, False)
    except Exception:
        pass


def play_copy_sound():
    """Plays a short confirmation blip when an item is copied."""
    threading.Thread(
        target=lambda: winsound.Beep(1200, 60),
        daemon=True
    ).start()


def play_paste_sound():
    """Plays a slightly lower confirmation blip when an item is pasted."""
    threading.Thread(
        target=lambda: winsound.Beep(800, 50),
        daemon=True
    ).start()


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
    def get_image_bytes(retries: int = 5, delay: float = 0.02) -> Optional[bytes]:
        """Reads image data (DIB) from Windows clipboard if available."""
        for _ in range(retries):
            try:
                win32clipboard.OpenClipboard()
                try:
                    if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                        data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                        return bytes(data)
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

    @staticmethod
    def set_image_bytes(dib_data: bytes, retries: int = 5, delay: float = 0.02) -> bool:
        """Sets image data (DIB) in Windows clipboard."""
        for _ in range(retries):
            try:
                win32clipboard.OpenClipboard()
                try:
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32con.CF_DIB, dib_data)
                    return True
                finally:
                    win32clipboard.CloseClipboard()
            except Exception:
                time.sleep(delay)
        return False

    @classmethod
    def paste_into_window(cls, text: str, target_hwnd: Optional[int] = None):
        """Sets clipboard text, restores focus to target, and simulates Ctrl+V."""
        cls.set_text(text)

        if target_hwnd:
            force_foreground(target_hwnd)

        time.sleep(0.06)

        # Simulate Ctrl + V
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

        play_paste_sound()

    @classmethod
    def paste_image_into_window(cls, dib_data: bytes, target_hwnd: Optional[int] = None):
        """Sets clipboard image, restores focus to target, and simulates Ctrl+V."""
        cls.set_image_bytes(dib_data)

        if target_hwnd:
            force_foreground(target_hwnd)

        time.sleep(0.06)

        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        user32.keybd_event(VK_V, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

        play_paste_sound()

    @classmethod
    def auto_fill_form(cls, items: List[str], target_hwnd: Optional[int] = None):
        """Cascade-pastes multiple items separated by Tab."""
        if target_hwnd:
            force_foreground(target_hwnd)

        time.sleep(0.06)

        for i, text in enumerate(items):
            cls.set_text(text)
            time.sleep(0.04)

            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            if i < len(items) - 1:
                time.sleep(0.05)
                user32.keybd_event(VK_TAB, 0, 0, 0)
                time.sleep(0.02)
                user32.keybd_event(VK_TAB, 0, KEYEVENTF_KEYUP, 0)
                time.sleep(0.05)

        play_paste_sound()
