#!/usr/bin/env python3
# ... [everything above unchanged] ...


def lint_file(path, cfg):
    """
    Analyzes a single Markdown file for RTL/LTR issues.
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

        if CODE_FENCE_START.match(line):
            continue

        # ✅ FIXED SECTION BELOW
        m_div_open = HTML_DIR_ATTR_RE.search(line)
        has_div_close = '</div>' in line

        if m_div_open and 'markdown="1"' in line:
            new_div_ctx = m_div_open.group(2).lower()
            block_context_stack.append(new_div_ctx)

        if has_div_close and len(block_context_stack) > 1:
            block_context_stack.pop()
        # ✅ FIXED SECTION END

        list_item = LIST_ITEM_RE.match(line)
        if not list_item:
            continue

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

        if (active_block_direction_ctx == 'rtl' and author and meta and
            rtl_char_re.search(author) and pure_ltr_re.match(meta) and
            len(meta) >= min_len and
            not any(author.strip().endswith(rlm_marker) for rlm_marker in RLM)):
            issues.append(
                f"::{sev['author_meta'].lower()} file={path},line={idx}::RTL author '{author.strip()}' "
                f"followed by LTR meta '{meta}' may need '&rlm;' after author."
            )

        for part, raw_text in [('title', title), ('author', author), ('meta', meta)]:
            if not raw_text or (part == 'meta' and raw_text in ignore_meta):
                continue

            segments = split_by_span(raw_text, active_block_direction_ctx)
            filtered_keywords = [kw for kw in keywords_orig]
            for sym in symbols:
                filtered_keywords = [kw for kw in filtered_keywords if kw not in sym]

            for segment_text, segment_direction_ctx in segments:
                s = segment_text.strip()
                m_bracket = BRACKET_CONTENT_RE.fullmatch(s)
                if m_bracket:
                    inner_content = m_bracket.group(2)
                    is_pure_ltr_inner = pure_ltr_re.match(inner_content) is not None
                    is_pure_rtl_inner = (
                        rtl_char_re.search(inner_content) is not None and
                        re.search(r"[A-Za-z0-9]", inner_content) is None
                    )
                    if is_pure_ltr_inner or is_pure_rtl_inner:
                        continue

                if any([
                    INLINE_CODE_RE.match(s),
                    any(mk in s for mk in RLM + LRM)
                ]):
                    continue

                if rtl_char_re.search(s) and re.search(r"[A-Za-z0-9]", s):
                    disp = get_display(s)
                    if disp != s:
                        issues.append(
                            f"::{sev['bidi_mismatch'].lower()} file={path},line={idx}::BIDI mismatch "
                            f"in {part}: the text '{s}' is displayed as '{disp}'"
                        )

                if segment_direction_ctx != 'rtl':
                    continue

                if not (part == 'title' and is_link_only_item):
                    for sym in symbols:
                        if sym in s and not any(m in s for m in LRM):
                            issues.append(
                                f"::{sev['symbol'].lower()} file={path},line={idx}::Symbol '{sym}' "
                                f"in {part} '{s}' may need trailing '&lrm;' marker."
                            )
                    for kw in filtered_keywords:
                        if kw in s and not any(m in s for m in RLM):
                            issues.append(
                                f"::{sev['keyword'].lower()} file={path},line={idx}::Keyword '{kw}' "
                                f"in {part} '{s}' may need trailing '&rlm;' marker."
                            )

                if (part != 'title' and pure_ltr_re.match(s) and
                    not rtl_char_re.search(s) and len(s) >= min_len):
                    issues.append(
                        f"::{sev['pure_ltr'].lower()} file={path},line={idx}::Pure LTR text '{s}' "
                        f"in {part} of RTL context may need trailing '&rlm;' marker."
                    )

    return issues

# ... [rest of file (get_changed_lines_for_file, main) unchanged] ...
