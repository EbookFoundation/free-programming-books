import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


class LinterConfigTests(unittest.TestCase):
    def test_cli_loads_bundled_keywords_and_symbols(self):
        script = Path(__file__).with_name('rtl_ltr_linter.py').resolve()
        cases = (
            ('books-ar.md', 'Python', "Keyword 'Python'", True),
            ('books-ar.md', 'C++', "Symbol 'C++'", True),
            ('books-ar.md', 'Python&rlm;', "Keyword 'Python'", False),
            ('books-ar.md', 'C++&lrm;', "Symbol 'C++'", False),
            ('books-en.md', 'Python', "Keyword 'Python'", False),
        )
        for filename, title, diagnostic, expected in cases:
            with self.subTest(filename=filename, title=title):
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory)
                    (path / filename).write_text(
                        f'* [{title}](https://example.com) - Author\n',
                        encoding='utf-8',
                    )
                    result = subprocess.run(
                        [sys.executable, str(script), filename, '--log-file', 'lint.log'],
                        cwd=directory,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    log = path / 'lint.log'
                    output = log.read_text(encoding='utf-8') if log.exists() else ''
                    self.assertEqual(diagnostic in output, expected, output)


if __name__ == '__main__':
    unittest.main()
