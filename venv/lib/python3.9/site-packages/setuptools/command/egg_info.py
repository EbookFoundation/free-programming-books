"""setuptools.command.egg_info

Create a distribution's .egg-info directory and contents"""

from distutils.filelist import FileList as _FileList
from distutils.errors import DistutilsInternalError
from distutils.util import convert_path
from distutils import log
import distutils.errors
import distutils.filelist
import functools
import os
import re
import sys
import io
import warnings
import time
import collections

from setuptools import Command
from setuptools.command.sdist import sdist
from setuptools.command.sdist import walk_revctrl
from setuptools.command.setopt import edit_config
from setuptools.command import bdist_egg
from pkg_resources import (
    parse_requirements, safe_name, parse_version,
    safe_version, yield_lines, EntryPoint, iter_entry_points, to_filename)
import setuptools.unicode_utils as unicode_utils
from setuptools.glob import glob

from setuptools.extern import packaging
from setuptools import SetuptoolsDeprecationWarning


def translate_pattern(glob):  # noqa: C901  # is too complex (14)  # FIXME
    """
    Translate a file path glob like '*.txt' in to a regular expression.
    This differs from fnmatch.translate which allows wildcards to match
    directory separators. It also knows about '**/' which matches any number of
    directories.
    """
    pat = ''

    # This will split on '/' within [character classes]. This is deliberate.
    chunks = glob.split(os.path.sep)

    sep = re.escape(os.sep)
    valid_char = '[^%s]' % (sep,)

    for c, chunk in enumerate(chunks):
        last_chunk = c == len(chunks) - 1

        # Chunks that are a literal ** are globstars. They match anything.
        if chunk == '**':
            if last_chunk:
                # Match anything if this is the last component
                pat += '.*'
            else:
                # Match '(name/)*'
                pat += '(?:%s+%s)*' % (valid_char, sep)
            continue  # Break here as the whole path component has been handled

        # Find any special characters in the remainder
        i = 0
        chunk_len = len(chunk)
        while i < chunk_len:
            char = chunk[i]
            if char == '*':
                # Match any number of name characters
                pat += valid_char + '*'
            elif char == '?':
                # Match a name character
                pat += valid_char
            elif char == '[':
                # Character class
                inner_i = i + 1
                # Skip initial !/] chars
                if inner_i < chunk_len and chunk[inner_i] == '!':
                    inner_i = inner_i + 1
                if inner_i < chunk_len and chunk[inner_i] == ']':
                    inner_i = inner_i + 1

                # Loop till the closing ] is found
                while inner_i < chunk_len and chunk[inner_i] != ']':
                    inner_i = inner_i + 1

                if inner_i >= chunk_len:
                    # Got to the end of the string without finding a closing ]
                    # Do not treat this as a matching group, but as a literal [
                    pat += re.escape(char)
                else:
                    # Grab the insides of the [brackets]
                    inner = chunk[i + 1:inner_i]
                    char_class = ''

                    # Class negation
                    if inner[0] == '!':
                        char_class = '^'
                        inner = inner[1:]

                    char_class += re.escape(inner)
                    pat += '[%s]' % (char_class,)

                    # Skip to the end ]
                    i = inner_i
            else:
                pat += re.escape(char)
            i += 1

        # Join each chunk with the dir separator
        if not last_chunk:
            pat += sep

    pat += r'\Z'
    return re.compile(pat, flags=re.MULTILINE | re.DOTALL)


class InfoCommon:
    tag_build = None
    tag_date = None

    @property
    def name(self):
        return safe_name(self.distribution.get_name())

    def tagged_version(self):
        return safe_version(self._maybe_tag(self.distribution.get_version()))

    def _maybe_tag(self, version):
        """
        egg_info may be called more than once for a distribution,
        in which case the version string already contains all tags.
        """
        return (
            version if self.vtags and version.endswith(self.vtags)
            else version + self.vtags
        )

    def tags(self):
        version = ''
        if self.tag_build:
            version += self.tag_build
        if self.tag_date:
            version += time.strftime("-%Y%m%d")
        return version
    vtags = property(tags)


