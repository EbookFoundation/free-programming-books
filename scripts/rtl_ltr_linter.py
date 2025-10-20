#!/usr/bin/env python3
"""
RTL/LTR Markdown Linter.

This script analyzes Markdown files to identify potential issues
in the display of mixed Right-To-Left (RTL) and Left-To-Right (LTR) text.
It reads configuration from a `rtl_linter_config.yml` file located in the same
directory as the script.

Key Features:
- Line-by-line parsing of Markdown list items.
- Detection of HTML 'dir' attributes to switch text direction context.
- Handling of nested 'dir' contexts within '<span>' tags.
- Detection of LTR keywords and symbols that might require Unicode markers.
- BIDI (Bidirectional Algorithm) visual analysis using the 'python-bidi' library.
- Parsing of metadata for book items (title, author, meta).
- Configurable severity levels for detected issues (error, warning, notice).
- Filters to ignore code blocks, inline code, and text within parentheses.
- Specific check for RTL authors followed by LTR metadata.

[MODIFICATION] Added professional inline comments and minor code readability improvements.
"""
import sys
import os
import argparse
import re
import yaml
from bidi.algorithm import get_display

# ============================
# CONFIGURATION LOADING
# ============================

def load_config(path):
    """
    Loads configuration from the specified YAML file.

    If the file does not exist or an error occurs during loading,
    default values will be used.

    Args:
        path (str): The path to the YAML configuration file.

    Returns:
        dict: Configuration dictionary combining defaults with user settings.
    """
    default = {
        'ltr_keywords': [],
        'ltr_symbols': [],
        'pure_ltr_pattern': r"^[\u0000-\u007F]+$",  # ASCII only
        'rtl_chars_pattern': r"[\u0590-\u08FF]",    # Arabic, Hebrew, etc.
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

    # [MODIFICATION] Merge YAML configuration if it exists
    if path and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                conf = data.get('rtl_config', {})
                default.update(conf)
        except Exception as e:
            print(f"::warning file={path}::Could not load config: {e}. Using defaults.")

    return default

# ============================
# FILE DIRECTION HELPER
# ============================

def is_rtl_filename(path):
    """
    Checks if filename suggests an RTL language based on suffix.
    """
    name = os.path.basename(path).lower()
    return any(name.endswith(suf) for suf in ['-ar.md','_ar.md','-he.md','_he.md','-fa.md','_fa.md','-ur.md','_ur.md'])

# ============================
# REGEX PATTERNS
# ============================

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
    (?:^|\W)        # Start of line or non-word character
    (\[|\()         # Open square or round bracket
    ([^\n\)\]]*?)   # Content
    (\]|\))         # Close square or round bracket
    (?:\W|$)        # End of line or non-word character
