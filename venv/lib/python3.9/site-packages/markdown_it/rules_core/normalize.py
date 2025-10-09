"""Normalize input string."""
import re

from .state_core import StateCore

# https://spec.commonmark.org/0.29/#line-ending
NEWLINES_RE = re.compile(r"\r\n?|\n")
NULL_RE = re.compile(r"\0")


def normalize(state: StateCore) -> None:
    # Normalize newlines
    string = NEWLINES_RE.sub("\n", state.src)

    # Replace NULL characters
    string = NULL_RE.sub("\uFFFD", string)

    state.src = string
