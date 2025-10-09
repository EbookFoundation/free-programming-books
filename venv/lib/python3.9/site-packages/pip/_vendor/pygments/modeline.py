"""
    pygments.modeline
    ~~~~~~~~~~~~~~~~~

    A simple modeline parser (based on pymodeline).

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re

__all__ = ['get_filetype_from_buffer']


modeline_re = re.compile(r'''
    (?: vi | vim | ex ) (?: [<=>]? \d* )? :
    .* (?: ft | filetype | syn | syntax ) = ( [^:\s]+ )
''', re.VERBOSE)


def get_filetype_from_line(l): # noqa: E741
    m = modeline_re.search(l)
    if m:
        return m.group(1)


def get_filetype_from_buffer(buf, max_lines=5):
    """
    Scan the buffer for modelines and return filetype if one is found.
    """
    lines = buf.splitlines()
    for line in lines[-1:-max_lines-1:-1]:
        ret = get_filetype_from_line(line)
        if ret:
            return ret
    for i in range(max_lines, -1, -1):
        if i < len(lines):
            ret = get_filetype_from_line(lines[i])
            if ret:
                return ret

    return None
