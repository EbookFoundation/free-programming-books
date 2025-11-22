#!/usr/bin/env python3
"""
RTL/LTR Markdown Linter (corrected)

This is a cleaned-up and slightly hardened version of the linter you provided.
Main changes and improvements:
- All file paths normalized to absolute paths so comparisons with changed-files work reliably.
- Defensive handling of git subprocess calls (handles CalledProcessError).
- Minor regex/logic clarifications and small performance tweaks.
- More robust detection of <div dir=...> tags when they appear multiple times on a line.
- Better comments and docstrings.

If you want, I can run unit tests on sample files or add a --debug flag to print more context.
"""
import sys
import os
import argparse
import re
import yaml
import subprocess
from bidi.algorithm import get_display


def load_config(path: str):
    """
    Loads configuration from the specified YAML file and merges it with defaults.
    If the file cannot be read or parsed, defaults are returned (with a warning).
    """
    default = {
        'ltr_keywords': [],
        'ltr_symbols': [],
        'pure_ltr_pattern': r"^[\u0000-\u007F]+$",
        'rtl_chars_pattern': r"[\u0590-\u08FF]",
        'severity': {
            'bidi_mismatch': 'error',
            'keyword': 'warning',
            'symbol': 'warning',
            'pure_ltr': 'notice',
            'author_meta': 'notice'
        },
        'ignore_meta': ['PDF', 'EPUB', 'HTML', 'podcast', 'videocast'],
        'min_ltr_length': 3,
        'rlm_entities': ['&rlm;', '&#x200F;', '&#8207;'],
        'lrm_entities': ['&lrm;', '&#x200E;', '&#8206;']
    }

    if path and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                # Support either a top-level mapping or nested under 'rtl_config'
                conf = data.get('rtl_config', data if isinstance(data, dict) else {})
                # Merge shallow keys (severity is replaced if provided)
                default.update(conf)
        except Exception as e:
            # Print a GitHub Actions style warning but continue with defaults
            print(f"::warning file={path}::Could not load config: {e}. Using defaults.")

    return default


def is_rtl_filename(path: str) -> bool:
    name = os.path.basename(path).lower()
    return any(name.endswith(suf) for suf in ['-ar.md', '_ar.md', '-he.md', '_he.md', '-fa.md', '_fa.md', '-ur.md', '_ur.md'])


# Regex patterns
LIST_ITEM_RE = re.compile(r'^\s*[\*\-\+]\s+(.*)')
BOOK_ITEM_RE = re.compile(
    r"^\s*\[(?P<title>.+?)\]\((?P<url>.+?)\)"
    r"(?:\s*[-–—]\s*(?P<author>[^\(\n\[]+?))?"
    r"(?:\s*[\(\[](?P<meta>.*?)[\)\]])?\s*$"
)
HTML_DIR_ATTR_RE = re.compile(r"dir\s*=\s*(['\"])(rtl|ltr)\1", re.IGNORECASE)
SPAN_DIR_RE = re.compile(r'<span[^>]*dir=["\'](rtl|ltr)["\'][^>]*>', re.IGNORECASE)
INLINE_CODE_RE = re.compile(r'^`.*`$')
CODE_FENCE_START = re.compile(r'^\s*>?\s*```')

BRACKET_CONTENT_RE = re.compile(r'''
    ^\s*             # optional leading whitespace
    (?:\[|\()       # open bracket or paren
    ([^\n\)\]]*?)  # content
    (?:\]|\))       # close
    \s*$             # optional trailing whitespace
''', re.VERBOSE | re.UNICODE)


def split_by_span(text: str, base_ctx: str):
    """Split text into (segment, ctx) pairs based on <span dir=...> nesting."""
    tokens = re.split(r'(<span[^>]*dir=["\'](?:rtl|ltr)["\'][^>]*>|</span>)', text)
    stack = [base_ctx]
    segments = []

    for tok in tokens:
        if not tok:
            continue
        m = SPAN_DIR_RE.match(tok)
        if m:
            stack.append(m.group(1).lower())
            continue
        if tok.lower() == '</span>':
            if len(stack) > 1:
                stack.pop()
            continue
        segments.append((tok, stack[-1]))

    return segments


