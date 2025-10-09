# Copyright Joyent, Inc. and other Node contributors.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the
# following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN
# NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
# USE OR OTHER DEALINGS IN THE SOFTWARE.


# Changes from joyent/node:
#
# 1. No leading slash in paths,
#    e.g. in `url.parse('http://foo?bar')` pathname is ``, not `/`
#
# 2. Backslashes are not replaced with slashes,
#    so `http:\\example.org\` is treated like a relative path
#
# 3. Trailing colon is treated like a part of the path,
#    i.e. in `http://example.org:foo` pathname is `:foo`
#
# 4. Nothing is URL-encoded in the resulting object,
#    (in joyent/node some chars in auth and paths are encoded)
#
# 5. `url.parse()` does not have `parseQueryString` argument
#
# 6. Removed extraneous result properties: `host`, `path`, `query`, etc.,
#    which can be constructed using other parts of the url.

from __future__ import annotations

from collections import defaultdict
import re

from mdurl._url import URL

# Reference: RFC 3986, RFC 1808, RFC 2396

# define these here so at least they only have to be
# compiled once on the first module load.
PROTOCOL_PATTERN = re.compile(r"^([a-z0-9.+-]+:)", flags=re.IGNORECASE)
PORT_PATTERN = re.compile(r":[0-9]*$")

# Special case for a simple path URL
SIMPLE_PATH_PATTERN = re.compile(r"^(//?(?!/)[^?\s]*)(\?[^\s]*)?$")

# RFC 2396: characters reserved for delimiting URLs.
# We actually just auto-escape these.
DELIMS = ("<", ">", '"', "`", " ", "\r", "\n", "\t")

# RFC 2396: characters not allowed for various reasons.
UNWISE = ("{", "}", "|", "\\", "^", "`") + DELIMS

# Allowed by RFCs, but cause of XSS attacks.  Always escape these.
AUTO_ESCAPE = ("'",) + UNWISE
# Characters that are never ever allowed in a hostname.
# Note that any invalid chars are also handled, but these
# are the ones that are *expected* to be seen, so we fast-path
# them.
NON_HOST_CHARS = ("%", "/", "?", ";", "#") + AUTO_ESCAPE
HOST_ENDING_CHARS = ("/", "?", "#")
HOSTNAME_MAX_LEN = 255
HOSTNAME_PART_PATTERN = re.compile(r"^[+a-z0-9A-Z_-]{0,63}$")
HOSTNAME_PART_START = re.compile(r"^([+a-z0-9A-Z_-]{0,63})(.*)$")
# protocols that can allow "unsafe" and "unwise" chars.

# protocols that never have a hostname.
HOSTLESS_PROTOCOL = defaultdict(
    bool,
    {
        "javascript": True,
        "javascript:": True,
    },
)
# protocols that always contain a // bit.
SLASHED_PROTOCOL = defaultdict(
    bool,
    {
        "http": True,
        "https": True,
        "ftp": True,
        "gopher": True,
        "file": True,
        "http:": True,
        "https:": True,
        "ftp:": True,
        "gopher:": True,
        "file:": True,
    },
)


