"""
    pygments.lexer
    ~~~~~~~~~~~~~~

    Base lexer classes.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import re
import sys
import time

from pip._vendor.pygments.filter import apply_filters, Filter
from pip._vendor.pygments.filters import get_filter_by_name
from pip._vendor.pygments.token import Error, Text, Other, Whitespace, _TokenType
from pip._vendor.pygments.util import get_bool_opt, get_int_opt, get_list_opt, \
    make_analysator, Future, guess_decode
from pip._vendor.pygments.regexopt import regex_opt

__all__ = ['Lexer', 'RegexLexer', 'ExtendedRegexLexer', 'DelegatingLexer',
           'LexerContext', 'include', 'inherit', 'bygroups', 'using', 'this',
           'default', 'words', 'line_re']

line_re = re.compile('.*?\n')

_encoding_map = [(b'\xef\xbb\xbf', 'utf-8'),
                 (b'\xff\xfe\0\0', 'utf-32'),
                 (b'\0\0\xfe\xff', 'utf-32be'),
                 (b'\xff\xfe', 'utf-16'),
                 (b'\xfe\xff', 'utf-16be')]

_default_analyse = staticmethod(lambda x: 0.0)


class LexerMeta(type):
    """
    This metaclass automagically converts ``analyse_text`` methods into
    static methods which always return float values.
    """

    def __new__(mcs, name, bases, d):
        if 'analyse_text' in d:
            d['analyse_text'] = make_analysator(d['analyse_text'])
        return type.__new__(mcs, name, bases, d)


class Lexer(metaclass=LexerMeta):
    """
    Lexer for a specific language.

    See also :doc:`lexerdevelopment`, a high-level guide to writing
    lexers.

    Lexer classes have attributes used for choosing the most appropriate
    lexer based on various criteria.

    .. autoattribute:: name
       :no-value:
    .. autoattribute:: aliases
       :no-value:
    .. autoattribute:: filenames
       :no-value:
    .. autoattribute:: alias_filenames
    .. autoattribute:: mimetypes
       :no-value:
    .. autoattribute:: priority

    Lexers included in Pygments should have two additional attributes:

    .. autoattribute:: url
       :no-value:
    .. autoattribute:: version_added
       :no-value:

    Lexers included in Pygments may have additional attributes:

    .. autoattribute:: _example
       :no-value:

    You can pass options to the constructor. The basic options recognized
    by all lexers and processed by the base `Lexer` class are:

    ``stripnl``
        Strip leading and trailing newlines from the input (default: True).
    ``stripall``
        Strip all leading and trailing whitespace from the input
        (default: False).
    ``ensurenl``
        Make sure that the input ends with a newline (default: True).  This
        is required for some lexers that consume input linewise.

        .. versionadded:: 1.3

    ``tabsize``
        If given and greater than 0, expand tabs in the input (default: 0).
    ``encoding``
        If given, must be an encoding name. This encoding will be used to
        convert the input string to Unicode, if it is not already a Unicode
        string (default: ``'guess'``, which uses a simple UTF-8 / Locale /
        Latin1 detection.  Can also be ``'chardet'`` to use the chardet
        library, if it is installed.
    ``inencoding``
        Overrides the ``encoding`` if given.
    """

    #: Full name of the lexer, in human-readable form
    name = None

    #: A list of short, unique identifiers that can be used to look
    #: up the lexer from a list, e.g., using `get_lexer_by_name()`.
    aliases = []

    #: A list of `fnmatch` patterns that match filenames which contain
    #: content for this lexer. The patterns in this list should be unique among
    #: all lexers.
    filenames = []

    #: A list of `fnmatch` patterns that match filenames which may or may not
    #: contain content for this lexer. This list is used by the
    #: :func:`.guess_lexer_for_filename()` function, to determine which lexers
    #: are then included in guessing the correct one. That means that
    #: e.g. every lexer for HTML and a template language should include
    #: ``\*.html`` in this list.
    alias_filenames = []

    #: A list of MIME types for content that can be lexed with this lexer.
    mimetypes = []

    #: Priority, should multiple lexers match and no content is provided
    priority = 0

    #: URL of the language specification/definition. Used in the Pygments
    #: documentation. Set to an empty string to disable.
    url = None

    #: Version of Pygments in which the lexer was added.
    version_added = None

    #: Example file name. Relative to the ``tests/examplefiles`` directory.
    #: This is used by the documentation generator to show an example.
    _example = None

    def __init__(self, **options):
        """
        This constructor takes arbitrary options as keyword arguments.
        Every subclass must first process its own options and then call
        the `Lexer` constructor, since it processes the basic
        options like `stripnl`.

        An example looks like this:

        .. sourcecode:: python

           def __init__(self, **options):
               self.compress = options.get('compress', '')
               Lexer.__init__(self, **options)

        As these options must all be specifiable as strings (due to the
        command line usage), there are various utility functions
        available to help with that, see `Utilities`_.
        """
        self.options = options
        self.stripnl = get_bool_opt(options, 'stripnl', True)
        self.stripall = get_bool_opt(options, 'stripall', False)
        self.ensurenl = get_bool_opt(options, 'ensurenl', True)
        self.tabsize = get_int_opt(options, 'tabsize', 0)
        self.encoding = options.get('encoding', 'guess')
        self.encoding = options.get('inencoding') or self.encoding
        self.filters = []
        for filter_ in get_list_opt(options, 'filters', ()):
            self.add_filter(filter_)

    def __repr__(self):
        if self.options:
            return f'<pygments.lexers.{self.__class__.__name__} with {self.options!r}>'
        else:
            return f'<pygments.lexers.{self.__class__.__name__}>'

    def add_filter(self, filter_, **options):
        """
        Add a new stream filter to this lexer.
        """
        if not isinstance(filter_, Filter):
            filter_ = get_filter_by_name(filter_, **options)
        self.filters.append(filter_)

    def analyse_text(text):
        """
        A static method which is called for lexer guessing.

        It should analyse the text and return a float in the range
        from ``0.0`` to ``1.0``.  If it returns ``0.0``, the lexer
        will not be selected as the most probable one, if it returns
        ``1.0``, it will be selected immediately.  This is used by
        `guess_lexer`.

        The `LexerMeta` metaclass automatically wraps this function so
        that it works like a static method (no ``self`` or ``cls``
        parameter) and the return value is automatically converted to
        `float`. If the return value is an object that is boolean `False`
        it's the same as if the return values was ``0.0``.
        """

    def _preprocess_lexer_input(self, text):
        """Apply preprocessing such as decoding the input, removing BOM and normalizing newlines."""

        if not isinstance(text, str):
            if self.encoding == 'guess':
                text, _ = guess_decode(text)
            elif self.encoding == 'chardet':
                try:
                    # pip vendoring note: this code is not reachable by pip,
                    # removed import of chardet to make it clear.
                    raise ImportError('chardet is not vendored by pip')
                except ImportError as e:
                    raise ImportError('To enable chardet encoding guessing, '
                                      'please install the chardet library '
                                      'from http://chardet.feedparser.org/') from e
                # check for BOM first
                decoded = None
                for bom, encoding in _encoding_map:
                    if text.startswith(bom):
                        decoded = text[len(bom):].decode(encoding, 'replace')
                        break
                # no BOM found, so use chardet
                if decoded is None:
                    enc = chardet.detect(text[:1024])  # Guess using first 1KB
                    decoded = text.decode(enc.get('encoding') or 'utf-8',
                                          'replace')
                text = decoded
            else:
                text = text.decode(self.encoding)
                if text.startswith('\ufeff'):
                    text = text[len('\ufeff'):]
        else:
            if text.startswith('\ufeff'):
                text = text[len('\ufeff'):]

        # text now *is* a unicode string
        text = text.replace('\r\n', '\n')
        text = text.replace('\r', '\n')
        if self.stripall:
            text = text.strip()
        elif self.stripnl:
            text = text.strip('\n')
        if self.tabsize > 0:
            text = text.expandtabs(self.tabsize)
        if self.ensurenl and not text.endswith('\n'):
            text += '\n'

        return text

    def get_tokens(self, text, unfiltered=False):
        """
        This method is the basic interface of a lexer. It is called by
        the `highlight()` function. It must process the text and return an
        iterable of ``(tokentype, value)`` pairs from `text`.

        Normally, you don't need to override this method. The default
        implementation processes the options recognized by all lexers
        (`stripnl`, `stripall` and so on), and then yields all tokens
        from `get_tokens_unprocessed()`, with the ``index`` dropped.

        If `unfiltered` is set to `True`, the filtering mechanism is
        bypassed even if filters are defined.
        """
        text = self._preprocess_lexer_input(text)

        def streamer():
            for _, t, v in self.get_tokens_unprocessed(text):
                yield t, v
        stream = streamer()
        if not unfiltered:
            stream = apply_filters(stream, self.filters, self)
        return stream

    def get_tokens_unprocessed(self, text):
        """
        This method should process the text and return an iterable of
        ``(index, tokentype, value)`` tuples where ``index`` is the starting
        position of the token within the input text.

        It must be overridden by subclasses. It is recommended to
        implement it as a generator to maximize effectiveness.
        """
        raise NotImplementedError


class DelegatingLexer(Lexer):
    """
    This lexer takes two lexer as arguments. A root lexer and
    a language lexer. First everything is scanned using the language
    lexer, afterwards all ``Other`` tokens are lexed using the root
    lexer.

    The lexers from the ``template`` lexer package use this base lexer.
    """

    def __init__(self, _root_lexer, _language_lexer, _needle=Other, **options):
        self.root_lexer = _root_lexer(**options)
        self.language_lexer = _language_lexer(**options)
        self.needle = _needle
        Lexer.__init__(self, **options)

    def get_tokens_unprocessed(self, text):
        buffered = ''
        insertions = []
        lng_buffer = []
        for i, t, v in self.language_lexer.get_tokens_unprocessed(text):
            if t is self.needle:
                if lng_buffer:
                    insertions.append((len(buffered), lng_buffer))
                    lng_buffer = []
                buffered += v
            else:
                lng_buffer.append((i, t, v))
        if lng_buffer:
            insertions.append((len(buffered), lng_buffer))
        return do_insertions(insertions,
                             self.root_lexer.get_tokens_unprocessed(buffered))


# ------------------------------------------------------------------------------
# RegexLexer and ExtendedRegexLexer
#


class include(str):  # pylint: disable=invalid-name
    """
    Indicates that a state should include rules from another state.
    """
    pass


class _inherit:
    """
    Indicates the a state should inherit from its superclass.
    """
    def __repr__(self):
        return 'inherit'

inherit = _inherit()  # pylint: disable=invalid-name


class combined(tuple):  # pylint: disable=invalid-name
    """
    Indicates a state combined from multiple states.
    """

    def __new__(cls, *args):
        return tuple.__new__(cls, args)

    def __init__(self, *args):
        # tuple.__init__ doesn't do anything
        pass


class _PseudoMatch:
    """
    A pseudo match object constructed from a string.
    """

    def __init__(self, start, text):
        self._text = text
        self._start = start

    def start(self, arg=None):
        return self._start

    def end(self, arg=None):
        return self._start + len(self._text)

    def group(self, arg=None):
        if arg:
            raise IndexError('No such group')
        return self._text

    def groups(self):
        return (self._text,)

    def groupdict(self):
        return {}


def bygroups(*args):
    """
    Callback that yields multiple actions for each group in the match.
    """
    def callback(lexer, match, ctx=None):
        for i, action in enumerate(args):
            if action is None:
                continue
            elif type(action) is _TokenType:
                data = match.group(i + 1)
                if data:
                    yield match.start(i + 1), action, data
            else:
                data = match.group(i + 1)
                if data is not None:
                    if ctx:
                        ctx.pos = match.start(i + 1)
                    for item in action(lexer,
                                       _PseudoMatch(match.start(i + 1), data), ctx):
                        if item:
                            yield item
        if ctx:
            ctx.pos = match.end()
    return callback


class _This:
    """
    Special singleton used for indicating the caller class.
    Used by ``using``.
    """

this = _This()


def using(_other, **kwargs):
    """
    Callback that processes the match with a different lexer.

    The keyword arguments are forwarded to the lexer, except `state` which
    is handled separately.

    `state` specifies the state that the new lexer will start in, and can
    be an enumerable such as ('root', 'inline', 'string') or a simple
    string which is assumed to be on top of the root state.

    Note: For that to work, `_other` must not be an `ExtendedRegexLexer`.
    """
    gt_kwargs = {}
    if 'state' in kwargs:
        s = kwargs.pop('state')
        if isinstance(s, (list, tuple)):
            gt_kwargs['stack'] = s
        else:
            gt_kwargs['stack'] = ('root', s)

    if _other is this:
        def callback(lexer, match, ctx=None):
            # if keyword arguments are given the callback
            # function has to create a new lexer instance
            if kwargs:
                # XXX: cache that somehow
                kwargs.update(lexer.options)
                lx = lexer.__class__(**kwargs)
            else:
                lx = lexer
            s = match.start()
            for i, t, v in lx.get_tokens_unprocessed(match.group(), **gt_kwargs):
                yield i + s, t, v
            if ctx:
                ctx.pos = match.end()
    else:
        def callback(lexer, match, ctx=None):
            # XXX: cache that somehow
            kwargs.update(lexer.options)
            lx = _other(**kwargs)

            s = match.start()
            for i, t, v in lx.get_tokens_unprocessed(match.group(), **gt_kwargs):
                yield i + s, t, v
            if ctx:
                ctx.pos = match.end()
    return callback


class default:
    """
    Indicates a state or state action (e.g. #pop) to apply.
    For example default('#pop') is equivalent to ('', Token, '#pop')
    Note that state tuples may be used as well.

    .. versionadded:: 2.0
    """
    def __init__(self, state):
        self.state = state


class words(Future):
    """
    Indicates a list of literal words that is transformed into an optimized
    regex that matches any of the words.

    .. versionadded:: 2.0
    """
    def __init__(self, words, prefix='', suffix=''):
        self.words = words
        self.prefix = prefix
        self.suffix = suffix

    def get(self):
        return regex_opt(self.words, prefix=self.prefix, suffix=self.suffix)


class RegexLexerMeta(LexerMeta):
    """
    Metaclass for RegexLexer, creates the self._tokens attribute from
    self.tokens on the first instantiation.
    """

    def _process_regex(cls, regex, rflags, state):
        """Preprocess the regular expression component of a token definition."""
        if isinstance(regex, Future):
            regex = regex.get()
        return re.compile(regex, rflags).match

    def _process_token(cls, token):
        """Preprocess the token component of a token definition."""
        assert type(token) is _TokenType or callable(token), \
            f'token type must be simple type or callable, not {token!r}'
        return token

    def _process_new_state(cls, new_state, unprocessed, processed):
        """Preprocess the state transition action of a token definition."""
        if isinstance(new_state, str):
            # an existing state
            if new_state == '#pop':
                return -1
            elif new_state in unprocessed:
                return (new_state,)
            elif new_state == '#push':
                return new_state
            elif new_state[:5] == '#pop:':
                return -int(new_state[5:])
            else:
                assert False, f'unknown new state {new_state!r}'
        elif isinstance(new_state, combined):
            # combine a new state from existing ones
            tmp_state = '_tmp_%d' % cls._tmpname
            cls._tmpname += 1
            itokens = []
            for istate in new_state:
                assert istate != new_state, f'circular state ref {istate!r}'
                itokens.extend(cls._process_state(unprocessed,
                                                  processed, istate))
            processed[tmp_state] = itokens
            return (tmp_state,)
        elif isinstance(new_state, tuple):
            # push more than one state
            for istate in new_state:
                assert (istate in unprocessed or
                        istate in ('#pop', '#push')), \
                    'unknown new state ' + istate
            return new_state
        else:
            assert False, f'unknown new state def {new_state!r}'

    def _process_state(cls, unprocessed, processed, state):
        """Preprocess a single state definition."""
        assert isinstance(state, str), f"wrong state name {state!r}"
        assert state[0] != '#', f"invalid state name {state!r}"
        if state in processed:
            return processed[state]
        tokens = processed[state] = []
        rflags = cls.flags
        for tdef in unprocessed[state]:
            if isinstance(tdef, include):
                # it's a state reference
                assert tdef != state, f"circular state reference {state!r}"
                tokens.extend(cls._process_state(unprocessed, processed,
                                                 str(tdef)))
                continue
            if isinstance(tdef, _inherit):
                # should be processed already, but may not in the case of:
                # 1. the state has no counterpart in any parent
                # 2. the state includes more than one 'inherit'
                continue
            if isinstance(tdef, default):
                new_state = cls._process_new_state(tdef.state, unprocessed, processed)
                tokens.append((re.compile('').match, None, new_state))
                continue

            assert type(tdef) is tuple, f"wrong rule def {tdef!r}"

            try:
                rex = cls._process_regex(tdef[0], rflags, state)
            except Exception as err:
                raise ValueError(f"uncompilable regex {tdef[0]!r} in state {state!r} of {cls!r}: {err}") from err

            token = cls._process_token(tdef[1])

            if len(tdef) == 2:
                new_state = None
            else:
                new_state = cls._process_new_state(tdef[2],
                                                   unprocessed, processed)

            tokens.append((rex, token, new_state))
        return tokens

    def process_tokendef(cls, name, tokendefs=None):
        """Preprocess a dictionary of token definitions."""
        processed = cls._all_tokens[name] = {}
        tokendefs = tokendefs or cls.tokens[name]
        for state in list(tokendefs):
            cls._process_state(tokendefs, processed, state)
        return processed

    def get_tokendefs(cls):
        """
        Merge tokens from superclasses in MRO order, returning a single tokendef
        dictionary.

        Any state that is not defined by a subclass will be inherited
        automatically.  States that *are* defined by subclasses will, by
        default, override that state in the superclass.  If a subclass wishes to
        inherit definitions from a superclass, it can use the special value
        "inherit", which will cause the superclass' state definition to be
        included at that point in the state.
        """
        tokens = {}
        inheritable = {}
        for c in cls.__mro__:
            toks = c.__dict__.get('tokens', {})

            for state, items in toks.items():
                curitems = tokens.get(state)
                if curitems is None:
                    # N.b. because this is assigned by reference, sufficiently
                    # deep hierarchies are processed incrementally (e.g. for
                    # A(B), B(C), C(RegexLexer), B will be premodified so X(B)
                    # will not see any inherits in B).
                    tokens[state] = items
                    try:
                        inherit_ndx = items.index(inherit)
                    except ValueError:
                        continue
                    inheritable[state] = inherit_ndx
                    continue

                inherit_ndx = inheritable.pop(state, None)
                if inherit_ndx is None:
                    continue

                # Replace the "inherit" value with the items
                curitems[inherit_ndx:inherit_ndx+1] = items
                try:
                    # N.b. this is the index in items (that is, the superclass
                    # copy), so offset required when storing below.
                    new_inh_ndx = items.index(inherit)
                except ValueError:
                    pass
                else:
                    inheritable[state] = inherit_ndx + new_inh_ndx

        return tokens

    def __call__(cls, *args, **kwds):
        """Instantiate cls after preprocessing its token definitions."""
        if '_tokens' not in cls.__dict__:
            cls._all_tokens = {}
            cls._tmpname = 0
            if hasattr(cls, 'token_variants') and cls.token_variants:
                # don't process yet
                pass
            else:
                cls._tokens = cls.process_tokendef('', cls.get_tokendefs())

        return type.__call__(cls, *args, **kwds)


class RegexLexer(Lexer, metaclass=RegexLexerMeta):
    """
    Base for simple stateful regular expression-based lexers.
    Simplifies the lexing process so that you need only
    provide a list of states and regular expressions.
    """

    #: Flags for compiling the regular expressions.
    #: Defaults to MULTILINE.
    flags = re.MULTILINE

    #: At all time there is a stack of states. Initially, the stack contains
    #: a single state 'root'. The top of the stack is called "the current state".
    #:
    #: Dict of ``{'state': [(regex, tokentype, new_state), ...], ...}``
    #:
    #: ``new_state`` can be omitted to signify no state transition.
    #: If ``new_state`` is a string, it is pushed on the stack. This ensure
    #: the new current state is ``new_state``.
    #: If ``new_state`` is a tuple of strings, all of those strings are pushed
    #: on the stack and the current state will be the last element of the list.
    #: ``new_state`` can also be ``combined('state1', 'state2', ...)``
    #: to signify a new, anonymous state combined from the rules of two
    #: or more existing ones.
    #: Furthermore, it can be '#pop' to signify going back one step in
    #: the state stack, or '#push' to push the current state on the stack
    #: again. Note that if you push while in a combined state, the combined
    #: state itself is pushed, and not only the state in which the rule is
    #: defined.
    #:
    #: The tuple can also be replaced with ``include('state')``, in which
    #: case the rules from the state named by the string are included in the
    #: current one.
    tokens = {}

    def get_tokens_unprocessed(self, text, stack=('root',)):
        """
        Split ``text`` into (tokentype, text) pairs.

        ``stack`` is the initial stack (default: ``['root']``)
        """
        pos = 0
        tokendefs = self._tokens
        statestack = list(stack)
        statetokens = tokendefs[statestack[-1]]
        while 1:
            for rexmatch, action, new_state in statetokens:
                m = rexmatch(text, pos)
                if m:
                    if action is not None:
                        if type(action) is _TokenType:
                            yield pos, action, m.group()
                        else:
                            yield from action(self, m)
                    pos = m.end()
                    if new_state is not None:
                        # state transition
                        if isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    if len(statestack) > 1:
                                        statestack.pop()
                                elif state == '#push':
                                    statestack.append(statestack[-1])
                                else:
                                    statestack.append(state)
                        elif isinstance(new_state, int):
                            # pop, but keep at least one state on the stack
                            # (random code leading to unexpected pops should
                            # not allow exceptions)
                            if abs(new_state) >= len(statestack):
                                del statestack[1:]
                            else:
                                del statestack[new_state:]
                        elif new_state == '#push':
                            statestack.append(statestack[-1])
                        else:
                            assert False, f"wrong state def: {new_state!r}"
                        statetokens = tokendefs[statestack[-1]]
                    break
            else:
                # We are here only if all state tokens have been considered
                # and there was not a match on any of them.
                try:
                    if text[pos] == '\n':
                        # at EOL, reset state to "root"
                        statestack = ['root']
                        statetokens = tokendefs['root']
                        yield pos, Whitespace, '\n'
                        pos += 1
                        continue
                    yield pos, Error, text[pos]
                    pos += 1
                except IndexError:
                    break


class LexerContext:
    """
    A helper object that holds lexer position data.
    """

    def __init__(self, text, pos, stack=None, end=None):
        self.text = text
        self.pos = pos
        self.end = end or len(text)  # end=0 not supported ;-)
        self.stack = stack or ['root']

    def __repr__(self):
        return f'LexerContext({self.text!r}, {self.pos!r}, {self.stack!r})'


class ExtendedRegexLexer(RegexLexer):
    """
    A RegexLexer that uses a context object to store its state.
    """

    def get_tokens_unprocessed(self, text=None, context=None):
        """
        Split ``text`` into (tokentype, text) pairs.
        If ``context`` is given, use this lexer context instead.
        """
        tokendefs = self._tokens
        if not context:
            ctx = LexerContext(text, 0)
            statetokens = tokendefs['root']
        else:
            ctx = context
            statetokens = tokendefs[ctx.stack[-1]]
            text = ctx.text
        while 1:
            for rexmatch, action, new_state in statetokens:
                m = rexmatch(text, ctx.pos, ctx.end)
                if m:
                    if action is not None:
                        if type(action) is _TokenType:
                            yield ctx.pos, action, m.group()
                            ctx.pos = m.end()
                        else:
                            yield from action(self, m, ctx)
                            if not new_state:
                                # altered the state stack?
                                statetokens = tokendefs[ctx.stack[-1]]
                    # CAUTION: callback must set ctx.pos!
                    if new_state is not None:
                        # state transition
                        if isinstance(new_state, tuple):
                            for state in new_state:
                                if state == '#pop':
                                    if len(ctx.stack) > 1:
                                        ctx.stack.pop()
                                elif state == '#push':
                                    ctx.stack.append(ctx.stack[-1])
                                else:
                                    ctx.stack.append(state)
                        elif isinstance(new_state, int):
                            # see RegexLexer for why this check is made
                            if abs(new_state) >= len(ctx.stack):
                                del ctx.stack[1:]
                            else:
                                del ctx.stack[new_state:]
                        elif new_state == '#push':
                            ctx.stack.append(ctx.stack[-1])
                        else:
                            assert False, f"wrong state def: {new_state!r}"
                        statetokens = tokendefs[ctx.stack[-1]]
                    break
            else:
                try:
                    if ctx.pos >= ctx.end:
                        break
                    if text[ctx.pos] == '\n':
                        # at EOL, reset state to "root"
                        ctx.stack = ['root']
                        statetokens = tokendefs['root']
                        yield ctx.pos, Text, '\n'
                        ctx.pos += 1
                        continue
                    yield ctx.pos, Error, text[ctx.pos]
                    ctx.pos += 1
                except IndexError:
                    break


def do_insertions(insertions, tokens):
    """
    Helper for lexers which must combine the results of several
    sublexers.

    ``insertions`` is a list of ``(index, itokens)`` pairs.
    Each ``itokens`` iterable should be inserted at position
    ``index`` into the token stream given by the ``tokens``
    argument.

    The result is a combined token stream.

    TODO: clean up the code here.
    """
    insertions = iter(insertions)
    try:
        index, itokens = next(insertions)
    except StopIteration:
        # no insertions
        yield from tokens
        return

    realpos = None
    insleft = True

    # iterate over the token stream where we want to insert
    # the tokens from the insertion list.
    for i, t, v in tokens:
        # first iteration. store the position of first item
        if realpos is None:
            realpos = i
        oldi = 0
        while insleft and i + len(v) >= index:
            tmpval = v[oldi:index - i]
            if tmpval:
                yield realpos, t, tmpval
                realpos += len(tmpval)
            for it_index, it_token, it_value in itokens:
                yield realpos, it_token, it_value
                realpos += len(it_value)
            oldi = index - i
            try:
                index, itokens = next(insertions)
            except StopIteration:
                insleft = False
                break  # not strictly necessary
        if oldi < len(v):
            yield realpos, t, v[oldi:]
            realpos += len(v) - oldi

    # leftover tokens
    while insleft:
        # no normal tokens, set realpos to zero
        realpos = realpos or 0
        for p, t, v in itokens:
            yield realpos, t, v
            realpos += len(v)
        try:
            index, itokens = next(insertions)
        except StopIteration:
            insleft = False
            break  # not strictly necessary


class ProfilingRegexLexerMeta(RegexLexerMeta):
    """Metaclass for ProfilingRegexLexer, collects regex timing info."""

    def _process_regex(cls, regex, rflags, state):
        if isinstance(regex, words):
            rex = regex_opt(regex.words, prefix=regex.prefix,
                            suffix=regex.suffix)
        else:
            rex = regex
        compiled = re.compile(rex, rflags)

        def match_func(text, pos, endpos=sys.maxsize):
            info = cls._prof_data[-1].setdefault((state, rex), [0, 0.0])
            t0 = time.time()
            res = compiled.match(text, pos, endpos)
            t1 = time.time()
            info[0] += 1
            info[1] += t1 - t0
            return res
        return match_func


class ProfilingRegexLexer(RegexLexer, metaclass=ProfilingRegexLexerMeta):
    """Drop-in replacement for RegexLexer that does profiling of its regexes."""

    _prof_data = []
    _prof_sort_index = 4  # defaults to time per call

    def get_tokens_unprocessed(self, text, stack=('root',)):
        # this needs to be a stack, since using(this) will produce nested calls
        self.__class__._prof_data.append({})
        yield from RegexLexer.get_tokens_unprocessed(self, text, stack)
        rawdata = self.__class__._prof_data.pop()
        data = sorted(((s, repr(r).strip('u\'').replace('\\\\', '\\')[:65],
                        n, 1000 * t, 1000 * t / n)
                       for ((s, r), (n, t)) in rawdata.items()),
                      key=lambda x: x[self._prof_sort_index],
                      reverse=True)
        sum_total = sum(x[3] for x in data)

        print()
        print('Profiling result for %s lexing %d chars in %.3f ms' %
              (self.__class__.__name__, len(text), sum_total))
        print('=' * 110)
        print('%-20s %-64s ncalls  tottime  percall' % ('state', 'regex'))
        print('-' * 110)
        for d in data:
            print('%-20s %-65s %5d %8.4f %8.4f' % d)
        print('=' * 110)
