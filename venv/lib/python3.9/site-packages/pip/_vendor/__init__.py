"""
pip._vendor is for vendoring dependencies of pip to prevent needing pip to
depend on something external.

Files inside of pip._vendor should be considered immutable and should only be
updated to versions from upstream.
"""
from __future__ import absolute_import

import glob
import os.path
import sys

# Downstream redistributors which have debundled our dependencies should also
# patch this value to be true. This will trigger the additional patching
# to cause things like "six" to be available as pip.
DEBUNDLED = False

# By default, look in this directory for a bunch of .whl files which we will
# add to the beginning of sys.path before attempting to import anything. This
# is done to support downstream re-distributors like Debian and Fedora who
# wish to create their own Wheels for our dependencies to aid in debundling.
WHEEL_DIR = os.path.abspath(os.path.dirname(__file__))


# Define a small helper function to alias our vendored modules to the real ones
# if the vendored ones do not exist. This idea of this was taken from
# https://github.com/kennethreitz/requests/pull/2567.
def vendored(modulename):
    vendored_name = "{0}.{1}".format(__name__, modulename)

    try:
        __import__(modulename, globals(), locals(), level=0)
    except ImportError:
        # We can just silently allow import failures to pass here. If we
        # got to this point it means that ``import pip._vendor.whatever``
        # failed and so did ``import whatever``. Since we're importing this
        # upfront in an attempt to alias imports, not erroring here will
        # just mean we get a regular import error whenever pip *actually*
        # tries to import one of these modules to use it, which actually
        # gives us a better error message than we would have otherwise
        # gotten.
        pass
    else:
        sys.modules[vendored_name] = sys.modules[modulename]
        base, head = vendored_name.rsplit(".", 1)
        setattr(sys.modules[base], head, sys.modules[modulename])


# If we're operating in a debundled setup, then we want to go ahead and trigger
# the aliasing of our vendored libraries as well as looking for wheels to add
# to our sys.path. This will cause all of this code to be a no-op typically
# however downstream redistributors can enable it in a consistent way across
# all platforms.
if DEBUNDLED:
    # Actually look inside of WHEEL_DIR to find .whl files and add them to the
    # front of our sys.path.
    sys.path[:] = glob.glob(os.path.join(WHEEL_DIR, "*.whl")) + sys.path

    # Actually alias all of our vendored dependencies.
    vendored("cachecontrol")
    vendored("certifi")
    vendored("dependency-groups")
    vendored("distlib")
    vendored("distro")
    vendored("packaging")
    vendored("packaging.version")
    vendored("packaging.specifiers")
    vendored("pkg_resources")
    vendored("platformdirs")
    vendored("progress")
    vendored("pyproject_hooks")
    vendored("requests")
    vendored("requests.exceptions")
    vendored("requests.packages")
    vendored("requests.packages.urllib3")
    vendored("requests.packages.urllib3._collections")
    vendored("requests.packages.urllib3.connection")
    vendored("requests.packages.urllib3.connectionpool")
    vendored("requests.packages.urllib3.contrib")
    vendored("requests.packages.urllib3.contrib.ntlmpool")
    vendored("requests.packages.urllib3.contrib.pyopenssl")
    vendored("requests.packages.urllib3.exceptions")
    vendored("requests.packages.urllib3.fields")
    vendored("requests.packages.urllib3.filepost")
    vendored("requests.packages.urllib3.packages")
    vendored("requests.packages.urllib3.packages.ordered_dict")
    vendored("requests.packages.urllib3.packages.six")
    vendored("requests.packages.urllib3.packages.ssl_match_hostname")
    vendored("requests.packages.urllib3.packages.ssl_match_hostname."
             "_implementation")
    vendored("requests.packages.urllib3.poolmanager")
    vendored("requests.packages.urllib3.request")
    vendored("requests.packages.urllib3.response")
    vendored("requests.packages.urllib3.util")
    vendored("requests.packages.urllib3.util.connection")
    vendored("requests.packages.urllib3.util.request")
    vendored("requests.packages.urllib3.util.response")
    vendored("requests.packages.urllib3.util.retry")
    vendored("requests.packages.urllib3.util.ssl_")
    vendored("requests.packages.urllib3.util.timeout")
    vendored("requests.packages.urllib3.util.url")
    vendored("resolvelib")
    vendored("rich")
    vendored("rich.console")
    vendored("rich.highlighter")
    vendored("rich.logging")
    vendored("rich.markup")
    vendored("rich.progress")
    vendored("rich.segment")
    vendored("rich.style")
    vendored("rich.text")
    vendored("rich.traceback")
    if sys.version_info < (3, 11):
        vendored("tomli")
    vendored("truststore")
    vendored("urllib3")