def lint_file(path: str, cfg: dict):
    issues = []

    try:
        # Ensure we use the absolute path inside the linter for consistent messages
        with open(path, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
    except Exception as e:
        return [f"::error file={path},line=1::Cannot read file: {e}"]

    keywords_orig = cfg.get('ltr_keywords', [])
    symbols = cfg.get('ltr_symbols', [])
    pure_ltr_re = re.compile(cfg.get('pure_ltr_pattern', r"^[\u0000-\u007F]+$"))
    rtl_char_re = re.compile(cfg.get('rtl_chars_pattern', r"[\u0590-\u08FF]"))
    sev = cfg.get('severity', {})
    ignore_meta = set(cfg.get('ignore_meta', []))
    min_len = cfg.get('min_ltr_length', 3)

    RLM = [chr(0x200F)] + cfg.get('rlm_entities', [])
    LRM = [chr(0x200E)] + cfg.get('lrm_entities', [])

    file_direction_ctx = 'rtl' if is_rtl_filename(path) else 'ltr'
    block_context_stack = [file_direction_ctx]

    for idx, line in enumerate(lines, 1):
        active_block_direction_ctx = block_context_stack[-1]

        # Skip code fences
        if CODE_FENCE_START.match(line):
            continue

        # Find div tags with dir attribute or closing </div>. We capture them in order.
        # This handles multiple tags on the same line as well.
        for match in re.finditer(r"(<div[^>]*dir=[\"'](rtl|ltr)[\"'][^>]*>|</div>)", line, re.IGNORECASE):
            tag = match.group(1)
            # If opening div with markdown="1", push
            if tag.lower().startswith('<div') and 'markdown="1"' in tag:
                # find the direction value
                d = 'rtl' if 'dir=' in tag.lower() and 'rtl' in tag.lower() else 'ltr'
                block_context_stack.append(d)
            elif tag.lower() == '</div>' and len(block_context_stack) > 1:
                block_context_stack.pop()

        list_item = LIST_ITEM_RE.match(line)
        if not list_item:
            continue

        text = list_item.group(1).strip()
        book_item = BOOK_ITEM_RE.match(text)

        if book_item:
            title = book_item.group('title') or ''
            author = (book_item.group('author') or '').strip()
            meta = (book_item.group('meta') or '').strip()
            is_link_only_item = not author and not meta
        else:
            title, author, meta = text, '', ''
            is_link_only_item = False

        # Check for RTL author followed by pure LTR meta
        if active_block_direction_ctx == 'rtl' and author and meta:
            if rtl_char_re.search(author) and pure_ltr_re.match(meta) and len(meta) >= min_len:
                if not any(author.strip().endswith(rlm_marker) for rlm_marker in RLM):
                    issues.append(
                        f"::{sev.get('author_meta','notice').lower()} file={path},line={idx}::RTL author '{author}' followed by LTR meta '{meta}' may need '&rlm;' after author."
                    )

        for part, raw_text in [('title', title), ('author', author), ('meta', meta)]:
            if not raw_text:
                continue
            if part == 'meta' and raw_text in ignore_meta:
                continue

            segments = split_by_span(raw_text, active_block_direction_ctx)

            # Avoid duplicate keyword matches that are part of symbols
            filtered_keywords = [kw for kw in keywords_orig if not any(kw in sym for sym in symbols)]

            for segment_text, segment_direction_ctx in segments:
                s = segment_text.strip()
                if not s:
                    continue

                m_bracket = BRACKET_CONTENT_RE.fullmatch(s)
                if m_bracket:
                    inner_content = m_bracket.group(1)
                    is_pure_ltr_inner = pure_ltr_re.match(inner_content) is not None
                    is_pure_rtl_inner = rtl_char_re.search(inner_content) is not None and re.search(r"[A-Za-z0-9]", inner_content) is None
                    if is_pure_ltr_inner or is_pure_rtl_inner:
                        continue

                if any([INLINE_CODE_RE.match(s), any(mk in s for mk in RLM + LRM)]):
                    continue

                # BIDI mismatch check: contains both RTL and LTR characters
                if rtl_char_re.search(s) and re.search(r"[A-Za-z0-9]", s):
                    try:
                        disp = get_display(s)
                        if disp != s:
                            issues.append(
                                f"::{sev.get('bidi_mismatch','error').lower()} file={path},line={idx}::BIDI mismatch in {part}: the text '{s}' is displayed as '{disp}'"
                            )
                    except Exception:
                        # If python-bidi fails for some string, skip the bidi check
                        pass

                # Only check for keyword/symbol markers when the current segment context is RTL
                if segment_direction_ctx != 'rtl':
                    # However, still check pure LTR segments that might need trailing RLM
                    if (part != 'title') and pure_ltr_re.match(s) and not rtl_char_re.search(s) and len(s) >= min_len:
                        issues.append(
                            f"::{sev.get('pure_ltr','notice').lower()} file={path},line={idx}::Pure LTR text '{s}' in {part} of RTL context may need trailing '&rlm;' marker."
                        )
                    continue

                if not (part == 'title' and is_link_only_item):
                    for sym in symbols:
                        if sym in s and not any(m in s for m in LRM):
                            issues.append(
                                f"::{sev.get('symbol','warning').lower()} file={path},line={idx}::Symbol '{sym}' in {part} '{s}' may need trailing '&lrm;' marker."
                            )

                    for kw in filtered_keywords:
                        if kw in s and not any(m in s for m in RLM):
                            issues.append(
                                f"::{sev.get('keyword','warning').lower()} file={path},line={idx}::Keyword '{kw}' in {part} '{s}' may need trailing '&rlm;' marker."
                            )

                # Pure LTR check (again) — applicable even inside RTL segments
                if (part != 'title') and pure_ltr_re.match(s) and not rtl_char_re.search(s) and len(s) >= min_len:
                    issues.append(
                        f"::{sev.get('pure_ltr','notice').lower()} file={path},line={idx}::Pure LTR text '{s}' in {part} of RTL context may need trailing '&rlm;' marker."
                    )

    if len(block_context_stack) > 1:
        issues.append(
            f"::error file={path},line={len(lines)}::Found unclosed <div dir='...'> tag. The final block context is '{block_context_stack[-1]}', not the file's base '{file_direction_ctx}'."
        )

    return issues


def get_changed_lines_for_file(filepath: str):
    """Return set of changed line numbers for the file against origin/main (best-effort).

    This will return an empty set if git fails or the merge base cannot be found.
    """
    changed_lines = set()
    try:
        # Use unified=0 to reduce noise and extract exact added/modified line ranges
        diff = subprocess.check_output(
            ['git', 'diff', '--unified=0', 'origin/main...', '--', filepath],
            encoding='utf-8', errors='ignore'
        )
        for line in diff.splitlines():
            if line.startswith('@@'):
                m = re.search(r'\+(\d+)(?:,(\d+))?', line)
                if m:
                    start = int(m.group(1))
                    count = int(m.group(2) or '1')
                    for i in range(start, start + count):
                        changed_lines.add(i)
    except subprocess.CalledProcessError:
        # git returned a non-zero status, return empty set (best-effort)
        pass
    except Exception:
        pass
    return changed_lines


def main():
    parser = argparse.ArgumentParser(description="Lints Markdown files for RTL/LTR issues, with PR annotation support.")
    parser.add_argument('paths_to_scan', nargs='+', help="List of files or directories to scan for all issues.")
    parser.add_argument('--changed-files', nargs='*', default=None, help="List of changed files to generate PR annotations for.")
    parser.add_argument('--log-file', default='rtl-linter-output.log', help="File to write all linter output to.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = load_config(os.path.join(script_dir, 'rtl_linter_config.yml'))

    total = errs = 0
    annotated_errs = 0
    any_issues = False

    # Normalize changed files to absolute paths for reliable matching
    changed_files_set = set(os.path.normpath(os.path.abspath(f)) for f in args.changed_files) if args.changed_files else set()

    changed_lines_map = {f: get_changed_lines_for_file(f) for f in changed_files_set}

    with open(args.log_file, 'w', encoding='utf-8') as log_f:
        for p_scan_arg in args.paths_to_scan:
            normalized_scan_path = os.path.normpath(os.path.abspath(p_scan_arg))

            if os.path.isdir(normalized_scan_path):
                for root, _, files in os.walk(normalized_scan_path):
                    for fn in files:
                        if fn.lower().endswith('.md'):
                            file_path = os.path.normpath(os.path.abspath(os.path.join(root, fn)))
                            total += 1
                            issues_found = lint_file(file_path, cfg)
                            for issue_str in issues_found:
                                log_f.write(issue_str + '\n')
                                any_issues = True
                                if file_path in changed_files_set:
                                    m = re.search(r'line=(\d+)', issue_str)
                                    if m and int(m.group(1)) in changed_lines_map.get(file_path, set()):
                                        print(issue_str)
                                        if issue_str.startswith('::error'):
                                            annotated_errs += 1
                                if issue_str.startswith('::error') or issue_str.startswith('::warning'):
                                    errs += 1

            elif normalized_scan_path.lower().endswith('.md'):
                file_path = normalized_scan_path
                total += 1
                issues_found = lint_file(file_path, cfg)
                for issue_str in issues_found:
                    log_f.write(issue_str + '\n')
                    any_issues = True
                    if file_path in changed_files_set:
                        m = re.search(r'line=(\d+)', issue_str)
                        if m and int(m.group(1)) in changed_lines_map.get(file_path, set()):
                            print(issue_str)
                            if issue_str.startswith('::error'):
                                annotated_errs += 1
                    if issue_str.startswith('::error') or issue_str.startswith('::warning'):
                        errs += 1

    if not any_issues:
        try:
            os.remove(args.log_file)
        except Exception:
            pass

    print(f"::notice ::Processed {total} files, found {errs} issues.")
    sys.exit(1 if annotated_errs else 0)


if __name__ == '__main__':
    main()
