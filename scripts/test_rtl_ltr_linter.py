"""
Unit tests for scripts/rtl_ltr_linter.py.
"""
import os
import sys
import tempfile
import unittest

# Ensure repository root and scripts directory are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
for p in (REPO_ROOT, SCRIPT_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

try:
    from scripts.rtl_ltr_linter import (
        is_rtl_filename,
        split_by_span,
        load_config,
        lint_file,
    )
except ImportError:
    from rtl_ltr_linter import (
        is_rtl_filename,
        split_by_span,
        load_config,
        lint_file,
    )


class TestFilenameDetection(unittest.TestCase):
    def test_rtl_filenames(self):
        self.assertTrue(is_rtl_filename("books/free-programming-books-ar.md"))
        self.assertTrue(is_rtl_filename("courses/free-courses-he.md"))
        self.assertTrue(is_rtl_filename("more/free-programming-fa.md"))
        self.assertTrue(is_rtl_filename("docs/HOWTO-ur.md"))
        self.assertTrue(is_rtl_filename("sample_ar.md"))

    def test_ltr_filenames(self):
        self.assertFalse(is_rtl_filename("books/free-programming-books-langs.md"))
        self.assertFalse(is_rtl_filename("courses/free-courses-en.md"))
        self.assertFalse(is_rtl_filename("README.md"))
        self.assertFalse(is_rtl_filename("docs/CONTRIBUTING.md"))


class TestSpanSplitting(unittest.TestCase):
    def test_plain_text(self):
        segments = split_by_span("Hello world", "ltr")
        self.assertEqual(segments, [("Hello world", "ltr")])

    def test_nested_spans(self):
        text = "Start <span dir='rtl'>Arabic <span dir='ltr'>English</span> More Arabic</span> End"
        segments = split_by_span(text, "ltr")
        expected = [
            ("Start ", "ltr"),
            ("Arabic ", "rtl"),
            ("English", "ltr"),
            (" More Arabic", "rtl"),
            (" End", "ltr"),
        ]
        self.assertEqual(segments, expected)


class TestConfigLoading(unittest.TestCase):
    def test_defaults_when_file_missing(self):
        cfg = load_config(None)
        self.assertIn("ltr_keywords", cfg)
        self.assertIn("ltr_symbols", cfg)
        self.assertIn("severity", cfg)
        self.assertEqual(cfg["severity"]["bidi_mismatch"], "error")

    def test_custom_config_override(self):
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as tf:
            tf.write("rtl_config:\n  min_ltr_length: 10\n  ignore_meta:\n    - CUSTOM\n")
            tf_path = tf.name
        try:
            cfg = load_config(tf_path)
            self.assertEqual(cfg["min_ltr_length"], 10)
            self.assertEqual(cfg["ignore_meta"], ["CUSTOM"])
            self.assertIn("ltr_keywords", cfg)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


class TestCodeBlockHandling(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(None)

    def test_backtick_code_block_items_ignored(self):
        content = (
            "# Code Example\n"
            "```markdown\n"
            "<div dir=\"rtl\" markdown=\"1\">\n"
            "* [كتاب الأمثلة في R](https://example.com) - John Doe (PDF)\n"
            "</div>\n"
            "```\n"
            "* [Valid Book](https://example.com) - Author (PDF)\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tf:
            tf.write(content)
            tf_path = tf.name
        try:
            issues = lint_file(tf_path, self.cfg)
            self.assertEqual(issues, [])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_tilde_code_block_items_ignored(self):
        content = (
            "# Code Example with Tildes\n"
            "~~~\n"
            "* [كتاب الأمثلة في R](https://example.com) - John Doe (PDF)\n"
            "~~~\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tf:
            tf.write(content)
            tf_path = tf.name
        try:
            issues = lint_file(tf_path, self.cfg)
            self.assertEqual(issues, [])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


class TestDivTagHandling(unittest.TestCase):
    def setUp(self):
        self.cfg = load_config(None)

    def test_single_line_opening_and_closing_div(self):
        content = (
            "<div dir=\"rtl\" markdown=\"1\">* [عنوان](https://example.com) - مؤلف (HTML)</div>\n"
            "* [Valid LTR Item](https://example.com) - LTR Author\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tf:
            tf.write(content)
            tf_path = tf.name
        try:
            issues = lint_file(tf_path, self.cfg)
            unclosed_errors = [i for i in issues if "Found unclosed <div" in i]
            self.assertEqual(unclosed_errors, [])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_nested_plain_and_dir_divs(self):
        content = (
            "<div align=\"center\">\n"
            "<div dir=\"rtl\" markdown=\"1\">\n"
            "<div>\n"
            "* [عنوان](https://example.com) - مؤلف (HTML)\n"
            "</div>\n"
            "</div>\n"
            "</div>\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tf:
            tf.write(content)
            tf_path = tf.name
        try:
            issues = lint_file(tf_path, self.cfg)
            unclosed_errors = [i for i in issues if "Found unclosed <div" in i]
            self.assertEqual(unclosed_errors, [])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_case_insensitive_and_single_quote_divs(self):
        content = (
            "<DIV DIR='rtl' MARKDOWN='1'>\n"
            "* [عنوان](https://example.com) - مؤلف (HTML)\n"
            "</DIV>\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tf:
            tf.write(content)
            tf_path = tf.name
        try:
            issues = lint_file(tf_path, self.cfg)
            unclosed_errors = [i for i in issues if "Found unclosed <div" in i]
            self.assertEqual(unclosed_errors, [])
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)

    def test_unclosed_dir_div_detected(self):
        content = (
            "<div dir=\"rtl\" markdown=\"1\">\n"
            "* [عنوان](https://example.com) - مؤلف (HTML)\n"
        )
        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tf:
            tf.write(content)
            tf_path = tf.name
        try:
            issues = lint_file(tf_path, self.cfg)
            unclosed_errors = [i for i in issues if "Found unclosed <div" in i]
            self.assertEqual(len(unclosed_errors), 1)
        finally:
            if os.path.exists(tf_path):
                os.remove(tf_path)


if __name__ == "__main__":
    unittest.main()