class MutableURL:
    def __init__(self) -> None:
        self.protocol: str | None = None
        self.slashes: bool = False
        self.auth: str | None = None
        self.port: str | None = None
        self.hostname: str | None = None
        self.hash: str | None = None
        self.search: str | None = None
        self.pathname: str | None = None

    def parse(self, url: str, slashes_denote_host: bool) -> "MutableURL":
        lower_proto = ""
        slashes = False
        rest = url

        # trim before proceeding.
        # This is to support parse stuff like "  http://foo.com  \n"
        rest = rest.strip()

        if not slashes_denote_host and len(url.split("#")) == 1:
            # Try fast path regexp
            simple_path = SIMPLE_PATH_PATTERN.match(rest)
            if simple_path:
                self.pathname = simple_path.group(1)
                if simple_path.group(2):
                    self.search = simple_path.group(2)
                return self

        proto = ""
        proto_match = PROTOCOL_PATTERN.match(rest)
        if proto_match:
            proto = proto_match.group()
            lower_proto = proto.lower()
            self.protocol = proto
            rest = rest[len(proto) :]

        # figure out if it's got a host
        # user@server is *always* interpreted as a hostname, and url
        # resolution will treat //foo/bar as host=foo,path=bar because that's
        # how the browser resolves relative URLs.
        if slashes_denote_host or proto or re.search(r"^//[^@/]+@[^@/]+", rest):
            slashes = rest.startswith("//")
            if slashes and not (proto and HOSTLESS_PROTOCOL[proto]):
                rest = rest[2:]
                self.slashes = True

        if not HOSTLESS_PROTOCOL[proto] and (
            slashes or (proto and not SLASHED_PROTOCOL[proto])
        ):

            # there's a hostname.
            # the first instance of /, ?, ;, or # ends the host.
            #
            # If there is an @ in the hostname, then non-host chars *are* allowed
            # to the left of the last @ sign, unless some host-ending character
            # comes *before* the @-sign.
            # URLs are obnoxious.
            #
            # ex:
            # http://a@b@c/ => user:a@b host:c
            # http://a@b?@c => user:a host:c path:/?@c

            # v0.12 TODO(isaacs): This is not quite how Chrome does things.
            # Review our test case against browsers more comprehensively.

            # find the first instance of any hostEndingChars
            host_end = -1
            for i in range(len(HOST_ENDING_CHARS)):
                hec = rest.find(HOST_ENDING_CHARS[i])
                if hec != -1 and (host_end == -1 or hec < host_end):
                    host_end = hec

            # at this point, either we have an explicit point where the
            # auth portion cannot go past, or the last @ char is the decider.
            if host_end == -1:
                # atSign can be anywhere.
                at_sign = rest.rfind("@")
            else:
                # atSign must be in auth portion.
                # http://a@b/c@d => host:b auth:a path:/c@d
                at_sign = rest.rfind("@", 0, host_end + 1)

            # Now we have a portion which is definitely the auth.
            # Pull that off.
            if at_sign != -1:
                auth = rest[:at_sign]
                rest = rest[at_sign + 1 :]
                self.auth = auth

            # the host is the remaining to the left of the first non-host char
            host_end = -1
            for i in range(len(NON_HOST_CHARS)):
                hec = rest.find(NON_HOST_CHARS[i])
                if hec != -1 and (host_end == -1 or hec < host_end):
                    host_end = hec
            # if we still have not hit it, then the entire thing is a host.
            if host_end == -1:
                host_end = len(rest)

            if host_end > 0 and rest[host_end - 1] == ":":
                host_end -= 1
            host = rest[:host_end]
            rest = rest[host_end:]

            # pull out port.
            self.parse_host(host)

            # we've indicated that there is a hostname,
            # so even if it's empty, it has to be present.
            self.hostname = self.hostname or ""

            # if hostname begins with [ and ends with ]
            # assume that it's an IPv6 address.
            ipv6_hostname = self.hostname.startswith("[") and self.hostname.endswith(
                "]"
            )

            # validate a little.
            if not ipv6_hostname:
                hostparts = self.hostname.split(".")
                l = len(hostparts)  # noqa: E741
                i = 0
                while i < l:
                    part = hostparts[i]
                    if not part:
                        i += 1  # emulate statement3 in JS for loop
                        continue
                    if not HOSTNAME_PART_PATTERN.search(part):
                        newpart = ""
                        k = len(part)
                        j = 0
                        while j < k:
                            if ord(part[j]) > 127:
                                # we replace non-ASCII char with a temporary placeholder
                                # we need this to make sure size of hostname is not
                                # broken by replacing non-ASCII by nothing
                                newpart += "x"
                            else:
                                newpart += part[j]
                            j += 1  # emulate statement3 in JS for loop

                        # we test again with ASCII char only
                        if not HOSTNAME_PART_PATTERN.search(newpart):
                            valid_parts = hostparts[:i]
                            not_host = hostparts[i + 1 :]
                            bit = HOSTNAME_PART_START.search(part)
                            if bit:
                                valid_parts.append(bit.group(1))
                                not_host.insert(0, bit.group(2))
                            if not_host:
                                rest = ".".join(not_host) + rest
                            self.hostname = ".".join(valid_parts)
                            break
                    i += 1  # emulate statement3 in JS for loop

            if len(self.hostname) > HOSTNAME_MAX_LEN:
                self.hostname = ""

            # strip [ and ] from the hostname
            # the host field still retains them, though
            if ipv6_hostname:
                self.hostname = self.hostname[1:-1]

        # chop off from the tail first.
        hash = rest.find("#")  # noqa: A001
        if hash != -1:
            # got a fragment string.
            self.hash = rest[hash:]
            rest = rest[:hash]
        qm = rest.find("?")
        if qm != -1:
            self.search = rest[qm:]
            rest = rest[:qm]
        if rest:
            self.pathname = rest
        if SLASHED_PROTOCOL[lower_proto] and self.hostname and not self.pathname:
            self.pathname = ""

        return self

    def parse_host(self, host: str) -> None:
        port_match = PORT_PATTERN.search(host)
        if port_match:
            port = port_match.group()
            if port != ":":
                self.port = port[1:]
            host = host[: -len(port)]
        if host:
            self.hostname = host


def url_parse(url: URL | str, *, slashes_denote_host: bool = False) -> URL:
    if isinstance(url, URL):
        return url
    u = MutableURL()
    u.parse(url, slashes_denote_host)
    return URL(
        u.protocol, u.slashes, u.auth, u.port, u.hostname, u.hash, u.search, u.pathname
    )
