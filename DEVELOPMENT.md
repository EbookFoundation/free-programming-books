# Development Guide

This guide helps contributors set up their development environment and run quality checks locally before submitting pull requests.

## Prerequisites

- **Python 3.7+**: For running linter scripts
- **pip**: Python package manager

## Setup

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `PyYAML`: For configuration file parsing
- `python-bidi`: For bidirectional text analysis (RTL languages)

### Verify Installation

```bash
python --version  # Should be 3.7 or higher
python -c "import yaml; import bidi; print('Dependencies installed successfully!')"
```


## Running Linters

### RTL/LTR Markdown Linter

This linter checks Right-to-Left language files (Arabic, Hebrew, Farsi, Urdu) for proper formatting and directionality markers.

#### Check RTL Files

```bash
# Single file
python scripts/rtl_ltr_linter.py books/free-programming-books-ar.md

# Multiple files
python scripts/rtl_ltr_linter.py books/*-ar.md books/*-he.md books/*-fa.md books/*-ur.md
```

#### Understanding Output

The linter checks for:
- **BIDI mismatch**: Text display order differs from logical order
- **Missing markers**: LTR keywords/symbols in RTL text need `&rlm;` or `&lrm;`

#### Fixing RTL Issues

**For LTR words (HTML, JavaScript, Python):**
```markdown
<!-- Before -->
* [كتاب HTML](url)

<!-- After -->
* [كتاب HTML&rlm;](url)
```

**For LTR symbols (C#, C++):**
```markdown
<!-- Before -->
* [أساسيات C#](url)

<!-- After -->
* [أساسيات C#&lrm;](url)
```

## Common Issues

### `ModuleNotFoundError: No module named 'yaml'`

**Solution**: Install dependencies
```bash
pip install -r requirements.txt
```

### RTL linter shows many warnings

**Solution**: Review each warning and add appropriate markers (`&rlm;` or `&lrm;`) as needed.

## Additional Resources

- [Contributing Guidelines](docs/CONTRIBUTING.md) - Detailed formatting rules
- [How-to Guide](docs/HOWTO.md) - GitHub basics for new contributors
- [Code of Conduct](docs/CODE_OF_CONDUCT.md) - Community guidelines

