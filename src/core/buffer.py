"""
PureClip Ring Buffer
Thread-safe in-memory storage for active clips.
"""

import time
import threading
from typing import List, Optional
from dataclasses import dataclass
from src.core.pipeline import Pipeline


@dataclass
class ClipItem:
    index: int                  # 1-indexed for hotkeys [1..9]
    content: str                # Cleaned content
    category: str               # "URL", "Email", "Code", "Text", "Multiline"
    char_count: int
    created_at: float
    
    @property
    def preview(self) -> str:
        """One-line concise preview for display in the Apple Liquid UI."""
        one_line = self.content.replace("\n", " ↵ ").strip()
        if len(one_line) > 42:
            return one_line[:39] + "..."
        return one_line

    @property
    def age_str(self) -> str:
        """Human-readable age string like '2s ago', '1m ago'."""
        diff = max(0, int(time.time() - self.created_at))
        if diff < 5:
            return "just now"
        if diff < 60:
            return f"{diff}s ago"
        mins = diff // 60
        if mins < 60:
            return f"{mins}m ago"
        return f"{mins // 60}h ago"


class ClipBuffer:
    """Thread-safe FIFO / Ring Buffer holding the most recent clips."""

    def __init__(self, max_size: int = 9):
        self.max_size = max_size
        self._items: List[ClipItem] = []
        self._lock = threading.Lock()

    def push(self, raw_text: str) -> Optional[ClipItem]:
        """Sanitizes text and pushes it to the front of the buffer."""
        cleaned, category, _ = Pipeline.process(raw_text)
        if not cleaned:
            return None

        with self._lock:
            # Avoid duplicate if it's identical to the most recent clip
            if self._items and self._items[0].content == cleaned:
                return None

            item = ClipItem(
                index=1,
                content=cleaned,
                category=category,
                char_count=len(cleaned),
                created_at=time.time()
            )

            # Insert at the beginning (most recent)
            self._items.insert(0, item)

            # Re-index items [1..9]
            if len(self._items) > self.max_size:
                self._items = self._items[:self.max_size]

            for idx, it in enumerate(self._items, start=1):
                it.index = idx

            return item

    def get_by_index(self, index: int) -> Optional[ClipItem]:
        """Gets clip by 1-based index."""
        with self._lock:
            for item in self._items:
                if item.index == index:
                    return item
            return None

    def get_all(self) -> List[ClipItem]:
        """Returns snapshot of current items."""
        with self._lock:
            return list(self._items)

    def clear(self):
        with self._lock:
            self._items.clear()

    def __len__(self):
        with self._lock:
            return len(self._items)
