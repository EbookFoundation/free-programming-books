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
"""
import sys
import os
import argparse
import re
import yaml
from bidi.algorithm import get_display


def load_config(path):
    """
    Loads configuration from the specified YAML file.

    If the file does not exist or an error occurs during loading,
    default values will be used.

    Args:
        path (str): The path to the YAML configuration file.

    Returns:
        dict: A dictionary containing the configuration parameters.
              Default values are merged with those loaded from the file,
              with the latter taking precedence.
    """
    # Default configuration values
    default = {
        'ltr_keywords': [],
        'ltr_symbols': [],
        'pure_ltr_pattern': r"^[\u0000-\u007F]+$",  # Matches ASCII characters (Basic Latin character)
        'rtl_chars_pattern': r"[\u0590-\u08FF]",    # Matches Right-to-Left (RTL) characters (Arabic, Hebrew, etc.)
        'severity': {
            'bidi_mismatch': 'error',   # A difference between the displayed and logical order of text
            'keyword': 'warning',       # An LTR keyword (e.g., "HTML") in an RTL context might need an &rlm;
            'symbol': 'warning',        # An LTR symbol (e.g., "C#") in an RTL context might need an &lrm;
            'pure_ltr': 'notice',       # A purely LTR segment in an RTL context might need a trailing &lrm;
            'author_meta': 'notice'     # Specific rules for LTR authors/metadata in RTL contexts.
        },
        'ignore_meta': ['PDF', 'EPUB', 'HTML', 'podcast', 'videocast'],
        'min_ltr_length': 3,
        'rlm_entities': ['&rlm;', '&#x200F;', '&#8207;'],
        'lrm_entities': ['&lrm;', '&#x200E;', '&#8206;']
    }

    # If a path is specified and the file exists, attempt to load it
    if path and os.path.exists(path):
        try:
            with open(path, encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}
                conf = data.get('rtl_config', {})
                default.update(conf)
        except Exception as e:
            print(f"::warning file={path}::Could not load config: {e}. Using defaults.") # Output to stdout for GitHub Actions

    # Return the configuration (updated defaults or just defaults)
    return default


def is_rtl_filename(path):
    '''
    Checks if the given filename indicates an RTL filename.

    Args:
        path (str): The path to the file.

    Returns:
        bool: True if the filename suggests an RTL language, False otherwise.
    '''
    name = os.path.basename(path).lower()
    return any(name.endswith(suf) for suf in ['-ar.md','_ar.md','-he.md','_he.md','-fa.md','_fa.md','-ur.md','_ur.md'])

# Regex to identify a Markdown list item (e.g., "* text", "- text")
LIST_ITEM_RE = re.compile(r'^\s*[\*\-\+]\s+(.*)')

# Regex to extract title, URL, author, and metadata from a formatted book item
# Example: Book Title - Author (Metadata)
BOOK_ITEM_RE = re.compile(
    r"^\s*\[(?P<title>.+?)\]\((?P<url>.+?)\)"   # Title and URL (required)
    r"(?:\s*[-–—]\s*(?P<author>[^\(\n\[]+?))?"  # Author (optional), separated by -, –, —
    r"(?:\s*[\(\[](?P<meta>.*?)[\)\]])?\s*$"    # Metadata (optional), enclosed in parentheses () or []
)

# Regex to find the dir="rtl" or dir="ltr" attribute in an HTML tag
HTML_DIR_ATTR_RE = re.compile(r"dir\s*=\s*(['\"])(rtl|ltr)\1", re.IGNORECASE)

# Regex to find <span> tags with a dir attribute
SPAN_DIR_RE = re.compile(r'<span[^>]*dir=["\'](rtl|ltr)["\'][^>]*>', re.IGNORECASE)

# Regex to identify inline code (text enclosed in single backticks)
INLINE_CODE_RE = re.compile(r'^`.*`$')

# Regex to identify the start of a code block (```)
# Can be preceded by spaces or a '>' character (for blockquotes)
CODE_FENCE_START = re.compile(r'^\s*>?\s*```')

# Regex to identify text entirely enclosed in parentheses or square brackets.
# Useful for skipping segments like "(PDF)" or "[Free]" during analysis.
BRACKET_CONTENT_RE = re.compile(r'''
    (?:^|\W)        # Start of line or non-word character
    (\[|\()         # Open square or round bracket
    ([^\n\)\]]*?)   # Content
    (\]|\))         # Close square or round bracket
    (?:\W|$)        # End of line or non-word character
''', re.VERBOSE | re.UNICODE)   # VERBOSE for comments, UNICODE for correct matching


def split_by_span(text, base_ctx):
    """
    Splits text into segments based on nested <span> tags with dir attributes.

    Args:
        text (str): The input string to split.
        base_ctx (str): The base directionality context ('rtl' or 'ltr').

    Returns:
        list: A list of tuples, where each tuple contains a text segment (str)
              and its corresponding directionality context ('rtl' or 'ltr').

    Example of stack behavior:
        Input: "Text <span dir='rtl'>RTL <span dir='ltr'>LTR</span> RTL</span> Text"
        base_ctx: 'ltr'

        Initial stack: ['ltr']
        Tokens: ["Text ", "<span dir='rtl'>", "RTL ", "<span dir='ltr'>", "LTR", "</span>", " RTL", "</span>", " Text"]

        Processing:
        1. "Text ": segments.append(("Text ", 'ltr')), stack: ['ltr']
        2. "<span dir='rtl'>": stack.append('rtl'), stack: ['ltr', 'rtl']
        3. "RTL ": segments.append(("RTL ", 'rtl')), stack: ['ltr', 'rtl']
        4. "<span dir='ltr'>": stack.append('ltr'), stack: ['ltr', 'rtl', 'ltr']
        5. "LTR": segments.append(("LTR", 'ltr')), stack: ['ltr', 'rtl', 'ltr']
        6. "</span>": stack.pop(), stack: ['ltr', 'rtl']
        7. " RTL": segments.append((" RTL", 'rtl')), stack: ['ltr', 'rtl']
        8. "</span>": stack.pop(), stack: ['ltr']
        9. " Text": segments.append((" Text", 'ltr')), stack: ['ltr']

        Resulting segments: [("Text ", 'ltr'), ("RTL ", 'rtl'), ("LTR", 'ltr'), (" RTL", 'rtl'), (" Text", 'ltr')]
    """
    # Split the text based on <span> tags
    tokens = re.split(r'(<span[^>]*dir=["\'](?:rtl|ltr)["\'][^>]*>|</span>)', text)

    # Initialize the stack with the base context
    stack = [base_ctx]

    # Initialize the segments
    segments = []

    # for each token
    for tok in tokens:

        # Skip empty tokens
        if not tok:
            continue

        # Check if the token is an opening <span> tag with a dir attribute
        m = SPAN_DIR_RE.match(tok)

        # If so, push the new context onto the stack
        if m:
            stack.append(m.group(1).lower()); continue
        
        # If the token is a closing </span> tag
        if tok.lower() == '</span>':

            # Pop the last context from the stack
            if len(stack) > 1: stack.pop()
            continue

        # Otherwise, if the token is not a span tag, it's a text segment.
        # So, we need to append the tuple (segment, current context) to segments[]
        # Where the current context is the top element of the stack.
        segments.append((tok, stack[-1]))

    # return the list of tuples
    return segments


def lint_file(path, cfg):
    """
    Analyzes a single Markdown file for RTL/LTR issues.

    Args:
        path (str): The path to the Markdown file to analyze.
        cfg (dict): The configuration dictionary.

    Returns:
        list: A list of strings, where each string represents a detected issue,
              formatted for GitHub Actions output.
    """
    # Initialize the list of issues
    issues = []

    # Try to read the file content and handle potential errors
    try:
        lines = open(path, encoding='utf-8').read().splitlines()
    except Exception as e:
        return [f"::error file={path},line=1::Cannot read file: {e}"] # Return as a list of issues

    # Extract configuration parameters for easier access and readability
    keywords_orig = cfg['ltr_keywords']
    symbols = cfg['ltr_symbols']
    pure_ltr_re = re.compile(cfg['pure_ltr_pattern'])
    rtl_char_re = re.compile(cfg['rtl_chars_pattern'])
    sev = cfg['severity']
    ignore_meta = set(cfg['ignore_meta'])
    min_len = cfg['min_ltr_length']

    # chr(0x200F) = RLM Unicode character
    # chr(0x200E) = LRM Unicode character
    # These control character must be added here in the code and not in the YAML configuration file,
    # due to the fact that if we included them in the YAML file they would be invisible and, therefore,
    # the YAML file would be less readable
    RLM = [chr(0x200F)] + cfg['rlm_entities']
    LRM = [chr(0x200E)] + cfg['lrm_entities']

    # Determine the directionality context of the file (RTL or LTR) based on the filename
    file_direction_ctx = 'rtl' if is_rtl_filename(path) else 'ltr'

    # Stack to manage block-level direction contexts for nested divs.
    # Initialized with the file's base direction context.
    block_context_stack = [file_direction_ctx]

    # Iterate over each line of the file with its line number
    for idx, line in enumerate(lines, 1):

        # The active block direction context for the current line is the top of the stack.
        active_block_direction_ctx = block_context_stack[-1]

        # Skip lines that start a code block (```)
        if CODE_FENCE_START.match(line): continue

        # Find all opening and closing <div> tags on the line to handle cases
        # where there can be multiple <div> opening and closing on the same line
        div_tags = re.findall(r"(<div[^>]*dir=['\"](rtl|ltr)['\"][^>]*>|</div>)", line, re.IGNORECASE)

        # Process each found tag in order to correctly update the context stack
        for tag_tuple in div_tags:
            # re.findall with multiple capture groups returns a list of tuples:
            # tag: The full matched tag (e.g., '<div...>' or '</div>')
            # direction: The captured direction ('rtl' or 'ltr'), or empty for a closing tag
            tag, direction = tag_tuple

            # If it's an opening tag with 'markdown="1"', push the new context
            if tag.startswith('<div') and 'markdown="1"' in tag:
                block_context_stack.append(direction.lower())
            # If it's a closing tag and we are inside a div, pop the context
            elif tag == '</div>' and len(block_context_stack) > 1:
                block_context_stack.pop()
        # Check if the line is a Markdown list item
        list_item = LIST_ITEM_RE.match(line)

        # If the line is not a list item, skip to the next line
        if not list_item: continue

        # Extract the text content of the list item and remove leading/trailing whitespace
        text = list_item.group(1).strip()

        # Extract item parts (title, author, metadata) if it matches the book format
        book_item = BOOK_ITEM_RE.match(text)

        # If the current line is a book item
        if book_item:

            # Extract title, author, and metadata from the book item
            title = book_item.group('title')
            author = (book_item.group('author') or '').strip()
            meta = (book_item.group('meta') or '').strip()

            # If the list item is just a link like the link in the section "### Index" of the .md files (i.e., [Title](url))
            is_link_only_item = not author and not meta

        # Otherwise, if it's not a book item
        else:

            # Initialize title, author, and meta with empty strings
            title, author, meta = text, '', ''

            # Set is_link_only_item to False
            is_link_only_item = False

        # Specific check: RTL author followed by LTR metadata (e.g., اسم المؤلف (PDF))
        if  active_block_direction_ctx == 'rtl' and \
            author and meta and \
            rtl_char_re.search(author) and pure_ltr_re.match(meta) and \
            len(meta) >= min_len and \
            not any(author.strip().endswith(rlm_marker) for rlm_marker in RLM):
            issues.append(
                f"::{sev['author_meta'].lower()} file={path},line={idx}::RTL author '{author.strip()}' followed by LTR meta '{meta}' may need '&rlm;' after author."
            )
        
        # Analyze individual parts of the item (title, author, metadata)
        for part, raw_text in [('title', title), ('author', author), ('meta', meta)]:

            # Skip if the part is empty or if it's metadata to be ignored (e.g., "PDF")
            if not raw_text or (part=='meta' and raw_text in ignore_meta): continue

            # Split the part into segments based on <span> tags with dir attributes
            segments = split_by_span(raw_text, active_block_direction_ctx)

            # Filter keywords to avoid duplicates with symbols (a symbol can contain a keyword)
            filtered_keywords = [kw for kw in keywords_orig]
            for sym in symbols:
                filtered_keywords = [kw for kw in filtered_keywords if kw not in sym]

            # Iterate over each text segment and its directionality context
            for segment_text, segment_direction_ctx in segments:

                # Remove leading/trailing whitespace from the segment text
                s = segment_text.strip()

                # In the following block of code, it's checked if the segment is entirely enclosed in parentheses or brackets.
                # In fact, if the content inside is purely LTR or RTL, its display is usually
                # well-isolated by the parentheses or brackets and less prone to BIDI issues.
                # Mixed LTR/RTL content inside brackets should still be checked.

                # Check if the segment is entirely enclosed in parentheses or brackets.
                m_bracket = BRACKET_CONTENT_RE.fullmatch(s)
                if m_bracket:

                    # If it is, extract the content inside the parentheses/brackets.
                    inner_content = m_bracket.group(2)

                    # Determine if the inner content is purely LTR or purely RTL.
                    is_pure_ltr_inner = pure_ltr_re.match(inner_content) is not None

                    # Check for pure RTL: contains RTL chars AND no LTR chars (using [A-Za-z0-9] as a proxy for common LTR chars)
                    is_pure_rtl_inner = rtl_char_re.search(inner_content) is not None and re.search(r"[A-Za-z0-9]", inner_content) is None
                    
                    # Skip the segment ONLY if the content inside is purely LTR or purely RTL.
                    if is_pure_ltr_inner or is_pure_rtl_inner: continue
                
                # Skip if it's inline code (i.e., `...`) or already contains directionality markers (e.g., &rlm; or &lrm;)
                if any([
                    INLINE_CODE_RE.match(s),
                    any(mk in s for mk in RLM+LRM)
                ]):
                    continue
                
                # Check for BIDI mismatch: if the text contains both RTL and LTR
                # characters and the calculated visual order differs from the logical order.
                if rtl_char_re.search(s) and re.search(r"[A-Za-z0-9]", s):
                    disp = get_display(s)
                    if disp != s:
                        issues.append(
                            f"::{sev['bidi_mismatch'].lower()} file={path},line={idx}::BIDI mismatch in {part}: the text '{s}' is displayed as '{disp}'"
                        )
                
                # If the segment context is LTR, there is no need to check LTR keywords and LTR symbols
                # that might need directionality markers, so we can skip the next checks and move on to the next line of the file
                if segment_direction_ctx != 'rtl': continue

                # Skip keyword and symbol checks for titles of link-only items (e.g., in the Index section of markdown files)
                if not (part == 'title' and is_link_only_item):

                    # Check for LTR symbols: if an LTR symbol is present and lacks an '&lrm;' marker
                    for sym in symbols:
                        if sym in s and not any(m in s for m in LRM):
                            issues.append(
                                f"::{sev['symbol'].lower()} file={path},line={idx}::Symbol '{sym}' in {part} '{s}' may need trailing '&lrm;' marker."
                            )

                    # Check for LTR keywords: if an LTR keyword is present and lacks an RLM marker
                    for kw in filtered_keywords:
                        if kw in s and not any(m in s for m in RLM):
                            issues.append(
                                f"::{sev['keyword'].lower()} file={path},line={idx}::Keyword '{kw}' in {part} '{s}' may need trailing '&rlm;' marker."
                            )
                
                # Check for "Pure LTR" text: if the segment is entirely LTR,
                # it's not a title, and has a minimum length, it might need a trailing RLM.
                if (part != 'title') and pure_ltr_re.match(s) and not rtl_char_re.search(s) and len(s)>=min_len:
                    issues.append(
                        f"::{sev['pure_ltr'].lower()} file={path},line={idx}::Pure LTR text '{s}' in {part} of RTL context may need trailing '&rlm;' marker."
                    )
    
    # Check for unclosed div tags at the end of the file
    if len(block_context_stack) > 1:
        issues.append(
            f"::error file={path},line={len(lines)}::Found unclosed <div dir='...'> tag. "
            f"The final block context is '{block_context_stack[-1]}', not the file's base '{file_direction_ctx}'."
        )

    # Return the list of found issues
    return issues

def get_changed_lines_for_file(filepath):
    """
    Returns a set of line numbers (1-based) that were changed in the given file in the current PR.

    This function uses 'git diff' to compare the current branch with 'origin/main' and extracts
    the line numbers of added or modified lines. It is used to restrict PR annotations to only
    those lines that have been changed in the pull request.

    Args:
        filepath (str): The path to the file to check for changes.

    Returns:
        set: A set of 1-based line numbers that were added or modified in the file.

    Note:
        - Requires that the script is run inside a Git repository.
        - If the merge base cannot be found, returns an empty set and does not print errors.
    """
    import subprocess
    changed_lines = set()
    try:
        # Get the diff for the file (unified=0 for no context lines)
        diff = subprocess.check_output(
            ['git', 'diff', '--unified=0', 'origin/main...', '--', filepath],
            encoding='utf-8', errors='ignore'
        )
        for line in diff.splitlines():
            if line.startswith('@@'):
                # Example: @@ -10,0 +11,3 @@
                m = re.search(r'\+(\d+)(?:,(\d+))?', line)
                if m:
                    start = int(m.group(1))
                    count = int(m.group(2) or '1')
                    for i in range(start, start + count):
                        changed_lines.add(i)
    except Exception:
        # Silently ignore errors (e.g., unable to find merge base)
        pass
    return changed_lines


def main():
    """
    Main entry point for the RTL/LTR Markdown linter.

    Parses command-line arguments, loads configuration, and scans the specified files or directories
    for Markdown files. For each file, it detects RTL/LTR issues and writes all findings to a log file.
    For files changed in the current PR, only issues on changed lines are printed to stdout as GitHub
    Actions annotations.

    Exit code is 1 if any error or warning is found on changed lines, otherwise 0.

    Command-line arguments:
        paths_to_scan: List of files or directories to scan for issues.
        --changed-files: List of files changed in the PR (for annotation filtering).
        --log-file: Path to the output log file (default: rtl-linter-output.log).
    """
    # Create an ArgumentParser object to handle command-line arguments
    parser = argparse.ArgumentParser(
        description="Lints Markdown files for RTL/LTR issues, with PR annotation support."
    )

    # Argument for files/directories to scan
    parser.add_argument(
        'paths_to_scan',
        nargs='+',
        help="List of files or directories to scan for all issues."
    )

    # Optional argument for changed files (for PR annotation filtering)
    parser.add_argument(
        '--changed-files',
        nargs='*',
        default=None,
        help="List of changed files to generate PR annotations for."
    )

    # Optional argument for the log file path
    parser.add_argument(
        '--log-file',
        default='rtl-linter-output.log',
        help="File to write all linter output to."
    )

    # Parse the command-line arguments
    args = parser.parse_args()

    # Determine the directory where the script is located to find the config file
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Load the configuration from 'rtl_linter_config.yml'
    cfg = load_config(os.path.join(script_dir, 'rtl_linter_config.yml'))

    # Initialize counters for total files processed and errors/warnings found
    total = errs = 0

    # Count errors/warnings ONLY on changed/added lines for PR annotation exit code
    annotated_errs = 0

    # Normalize changed file paths for consistent comparison
    changed_files_set = set(os.path.normpath(f) for f in args.changed_files) if args.changed_files else set()

    # Build a map: {filepath: set(line_numbers)} for changed files
    changed_lines_map = {}
    for f in changed_files_set:
        changed_lines_map[f] = get_changed_lines_for_file(f)

    # Flag to check if any issues were found
    any_issues = False

    # Open the specified log file in write mode with UTF-8 encoding
    with open(args.log_file, 'w', encoding='utf-8') as log_f:

        # Iterate over each path provided in 'paths_to_scan'
        for p_scan_arg in args.paths_to_scan:

            # Normalize the scan path to ensure consistent handling (e.g., slashes)
            normalized_scan_path = os.path.normpath(p_scan_arg)

            # If the path is a directory, recursively scan for .md files
            if os.path.isdir(normalized_scan_path):

                # Walk through the directory and its subdirectories to find all Markdown files
                for root, _, files in os.walk(normalized_scan_path):

                    # For each file in the directory
                    for fn in files:

                        # If the file is a Markdown file, lint it
                        if fn.lower().endswith('.md'):
                            file_path = os.path.normpath(os.path.join(root, fn))
                            total += 1
                            issues_found = lint_file(file_path, cfg)

                            # Process each issue found
                            for issue_str in issues_found:
                                log_f.write(issue_str + '\n')
                                any_issues = True # Flag to check if any issues were found

                                # For GitHub Actions PR annotations: print only if the file is changed
                                # and the issue is on a line that was actually modified or added in the PR
                                if file_path in changed_files_set:
                                    m = re.search(r'line=(\d+)', issue_str)
                                    if m and int(m.group(1)) in changed_lines_map.get(file_path, set()):
                                        print(issue_str)

                                        # Count errors on changed lines for the exit code logic
                                        if issue_str.startswith("::error"):
                                            annotated_errs += 1
                                
                                # Count all errors/warnings for reporting/debugging purposes
                                if issue_str.startswith("::error") or issue_str.startswith("::warning"):
                                    errs += 1

            # If the path is a Markdown file, lint it directly
            elif normalized_scan_path.lower().endswith('.md'):
                total += 1
                issues_found = lint_file(normalized_scan_path, cfg)

                # Process each issue found
                for issue_str in issues_found:

                    # Always write the issue to the log file for full reporting
                    log_f.write(issue_str + '\n')
                    any_issues = True # Flag to check if any issues were found

                    # For GitHub Actions PR annotations: print only if the file is changed
                    # and the issue is on a line that was actually modified or added in the PR
                    if normalized_scan_path in changed_files_set:

                        # Extract the line number from the issue string (e.g., ...line=123::)
                        m = re.search(r'line=(\d+)', issue_str)

                        if m and int(m.group(1)) in changed_lines_map.get(normalized_scan_path, set()):

                            # For GitHub Actions PR annotations: print the annotation
                            # so that GitHub Actions can display it in the PR summary
                            print(issue_str)

                            # Count errors on changed lines for the exit code logic
                            if issue_str.startswith("::error"):
                                annotated_errs += 1

                    # Count all errors/warnings for reporting/debugging purposes
                    if issue_str.startswith("::error") or issue_str.startswith("::warning"):
                        errs += 1

    # If no issues were found, remove the log file
    if not any_issues:
        try:
            os.remove(args.log_file)
        except Exception:
            pass

    # Print a debug message to stderr summarizing the linting process
    print(f"::notice ::Processed {total} files, found {errs} issues.")

    # Exit code: 1 only if there are annotated errors/warnings on changed lines
    sys.exit(1 if annotated_errs else 0)

if __name__ == '__main__':
    main()
