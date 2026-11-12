"""Regression tests for filename-based RTL direction detection.

Run from the repository root:
    python -m unittest discover -s scripts/tests -v
Requires the same python-bidi and PyYAML dependencies as the linter.
"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rtl_ltr_linter import is_rtl_filename, lint_file, load_config


class TestRtlFilenames(unittest.TestCase):
    def test_existing_persian_files(self):
        repo_root = Path(__file__).resolve().parents[2]
        filenames = sorted(repo_root.glob('*/*-fa_IR.md'))
        self.assertTrue(filenames, 'The repository contains Persian resource lists')
        for filename in filenames:
            with self.subTest(filename=filename.relative_to(repo_root)):
                self.assertTrue(is_rtl_filename(str(filename)))

    def test_language_only_suffixes(self):
        for language in ('ar', 'he', 'fa', 'ur'):
            for separator in ('-', '_'):
                filename = f'books/sample{separator}{language}.md'
                with self.subTest(filename=filename):
                    self.assertTrue(is_rtl_filename(filename))

    def test_regional_suffixes(self):
        for locale in ('fa_IR', 'ar_EG', 'he_IL', 'ur_PK'):
            for separator in ('-', '_'):
                for locale_separator in ('_', '-'):
                    suffix = locale.replace('_', locale_separator)
                    filename = f'books/sample{separator}{suffix}.md'
                    with self.subTest(filename=filename):
                        self.assertTrue(is_rtl_filename(filename))

    def test_case_and_path_separators(self):
        for filename in (
            'books/FREE-PROGRAMMING-BOOKS-FA_IR.MD',
            r'C:\books\sample-fa_IR.md',
            '/books/sample-fa_IR.md',
            'books/SAMPLE_HE.MD',
        ):
            with self.subTest(filename=filename):
                self.assertTrue(is_rtl_filename(filename))

    def test_unrelated_names_remain_ltr(self):
        for filename in (
            'README.md',
            'factory.md',
            'foobar-fa-like.md',
            'sample-fa_IR-extra.md',
            'sample-fa_IR.md.bak',
            'sample-fa.md\n',
            'sample-fa_IR.md\n',
            'sample-fa_IR.md\r\n',
            'sample-fa_IR.txt',
            'sample-en.md',
            'sample-en_US.md',
            'sample-zh_TW.md',
            'sample-fr.md',
            'sample-safari.md',
            'sample-faIR.md',
            'sample-fa_irish.md',
            'books-fa_IR/sample-en.md',
            r'books-fa_IR\sample-en.md',
        ):
            with self.subTest(filename=filename):
                self.assertFalse(is_rtl_filename(filename))

    def test_regional_filename_sets_default_lint_direction(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'sample-fa_IR.md'
            path.write_text('* [\u06a9\u062a\u0627\u0628](https://example.com) - Alice\n', encoding='utf-8')
            issues = lint_file(str(path), load_config(None))
            self.assertTrue(any("Pure LTR text 'Alice'" in issue for issue in issues), issues)

    def test_explicit_html_direction_overrides_filename(self):
        for direction, expected_notice in (('ltr', False), ('rtl', True)):
            with self.subTest(direction=direction), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / 'sample-fa_IR.md'
                path.write_text(
                    f'<div dir="{direction}" markdown="1">\n'
                    '* [\u06a9\u062a\u0627\u0628](https://example.com) - Alice\n'
                    '</div>\n',
                    encoding='utf-8',
                )
                issues = lint_file(str(path), load_config(None))
                self.assertEqual(any("Pure LTR text 'Alice'" in issue for issue in issues), expected_notice)


if __name__ == '__main__':
    unittest.main()
