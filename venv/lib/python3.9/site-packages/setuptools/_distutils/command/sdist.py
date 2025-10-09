"""distutils.command.sdist

Implements the Distutils 'sdist' command (create a source distribution)."""

import os
import sys
from glob import glob
from warnings import warn

from distutils.core import Command
from distutils import dir_util
from distutils import file_util
from distutils import archive_util
from distutils.text_file import TextFile
from distutils.filelist import FileList
from distutils import log
from distutils.util import convert_path
from distutils.errors import DistutilsTemplateError, DistutilsOptionError


def show_formats():
    """Print all possible values for the 'formats' option (used by
    the "--help-formats" command-line option).
    """
    from distutils.fancy_getopt import FancyGetopt
    from distutils.archive_util import ARCHIVE_FORMATS
    formats = []
    for format in ARCHIVE_FORMATS.keys():
        formats.append(("formats=" + format, None,
                        ARCHIVE_FORMATS[format][2]))
    formats.sort()
    FancyGetopt(formats).print_help(
        "List of available source distribution formats:")


class sdist(Command):

    description = "create a source distribution (tarball, zip file, etc.)"

    def checking_metadata(self):
        """Callable used for the check sub-command.

        Placed here so user_options can view it"""
        return self.metadata_check

    user_options = [
        ('template=', 't',
         "name of manifest template file [default: MANIFEST.in]"),
        ('manifest=', 'm',
         "name of manifest file [default: MANIFEST]"),
        ('use-defaults', None,
         "include the default file set in the manifest "
         "[default; disable with --no-defaults]"),
        ('no-defaults', None,
         "don't include the default file set"),
        ('prune', None,
         "specifically exclude files/directories that should not be "
         "distributed (build tree, RCS/CVS dirs, etc.) "
         "[default; disable with --no-prune]"),
        ('no-prune', None,
         "don't automatically exclude anything"),
        ('manifest-only', 'o',
         "just regenerate the manifest and then stop "
         "(implies --force-manifest)"),
        ('force-manifest', 'f',
         "forcibly regenerate the manifest and carry on as usual. "
         "Deprecated: now the manifest is always regenerated."),
        ('formats=', None,
         "formats for source distribution (comma-separated list)"),
        ('keep-temp', 'k',
         "keep the distribution tree around after creating " +
         "archive file(s)"),
        ('dist-dir=', 'd',
         "directory to put the source distribution archive(s) in "
         "[default: dist]"),
        ('metadata-check', None,
         "Ensure that all required elements of meta-data "
         "are supplied. Warn if any missing. [default]"),
        ('owner=', 'u',
         "Owner name used when creating a tar file [default: current user]"),
        ('group=', 'g',
         "Group name used when creating a tar file [default: current group]"),
        ]

    boolean_options = ['use-defaults', 'prune',
                       'manifest-only', 'force-manifest',
                       'keep-temp', 'metadata-check']

    help_options = [
        ('help-formats', None,
         "list available distribution formats", show_formats),
        ]

    negative_opt = {'no-defaults': 'use-defaults',
                    'no-prune': 'prune' }

    sub_commands = [('check', checking_metadata)]

    READMES = ('README', 'README.txt', 'README.rst')

    def initialize_options(self):
        # 'template' and 'manifest' are, respectively, the names of
        # the manifest template and manifest file.
        self.template = None
        self.manifest = None

        # 'use_defaults': if true, we will include the default file set
        # in the manifest
        self.use_defaults = 1
        self.prune = 1

        self.manifest_only = 0
        self.force_manifest = 0

        self.formats = ['gztar']
        self.keep_temp = 0
        self.dist_dir = None

        self.archive_files = None
        self.metadata_check = 1
        self.owner = None
        self.group = None

    def finalize_options(self):
        if self.manifest is None:
            self.manifest = "MANIFEST"
        if self.template is None:
            self.template = "MANIFEST.in"

        self.ensure_string_list('formats')

        bad_format = archive_util.check_archive_formats(self.formats)
        if bad_format:
            raise DistutilsOptionError(
                  "unknown archive format '%s'" % bad_format)

        if self.dist_dir is None:
            self.dist_dir = "dist"

    def run(self):
        # 'filelist' contains the list of files that will make up the
        # manifest
        self.filelist = FileList()

        # Run sub commands
        for cmd_name in self.get_sub_commands():
            self.run_command(cmd_name)

        # Do whatever it takes to get the list of files to process
        # (process the manifest template, read an existing manifest,
        # whatever).  File list is accumulated in 'self.filelist'.
        self.get_file_list()

        # If user just wanted us to regenerate the manifest, stop now.
        if self.manifest_only:
            return

        # Otherwise, go ahead and create the source distribution tarball,
        # or zipfile, or whatever.
        self.make_distribution()

    def check_metadata(self):
        """Deprecated API."""
        warn("distutils.command.sdist.check_metadata is deprecated, \
              use the check command instead", PendingDeprecationWarning)
        check = self.distribution.get_command_obj('check')
        check.ensure_finalized()
        check.run()

    def get_file_list(self):
        """Figure out the list of files to include in the source
        distribution, and put it in 'self.filelist'.  This might involve
        reading the manifest template (and writing the manifest), or just
        reading the manifest, or just using the default file set -- it all
        depends on the user's options.
        """
        # new behavior when using a template:
        # the file list is recalculated every time because
        # even if MANIFEST.in or setup.py are not changed
        # the user might have added some files in the tree that
        # need to be included.
        #
        #  This makes --force the default and only behavior with templates.
        template_exists = os.path.isfile(self.template)
        if not template_exists and self._manifest_is_not_generated():
            self.read_manifest()
            self.filelist.sort()
            self.filelist.remove_duplicates()
            return

        if not template_exists:
            self.warn(("manifest template '%s' does not exist " +
                        "(using default file list)") %
                        self.template)
        self.filelist.findall()

        if self.use_defaults:
            self.add_defaults()

        if template_exists:
            self.read_template()

        if self.prune:
            self.prune_file_list()

        self.filelist.sort()
        self.filelist.remove_duplicates()
        self.write_manifest()

    def add_defaults(self):
        """Add all the default files to self.filelist:
          - README or README.txt
          - setup.py
          - test/test*.py
          - all pure Python modules mentioned in setup script
          - all files pointed by package_data (build_py)
          - all files defined in data_files.
          - all files defined as scripts.
          - all C sources listed as part of extensions or C libraries
            in the setup script (doesn't catch C headers!)
        Warns if (README or README.txt) or setup.py are missing; everything
        else is optional.
        """
        self._add_defaults_standards()
        self._add_defaults_optional()
        self._add_defaults_python()
        self._add_defaults_data_files()
        self._add_defaults_ext()
        self._add_defaults_c_libs()
        self._add_defaults_scripts()

    @staticmethod
    def _cs_path_exists(fspath):
        """
        Case-sensitive path existence check

        >>> sdist._cs_path_exists(__file__)
        True
        >>> sdist._cs_path_exists(__file__.upper())
        False
        """
        if not os.path.exists(fspath):
            return False
        # make absolute so we always have a directory
        abspath = os.path.abspath(fspath)
        directory, filename = os.path.split(abspath)
        return filename in os.listdir(directory)

    def _add_defaults_standards(self):
        standards = [self.READMES, self.distribution.script_name]
        for fn in standards:
            if isinstance(fn, tuple):
                alts = fn
                got_it = False
                for fn in alts:
                    if self._cs_path_exists(fn):
                        got_it = True
                        self.filelist.append(fn)
                        break

                if not got_it:
                    self.warn("standard file not found: should have one of " +
                              ', '.join(alts))
            else:
                if self._cs_path_exists(fn):
                    self.filelist.append(fn)
                else:
                    self.warn("standard file '%s' not found" % fn)

    def _add_defaults_optional(self):
        optional = ['test/test*.py', 'setup.cfg']
        for pattern in optional:
            files = filter(os.path.isfile, glob(pattern))
            self.filelist.extend(files)

    def _add_defaults_python(self):
        # build_py is used to get:
        #  - python modules
        #  - files defined in package_data
        build_py = self.get_finalized_command('build_py')

        # getting python files
        if self.distribution.has_pure_modules():
            self.filelist.extend(build_py.get_source_files())

        # getting package_data files
        # (computed in build_py.data_files by build_py.finalize_options)
        for pkg, src_dir, build_dir, filenames in build_py.data_files:
            for filename in filenames:
                self.filelist.append(os.path.join(src_dir, filename))

    def _add_defaults_data_files(self):
        # getting distribution.data_files
        if self.distribution.has_data_files():
            for item in self.distribution.data_files:
                if isinstance(item, str):
                    # plain file
                    item = convert_path(item)
                    if os.path.isfile(item):
                        self.filelist.append(item)
                else:
                    # a (dirname, filenames) tuple
                    dirname, filenames = item
                    for f in filenames:
                        f = convert_path(f)
                        if os.path.isfile(f):
                            self.filelist.append(f)

    def _add_defaults_ext(self):
        if self.distribution.has_ext_modules():
            build_ext = self.get_finalized_command('build_ext')
            self.filelist.extend(build_ext.get_source_files())

    def _add_defaults_c_libs(self):
        if self.distribution.has_c_libraries():
            build_clib = self.get_finalized_command('build_clib')
            self.filelist.extend(build_clib.get_source_files())

    def _add_defaults_scripts(self):
        if self.distribution.has_scripts():
            build_scripts = self.get_finalized_command('build_scripts')
            self.filelist.extend(build_scripts.get_source_files())

    def read_template(self):
        """Read and parse manifest template file named by self.template.

        (usually "MANIFEST.in") The parsing and processing is done by
        'self.filelist', which updates itself accordingly.
        """
        log.info("reading manifest template '%s'", self.template)
        template = TextFile(self.template, strip_comments=1, skip_blanks=1,
                            join_lines=1, lstrip_ws=1, rstrip_ws=1,
                            collapse_join=1)

        try:
            while True:
                line = template.readline()
                if line is None:            # end of file
                    break

                try:
                    self.filelist.process_template_line(line)
                # the call above can raise a DistutilsTemplateError for
                # malformed lines, or a ValueError from the lower-level
                # convert_path function
                except (DistutilsTemplateError, ValueError) as msg:
                    self.warn("%s, line %d: %s" % (template.filename,
                                                   template.current_line,
                                                   msg))
        finally:
            template.close()

    def prune_file_list(self):
        """Prune off branches that might slip into the file list as created
        by 'read_template()', but really don't belong there:
          * the build tree (typically "build")
          * the release tree itself (only an issue if we ran "sdist"
            previously with --keep-temp, or it aborted)
          * any RCS, CVS, .svn, .hg, .git, .bzr, _darcs directories
        """
        build = self.get_finalized_command('build')
        base_dir = self.distribution.get_fullname()

        self.filelist.exclude_pattern(None, prefix=build.build_base)
        self.filelist.exclude_pattern(None, prefix=base_dir)

        if sys.platform == 'win32':
            seps = r'/|\\'
        else:
            seps = '/'

        vcs_dirs = ['RCS', 'CVS', r'\.svn', r'\.hg', r'\.git', r'\.bzr',
                    '_darcs']
        vcs_ptrn = r'(^|%s)(%s)(%s).*' % (seps, '|'.join(vcs_dirs), seps)
        self.filelist.exclude_pattern(vcs_ptrn, is_regex=1)

    def write_manifest(self):
        """Write the file list in 'self.filelist' (presumably as filled in
        by 'add_defaults()' and 'read_template()') to the manifest file
        named by 'self.manifest'.
        """
        if self._manifest_is_not_generated():
            log.info("not writing to manually maintained "
                     "manifest file '%s'" % self.manifest)
            return

        content = self.filelist.files[:]
        content.insert(0, '# file GENERATED by distutils, do NOT edit')
        self.execute(file_util.write_file, (self.manifest, content),
                     "writing manifest file '%s'" % self.manifest)

    def _manifest_is_not_generated(self):
        # check for special comment used in 3.1.3 and higher
        if not os.path.isfile(self.manifest):
            return False

        fp = open(self.manifest)
        try:
            first_line = fp.readline()
        finally:
            fp.close()
        return first_line != '# file GENERATED by distutils, do NOT edit\n'

    def read_manifest(self):
        """Read the manifest file (named by 'self.manifest') and use it to
        fill in 'self.filelist', the list of files to include in the source
        distribution.
        """
        log.info("reading manifest file '%s'", self.manifest)
        with open(self.manifest) as manifest:
            for line in manifest:
                # ignore comments and blank lines
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                self.filelist.append(line)

    def make_release_tree(self, base_dir, files):
        """Create the directory tree that will become the source
        distribution archive.  All directories implied by the filenames in
        'files' are created under 'base_dir', and then we hard link or copy
        (if hard linking is unavailable) those files into place.
        Essentially, this duplicates the developer's source tree, but in a
        directory named after the distribution, containing only the files
        to be distributed.
        """
        # Create all the directories under 'base_dir' necessary to
        # put 'files' there; the 'mkpath()' is just so we don't die
        # if the manifest happens to be empty.
        self.mkpath(base_dir)
        dir_util.create_tree(base_dir, files, dry_run=self.dry_run)

        # And walk over the list of files, either making a hard link (if
        # os.link exists) to each one that doesn't already exist in its
        # corresponding location under 'base_dir', or copying each file
        # that's out-of-date in 'base_dir'.  (Usually, all files will be
        # out-of-date, because by default we blow away 'base_dir' when
        # we're done making the distribution archives.)

        if hasattr(os, 'link'):        # can make hard links on this system
            link = 'hard'
            msg = "making hard links in %s..." % base_dir
        else:                           # nope, have to copy
            link = None
            msg = "copying files to %s..." % base_dir

        if not files:
            log.warn("no files to distribute -- empty manifest?")
        else:
            log.info(msg)
        for file in files:
            if not os.path.isfile(file):
                log.warn("'%s' not a regular file -- skipping", file)
            else:
                dest = os.path.join(base_dir, file)
                self.copy_file(file, dest, link=link)

        self.distribution.metadata.write_pkg_info(base_dir)

    def make_distribution(self):
        """Create the source distribution(s).  First, we create the release
        tree with 'make_release_tree()'; then, we create all required
        archive files (according to 'self.formats') from the release tree.
        Finally, we clean up by blowing away the release tree (unless
        'self.keep_temp' is true).  The list of archive files created is
        stored so it can be retrieved later by 'get_archive_files()'.
        """
        # Don't warn about missing meta-data here -- should be (and is!)
        # done elsewhere.
        base_dir = self.distribution.get_fullname()
        base_name = os.path.join(self.dist_dir, base_dir)

        self.make_release_tree(base_dir, self.filelist.files)
        archive_files = []              # remember names of files we create
        # tar archive must be created last to avoid overwrite and remove
        if 'tar' in self.formats:
            self.formats.append(self.formats.pop(self.formats.index('tar')))

        for fmt in self.formats:
            file = self.make_archive(base_name, fmt, base_dir=base_dir,
                                     owner=self.owner, group=self.group)
            archive_files.append(file)
            self.distribution.dist_files.append(('sdist', '', file))

        self.archive_files = archive_files

        if not self.keep_temp:
            dir_util.remove_tree(base_dir, dry_run=self.dry_run)

    def get_archive_files(self):
        """Return the list of archive files created when the command
        was run, or None if the command hasn't run yet.
        """
        return self.archive_files
