import glob
import os
import subprocess
import sys
import tempfile
from distutils import log
from distutils.errors import DistutilsError

import pkg_resources
from setuptools.wheel import Wheel


def _fixup_find_links(find_links):
    """Ensure find-links option end-up being a list of strings."""
    if isinstance(find_links, str):
        return find_links.split()
    assert isinstance(find_links, (tuple, list))
    return find_links


def fetch_build_egg(dist, req):  # noqa: C901  # is too complex (16)  # FIXME
    """Fetch an egg needed for building.

    Use pip/wheel to fetch/build a wheel."""
    # Warn if wheel is not available
    try:
        pkg_resources.get_distribution('wheel')
    except pkg_resources.DistributionNotFound:
        dist.announce('WARNING: The wheel package is not available.', log.WARN)
    # Ignore environment markers; if supplied, it is required.
    req = strip_marker(req)
    # Take easy_install options into account, but do not override relevant
    # pip environment variables (like PIP_INDEX_URL or PIP_QUIET); they'll
    # take precedence.
    opts = dist.get_option_dict('easy_install')
    if 'allow_hosts' in opts:
        raise DistutilsError('the `allow-hosts` option is not supported '
                             'when using pip to install requirements.')
    quiet = 'PIP_QUIET' not in os.environ and 'PIP_VERBOSE' not in os.environ
    if 'PIP_INDEX_URL' in os.environ:
        index_url = None
    elif 'index_url' in opts:
        index_url = opts['index_url'][1]
    else:
        index_url = None
    find_links = (
        _fixup_find_links(opts['find_links'][1])[:] if 'find_links' in opts
        else []
    )
    if dist.dependency_links:
        find_links.extend(dist.dependency_links)
    eggs_dir = os.path.realpath(dist.get_egg_cache_dir())
    environment = pkg_resources.Environment()
    for egg_dist in pkg_resources.find_distributions(eggs_dir):
        if egg_dist in req and environment.can_add(egg_dist):
            return egg_dist
    with tempfile.TemporaryDirectory() as tmpdir:
        cmd = [
            sys.executable, '-m', 'pip',
            '--disable-pip-version-check',
            'wheel', '--no-deps',
            '-w', tmpdir,
        ]
        if quiet:
            cmd.append('--quiet')
        if index_url is not None:
            cmd.extend(('--index-url', index_url))
        for link in find_links or []:
            cmd.extend(('--find-links', link))
        # If requirement is a PEP 508 direct URL, directly pass
        # the URL to pip, as `req @ url` does not work on the
        # command line.
        cmd.append(req.url or str(req))
        try:
            subprocess.check_call(cmd)
        except subprocess.CalledProcessError as e:
            raise DistutilsError(str(e)) from e
        wheel = Wheel(glob.glob(os.path.join(tmpdir, '*.whl'))[0])
        dist_location = os.path.join(eggs_dir, wheel.egg_name())
        wheel.install_as_egg(dist_location)
        dist_metadata = pkg_resources.PathMetadata(
            dist_location, os.path.join(dist_location, 'EGG-INFO'))
        dist = pkg_resources.Distribution.from_filename(
            dist_location, metadata=dist_metadata)
        return dist


def strip_marker(req):
    """
    Return a new requirement without the environment marker to avoid
    calling pip with something like `babel; extra == "i18n"`, which
    would always be ignored.
    """
    # create a copy to avoid mutating the input
    req = pkg_resources.Requirement.parse(str(req))
    req.marker = None
    return req
