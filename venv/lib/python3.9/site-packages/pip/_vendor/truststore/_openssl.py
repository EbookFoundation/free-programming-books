import contextlib
import os
import re
import ssl
import typing

# candidates based on https://github.com/tiran/certifi-system-store by Christian Heimes
_CA_FILE_CANDIDATES = [
    # Alpine, Arch, Fedora 34+, OpenWRT, RHEL 9+, BSD
    "/etc/ssl/cert.pem",
    # Fedora <= 34, RHEL <= 9, CentOS <= 9
    "/etc/pki/tls/cert.pem",
    # Debian, Ubuntu (requires ca-certificates)
    "/etc/ssl/certs/ca-certificates.crt",
    # SUSE
    "/etc/ssl/ca-bundle.pem",
]

_HASHED_CERT_FILENAME_RE = re.compile(r"^[0-9a-fA-F]{8}\.[0-9]$")


@contextlib.contextmanager
def _configure_context(ctx: ssl.SSLContext) -> typing.Iterator[None]:
    # First, check whether the default locations from OpenSSL
    # seem like they will give us a usable set of CA certs.
    # ssl.get_default_verify_paths already takes care of:
    # - getting cafile from either the SSL_CERT_FILE env var
    #   or the path configured when OpenSSL was compiled,
    #   and verifying that that path exists
    # - getting capath from either the SSL_CERT_DIR env var
    #   or the path configured when OpenSSL was compiled,
    #   and verifying that that path exists
    # In addition we'll check whether capath appears to contain certs.
    defaults = ssl.get_default_verify_paths()
    if defaults.cafile or (defaults.capath and _capath_contains_certs(defaults.capath)):
        ctx.set_default_verify_paths()
    else:
        # cafile from OpenSSL doesn't exist
        # and capath from OpenSSL doesn't contain certs.
        # Let's search other common locations instead.
        for cafile in _CA_FILE_CANDIDATES:
            if os.path.isfile(cafile):
                ctx.load_verify_locations(cafile=cafile)
                break

    yield


def _capath_contains_certs(capath: str) -> bool:
    """Check whether capath exists and contains certs in the expected format."""
    if not os.path.isdir(capath):
        return False
    for name in os.listdir(capath):
        if _HASHED_CERT_FILENAME_RE.match(name):
            return True
    return False


def _verify_peercerts_impl(
    ssl_context: ssl.SSLContext,
    cert_chain: list[bytes],
    server_hostname: str | None = None,
) -> None:
    # This is a no-op because we've enabled SSLContext's built-in
    # verification via verify_mode=CERT_REQUIRED, and don't need to repeat it.
    pass
