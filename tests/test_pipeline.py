"""
Unit tests for PureClip Sanitization Pipeline
"""

import unittest
from src.core.pipeline import Pipeline


class TestPipeline(unittest.TestCase):
    def test_clean_url_strips_utm(self):
        dirty_url = "https://example.com/product?utm_source=twitter&utm_medium=cpc&id=42&fbclid=xyz"
        clean_url, cat, trackers = Pipeline.process(dirty_url)
        self.assertEqual(clean_url, "https://example.com/product?id=42")
        self.assertEqual(cat, "URL")
        self.assertEqual(trackers, 1)

    def test_unwrap_pdf_text(self):
        broken_pdf = "This is a sentence that was broken across multiple\nlines by a PDF column layout."
        clean, cat, _ = Pipeline.process(broken_pdf)
        self.assertEqual(clean, "This is a sentence that was broken across multiple lines by a PDF column layout.")
        self.assertEqual(cat, "Text")

    def test_preserve_bullet_lists(self):
        bullet_list = "• Item one\n• Item two\n• Item three"
        clean, cat, _ = Pipeline.process(bullet_list)
        self.assertEqual(clean, bullet_list)
        self.assertEqual(cat, "Multiline")

    def test_sanitize_whitespace_and_nbsp(self):
        dirty_text = "Hello\u00a0World\u200b  "
        clean, cat, _ = Pipeline.process(dirty_text)
        self.assertEqual(clean, "Hello World")
        self.assertEqual(cat, "Text")

    def test_email_classification(self):
        email = "support@pureclip.dev"
        clean, cat, _ = Pipeline.process(email)
        self.assertEqual(clean, email)
        self.assertEqual(cat, "Email")


if __name__ == "__main__":
    unittest.main()