''', re.VERBOSE | re.UNICODE)

# ============================
# SPAN SPLITTING HELPER
# ============================

def split_by_span(text, base_ctx):
    """
    Splits text into segments based on nested <span> tags with dir attributes.
    Returns a list of tuples: (segment_text, context)
    """
    tokens = re.split(r'(<span[^>]*dir=["\'](?:rtl|ltr)["\'][^>]*>|</span>)', text)
    stack = [base_ctx]
    segments = []

    for tok in tokens:
        if not tok:
            continue
        m = SPAN_DIR_RE.match(tok)
        if m:
            stack.append(m.group(1).lower()); continue
        if tok.lower() == '</span>':
            if len(stack) > 1: stack.pop()
            continue
        segments.append((tok, stack[-1]))

    return segments

# ============================
# MAIN LINT FUNCTION
# ============================

def lint_file(path, cfg):
    """
    Analyze a single Markdown file for RTL/LTR issues.
    Returns a list of strings formatted for GitHub Actions.
    """
    issues = []
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except Exception as e:
        return [f"::error file={path},line=1::Cannot read file: {e}"]

    keywords_orig = cfg['ltr_keywords']
    symbols = cfg['ltr_symbols']
    pure_ltr_re = re.compile(cfg['pure_ltr_pattern'])
    rtl_char_re = re.compile(cfg['rtl_chars_pattern'])
    sev = cfg['severity']
    ignore_meta = set(cfg['ignore_meta'])
    min_len = cfg['min_ltr_length']
    RLM = [chr(0x200F)] + cfg['rlm_entities']
    LRM = [chr(0x200E)] + cfg['lrm_entities']

    file_direction_ctx = 'rtl' if is_rtl_filename(path) else 'ltr'
    block_context_stack = [file_direction_ctx]

    for idx, line in enumerate(lines, 1):
        active_block_direction_ctx = block_context_stack[-1]

        if CODE_FENCE_START.match(line): continue

        div_tags = re.findall(r"(<div[^>]*dir=['\"](rtl|ltr)['\"][^>]*>|</div>)", line, re.IGNORECASE)
        for tag_tuple in div_tags:
            tag, direction = tag_tuple
            if tag.startswith('<div') and 'markdown="1"' in tag:
                block_context_stack.append(direction.lower())
            elif tag == '</div>' and len(block_context_stack) > 1:
                block_context_stack.pop()

        list_item = LIST_ITEM_RE.match(line)
        if not list_item: continue
        text = list_item.group(1).strip()
        book_item = BOOK_ITEM_RE.match(text)

        if book_item:
            title = book_item.group('title')
            author = (book_item.group('author') or '').strip()
            meta = (book_item.group('meta') or '').strip()
            is_link_only_item = not author and not meta
        else:
            title, author, meta = text, '', ''
            is_link_only_item = False

        # [MODIFICATION] Check for RTL author followed by LTR metadata
        if  active_block_direction_ctx == 'rtl' and \
            author and meta and \
            rtl_char_re.search(author) and pure_ltr_re.match(meta) and \
            len(meta) >= min_len and \
            not any(author.strip().endswith(rlm_marker) for rlm_marker in RLM):
            issues.append(
                f"::{sev['author_meta'].lower()} file={path},line={idx}::RTL author '{author.strip()}' followed by LTR meta '{meta}' may need '&rlm;' after author."
            )

        for part, raw_text in [('title', title), ('author', author), ('meta', meta)]:
            if not raw_text or (part=='meta' and raw_text in ignore_meta): continue
            segments = split_by_span(raw_text, active_block_direction_ctx)
            filtered_keywords = [kw for kw in keywords_orig if all(kw not in sym for sym in symbols)]

            for segment_text, segment_direction_ctx in segments:
                s = segment_text.strip()
                m_bracket = BRACKET_CONTENT_RE.fullmatch(s)
                if m_bracket:
                    inner_content = m_bracket.group(2)
                    is_pure_ltr_inner = pure_ltr_re.match(inner_content) is not None
                    is_pure_rtl_inner = rtl_char_re.search(inner_content) is not None and re.search(r"[A-Za-z0-9]", inner_content) is None
                    if is_pure_ltr_inner or is_pure_rtl_inner: continue

                if any([INLINE_CODE_RE.match(s), any(mk in s for mk in RLM+LRM)]): continue
                if rtl_char_re.search(s) and re.search(r"[A-Za-z0-9]", s):
                    disp = get_display(s)
                    if disp != s:
                        issues.append(
                            f"::{sev['bidi_mismatch'].lower()} file={path},line={idx}::BIDI mismatch in {part}: the text '{s}' is displayed as '{disp}'"
                        )

                if segment_direction_ctx != 'rtl': continue
                if not (part == 'title' and is_link_only_item):
                    for sym in symbols:
                        if sym in s and not any(m in s for m in LRM):
                            issues.append(
                                f"::{sev['symbol'].lower()} file={path},line={idx}::Symbol '{sym}' in {part} '{s}' may need trailing '&lrm;' marker."
                            )
                    for kw in filtered_keywords:
                        if kw in s and not any(m in s for m in RLM):
                            issues.append(
                                f"::{sev['keyword'].lower()} file={path},line={idx}::Keyword '{kw}' in {part} '{s}' may need trailing '&rlm;' marker."
                            )

                if (part != 'title') and pure_ltr_re.match(s) and not rtl_char_re.search(s) and len(s)>=min_len:
                    issues.append(
                        f"::{sev['pure_ltr'].lower()} file={path},line={idx}::Pure LTR text '{s}' in {part} of RTL context may need trailing '&rlm;' marker."
                    )

    if len(block_context_stack) > 1:
        issues.append(
            f"::error file={path},line={len(lines)}::Found unclosed <div dir='...'> tag. "
            f"The final block context is '{block_context_stack[-1]}', not the file's base '{file_direction_ctx}'."
        )

    return issues

# ============================
# GIT CHANGE LINES HELPER
# ============================

def get_changed_lines_for_file(filepath):
    """
    Returns line numbers changed in current PR for a file.
    Used to restrict annotations only to modified lines.
    """
    import subprocess
    changed_lines = set()
    try:
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
    except Exception:
        pass
    return changed_lines

# ============================
# MAIN ENTRY POINT
# ============================

def main():
    parser = argparse.ArgumentParser(
        description="Lints Markdown files for RTL/LTR issues, with PR annotation support."
    )
    parser.add_argument('paths_to_scan', nargs='+', help="List of files or directories to scan for all issues.")
    parser.add_argument('--changed-files', nargs='*', default=None, help="List of changed files to generate PR annotations for.")
    parser.add_argument('--log-file', default='rtl-linter-output.log', help="File to write all linter output to.")
    args = parser.parse_args()

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cfg = load_config(os.path.join(script_dir, 'rtl_linter_config.yml'))

    total = errs = annotated_errs = 0
    any_issues = False
    changed_files_set = set(os.path.normpath(f) for f in args.changed_files) if args.changed_files else set()
    changed_lines_map = {f: get_changed_lines_for_file(f) for f in changed_files_set}

    with open(args.log_file, 'w', encoding='utf-8') as log_f:
        for p_scan_arg in args.paths_to_scan:
            normalized_scan_path = os.path.normpath(p_scan_arg)
            files_to_lint = []

            if os.path.isdir(normalized_scan_path):
                for root, _, files in os.walk(normalized_scan_path):
                    files_to_lint.extend([os.path.join(root, fn) for fn in files if fn.lower().endswith('.md')])
            elif normalized_scan_path.lower().endswith('.md'):
                files_to_lint.append(normalized_scan_path)

            for file_path in files_to_lint:
                total += 1
                issues_found = lint_file(file_path, cfg)
                for issue_str in issues_found:
                    log_f.write(issue_str + '\n')
                    any_issues = True
                    if file_path in changed_files_set:
                        m = re.search(r'line=(\d+)', issue_str)
                        if m and int(m.group(1)) in changed_lines_map.get(file_path, set()):
                            print(issue_str)
                            if issue_str.startswith("::error"):
                                annotated_errs += 1
                    if issue_str.startswith(("::error","::warning")):
                        errs += 1

    if not any_issues:
        try:
            os.remove(args.log_file)
        except Exception:
            pass

    # [MODIFICATION] Professional notice with summary
    print(f"::notice ::Processed {total} files, found {errs} issues.")
    sys.exit(1 if annotated_errs else 0)

if __name__ == '__main__':
    main()