class egg_info(InfoCommon, Command):
    description = "create a distribution's .egg-info directory"

    user_options = [
        ('egg-base=', 'e', "directory containing .egg-info directories"
                           " (default: top of the source tree)"),
        ('tag-date', 'd', "Add date stamp (e.g. 20050528) to version number"),
        ('tag-build=', 'b', "Specify explicit tag to add to version number"),
        ('no-date', 'D', "Don't include date stamp [default]"),
    ]

    boolean_options = ['tag-date']
    negative_opt = {
        'no-date': 'tag-date',
    }

    def initialize_options(self):
        self.egg_base = None
        self.egg_name = None
        self.egg_info = None
        self.egg_version = None
        self.broken_egg_info = False

    ####################################
    # allow the 'tag_svn_revision' to be detected and
    # set, supporting sdists built on older Setuptools.
    @property
    def tag_svn_revision(self):
        pass

    @tag_svn_revision.setter
    def tag_svn_revision(self, value):
        pass
    ####################################

    def save_version_info(self, filename):
        """
        Materialize the value of date into the
        build tag. Install build keys in a deterministic order
        to avoid arbitrary reordering on subsequent builds.
        """
        egg_info = collections.OrderedDict()
        # follow the order these keys would have been added
        # when PYTHONHASHSEED=0
        egg_info['tag_build'] = self.tags()
        egg_info['tag_date'] = 0
        edit_config(filename, dict(egg_info=egg_info))

    def finalize_options(self):
        # Note: we need to capture the current value returned
        # by `self.tagged_version()`, so we can later update
        # `self.distribution.metadata.version` without
        # repercussions.
        self.egg_name = self.name
        self.egg_version = self.tagged_version()
        parsed_version = parse_version(self.egg_version)

        try:
            is_version = isinstance(parsed_version, packaging.version.Version)
            spec = (
                "%s==%s" if is_version else "%s===%s"
            )
            list(
                parse_requirements(spec % (self.egg_name, self.egg_version))
            )
        except ValueError as e:
            raise distutils.errors.DistutilsOptionError(
                "Invalid distribution name or version syntax: %s-%s" %
                (self.egg_name, self.egg_version)
            ) from e

        if self.egg_base is None:
            dirs = self.distribution.package_dir
            self.egg_base = (dirs or {}).get('', os.curdir)

        self.ensure_dirname('egg_base')
        self.egg_info = to_filename(self.egg_name) + '.egg-info'
        if self.egg_base != os.curdir:
            self.egg_info = os.path.join(self.egg_base, self.egg_info)
        if '-' in self.egg_name:
            self.check_broken_egg_info()

        # Set package version for the benefit of dumber commands
        # (e.g. sdist, bdist_wininst, etc.)
        #
        self.distribution.metadata.version = self.egg_version

        # If we bootstrapped around the lack of a PKG-INFO, as might be the
        # case in a fresh checkout, make sure that any special tags get added
        # to the version info
        #
        pd = self.distribution._patched_dist
        if pd is not None and pd.key == self.egg_name.lower():
            pd._version = self.egg_version
            pd._parsed_version = parse_version(self.egg_version)
            self.distribution._patched_dist = None

    def write_or_delete_file(self, what, filename, data, force=False):
        """Write `data` to `filename` or delete if empty

        If `data` is non-empty, this routine is the same as ``write_file()``.
        If `data` is empty but not ``None``, this is the same as calling
        ``delete_file(filename)`.  If `data` is ``None``, then this is a no-op
        unless `filename` exists, in which case a warning is issued about the
        orphaned file (if `force` is false), or deleted (if `force` is true).
        """
        if data:
            self.write_file(what, filename, data)
        elif os.path.exists(filename):
            if data is None and not force:
                log.warn(
                    "%s not set in setup(), but %s exists", what, filename
                )
                return
            else:
                self.delete_file(filename)

    def write_file(self, what, filename, data):
        """Write `data` to `filename` (if not a dry run) after announcing it

        `what` is used in a log message to identify what is being written
        to the file.
        """
        log.info("writing %s to %s", what, filename)
        data = data.encode("utf-8")
        if not self.dry_run:
            f = open(filename, 'wb')
            f.write(data)
            f.close()

    def delete_file(self, filename):
        """Delete `filename` (if not a dry run) after announcing it"""
        log.info("deleting %s", filename)
        if not self.dry_run:
            os.unlink(filename)

    def run(self):
        self.mkpath(self.egg_info)
        os.utime(self.egg_info, None)
        installer = self.distribution.fetch_build_egg
        for ep in iter_entry_points('egg_info.writers'):
            ep.require(installer=installer)
            writer = ep.resolve()
            writer(self, ep.name, os.path.join(self.egg_info, ep.name))

        # Get rid of native_libs.txt if it was put there by older bdist_egg
        nl = os.path.join(self.egg_info, "native_libs.txt")
        if os.path.exists(nl):
            self.delete_file(nl)

        self.find_sources()

    def find_sources(self):
        """Generate SOURCES.txt manifest file"""
        manifest_filename = os.path.join(self.egg_info, "SOURCES.txt")
        mm = manifest_maker(self.distribution)
        mm.manifest = manifest_filename
        mm.run()
        self.filelist = mm.filelist

    def check_broken_egg_info(self):
        bei = self.egg_name + '.egg-info'
        if self.egg_base != os.curdir:
            bei = os.path.join(self.egg_base, bei)
        if os.path.exists(bei):
            log.warn(
                "-" * 78 + '\n'
                "Note: Your current .egg-info directory has a '-' in its name;"
                '\nthis will not work correctly with "setup.py develop".\n\n'
                'Please rename %s to %s to correct this problem.\n' + '-' * 78,
                bei, self.egg_info
            )
            self.broken_egg_info = self.egg_info
            self.egg_info = bei  # make it work for now


