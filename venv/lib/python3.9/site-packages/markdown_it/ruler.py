"""
class Ruler

Helper class, used by [[MarkdownIt#core]], [[MarkdownIt#block]] and
[[MarkdownIt#inline]] to manage sequences of functions (rules):

- keep rules in defined order
- assign the name to each rule
- enable/disable rules
- add/replace rules
- allow assign rules to additional named chains (in the same)
- caching lists of active rules

You will not need use this class directly until write plugins. For simple
rules control use [[MarkdownIt.disable]], [[MarkdownIt.enable]] and
[[MarkdownIt.use]].
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypedDict, TypeVar
import warnings

from markdown_it._compat import DATACLASS_KWARGS

from .utils import EnvType

if TYPE_CHECKING:
    from markdown_it import MarkdownIt


class StateBase:
    def __init__(self, src: str, md: MarkdownIt, env: EnvType):
        self.src = src
        self.env = env
        self.md = md

    @property
    def src(self) -> str:
        return self._src

    @src.setter
    def src(self, value: str) -> None:
        self._src = value
        self._srcCharCode: tuple[int, ...] | None = None

    @property
    def srcCharCode(self) -> tuple[int, ...]:
        warnings.warn(
            "StateBase.srcCharCode is deprecated. Use StateBase.src instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if self._srcCharCode is None:
            self._srcCharCode = tuple(ord(c) for c in self._src)
        return self._srcCharCode


class RuleOptionsType(TypedDict, total=False):
    alt: list[str]


RuleFuncTv = TypeVar("RuleFuncTv")
"""A rule function, whose signature is dependent on the state type."""


@dataclass(**DATACLASS_KWARGS)
class Rule(Generic[RuleFuncTv]):
    name: str
    enabled: bool
    fn: RuleFuncTv = field(repr=False)
    alt: list[str]


class Ruler(Generic[RuleFuncTv]):
    def __init__(self) -> None:
        # List of added rules.
        self.__rules__: list[Rule[RuleFuncTv]] = []
        # Cached rule chains.
        # First level - chain name, '' for default.
        # Second level - diginal anchor for fast filtering by charcodes.
        self.__cache__: dict[str, list[RuleFuncTv]] | None = None

    def __find__(self, name: str) -> int:
        """Find rule index by name"""
        for i, rule in enumerate(self.__rules__):
            if rule.name == name:
                return i
        return -1

    def __compile__(self) -> None:
        """Build rules lookup cache"""
        chains = {""}
        # collect unique names
        for rule in self.__rules__:
            if not rule.enabled:
                continue
            for name in rule.alt:
                chains.add(name)
        self.__cache__ = {}
        for chain in chains:
            self.__cache__[chain] = []
            for rule in self.__rules__:
                if not rule.enabled:
                    continue
                if chain and (chain not in rule.alt):
                    continue
                self.__cache__[chain].append(rule.fn)

    def at(
        self, ruleName: str, fn: RuleFuncTv, options: RuleOptionsType | None = None
    ) -> None:
        """Replace rule by name with new function & options.

        :param ruleName: rule name to replace.
        :param fn: new rule function.
        :param options: new rule options (not mandatory).
        :raises: KeyError if name not found
        """
        index = self.__find__(ruleName)
        options = options or {}
        if index == -1:
            raise KeyError(f"Parser rule not found: {ruleName}")
        self.__rules__[index].fn = fn
        self.__rules__[index].alt = options.get("alt", [])
        self.__cache__ = None

    def before(
        self,
        beforeName: str,
        ruleName: str,
        fn: RuleFuncTv,
        options: RuleOptionsType | None = None,
    ) -> None:
        """Add new rule to chain before one with given name.

        :param beforeName: new rule will be added before this one.
        :param ruleName: new rule will be added before this one.
        :param fn: new rule function.
        :param options: new rule options (not mandatory).
        :raises: KeyError if name not found
        """
        index = self.__find__(beforeName)
        options = options or {}
        if index == -1:
            raise KeyError(f"Parser rule not found: {beforeName}")
        self.__rules__.insert(
            index, Rule[RuleFuncTv](ruleName, True, fn, options.get("alt", []))
        )
        self.__cache__ = None

    def after(
        self,
        afterName: str,
        ruleName: str,
        fn: RuleFuncTv,
        options: RuleOptionsType | None = None,
    ) -> None:
        """Add new rule to chain after one with given name.

        :param afterName: new rule will be added after this one.
        :param ruleName: new rule will be added after this one.
        :param fn: new rule function.
        :param options: new rule options (not mandatory).
        :raises: KeyError if name not found
        """
        index = self.__find__(afterName)
        options = options or {}
        if index == -1:
            raise KeyError(f"Parser rule not found: {afterName}")
        self.__rules__.insert(
            index + 1, Rule[RuleFuncTv](ruleName, True, fn, options.get("alt", []))
        )
        self.__cache__ = None

    def push(
        self, ruleName: str, fn: RuleFuncTv, options: RuleOptionsType | None = None
    ) -> None:
        """Push new rule to the end of chain.

        :param ruleName: new rule will be added to the end of chain.
        :param fn: new rule function.
        :param options: new rule options (not mandatory).

        """
        self.__rules__.append(
            Rule[RuleFuncTv](ruleName, True, fn, (options or {}).get("alt", []))
        )
        self.__cache__ = None

    def enable(
        self, names: str | Iterable[str], ignoreInvalid: bool = False
    ) -> list[str]:
        """Enable rules with given names.

        :param names: name or list of rule names to enable.
        :param ignoreInvalid: ignore errors when rule not found
        :raises: KeyError if name not found and not ignoreInvalid
        :return: list of found rule names
        """
        if isinstance(names, str):
            names = [names]
        result: list[str] = []
        for name in names:
            idx = self.__find__(name)
            if (idx < 0) and ignoreInvalid:
                continue
            if (idx < 0) and not ignoreInvalid:
                raise KeyError(f"Rules manager: invalid rule name {name}")
            self.__rules__[idx].enabled = True
            result.append(name)
        self.__cache__ = None
        return result

    def enableOnly(
        self, names: str | Iterable[str], ignoreInvalid: bool = False
    ) -> list[str]:
        """Enable rules with given names, and disable everything else.

        :param names: name or list of rule names to enable.
        :param ignoreInvalid: ignore errors when rule not found
        :raises: KeyError if name not found and not ignoreInvalid
        :return: list of found rule names
        """
        if isinstance(names, str):
            names = [names]
        for rule in self.__rules__:
            rule.enabled = False
        return self.enable(names, ignoreInvalid)

    def disable(
        self, names: str | Iterable[str], ignoreInvalid: bool = False
    ) -> list[str]:
        """Disable rules with given names.

        :param names: name or list of rule names to enable.
        :param ignoreInvalid: ignore errors when rule not found
        :raises: KeyError if name not found and not ignoreInvalid
        :return: list of found rule names
        """
        if isinstance(names, str):
            names = [names]
        result = []
        for name in names:
            idx = self.__find__(name)
            if (idx < 0) and ignoreInvalid:
                continue
            if (idx < 0) and not ignoreInvalid:
                raise KeyError(f"Rules manager: invalid rule name {name}")
            self.__rules__[idx].enabled = False
            result.append(name)
        self.__cache__ = None
        return result

    def getRules(self, chainName: str = "") -> list[RuleFuncTv]:
        """Return array of active functions (rules) for given chain name.
        It analyzes rules configuration, compiles caches if not exists and returns result.

        Default chain name is `''` (empty string). It can't be skipped.
        That's done intentionally, to keep signature monomorphic for high speed.

        """
        if self.__cache__ is None:
            self.__compile__()
            assert self.__cache__ is not None
        # Chain can be empty, if rules disabled. But we still have to return Array.
        return self.__cache__.get(chainName, []) or []

    def get_all_rules(self) -> list[str]:
        """Return all available rule names."""
        return [r.name for r in self.__rules__]

    def get_active_rules(self) -> list[str]:
        """Return the active rule names."""
        return [r.name for r in self.__rules__ if r.enabled]
