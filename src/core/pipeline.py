"""
PureClip Sanitization & Intelligence Pipeline
Transforms raw clipboard content into clean, structured snippets.
"""

import re
import urllib.parse
from typing import Tuple, List

TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "utm_id", "fbclid", "gclid", "dclid", "msclkid", "ref", "ref_src",
    "si", "igshid", "mc_cid", "mc_eid"
}


class Pipeline:
    """Executes a series of sanitizers and classifies content."""

    @staticmethod
    def clean_url(url: str) -> str:
        """Strips marketing trackers and surveillance parameters from URLs."""
        try:
            parsed = urllib.parse.urlparse(url.strip())
            if not parsed.scheme or not parsed.netloc:
                return url
            
            # Parse query params
            query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
            cleaned_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_PARAMS]
            
            new_query = urllib.parse.urlencode(cleaned_pairs)
            cleaned_url = urllib.parse.urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
            return cleaned_url
        except Exception:
            return url

    @staticmethod
    def unwrap_pdf_text(text: str) -> str:
        """
        Stitches broken line wraps from PDF column copies into clean paragraphs
        while preserving list items, code blocks, and double newlines.
        """
        paragraphs = text.split("\n\n")
        cleaned_paragraphs = []
        
        for para in paragraphs:
            lines = para.split("\n")
            if len(lines) <= 1:
                cleaned_paragraphs.append(para)
                continue
            
            # Check if this paragraph is a list (e.g. bullets, dashes, numbers)
            is_list = any(re.match(r"^\s*([•\-\*]|\d+[\.\)])\s+", line) for line in lines)
            if is_list:
                cleaned_paragraphs.append(para)
                continue
            
            # Unwrap: join lines if previous line does not end with terminal punctuation
            unwrapped = ""
            for i, line in enumerate(lines):
                s_line = line.strip()
                if not s_line:
                    continue
                if not unwrapped:
                    unwrapped = s_line
                else:
                    # If unwrapped ends with hyphen, remove it and join (word-break)
                    if unwrapped.endswith("-") and not unwrapped.endswith(" -"):
                        unwrapped = unwrapped[:-1] + s_line
                    else:
                        unwrapped = unwrapped + " " + s_line
            cleaned_paragraphs.append(unwrapped)

        return "\n\n".join(cleaned_paragraphs)

    @staticmethod
    def sanitize_whitespace(text: str) -> str:
        """Removes zero-width characters, non-breaking spaces, and cleans whitespace."""
        # Replace non-breaking spaces
        text = text.replace("\u00a0", " ")
        # Remove zero-width spaces
        text = re.sub(r"[\u200b\u200c\u200d\ufeff]", "", text)
        # Strip trailing whitespace on each line
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines).strip()

    @staticmethod
    def classify(text: str) -> str:
        """Returns the content category for the Apple Liquid UI badge."""
        trimmed = text.strip()
        if re.match(r"^https?://[^\s]+$", trimmed):
            return "URL"
        if re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", trimmed):
            return "Email"
        if "\n" in trimmed:
            return "Multiline"
        if re.search(r"[{};=<>()\[\]]", trimmed) and len(trimmed) < 150:
            return "Code"
        return "Text"

    @classmethod
    def process(cls, text: str) -> Tuple[str, str, int]:
        """
        Runs the full sanitization pipeline.
        Returns: (cleaned_text, category, trackers_removed_count)
        """
        if not text:
            return "", "Text", 0

        original_text = text
        cleaned = text

        # 1. Whitespace Sanitization
        cleaned = cls.sanitize_whitespace(cleaned)

        # 2. URL Cleaning
        trackers_removed = 0
        if cleaned.startswith("http://") or cleaned.startswith("https://"):
            before_url = cleaned
            cleaned = cls.clean_url(cleaned)
            if before_url != cleaned:
                trackers_removed = 1
        
        # 3. PDF unwrapping (if contains newlines and not code/list)
        if "\n" in cleaned and not any(kw in cleaned for kw in ["def ", "class ", "import ", "function "]):
            cleaned = cls.unwrap_pdf_text(cleaned)

        # 4. Classify
        category = cls.classify(cleaned)

        return cleaned, category, trackers_removed
