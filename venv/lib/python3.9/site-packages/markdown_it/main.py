from __future__ import annotations

from collections.abc import Callable, Generator, Iterable, Mapping, MutableMapping
from contextlib import contextmanager
from typing import Any, Literal, overload

from . import helpers, presets
from .common import normalize_url, utils
from .parser_block import ParserBlock
from .parser_core import ParserCore
from .parser_inline import ParserInline
from .renderer import RendererHTML, RendererProtocol
from .rules_core.state_core import StateCore
from .token import Token
from .utils import EnvType, OptionsDict, OptionsType, PresetType

try:
    import linkify_it
except ModuleNotFoundError:
    linkify_it = None


_PRESETS: dict[str, PresetType] = {
    "default": presets.default.make(),
    "js-default": presets.js_default.make(),
    "zero": presets.zero.make(),
    "commonmark": presets.commonmark.make(),
    "gfm-like": presets.gfm_like.make(),
}


class MarkdownIt:
    def __init__(
        self,
        config: str | PresetType = "commonmark",
        options_update: Mapping[str, Any] | None = None,
        *,
        renderer_cls: Callable[[MarkdownIt], RendererProtocol] = RendererHTML,
    ):
        """Main parser class

        :param config: name of configuration to load or a pre-defined dictionary
        :param options_update: dictionary that will be merged into ``config["options"]``
        :param renderer_cls: the class to load as the renderer:
            ``self.renderer = renderer_cls(self)
        """
        # add modules
        self.utils = utils
        self.helpers = helpers

        # initialise classes
        self.inline = ParserInline()
        self.block = ParserBlock()
        self.core = ParserCore()
        self.renderer = renderer_cls(self)
        self.linkify = linkify_it.LinkifyIt() if linkify_it else None

        # set the configuration
        if options_update and not isinstance(options_update, Mapping):
            # catch signature change where renderer_cls was not used as a key-word
            raise TypeError(
                f"options_update should be a mapping: {options_update}"
                "\n(Perhaps you intended this to be the renderer_cls?)"
            )
        self.configure(config, options_update=options_update)

    def __repr__(self) -> str:
        return f"{self.__class__.__module__}.{self.__class__.__name__}()"

    @overload
    def __getitem__(self, name: Literal["inline"]) -> ParserInline:
        ...

    @overload
    def __getitem__(self, name: Literal["block"]) -> ParserBlock:
        ...

    @overload
    def __getitem__(self, name: Literal["core"]) -> ParserCore:
        ...

    @overload
    def __getitem__(self, name: Literal["renderer"]) -> RendererProtocol:
        ...

    @overload
    def __getitem__(self, name: str) -> Any:
        ...

    def __getitem__(self, name: str) -> Any:
        return {
            "inline": self.inline,
            "block": self.block,
            "core": self.core,
            "renderer": self.renderer,
        }[name]

    def set(self, options: OptionsType) -> None:
        """Set parser options (in the same format as in constructor).
        Probably, you will never need it, but you can change options after constructor call.

        __Note:__ To achieve the best possible performance, don't modify a
        `markdown-it` instance options on the fly. If you need multiple configurations
        it's best to create multiple instances and initialize each with separate config.
        """
        self.options = OptionsDict(options)

    def configure(
        self, presets: str | PresetType, options_update: Mapping[str, Any] | None = None
    ) -> MarkdownIt:
        """Batch load of all options and component settings.
        This is an internal method, and you probably will not need it.
        But if you will - see available presets and data structure
        [here](https://github.com/markdown-it/markdown-it/tree/master/lib/presets)

        We strongly recommend to use presets instead of direct config loads.
        That will give better compatibility with next versions.
        """
        if isinstance(presets, str):
            if presets not in _PRESETS:
                raise KeyError(f"Wrong `markdown-it` preset '{presets}', check name")
            config = _PRESETS[presets]
        else:
            config = presets

        if not config:
            raise ValueError("Wrong `markdown-it` config, can't be empty")

        options = config.get("options", {}) or {}
        if options_update:
            options = {**options, **options_update}  # type: ignore

        self.set(options)  # type: ignore

        if "components" in config:
            for name, component in config["components"].items():
                rules = component.get("rules", None)
                if rules:
                    self[name].ruler.enableOnly(rules)
                rules2 = component.get("rules2", None)
                if rules2:
                    self[name].ruler2.enableOnly(rules2)

        return self

    def get_all_rules(self) -> dict[str, list[str]]:
        """Return the names of all active rules."""
        rules = {
            chain: self[chain].ruler.get_all_rules()
            for chain in ["core", "block", "inline"]
        }
        rules["inline2"] = self.inline.ruler2.get_all_rules()
        return rules

    def get_active_rules(self) -> dict[str, list[str]]:
        """Return the names of all active rules."""
        rules = {
            chain: self[chain].ruler.get_active_rules()
            for chain in ["core", "block", "inline"]
        }
        rules["inline2"] = self.inline.ruler2.get_active_rules()
        return rules

    def enable(
        self, names: str | Iterable[str], ignoreInvalid: bool = False
    ) -> MarkdownIt:
        """Enable list or rules. (chainable)

        :param names: rule name or list of rule names to enable.
        :param ignoreInvalid: set `true` to ignore errors when rule not found.

        It will automatically find appropriate components,
        containing rules with given names. If rule not found, and `ignoreInvalid`
        not set - throws exception.

        Example::

            md = MarkdownIt().enable(['sub', 'sup']).disable('smartquotes')

        """
        result = []

        if isinstance(names, str):
            names = [names]

        for chain in ["core", "block", "inline"]:
            result.extend(self[chain].ruler.enable(names, True))
        result.extend(self.inline.ruler2.enable(names, True))

        missed = [name for name in names if name not in result]
        if missed and not ignoreInvalid:
            raise ValueError(f"MarkdownIt. Failed to enable unknown rule(s): {missed}")

        return self

    def disable(
        self, names: str | Iterable[str], ignoreInvalid: bool = False
    ) -> MarkdownIt:
        """The same as [[MarkdownIt.enable]], but turn specified rules off. (chainable)

        :param names: rule name or list of rule names to disable.
        :param ignoreInvalid: set `true` to ignore errors when rule not found.

        """
        result = []

        if isinstance(names, str):
            names = [names]

        for chain in ["core", "block", "inline"]:
            result.extend(self[chain].ruler.disable(names, True))
        result.extend(self.inline.ruler2.disable(names, True))

        missed = [name for name in names if name not in result]
        if missed and not ignoreInvalid:
            raise ValueError(f"MarkdownIt. Failed to disable unknown rule(s): {missed}")
        return self

    @contextmanager
    def reset_rules(self) -> Generator[None, None, None]:
        """A context manager, that will reset the current enabled rules on exit."""
        chain_rules = self.get_active_rules()
        yield
        for chain, rules in chain_rules.items():
            if chain != "inline2":
                self[chain].ruler.enableOnly(rules)
        self.inline.ruler2.enableOnly(chain_rules["inline2"])

    def add_render_rule(
        self, name: str, function: Callable[..., Any], fmt: str = "html"
    ) -> None:
        """Add a rule for rendering a particular Token type.

        Only applied when ``renderer.__output__ == fmt``
        """
        if self.renderer.__output__ == fmt:
            self.renderer.rules[name] = function.__get__(self.renderer)  # type: ignore

    def use(
        self, plugin: Callable[..., None], *params: Any, **options: Any
    ) -> MarkdownIt:
        """Load specified plugin with given params into current parser instance. (chainable)

        It's just a sugar to call `plugin(md, params)` with curring.

        Example::

            def func(tokens, idx):
                tokens[idx].content = tokens[idx].content.replace('foo', 'bar')
            md = MarkdownIt().use(plugin, 'foo_replace', 'text', func)

        """
        plugin(self, *params, **options)
        return self

    def parse(self, src: str, env: EnvType | None = None) -> list[Token]:
        """Parse the source string to a token stream

        :param src: source string
        :param env: environment sandbox

        Parse input string and return list of block tokens (special token type
        "inline" will contain list of inline tokens).

        `env` is used to pass data between "distributed" rules and return additional
        metadata like reference info, needed for the renderer. It also can be used to
        inject data in specific cases. Usually, you will be ok to pass `{}`,
        and then pass updated object to renderer.
        """
        env = {} if env is None else env
        if not isinstance(env, MutableMapping):
            raise TypeError(f"Input data should be a MutableMapping, not {type(env)}")
        if not isinstance(src, str):
            raise TypeError(f"Input data should be a string, not {type(src)}")
        state = StateCore(src, self, env)
        self.core.process(state)
        return state.tokens

    def render(self, src: str, env: EnvType | None = None) -> Any:
        """Render markdown string into html. It does all magic for you :).

        :param src: source string
        :param env: environment sandbox
        :returns: The output of the loaded renderer

        `env` can be used to inject additional metadata (`{}` by default).
        But you will not need it with high probability. See also comment
        in [[MarkdownIt.parse]].
        """
        env = {} if env is None else env
        return self.renderer.render(self.parse(src, env), self.options, env)

    def parseInline(self, src: str, env: EnvType | None = None) -> list[Token]:
        """The same as [[MarkdownIt.parse]] but skip all block rules.

        :param src: source string
        :param env: environment sandbox

        It returns the
        block tokens list with the single `inline` element, containing parsed inline
        tokens in `children` property. Also updates `env` object.
        """
        env = {} if env is None else env
        if not isinstance(env, MutableMapping):
            raise TypeError(f"Input data should be an MutableMapping, not {type(env)}")
        if not isinstance(src, str):
            raise TypeError(f"Input data should be a string, not {type(src)}")
        state = StateCore(src, self, env)
        state.inlineMode = True
        self.core.process(state)
        return state.tokens

    def renderInline(self, src: str, env: EnvType | None = None) -> Any:
        """Similar to [[MarkdownIt.render]] but for single paragraph content.

        :param src: source string
        :param env: environment sandbox

        Similar to [[MarkdownIt.render]] but for single paragraph content. Result
        will NOT be wrapped into `<p>` tags.
        """
        env = {} if env is None else env
        return self.renderer.render(self.parseInline(src, env), self.options, env)

    # link methods

    def validateLink(self, url: str) -> bool:
        """Validate if the URL link is allowed in output.

        This validator can prohibit more than really needed to prevent XSS.
        It's a tradeoff to keep code simple and to be secure by default.

        Note: the url should be normalized at this point, and existing entities decoded.
        """
        return normalize_url.validateLink(url)

    def normalizeLink(self, url: str) -> str:
        """Normalize destination URLs in links

        ::

            [label]:   destination   'title'
                    ^^^^^^^^^^^
        """
        return normalize_url.normalizeLink(url)

    def normalizeLinkText(self, link: str) -> str:
        """Normalize autolink content

        ::

            <destination>
            ~~~~~~~~~~~
        """
        return normalize_url.normalizeLinkText(link)