class FileList(_FileList):
    # Implementations of the various MANIFEST.in commands

    def process_template_line(self, line):
        # Parse the line: split it up, make sure the right number of words
        # is there, and return the relevant words.  'action' is always
        # defined: it's the first word of the line.  Which of the other
        # three are defined depends on the action; it'll be either
        # patterns, (dir and patterns), or (dir_pattern).
        (action, patterns, dir, dir_pattern) = self._parse_template_line(line)

        action_map = {
            'include': self.include,
            'exclude': self.exclude,
            'global-include': self.global_include,
            'global-exclude': self.global_exclude,
            'recursive-include': functools.partial(
                self.recursive_include, dir,
            ),
            'recursive-exclude': functools.partial(
                self.recursive_exclude, dir,
            ),
            'graft': self.graft,
            'prune': self.prune,
        }
        log_map = {
            'include': "warning: no files found matching '%s'",
            'exclude': (
                "warning: no previously-included files found "
                "matching '%s'"
            ),
            'global-include': (
                "warning: no files found matching '%s' "
                "anywhere in distribution"
            ),
            'global-exclude': (
                "warning: no previously-included files matching "
                "'%s' found anywhere in distribution"
            ),
            'recursive-include': (
                "warning: no files found matching '%s' "
                "under directory '%s'"
            ),
            'recursive-exclude': (
                "warning: no previously-included files matching "
                "'%s' found under directory '%s'"
            ),
            'graft': "warning: no directories found matching '%s'",
            'prune': "no previously-included directories found matching '%s'",
        }

        try:
            process_action = action_map[action]
        except KeyError:
            raise DistutilsInternalError(
                "this cannot happen: invalid action '{action!s}'".
                format(action=action),
            )

        # OK, now we know that the action is valid and we have the
        # right number of words on the line for that action -- so we
        # can proceed with minimal error-checking.

        action_is_recursive = action.startswith('recursive-')
        if action in {'graft', 'prune'}:
            patterns = [dir_pattern]
        extra_log_args = (dir, ) if action_is_recursive else ()
        log_tmpl = log_map[action]

        self.debug_print(
            ' '.join(
                [action] +
                ([dir] if action_is_recursive else []) +
                patterns,
            )
        )
        for pattern in patterns:
            if not process_action(pattern):
                log.warn(log_tmpl, pattern, *extra_log_args)

    def _remove_files(self, predicate):
        """
        Remove all files from the file list that match the predicate.
        Return True if any matching files were removed
        """
        found = False
        for i in range(len(self.files) - 1, -1, -1):
            if predicate(self.files[i]):
                self.debug_print(" removing " + self.files[i])
                del self.files[i]
                found = True
        return found

    def include(self, pattern):
        """Include files that match 'pattern'."""
        found = [f for f in glob(pattern) if not os.path.isdir(f)]
        self.extend(found)
        return bool(found)

    def exclude(self, pattern):
        """Exclude files that match 'pattern'."""
        match = translate_pattern(pattern)
        return self._remove_files(match.match)

    def recursive_include(self, dir, pattern):
        """
        Include all files anywhere in 'dir/' that match the pattern.
        """
        full_pattern = os.path.join(dir, '**', pattern)
        found = [f for f in glob(full_pattern, recursive=True)
                 if not os.path.isdir(f)]
        self.extend(found)
        return bool(found)

    def recursive_exclude(self, dir, pattern):
        """
        Exclude any file anywhere in 'dir/' that match the pattern.
        """
        match = translate_pattern(os.path.join(dir, '**', pattern))
        return self._remove_files(match.match)

    def graft(self, dir):
        """Include all files from 'dir/'."""
        found = [
            item
            for match_dir in glob(dir)
            for item in distutils.filelist.findall(match_dir)
        ]
        self.extend(found)
        return bool(found)

    def prune(self, dir):
        """Filter out files from 'dir/'."""
        match = translate_pattern(os.path.join(dir, '**'))
        return self._remove_files(match.match)

    def global_include(self, pattern):
        """
        Include all files anywhere in the current directory that match the
        pattern. This is very inefficient on large file trees.
        """
        if self.allfiles is None:
            self.findall()
        match = translate_pattern(os.path.join('**', pattern))
        found = [f for f in self.allfiles if match.match(f)]
        self.extend(found)
        return bool(found)

    def global_exclude(self, pattern):
        """
        Exclude all files anywhere that match the pattern.
        """
        match = translate_pattern(os.path.join('**', pattern))
        return self._remove_files(match.match)

    def append(self, item):
        if item.endswith('\r'):  # Fix older sdists built on Windows
            item = item[:-1]
        path = convert_path(item)

        if self._safe_path(path):
            self.files.append(path)

    def extend(self, paths):
        self.files.extend(filter(self._safe_path, paths))

    def _repair(self):
        """
        Replace self.files with only safe paths

        Because some owners of FileList manipulate the underlying
        ``files`` attribute directly, this method must be called to
        repair those paths.
        """
        self.files = list(filter(self._safe_path, self.files))

    def _safe_path(self, path):
        enc_warn = "'%s' not %s encodable -- skipping"

        # To avoid accidental trans-codings errors, first to unicode
        u_path = unicode_utils.filesys_decode(path)
        if u_path is None:
            log.warn("'%s' in unexpected encoding -- skipping" % path)
            return False

        # Must ensure utf-8 encodability
        utf8_path = unicode_utils.try_encode(u_path, "utf-8")
        if utf8_path is None:
            log.warn(enc_warn, path, 'utf-8')
            return False

        try:
            # accept is either way checks out
            if os.path.exists(u_path) or os.path.exists(utf8_path):
                return True
        # this will catch any encode errors decoding u_path
        except UnicodeEncodeError:
            log.warn(enc_warn, path, sys.getfilesystemencoding())


