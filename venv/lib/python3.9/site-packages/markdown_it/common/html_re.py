"""Regexps to match html elements
"""

import re

attr_name = "[a-zA-Z_:][a-zA-Z0-9:._-]*"

unquoted = "[^\"'=<>`\\x00-\\x20]+"
single_quoted = "'[^']*'"
double_quoted = '"[^"]*"'

attr_value = "(?:" + unquoted + "|" + single_quoted + "|" + double_quoted + ")"

attribute = "(?:\\s+" + attr_name + "(?:\\s*=\\s*" + attr_value + ")?)"

open_tag = "<[A-Za-z][A-Za-z0-9\\-]*" + attribute + "*\\s*\\/?>"

close_tag = "<\\/[A-Za-z][A-Za-z0-9\\-]*\\s*>"
comment = "<!---->|<!--(?:-?[^>-])(?:-?[^-])*-->"
processing = "<[?][\\s\\S]*?[?]>"
declaration = "<![A-Z]+\\s+[^>]*>"
cdata = "<!\\[CDATA\\[[\\s\\S]*?\\]\\]>"

HTML_TAG_RE = re.compile(
    "^(?:"
    + open_tag
    + "|"
    + close_tag
    + "|"
    + comment
    + "|"
    + processing
    + "|"
    + declaration
    + "|"
    + cdata
    + ")"
)
HTML_OPEN_CLOSE_TAG_STR = "^(?:" + open_tag + "|" + close_tag + ")"
HTML_OPEN_CLOSE_TAG_RE = re.compile(HTML_OPEN_CLOSE_TAG_STR)
