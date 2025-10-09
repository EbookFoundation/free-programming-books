"""distutils.dep_util

Utility functions for simple, timestamp-based dependency of files
and groups of files; also, function based entirely on such
timestamp dependency analysis."""

import os
from distutils.errors import DistutilsFileError


def newer (source, target):
    """Return true if 'source' exists and is more recently modified than
    'target', or if 'source' exists and 'target' doesn't.  Return false if
    both exist and 'target' is the same age or younger than 'source'.
    Raise DistutilsFileError if 'source' does not exist.
    """
    if not os.path.exists(source):
        raise DistutilsFileError("file '%s' does not exist" %
                                 os.path.abspath(source))
    if not os.path.exists(target):
        return 1

    from stat import ST_MTIME
    mtime1 = os.stat(source)[ST_MTIME]
    mtime2 = os.stat(target)[ST_MTIME]

    return mtime1 > mtime2

# newer ()


def newer_pairwise (sources, targets):
    """Walk two filename lists in parallel, testing if each source is newer
    than its corresponding target.  Return a pair of lists (sources,
    targets) where source is newer than target, according to the semantics
    of 'newer()'.
    """
    if len(sources) != len(targets):
        raise ValueError("'sources' and 'targets' must be same length")

    # build a pair of lists (sources, targets) where  source is newer
    n_sources = []
    n_targets = []
    for i in range(len(sources)):
        if newer(sources[i], targets[i]):
            n_sources.append(sources[i])
            n_targets.append(targets[i])

    return (n_sources, n_targets)

# newer_pairwise ()


def newer_group (sources, target, missing='error'):
    """Return true if 'target' is out-of-date with respect to any file
    listed in 'sources'.  In other words, if 'target' exists and is newer
    than every file in 'sources', return false; otherwise return true.
    'missing' controls what we do when a source file is missing; the
    default ("error") is to blow up with an OSError from inside 'stat()';
    if it is "ignore", we silently drop any missing source files; if it is
    "newer", any missing source files make us assume that 'target' is
    out-of-date (this is handy in "dry-run" mode: it'll make you pretend to
    carry out commands that wouldn't work because inputs are missing, but
    that doesn't matter because you're not actually going to run the
    commands).
    """
    # If the target doesn't even exist, then it's definitely out-of-date.
    if not os.path.exists(target):
        return 1

    # Otherwise we have to find out the hard way: if *any* source file
    # is more recent than 'target', then 'target' is out-of-date and
    # we can immediately return true.  If we fall through to the end
    # of the loop, then 'target' is up-to-date and we return false.
    from stat import ST_MTIME
    target_mtime = os.stat(target)[ST_MTIME]
    for source in sources:
        if not os.path.exists(source):
            if missing == 'error':      # blow up when we stat() the file
                pass
            elif missing == 'ignore':   # missing source dropped from
                continue                #  target's dependency list
            elif missing == 'newer':    # missing source means target is
                return 1                #  out-of-date

        source_mtime = os.stat(source)[ST_MTIME]
        if source_mtime > target_mtime:
            return 1
    else:
        return 0

# newer_group ()
