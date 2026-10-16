"""
PureClip Windows System Tray Controller
Allows PureClip to run quietly in the background taskbar tray.
"""

import threading
from PIL import Image, ImageDraw
import pystray
from typing import Callable


def create_tray_icon_image(theme: str = "dark") -> Image.Image:
    """Generates a crisp 64x64 PureClip icon for the Windows taskbar tray."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Draw rounded background badge
    bg_color = (30, 30, 45, 255) if theme == "dark" else (240, 240, 245, 255)
    draw.rounded_rectangle([4, 4, 60, 60], radius=14, fill=bg_color)

    # Draw stylized PureClip sparkle / clipboard symbol
    accent_color = (99, 102, 241, 255)  # Indigo
    # Central clip rect
    draw.rounded_rectangle([18, 14, 46, 50], radius=6, outline=accent_color, width=3)
    # Clip top tab
    draw.rounded_rectangle([25, 9, 39, 18], radius=3, fill=accent_color)
    # Clip lines
    draw.line([24, 26, 40, 26], fill=accent_color, width=2)
    draw.line([24, 34, 40, 34], fill=accent_color, width=2)
    draw.line([24, 42, 34, 42], fill=accent_color, width=2)

    return image


class SystemTrayApp:
    """Manages the Windows taskbar notification area tray icon."""

    def __init__(
        self,
        on_open_palette: Callable[[], None],
        on_toggle_theme: Callable[[], None],
        on_exit: Callable[[], None]
    ):
        self.on_open_palette = on_open_palette
        self.on_toggle_theme = on_toggle_theme
        self.on_exit = on_exit
        self.icon = None

    def start(self):
        """Runs the tray icon in a dedicated daemon thread."""
        img = create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem("Open PureClip (Alt+V)", lambda: self.on_open_palette()),
            pystray.MenuItem("Toggle Light / Dark Theme", lambda: self.on_toggle_theme()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit PureClip", lambda: self._stop_and_exit())
        )

        self.icon = pystray.Icon("PureClip", img, "PureClip - Smart Multi-Slot Clipboard", menu)
        threading.Thread(target=self.icon.run, daemon=True).start()

    def _stop_and_exit(self):
        if self.icon:
            self.icon.stop()
        self.on_exit()
