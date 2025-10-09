"""Process links like https://example.org/"""
import re

from .state_inline import StateInline

# RFC3986: scheme = ALPHA *( ALPHA / DIGIT / "+" / "-" / "." )
SCHEME_RE = re.compile(r"(?:^|[^a-z0-9.+-])([a-z][a-z0-9.+-]*)$", re.IGNORECASE)


def linkify(state: StateInline, silent: bool) -> bool:
    """Rule for identifying plain-text links."""
    if not state.md.options.linkify:
        return False
    if state.linkLevel > 0:
        return False
    if not state.md.linkify:
        raise ModuleNotFoundError("Linkify enabled but not installed.")

    pos = state.pos
    maximum = state.posMax

    if (
        (pos + 3) > maximum
        or state.src[pos] != ":"
        or state.src[pos + 1] != "/"
        or state.src[pos + 2] != "/"
    ):
        return False

    if not (match := SCHEME_RE.match(state.pending)):
        return False

    proto = match.group(1)
    if not (link := state.md.linkify.match_at_start(state.src[pos - len(proto) :])):
        return False
    url: str = link.url

    # disallow '*' at the end of the link (conflicts with emphasis)
    url = url.rstrip("*")

    full_url = state.md.normalizeLink(url)
    if not state.md.validateLink(full_url):
        return False

    if not silent:
        state.pending = state.pending[: -len(proto)]

        token = state.push("link_open", "a", 1)
        token.attrs = {"href": full_url}
        token.markup = "linkify"
        token.info = "auto"

        token = state.push("text", "", 0)
        token.content = state.md.normalizeLinkText(url)

        token = state.push("link_close", "a", -1)
        token.markup = "linkify"
        token.info = "auto"

    state.pos += len(url) - len(proto)
    return True
