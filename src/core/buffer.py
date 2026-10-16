"""
PureClip Ring Buffer
Thread-safe in-memory storage for active clips (text and images).
"""

import time
import hashlib
import threading
from typing import List, Optional
from dataclasses import dataclass, field
from src.core.pipeline import Pipeline


@dataclass
class ClipItem:
    index: int                       # 1-indexed for hotkeys [1..9]
    content: str                     # Cleaned text content (or "[Image]" for images)
    category: str                    # "URL", "Email", "Code", "Text", "Multiline", "Image"
    char_count: int
    created_at: float
    is_image: bool = False           # Whether this clip is an image
    image_data: Optional[bytes] = field(default=None, repr=False)  # Raw DIB bytes for images
    content_hash: str = ""           # Dedup hash

    @property
    def preview(self) -> str:
        """One-line concise preview for display in the Apple Liquid UI."""
        if self.is_image:
            kb = len(self.image_data) // 1024 if self.image_data else 0
            return f"🖼 Image ({kb} KB)"
        one_line = self.content.replace("\n", " ↵ ").strip()
        if len(one_line) > 50:
            return one_line[:47] + "..."
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

    def push_text(self, raw_text: str) -> Optional[ClipItem]:
        """Sanitizes text and pushes it to the front of the buffer."""
        cleaned, category, _ = Pipeline.process(raw_text)
        if not cleaned:
            return None

        content_hash = hashlib.md5(cleaned.encode()).hexdigest()

        with self._lock:
            # Deduplicate: skip if identical to most recent
            if self._items and self._items[0].content_hash == content_hash:
                return None

            item = ClipItem(
                index=1,
                content=cleaned,
                category=category,
                char_count=len(cleaned),
                created_at=time.time(),
                is_image=False,
                image_data=None,
                content_hash=content_hash
            )

            self._items.insert(0, item)
            self._trim_and_reindex()
            return item

    def push_image(self, image_data: bytes) -> Optional[ClipItem]:
        """Pushes an image clip to the front of the buffer."""
        if not image_data:
            return None

        content_hash = hashlib.md5(image_data[:1024]).hexdigest()

        with self._lock:
            if self._items and self._items[0].content_hash == content_hash:
                return None

            item = ClipItem(
                index=1,
                content="[Image]",
                category="Image",
                char_count=0,
                created_at=time.time(),
                is_image=True,
                image_data=image_data,
                content_hash=content_hash
            )

            self._items.insert(0, item)
            self._trim_and_reindex()
            return item

    # Keep backward compat
    def push(self, raw_text: str) -> Optional[ClipItem]:
        return self.push_text(raw_text)

    def _trim_and_reindex(self):
        if len(self._items) > self.max_size:
            self._items = self._items[:self.max_size]
        for idx, it in enumerate(self._items, start=1):
            it.index = idx

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
