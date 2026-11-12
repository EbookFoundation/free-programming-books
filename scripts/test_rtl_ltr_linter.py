"""
Unit tests for scripts/rtl_ltr_linter.py.

Run with: pytest scripts/test_rtl_ltr_linter.py
Requires: pip install python-bidi PyYAML pytest
"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from rtl_ltr_linter import is_rtl_filename, lint_file, load_config, split_by_span


@pytest.fixture
def cfg():
    return load_config(None)


def write_md(tmp_path, name, content):
    path = tmp_path / name
    path.write_text(content, encoding="utf-8")
    return str(path)


@pytest.mark.parametrize(
    "filename,expected",
    [
        ("free-programming-books-ar.md", True),
        ("free-programming-books-he.md", True),
        ("free-programming-books-fa.md", True),
        ("free-programming-books-ur.md", True),
        ("free-programming-books-en.md", False),
        ("free-programming-books.md", False),
    ],
)
def test_is_rtl_filename(filename, expected):
    assert is_rtl_filename(filename) is expected


def test_div_open_and_close_on_same_line_does_not_leave_unclosed_context(tmp_path, cfg):
    # Regression test for https://github.com/EbookFoundation/free-programming-books/issues/12500
    # A line containing BOTH an opening and a closing <div dir="..."> tag must be fully
    # processed so the block context correctly returns to the file's base direction.
    content = (
        '<div dir="rtl" markdown="1">Some Text</div>\n'
        "\n"
        "* [A Book](http://example.com/book.html) - Author (PDF)\n"
    )
    path = write_md(tmp_path, "sample-en.md", content)
    issues = lint_file(path, cfg)
    assert not any("unclosed" in issue.lower() for issue in issues)


def test_unclosed_div_is_still_detected(tmp_path, cfg):
    # Sanity check that the "unclosed <div>" detection itself still works,
    # so the previous test isn't passing vacuously.
    content = '<div dir="rtl" markdown="1">Some Text\n'
    path = write_md(tmp_path, "sample-en.md", content)
    issues = lint_file(path, cfg)
    assert any("unclosed" in issue.lower() for issue in issues)


def test_split_by_span_nested_context():
    segments = split_by_span(
        "Text <span dir='rtl'>RTL <span dir='ltr'>LTR</span> RTL</span> Text",
        "ltr",
    )
    contexts = [ctx for _, ctx in segments]
    assert contexts == ["ltr", "rtl", "ltr", "rtl", "ltr"]


def test_load_config_defaults_when_no_file():
    cfg = load_config(None)
    assert cfg["min_ltr_length"] == 3
    assert cfg["severity"]["bidi_mismatch"] == "error"
