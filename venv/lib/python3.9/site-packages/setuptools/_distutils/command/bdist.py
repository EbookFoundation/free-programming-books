"""distutils.command.bdist

Implements the Distutils 'bdist' command (create a built [binary]
distribution)."""

import os
from distutils.core import Command
from distutils.errors import *
from distutils.util import get_platform


def show_formats():
    """Print list of available formats (arguments to "--format" option).
    """
    from distutils.fancy_getopt import FancyGetopt
    formats = []
    for format in bdist.format_commands:
        formats.append(("formats=" + format, None,
                        bdist.format_command[format][1]))
    pretty_printer = FancyGetopt(formats)
    pretty_printer.print_help("List of available distribution formats:")


class bdist(Command):

    description = "create a built (binary) distribution"

    user_options = [('bdist-base=', 'b',
                     "temporary directory for creating built distributions"),
                    ('plat-name=', 'p',
                     "platform name to embed in generated filenames "
                     "(default: %s)" % get_platform()),
                    ('formats=', None,
                     "formats for distribution (comma-separated list)"),
                    ('dist-dir=', 'd',
                     "directory to put final built distributions in "
                     "[default: dist]"),
                    ('skip-build', None,
                     "skip rebuilding everything (for testing/debugging)"),
                    ('owner=', 'u',
                     "Owner name used when creating a tar file"
                     " [default: current user]"),
                    ('group=', 'g',
                     "Group name used when creating a tar file"
                     " [default: current group]"),
                   ]

    boolean_options = ['skip-build']

    help_options = [
        ('help-formats', None,
         "lists available distribution formats", show_formats),
        ]

    # The following commands do not take a format option from bdist
    no_format_option = ('bdist_rpm',)

    # This won't do in reality: will need to distinguish RPM-ish Linux,
    # Debian-ish Linux, Solaris, FreeBSD, ..., Windows, Mac OS.
    default_format = {'posix': 'gztar',
                      'nt': 'zip'}

    # Establish the preferred order (for the --help-formats option).
    format_commands = ['rpm', 'gztar', 'bztar', 'xztar', 'ztar', 'tar',
                       'wininst', 'zip', 'msi']

    # And the real information.
    format_command = {'rpm':   ('bdist_rpm',  "RPM distribution"),
                      'gztar': ('bdist_dumb', "gzip'ed tar file"),
                      'bztar': ('bdist_dumb', "bzip2'ed tar file"),
                      'xztar': ('bdist_dumb', "xz'ed tar file"),
                      'ztar':  ('bdist_dumb', "compressed tar file"),
                      'tar':   ('bdist_dumb', "tar file"),
                      'wininst': ('bdist_wininst',
                                  "Windows executable installer"),
                      'zip':   ('bdist_dumb', "ZIP file"),
                      'msi':   ('bdist_msi',  "Microsoft Installer")
                      }


    def initialize_options(self):
        self.bdist_base = None
        self.plat_name = None
        self.formats = None
        self.dist_dir = None
        self.skip_build = 0
        self.group = None
        self.owner = None

    def finalize_options(self):
        # have to finalize 'plat_name' before 'bdist_base'
        if self.plat_name is None:
            if self.skip_build:
                self.plat_name = get_platform()
            else:
                self.plat_name = self.get_finalized_command('build').plat_name

        # 'bdist_base' -- parent of per-built-distribution-format
        # temporary directories (eg. we'll probably have
        # "build/bdist.<plat>/dumb", "build/bdist.<plat>/rpm", etc.)
        if self.bdist_base is None:
            build_base = self.get_finalized_command('build').build_base
            self.bdist_base = os.path.join(build_base,
                                           'bdist.' + self.plat_name)

        self.ensure_string_list('formats')
        if self.formats is None:
            try:
                self.formats = [self.default_format[os.name]]
            except KeyError:
                raise DistutilsPlatformError(
                      "don't know how to create built distributions "
                      "on platform %s" % os.name)

        if self.dist_dir is None:
            self.dist_dir = "dist"

    def run(self):
        # Figure out which sub-commands we need to run.
        commands = []
        for format in self.formats:
            try:
                commands.append(self.format_command[format][0])
            except KeyError:
                raise DistutilsOptionError("invalid format '%s'" % format)

        # Reinitialize and run each command.
        for i in range(len(self.formats)):
            cmd_name = commands[i]
            sub_cmd = self.reinitialize_command(cmd_name)
            if cmd_name not in self.no_format_option:
                sub_cmd.format = self.formats[i]

            # passing the owner and group names for tar archiving
            if cmd_name == 'bdist_dumb':
                sub_cmd.owner = self.owner
                sub_cmd.group = self.group

            # If we're going to need to run this command again, tell it to
            # keep its temporary files around so subsequent runs go faster.
            if cmd_name in commands[i+1:]:
                sub_cmd.keep_temp = 1
            self.run_command(cmd_name)