class manifest_maker(sdist):
    template = "MANIFEST.in"

    def initialize_options(self):
        self.use_defaults = 1
        self.prune = 1
        self.manifest_only = 1
        self.force_manifest = 1

    def finalize_options(self):
        pass

    def run(self):
        self.filelist = FileList()
        if not os.path.exists(self.manifest):
            self.write_manifest()  # it must exist so it'll get in the list
        self.add_defaults()
        if os.path.exists(self.template):
            self.read_template()
        self.add_license_files()
        self.prune_file_list()
        self.filelist.sort()
        self.filelist.remove_duplicates()
        self.write_manifest()

    def _manifest_normalize(self, path):
        path = unicode_utils.filesys_decode(path)
        return path.replace(os.sep, '/')

    def write_manifest(self):
        """
        Write the file list in 'self.filelist' to the manifest file
        named by 'self.manifest'.
        """
        self.filelist._repair()

        # Now _repairs should encodability, but not unicode
        files = [self._manifest_normalize(f) for f in self.filelist.files]
        msg = "writing manifest file '%s'" % self.manifest
        self.execute(write_file, (self.manifest, files), msg)

    def warn(self, msg):
        if not self._should_suppress_warning(msg):
            sdist.warn(self, msg)

    @staticmethod
    def _should_suppress_warning(msg):
        """
        suppress missing-file warnings from sdist
        """
        return re.match(r"standard file .*not found", msg)

    def add_defaults(self):
        sdist.add_defaults(self)
        self.filelist.append(self.template)
        self.filelist.append(self.manifest)
        rcfiles = list(walk_revctrl())
        if rcfiles:
            self.filelist.extend(rcfiles)
        elif os.path.exists(self.manifest):
            self.read_manifest()

        if os.path.exists("setup.py"):
            # setup.py should be included by default, even if it's not
            # the script called to create the sdist
            self.filelist.append("setup.py")

        ei_cmd = self.get_finalized_command('egg_info')
        self.filelist.graft(ei_cmd.egg_info)

    def add_license_files(self):
        license_files = self.distribution.metadata.license_files or []
        for lf in license_files:
            log.info("adding license file '%s'", lf)
            pass
        self.filelist.extend(license_files)

    def prune_file_list(self):
        build = self.get_finalized_command('build')
        base_dir = self.distribution.get_fullname()
        self.filelist.prune(build.build_base)
        self.filelist.prune(base_dir)
        sep = re.escape(os.sep)
        self.filelist.exclude_pattern(r'(^|' + sep + r')(RCS|CVS|\.svn)' + sep,
                                      is_regex=1)


