"""
    pygments.style
    ~~~~~~~~~~~~~~

    Basic style object.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from pip._vendor.pygments.token import Token, STANDARD_TYPES

# Default mapping of ansixxx to RGB colors.
_ansimap = {
    # dark
    'ansiblack': '000000',
    'ansired': '7f0000',
    'ansigreen': '007f00',
    'ansiyellow': '7f7fe0',
    'ansiblue': '00007f',
    'ansimagenta': '7f007f',
    'ansicyan': '007f7f',
    'ansigray': 'e5e5e5',
    # normal
    'ansibrightblack': '555555',
    'ansibrightred': 'ff0000',
    'ansibrightgreen': '00ff00',
    'ansibrightyellow': 'ffff00',
    'ansibrightblue': '0000ff',
    'ansibrightmagenta': 'ff00ff',
    'ansibrightcyan': '00ffff',
    'ansiwhite': 'ffffff',
}
# mapping of deprecated #ansixxx colors to new color names
_deprecated_ansicolors = {
    # dark
    '#ansiblack': 'ansiblack',
    '#ansidarkred': 'ansired',
    '#ansidarkgreen': 'ansigreen',
    '#ansibrown': 'ansiyellow',
    '#ansidarkblue': 'ansiblue',
    '#ansipurple': 'ansimagenta',
    '#ansiteal': 'ansicyan',
    '#ansilightgray': 'ansigray',
    # normal
    '#ansidarkgray': 'ansibrightblack',
    '#ansired': 'ansibrightred',
    '#ansigreen': 'ansibrightgreen',
    '#ansiyellow': 'ansibrightyellow',
    '#ansiblue': 'ansibrightblue',
    '#ansifuchsia': 'ansibrightmagenta',
    '#ansiturquoise': 'ansibrightcyan',
    '#ansiwhite': 'ansiwhite',
}
ansicolors = set(_ansimap)


class StyleMeta(type):

    def __new__(mcs, name, bases, dct):
        obj = type.__new__(mcs, name, bases, dct)
        for token in STANDARD_TYPES:
            if token not in obj.styles:
                obj.styles[token] = ''

        def colorformat(text):
            if text in ansicolors:
                return text
            if text[0:1] == '#':
                col = text[1:]
                if len(col) == 6:
                    return col
                elif len(col) == 3:
                    return col[0] * 2 + col[1] * 2 + col[2] * 2
            elif text == '':
                return ''
            elif text.startswith('var') or text.startswith('calc'):
                return text
            assert False, f"wrong color format {text!r}"

        _styles = obj._styles = {}

        for ttype in obj.styles:
            for token in ttype.split():
                if token in _styles:
                    continue
                ndef = _styles.get(token.parent, None)
                styledefs = obj.styles.get(token, '').split()
                if not ndef or token is None:
                    ndef = ['', 0, 0, 0, '', '', 0, 0, 0]
                elif 'noinherit' in styledefs and token is not Token:
                    ndef = _styles[Token][:]
                else:
                    ndef = ndef[:]
                _styles[token] = ndef
                for styledef in obj.styles.get(token, '').split():
                    if styledef == 'noinherit':
                        pass
                    elif styledef == 'bold':
                        ndef[1] = 1
                    elif styledef == 'nobold':
                        ndef[1] = 0
                    elif styledef == 'italic':
                        ndef[2] = 1
                    elif styledef == 'noitalic':
                        ndef[2] = 0
                    elif styledef == 'underline':
                        ndef[3] = 1
                    elif styledef == 'nounderline':
                        ndef[3] = 0
                    elif styledef[:3] == 'bg:':
                        ndef[4] = colorformat(styledef[3:])
                    elif styledef[:7] == 'border:':
                        ndef[5] = colorformat(styledef[7:])
                    elif styledef == 'roman':
                        ndef[6] = 1
                    elif styledef == 'sans':
                        ndef[7] = 1
                    elif styledef == 'mono':
                        ndef[8] = 1
                    else:
                        ndef[0] = colorformat(styledef)

        return obj

    def style_for_token(cls, token):
        t = cls._styles[token]
        ansicolor = bgansicolor = None
        color = t[0]
        if color in _deprecated_ansicolors:
            color = _deprecated_ansicolors[color]
        if color in ansicolors:
            ansicolor = color
            color = _ansimap[color]
        bgcolor = t[4]
        if bgcolor in _deprecated_ansicolors:
            bgcolor = _deprecated_ansicolors[bgcolor]
        if bgcolor in ansicolors:
            bgansicolor = bgcolor
            bgcolor = _ansimap[bgcolor]

        return {
            'color':        color or None,
            'bold':         bool(t[1]),
            'italic':       bool(t[2]),
            'underline':    bool(t[3]),
            'bgcolor':      bgcolor or None,
            'border':       t[5] or None,
            'roman':        bool(t[6]) or None,
            'sans':         bool(t[7]) or None,
            'mono':         bool(t[8]) or None,
            'ansicolor':    ansicolor,
            'bgansicolor':  bgansicolor,
        }

    def list_styles(cls):
        return list(cls)

    def styles_token(cls, ttype):
        return ttype in cls._styles

    def __iter__(cls):
        for token in cls._styles:
            yield token, cls.style_for_token(token)

    def __len__(cls):
        return len(cls._styles)


class Style(metaclass=StyleMeta):

    #: overall background color (``None`` means transparent)
    background_color = '#ffffff'

    #: highlight background color
    highlight_color = '#ffffcc'

    #: line number font color
    line_number_color = 'inherit'

    #: line number background color
    line_number_background_color = 'transparent'

    #: special line number font color
    line_number_special_color = '#000000'

    #: special line number background color
    line_number_special_background_color = '#ffffc0'

    #: Style definitions for individual token types.
    styles = {}

    #: user-friendly style name (used when selecting the style, so this
    # should be all-lowercase, no spaces, hyphens)
    name = 'unnamed'

    aliases = []

    # Attribute for lexers defined within Pygments. If set
    # to True, the style is not shown in the style gallery
    # on the website. This is intended for language-specific
    # styles.
    web_style_gallery_exclude = False
