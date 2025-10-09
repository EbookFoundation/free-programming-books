"""Commonmark default options.

This differs to presets.default,
primarily in that it allows HTML and does not enable components:

- block: table
- inline: strikethrough
"""
from ..utils import PresetType


def make() -> PresetType:
    return {
        "options": {
            "maxNesting": 20,  # Internal protection, recursion limit
            "html": True,  # Enable HTML tags in source,
            # this is just a shorthand for .enable(["html_inline", "html_block"])
            # used by the linkify rule:
            "linkify": False,  # autoconvert URL-like texts to links
            # used by the replacements and smartquotes rules
            # Enable some language-neutral replacements + quotes beautification
            "typographer": False,
            # used by the smartquotes rule:
            # Double + single quotes replacement pairs, when typographer enabled,
            # and smartquotes on. Could be either a String or an Array.
            #
            # For example, you can use '«»„“' for Russian, '„“‚‘' for German,
            # and ['«\xA0', '\xA0»', '‹\xA0', '\xA0›'] for French (including nbsp).
            "quotes": "\u201c\u201d\u2018\u2019",  # /* “”‘’ */
            # Renderer specific; these options are used directly in the HTML renderer
            "xhtmlOut": True,  # Use '/' to close single tags (<br />)
            "breaks": False,  # Convert '\n' in paragraphs into <br>
            "langPrefix": "language-",  # CSS language prefix for fenced blocks
            # Highlighter function. Should return escaped HTML,
            # or '' if the source string is not changed and should be escaped externally.
            # If result starts with <pre... internal wrapper is skipped.
            #
            # function (/*str, lang, attrs*/) { return ''; }
            #
            "highlight": None,
        },
        "components": {
            "core": {"rules": ["normalize", "block", "inline", "text_join"]},
            "block": {
                "rules": [
                    "blockquote",
                    "code",
                    "fence",
                    "heading",
                    "hr",
                    "html_block",
                    "lheading",
                    "list",
                    "reference",
                    "paragraph",
                ]
            },
            "inline": {
                "rules": [
                    "autolink",
                    "backticks",
                    "emphasis",
                    "entity",
                    "escape",
                    "html_inline",
                    "image",
                    "link",
                    "newline",
                    "text",
                ],
                "rules2": ["balance_pairs", "emphasis", "fragments_join"],
            },
        },
    }