def write_file(filename, contents):
    """Create a file with the specified name and write 'contents' (a
    sequence of strings without line terminators) to it.
    """
    contents = "\n".join(contents)

    # assuming the contents has been vetted for utf-8 encoding
    contents = contents.encode("utf-8")

    with open(filename, "wb") as f:  # always write POSIX-style manifest
        f.write(contents)


def write_pkg_info(cmd, basename, filename):
    log.info("writing %s", filename)
    if not cmd.dry_run:
        metadata = cmd.distribution.metadata
        metadata.version, oldver = cmd.egg_version, metadata.version
        metadata.name, oldname = cmd.egg_name, metadata.name

        try:
            # write unescaped data to PKG-INFO, so older pkg_resources
            # can still parse it
            metadata.write_pkg_info(cmd.egg_info)
        finally:
            metadata.name, metadata.version = oldname, oldver

        safe = getattr(cmd.distribution, 'zip_safe', None)

        bdist_egg.write_safety_flag(cmd.egg_info, safe)


def warn_depends_obsolete(cmd, basename, filename):
    if os.path.exists(filename):
        log.warn(
            "WARNING: 'depends.txt' is not used by setuptools 0.6!\n"
            "Use the install_requires/extras_require setup() args instead."
        )


def _write_requirements(stream, reqs):
    lines = yield_lines(reqs or ())

    def append_cr(line):
        return line + '\n'
    lines = map(append_cr, lines)
    stream.writelines(lines)


def write_requirements(cmd, basename, filename):
    dist = cmd.distribution
    data = io.StringIO()
    _write_requirements(data, dist.install_requires)
    extras_require = dist.extras_require or {}
    for extra in sorted(extras_require):
        data.write('\n[{extra}]\n'.format(**vars()))
        _write_requirements(data, extras_require[extra])
    cmd.write_or_delete_file("requirements", filename, data.getvalue())


def write_setup_requirements(cmd, basename, filename):
    data = io.StringIO()
    _write_requirements(data, cmd.distribution.setup_requires)
    cmd.write_or_delete_file("setup-requirements", filename, data.getvalue())


def write_toplevel_names(cmd, basename, filename):
    pkgs = dict.fromkeys(
        [
            k.split('.', 1)[0]
            for k in cmd.distribution.iter_distribution_names()
        ]
    )
    cmd.write_file("top-level names", filename, '\n'.join(sorted(pkgs)) + '\n')


def overwrite_arg(cmd, basename, filename):
    write_arg(cmd, basename, filename, True)


def write_arg(cmd, basename, filename, force=False):
    argname = os.path.splitext(basename)[0]
    value = getattr(cmd.distribution, argname, None)
    if value is not None:
        value = '\n'.join(value) + '\n'
    cmd.write_or_delete_file(argname, filename, value, force)


def write_entries(cmd, basename, filename):
    ep = cmd.distribution.entry_points

    if isinstance(ep, str) or ep is None:
        data = ep
    elif ep is not None:
        data = []
        for section, contents in sorted(ep.items()):
            if not isinstance(contents, str):
                contents = EntryPoint.parse_group(section, contents)
                contents = '\n'.join(sorted(map(str, contents.values())))
            data.append('[%s]\n%s\n\n' % (section, contents))
        data = ''.join(data)

    cmd.write_or_delete_file('entry points', filename, data, True)


def get_pkg_info_revision():
    """
    Get a -r### off of PKG-INFO Version in case this is an sdist of
    a subversion revision.
    """
    warnings.warn(
        "get_pkg_info_revision is deprecated.", EggInfoDeprecationWarning)
    if os.path.exists('PKG-INFO'):
        with io.open('PKG-INFO') as f:
            for line in f:
                match = re.match(r"Version:.*-r(\d+)\s*$", line)
                if match:
                    return int(match.group(1))
    return 0


class EggInfoDeprecationWarning(SetuptoolsDeprecationWarning):
    """Deprecated behavior warning for EggInfo, bypassing suppression."""
