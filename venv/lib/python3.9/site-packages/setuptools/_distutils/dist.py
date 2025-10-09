"""distutils.dist

Provides the Distribution class, which represents the module distribution
being built/installed/distributed.
"""

import sys
import os
import re
from email import message_from_file

try:
    import warnings
except ImportError:
    warnings = None

from distutils.errors import *
from distutils.fancy_getopt import FancyGetopt, translate_longopt
from distutils.util import check_environ, strtobool, rfc822_escape
from distutils import log
from distutils.debug import DEBUG

# Regex to define acceptable Distutils command names.  This is not *quite*
# the same as a Python NAME -- I don't allow leading underscores.  The fact
# that they're very similar is no coincidence; the default naming scheme is
# to look for a Python module named after the command.
command_re = re.compile(r'^[a-zA-Z]([a-zA-Z0-9_]*)$')


def _ensure_list(value, fieldname):
    if isinstance(value, str):
        # a string containing comma separated values is okay.  It will
        # be converted to a list by Distribution.finalize_options().
        pass
    elif not isinstance(value, list):
        # passing a tuple or an iterator perhaps, warn and convert
        typename = type(value).__name__
        msg = "Warning: '{fieldname}' should be a list, got type '{typename}'"
        msg = msg.format(**locals())
        log.log(log.WARN, msg)
        value = list(value)
    return value


class Distribution:
    """The core of the Distutils.  Most of the work hiding behind 'setup'
    is really done within a Distribution instance, which farms the work out
    to the Distutils commands specified on the command line.

    Setup scripts will almost never instantiate Distribution directly,
    unless the 'setup()' function is totally inadequate to their needs.
    However, it is conceivable that a setup script might wish to subclass
    Distribution for some specialized purpose, and then pass the subclass
    to 'setup()' as the 'distclass' keyword argument.  If so, it is
    necessary to respect the expectations that 'setup' has of Distribution.
    See the code for 'setup()', in core.py, for details.
    """

    # 'global_options' describes the command-line options that may be
    # supplied to the setup script prior to any actual commands.
    # Eg. "./setup.py -n" or "./setup.py --quiet" both take advantage of
    # these global options.  This list should be kept to a bare minimum,
    # since every global option is also valid as a command option -- and we
    # don't want to pollute the commands with too many options that they
    # have minimal control over.
    # The fourth entry for verbose means that it can be repeated.
    global_options = [
        ('verbose', 'v', "run verbosely (default)", 1),
        ('quiet', 'q', "run quietly (turns verbosity off)"),
        ('dry-run', 'n', "don't actually do anything"),
        ('help', 'h', "show detailed help message"),
        ('no-user-cfg', None,
            'ignore pydistutils.cfg in your home directory'),
    ]

    # 'common_usage' is a short (2-3 line) string describing the common
    # usage of the setup script.
    common_usage = """\
Common commands: (see '--help-commands' for more)

  setup.py build      will build the package underneath 'build/'
  setup.py install    will install the package
"""

    # options that are not propagated to the commands
    display_options = [
        ('help-commands', None,
         "list all available commands"),
        ('name', None,
         "print package name"),
        ('version', 'V',
         "print package version"),
        ('fullname', None,
         "print <package name>-<version>"),
        ('author', None,
         "print the author's name"),
        ('author-email', None,
         "print the author's email address"),
        ('maintainer', None,
         "print the maintainer's name"),
        ('maintainer-email', None,
         "print the maintainer's email address"),
        ('contact', None,
         "print the maintainer's name if known, else the author's"),
        ('contact-email', None,
         "print the maintainer's email address if known, else the author's"),
        ('url', None,
         "print the URL for this package"),
        ('license', None,
         "print the license of the package"),
        ('licence', None,
         "alias for --license"),
        ('description', None,
         "print the package description"),
        ('long-description', None,
         "print the long package description"),
        ('platforms', None,
         "print the list of platforms"),
        ('classifiers', None,
         "print the list of classifiers"),
        ('keywords', None,
         "print the list of keywords"),
        ('provides', None,
         "print the list of packages/modules provided"),
        ('requires', None,
         "print the list of packages/modules required"),
        ('obsoletes', None,
         "print the list of packages/modules made obsolete")
        ]
    display_option_names = [translate_longopt(x[0]) for x in display_options]

    # negative options are options that exclude other options
    negative_opt = {'quiet': 'verbose'}

    # -- Creation/initialization methods -------------------------------

    def __init__(self, attrs=None):
        """Construct a new Distribution instance: initialize all the
        attributes of a Distribution, and then use 'attrs' (a dictionary
        mapping attribute names to values) to assign some of those
        attributes their "real" values.  (Any attributes not mentioned in
        'attrs' will be assigned to some null value: 0, None, an empty list
        or dictionary, etc.)  Most importantly, initialize the
        'command_obj' attribute to the empty dictionary; this will be
        filled in with real command objects by 'parse_command_line()'.
        """

        # Default values for our command-line options
        self.verbose = 1
        self.dry_run = 0
        self.help = 0
        for attr in self.display_option_names:
            setattr(self, attr, 0)

        # Store the distribution meta-data (name, version, author, and so
        # forth) in a separate object -- we're getting to have enough
        # information here (and enough command-line options) that it's
        # worth it.  Also delegate 'get_XXX()' methods to the 'metadata'
        # object in a sneaky and underhanded (but efficient!) way.
        self.metadata = DistributionMetadata()
        for basename in self.metadata._METHOD_BASENAMES:
            method_name = "get_" + basename
            setattr(self, method_name, getattr(self.metadata, method_name))

        # 'cmdclass' maps command names to class objects, so we
        # can 1) quickly figure out which class to instantiate when
        # we need to create a new command object, and 2) have a way
        # for the setup script to override command classes
        self.cmdclass = {}

        # 'command_packages' is a list of packages in which commands
        # are searched for.  The factory for command 'foo' is expected
        # to be named 'foo' in the module 'foo' in one of the packages
        # named here.  This list is searched from the left; an error
        # is raised if no named package provides the command being
        # searched for.  (Always access using get_command_packages().)
        self.command_packages = None

        # 'script_name' and 'script_args' are usually set to sys.argv[0]
        # and sys.argv[1:], but they can be overridden when the caller is
        # not necessarily a setup script run from the command-line.
        self.script_name = None
        self.script_args = None

        # 'command_options' is where we store command options between
        # parsing them (from config files, the command-line, etc.) and when
        # they are actually needed -- ie. when the command in question is
        # instantiated.  It is a dictionary of dictionaries of 2-tuples:
        #   command_options = { command_name : { option : (source, value) } }
        self.command_options = {}

        # 'dist_files' is the list of (command, pyversion, file) that
        # have been created by any dist commands run so far. This is
        # filled regardless of whether the run is dry or not. pyversion
        # gives sysconfig.get_python_version() if the dist file is
        # specific to a Python version, 'any' if it is good for all
        # Python versions on the target platform, and '' for a source
        # file. pyversion should not be used to specify minimum or
        # maximum required Python versions; use the metainfo for that
        # instead.
        self.dist_files = []

        # These options are really the business of various commands, rather
        # than of the Distribution itself.  We provide aliases for them in
        # Distribution as a convenience to the developer.
        self.packages = None
        self.package_data = {}
        self.package_dir = None
        self.py_modules = None
        self.libraries = None
        self.headers = None
        self.ext_modules = None
        self.ext_package = None
        self.include_dirs = None
        self.extra_path = None
        self.scripts = None
        self.data_files = None
        self.password = ''

        # And now initialize bookkeeping stuff that can't be supplied by
        # the caller at all.  'command_obj' maps command names to
        # Command instances -- that's how we enforce that every command
        # class is a singleton.
        self.command_obj = {}

        # 'have_run' maps command names to boolean values; it keeps track
        # of whether we have actually run a particular command, to make it
        # cheap to "run" a command whenever we think we might need to -- if
        # it's already been done, no need for expensive filesystem
        # operations, we just check the 'have_run' dictionary and carry on.
        # It's only safe to query 'have_run' for a command class that has
        # been instantiated -- a false value will be inserted when the
        # command object is created, and replaced with a true value when
        # the command is successfully run.  Thus it's probably best to use
        # '.get()' rather than a straight lookup.
        self.have_run = {}

        # Now we'll use the attrs dictionary (ultimately, keyword args from
        # the setup script) to possibly override any or all of these
        # distribution options.

        if attrs:
            # Pull out the set of command options and work on them
            # specifically.  Note that this order guarantees that aliased
            # command options will override any supplied redundantly
            # through the general options dictionary.
            options = attrs.get('options')
            if options is not None:
                del attrs['options']
                for (command, cmd_options) in options.items():
                    opt_dict = self.get_option_dict(command)
                    for (opt, val) in cmd_options.items():
                        opt_dict[opt] = ("setup script", val)

            if 'licence' in attrs:
                attrs['license'] = attrs['licence']
                del attrs['licence']
                msg = "'licence' distribution option is deprecated; use 'license'"
                if warnings is not None:
                    warnings.warn(msg)
                else:
                    sys.stderr.write(msg + "\n")

            # Now work on the rest of the attributes.  Any attribute that's
            # not already defined is invalid!
            for (key, val) in attrs.items():
                if hasattr(self.metadata, "set_" + key):
                    getattr(self.metadata, "set_" + key)(val)
                elif hasattr(self.metadata, key):
                    setattr(self.metadata, key, val)
                elif hasattr(self, key):
                    setattr(self, key, val)
                else:
                    msg = "Unknown distribution option: %s" % repr(key)
                    warnings.warn(msg)

        # no-user-cfg is handled before other command line args
        # because other args override the config files, and this
        # one is needed before we can load the config files.
        # If attrs['script_args'] wasn't passed, assume false.
        #
        # This also make sure we just look at the global options
        self.want_user_cfg = True

        if self.script_args is not None:
            for arg in self.script_args:
                if not arg.startswith('-'):
                    break
                if arg == '--no-user-cfg':
                    self.want_user_cfg = False
                    break

        self.finalize_options()

    def get_option_dict(self, command):
        """Get the option dictionary for a given command.  If that
        command's option dictionary hasn't been created yet, then create it
        and return the new dictionary; otherwise, return the existing
        option dictionary.
        """
        dict = self.command_options.get(command)
        if dict is None:
            dict = self.command_options[command] = {}
        return dict

    def dump_option_dicts(self, header=None, commands=None, indent=""):
        from pprint import pformat

        if commands is None:             # dump all command option dicts
            commands = sorted(self.command_options.keys())

        if header is not None:
            self.announce(indent + header)
            indent = indent + "  "

        if not commands:
            self.announce(indent + "no commands known yet")
            return

        for cmd_name in commands:
            opt_dict = self.command_options.get(cmd_name)
            if opt_dict is None:
                self.announce(indent +
                              "no option dict for '%s' command" % cmd_name)
            else:
                self.announce(indent +
                              "option dict for '%s' command:" % cmd_name)
                out = pformat(opt_dict)
                for line in out.split('\n'):
                    self.announce(indent + "  " + line)

    # -- Config file finding/parsing methods ---------------------------

    def find_config_files(self):
        """Find as many configuration files as should be processed for this
        platform, and return a list of filenames in the order in which they
        should be parsed.  The filenames returned are guaranteed to exist
        (modulo nasty race conditions).

        There are three possible config files: distutils.cfg in the
        Distutils installation directory (ie. where the top-level
        Distutils __inst__.py file lives), a file in the user's home
        directory named .pydistutils.cfg on Unix and pydistutils.cfg
        on Windows/Mac; and setup.cfg in the current directory.

        The file in the user's home directory can be disabled with the
        --no-user-cfg option.
        """
        files = []
        check_environ()

        # Where to look for the system-wide Distutils config file
        sys_dir = os.path.dirname(sys.modules['distutils'].__file__)

        # Look for the system config file
        sys_file = os.path.join(sys_dir, "distutils.cfg")
        if os.path.isfile(sys_file):
            files.append(sys_file)

        # What to call the per-user config file
        if os.name == 'posix':
            user_filename = ".pydistutils.cfg"
        else:
            user_filename = "pydistutils.cfg"

        # And look for the user config file
        if self.want_user_cfg:
            user_file = os.path.join(os.path.expanduser('~'), user_filename)
            if os.path.isfile(user_file):
                files.append(user_file)

        # All platforms support local setup.cfg
        local_file = "setup.cfg"
        if os.path.isfile(local_file):
            files.append(local_file)

        if DEBUG:
            self.announce("using config files: %s" % ', '.join(files))

        return files

    def parse_config_files(self, filenames=None):
        from configparser import ConfigParser

        # Ignore install directory options if we have a venv
        if sys.prefix != sys.base_prefix:
            ignore_options = [
                'install-base', 'install-platbase', 'install-lib',
                'install-platlib', 'install-purelib', 'install-headers',
                'install-scripts', 'install-data', 'prefix', 'exec-prefix',
                'home', 'user', 'root']
        else:
            ignore_options = []

        ignore_options = frozenset(ignore_options)

        if filenames is None:
            filenames = self.find_config_files()

        if DEBUG:
            self.announce("Distribution.parse_config_files():")

        parser = ConfigParser()
        for filename in filenames:
            if DEBUG:
                self.announce("  reading %s" % filename)
            parser.read(filename)
            for section in parser.sections():
                options = parser.options(section)
                opt_dict = self.get_option_dict(section)

                for opt in options:
                    if opt != '__name__' and opt not in ignore_options:
                        val = parser.get(section,opt)
                        opt = opt.replace('-', '_')
                        opt_dict[opt] = (filename, val)

            # Make the ConfigParser forget everything (so we retain
            # the original filenames that options come from)
            parser.__init__()

        # If there was a "global" section in the config file, use it
        # to set Distribution options.

        if 'global' in self.command_options:
            for (opt, (src, val)) in self.command_options['global'].items():
                alias = self.negative_opt.get(opt)
                try:
                    if alias:
                        setattr(self, alias, not strtobool(val))
                    elif opt in ('verbose', 'dry_run'): # ugh!
                        setattr(self, opt, strtobool(val))
                    else:
                        setattr(self, opt, val)
                except ValueError as msg:
                    raise DistutilsOptionError(msg)

    # -- Command-line parsing methods ----------------------------------

    def parse_command_line(self):
        """Parse the setup script's command line, taken from the
        'script_args' instance attribute (which defaults to 'sys.argv[1:]'
        -- see 'setup()' in core.py).  This list is first processed for
        "global options" -- options that set attributes of the Distribution
        instance.  Then, it is alternately scanned for Distutils commands
        and options for that command.  Each new command terminates the
        options for the previous command.  The allowed options for a
        command are determined by the 'user_options' attribute of the
        command class -- thus, we have to be able to load command classes
        in order to parse the command line.  Any error in that 'options'
        attribute raises DistutilsGetoptError; any error on the
        command-line raises DistutilsArgError.  If no Distutils commands
        were found on the command line, raises DistutilsArgError.  Return
        true if command-line was successfully parsed and we should carry
        on with executing commands; false if no errors but we shouldn't
        execute commands (currently, this only happens if user asks for
        help).
        """
        #
        # We now have enough information to show the Macintosh dialog
        # that allows the user to interactively specify the "command line".
        #
        toplevel_options = self._get_toplevel_options()

        # We have to parse the command line a bit at a time -- global
        # options, then the first command, then its options, and so on --
        # because each command will be handled by a different class, and
        # the options that are valid for a particular class aren't known
        # until we have loaded the command class, which doesn't happen
        # until we know what the command is.

        self.commands = []
        parser = FancyGetopt(toplevel_options + self.display_options)
        parser.set_negative_aliases(self.negative_opt)
        parser.set_aliases({'licence': 'license'})
        args = parser.getopt(args=self.script_args, object=self)
        option_order = parser.get_option_order()
        log.set_verbosity(self.verbose)

        # for display options we return immediately
        if self.handle_display_options(option_order):
            return
        while args:
            args = self._parse_command_opts(parser, args)
            if args is None:            # user asked for help (and got it)
                return

        # Handle the cases of --help as a "global" option, ie.
        # "setup.py --help" and "setup.py --help command ...".  For the
        # former, we show global options (--verbose, --dry-run, etc.)
        # and display-only options (--name, --version, etc.); for the
        # latter, we omit the display-only options and show help for
        # each command listed on the command line.
        if self.help:
            self._show_help(parser,
                            display_options=len(self.commands) == 0,
                            commands=self.commands)
            return

        # Oops, no commands found -- an end-user error
        if not self.commands:
            raise DistutilsArgError("no commands supplied")

        # All is well: return true
        return True

    def _get_toplevel_options(self):
        """Return the non-display options recognized at the top level.

        This includes options that are recognized *only* at the top
        level as well as options recognized for commands.
        """
        return self.global_options + [
            ("command-packages=", None,
             "list of packages that provide distutils commands"),
            ]

    def _parse_command_opts(self, parser, args):
        """Parse the command-line options for a single command.
        'parser' must be a FancyGetopt instance; 'args' must be the list
        of arguments, starting with the current command (whose options
        we are about to parse).  Returns a new version of 'args' with
        the next command at the front of the list; will be the empty
        list if there are no more commands on the command line.  Returns
        None if the user asked for help on this command.
        """
        # late import because of mutual dependence between these modules
        from distutils.cmd import Command

        # Pull the current command from the head of the command line
        command = args[0]
        if not command_re.match(command):
            raise SystemExit("invalid command name '%s'" % command)
        self.commands.append(command)

        # Dig up the command class that implements this command, so we
        # 1) know that it's a valid command, and 2) know which options
        # it takes.
        try:
            cmd_class = self.get_command_class(command)
        except DistutilsModuleError as msg:
            raise DistutilsArgError(msg)

        # Require that the command class be derived from Command -- want
        # to be sure that the basic "command" interface is implemented.
        if not issubclass(cmd_class, Command):
            raise DistutilsClassError(
                "command class %s must subclass Command" % cmd_class)

        # Also make sure that the command object provides a list of its
        # known options.
        if not (hasattr(cmd_class, 'user_options') and
                isinstance(cmd_class.user_options, list)):
            msg = ("command class %s must provide "
                "'user_options' attribute (a list of tuples)")
            raise DistutilsClassError(msg % cmd_class)

        # If the command class has a list of negative alias options,
        # merge it in with the global negative aliases.
        negative_opt = self.negative_opt
        if hasattr(cmd_class, 'negative_opt'):
            negative_opt = negative_opt.copy()
            negative_opt.update(cmd_class.negative_opt)

        # Check for help_options in command class.  They have a different
        # format (tuple of four) so we need to preprocess them here.
        if (hasattr(cmd_class, 'help_options') and
                isinstance(cmd_class.help_options, list)):
            help_options = fix_help_options(cmd_class.help_options)
        else:
            help_options = []

        # All commands support the global options too, just by adding
        # in 'global_options'.
        parser.set_option_table(self.global_options +
                                cmd_class.user_options +
                                help_options)
        parser.set_negative_aliases(negative_opt)
        (args, opts) = parser.getopt(args[1:])
        if hasattr(opts, 'help') and opts.help:
            self._show_help(parser, display_options=0, commands=[cmd_class])
            return

        if (hasattr(cmd_class, 'help_options') and
                isinstance(cmd_class.help_options, list)):
            help_option_found=0
            for (help_option, short, desc, func) in cmd_class.help_options:
                if hasattr(opts, parser.get_attr_name(help_option)):
                    help_option_found=1
                    if callable(func):
                        func()
                    else:
                        raise DistutilsClassError(
                            "invalid help function %r for help option '%s': "
                            "must be a callable object (function, etc.)"
                            % (func, help_option))

            if help_option_found:
                return

        # Put the options from the command-line into their official
        # holding pen, the 'command_options' dictionary.
        opt_dict = self.get_option_dict(command)
        for (name, value) in vars(opts).items():
            opt_dict[name] = ("command line", value)

        return args

    def finalize_options(self):
        """Set final values for all the options on the Distribution
        instance, analogous to the .finalize_options() method of Command
        objects.
        """
        for attr in ('keywords', 'platforms'):
            value = getattr(self.metadata, attr)
            if value is None:
                continue
            if isinstance(value, str):
                value = [elm.strip() for elm in value.split(',')]
                setattr(self.metadata, attr, value)

    def _show_help(self, parser, global_options=1, display_options=1,
                   commands=[]):
        """Show help for the setup script command-line in the form of
        several lists of command-line options.  'parser' should be a
        FancyGetopt instance; do not expect it to be returned in the
        same state, as its option table will be reset to make it
        generate the correct help text.

        If 'global_options' is true, lists the global options:
        --verbose, --dry-run, etc.  If 'display_options' is true, lists
        the "display-only" options: --name, --version, etc.  Finally,
        lists per-command help for every command name or command class
        in 'commands'.
        """
        # late import because of mutual dependence between these modules
        from distutils.core import gen_usage
        from distutils.cmd import Command

        if global_options:
            if display_options:
                options = self._get_toplevel_options()
            else:
                options = self.global_options
            parser.set_option_table(options)
            parser.print_help(self.common_usage + "\nGlobal options:")
            print('')

        if display_options:
            parser.set_option_table(self.display_options)
            parser.print_help(
                "Information display options (just display " +
                "information, ignore any commands)")
            print('')

        for command in self.commands:
            if isinstance(command, type) and issubclass(command, Command):
                klass = command
            else:
                klass = self.get_command_class(command)
            if (hasattr(klass, 'help_options') and
                    isinstance(klass.help_options, list)):
                parser.set_option_table(klass.user_options +
                                        fix_help_options(klass.help_options))
            else:
                parser.set_option_table(klass.user_options)
            parser.print_help("Options for '%s' command:" % klass.__name__)
            print('')

        print(gen_usage(self.script_name))

    def handle_display_options(self, option_order):
        """If there were any non-global "display-only" options
        (--help-commands or the metadata display options) on the command
        line, display the requested info and return true; else return
        false.
        """
        from distutils.core import gen_usage

        # User just wants a list of commands -- we'll print it out and stop
        # processing now (ie. if they ran "setup --help-commands foo bar",
        # we ignore "foo bar").
        if self.help_commands:
            self.print_commands()
            print('')
            print(gen_usage(self.script_name))
            return 1

        # If user supplied any of the "display metadata" options, then
        # display that metadata in the order in which the user supplied the
        # metadata options.
        any_display_options = 0
        is_display_option = {}
        for option in self.display_options:
            is_display_option[option[0]] = 1

        for (opt, val) in option_order:
            if val and is_display_option.get(opt):
                opt = translate_longopt(opt)
                value = getattr(self.metadata, "get_"+opt)()
                if opt in ['keywords', 'platforms']:
                    print(','.join(value))
                elif opt in ('classifiers', 'provides', 'requires',
                             'obsoletes'):
                    print('\n'.join(value))
                else:
                    print(value)
                any_display_options = 1

        return any_display_options

    def print_command_list(self, commands, header, max_length):
        """Print a subset of the list of all commands -- used by
        'print_commands()'.
        """
        print(header + ":")

        for cmd in commands:
            klass = self.cmdclass.get(cmd)
            if not klass:
                klass = self.get_command_class(cmd)
            try:
                description = klass.description
            except AttributeError:
                description = "(no description available)"

            print("  %-*s  %s" % (max_length, cmd, description))

    def print_commands(self):
        """Print out a help message listing all available commands with a
        description of each.  The list is divided into "standard commands"
        (listed in distutils.command.__all__) and "extra commands"
        (mentioned in self.cmdclass, but not a standard command).  The
        descriptions come from the command class attribute
        'description'.
        """
        import distutils.command
        std_commands = distutils.command.__all__
        is_std = {}
        for cmd in std_commands:
            is_std[cmd] = 1

        extra_commands = []
        for cmd in self.cmdclass.keys():
            if not is_std.get(cmd):
                extra_commands.append(cmd)

        max_length = 0
        for cmd in (std_commands + extra_commands):
            if len(cmd) > max_length:
                max_length = len(cmd)

        self.print_command_list(std_commands,
                                "Standard commands",
                                max_length)
        if extra_commands:
            print()
            self.print_command_list(extra_commands,
                                    "Extra commands",
                                    max_length)

    def get_command_list(self):
        """Get a list of (command, description) tuples.
        The list is divided into "standard commands" (listed in
        distutils.command.__all__) and "extra commands" (mentioned in
        self.cmdclass, but not a standard command).  The descriptions come
        from the command class attribute 'description'.
        """
        # Currently this is only used on Mac OS, for the Mac-only GUI
        # Distutils interface (by Jack Jansen)
        import distutils.command
        std_commands = distutils.command.__all__
        is_std = {}
        for cmd in std_commands:
            is_std[cmd] = 1

        extra_commands = []
        for cmd in self.cmdclass.keys():
            if not is_std.get(cmd):
                extra_commands.append(cmd)

        rv = []
        for cmd in (std_commands + extra_commands):
            klass = self.cmdclass.get(cmd)
            if not klass:
                klass = self.get_command_class(cmd)
            try:
                description = klass.description
            except AttributeError:
                description = "(no description available)"
            rv.append((cmd, description))
        return rv

    # -- Command class/object methods ----------------------------------

    def get_command_packages(self):
        """Return a list of packages from which commands are loaded."""
        pkgs = self.command_packages
        if not isinstance(pkgs, list):
            if pkgs is None:
                pkgs = ''
            pkgs = [pkg.strip() for pkg in pkgs.split(',') if pkg != '']
            if "distutils.command" not in pkgs:
                pkgs.insert(0, "distutils.command")
            self.command_packages = pkgs
        return pkgs

    def get_command_class(self, command):
        """Return the class that implements the Distutils command named by
        'command'.  First we check the 'cmdclass' dictionary; if the
        command is mentioned there, we fetch the class object from the
        dictionary and return it.  Otherwise we load the command module
        ("distutils.command." + command) and fetch the command class from
        the module.  The loaded class is also stored in 'cmdclass'
        to speed future calls to 'get_command_class()'.

        Raises DistutilsModuleError if the expected module could not be
        found, or if that module does not define the expected class.
        """
        klass = self.cmdclass.get(command)
        if klass:
            return klass

        for pkgname in self.get_command_packages():
            module_name = "%s.%s" % (pkgname, command)
            klass_name = command

            try:
                __import__(module_name)
                module = sys.modules[module_name]
            except ImportError:
                continue

            try:
                klass = getattr(module, klass_name)
            except AttributeError:
                raise DistutilsModuleError(
                    "invalid command '%s' (no class '%s' in module '%s')"
                    % (command, klass_name, module_name))

            self.cmdclass[command] = klass
            return klass

        raise DistutilsModuleError("invalid command '%s'" % command)

    def get_command_obj(self, command, create=1):
        """Return the command object for 'command'.  Normally this object
        is cached on a previous call to 'get_command_obj()'; if no command
        object for 'command' is in the cache, then we either create and
        return it (if 'create' is true) or return None.
        """
        cmd_obj = self.command_obj.get(command)
        if not cmd_obj and create:
            if DEBUG:
                self.announce("Distribution.get_command_obj(): "
                              "creating '%s' command object" % command)

            klass = self.get_command_class(command)
            cmd_obj = self.command_obj[command] = klass(self)
            self.have_run[command] = 0

            # Set any options that were supplied in config files
            # or on the command line.  (NB. support for error
            # reporting is lame here: any errors aren't reported
            # until 'finalize_options()' is called, which means
            # we won't report the source of the error.)
            options = self.command_options.get(command)
            if options:
                self._set_command_options(cmd_obj, options)

        return cmd_obj

    def _set_command_options(self, command_obj, option_dict=None):
        """Set the options for 'command_obj' from 'option_dict'.  Basically
        this means copying elements of a dictionary ('option_dict') to
        attributes of an instance ('command').

        'command_obj' must be a Command instance.  If 'option_dict' is not
        supplied, uses the standard option dictionary for this command
        (from 'self.command_options').
        """
        command_name = command_obj.get_command_name()
        if option_dict is None:
            option_dict = self.get_option_dict(command_name)

        if DEBUG:
            self.announce("  setting options for '%s' command:" % command_name)
        for (option, (source, value)) in option_dict.items():
            if DEBUG:
                self.announce("    %s = %s (from %s)" % (option, value,
                                                         source))
            try:
                bool_opts = [translate_longopt(o)
                             for o in command_obj.boolean_options]
            except AttributeError:
                bool_opts = []
            try:
                neg_opt = command_obj.negative_opt
            except AttributeError:
                neg_opt = {}

            try:
                is_string = isinstance(value, str)
                if option in neg_opt and is_string:
                    setattr(command_obj, neg_opt[option], not strtobool(value))
                elif option in bool_opts and is_string:
                    setattr(command_obj, option, strtobool(value))
                elif hasattr(command_obj, option):
                    setattr(command_obj, option, value)
                else:
                    raise DistutilsOptionError(
                        "error in %s: command '%s' has no such option '%s'"
                        % (source, command_name, option))
            except ValueError as msg:
                raise DistutilsOptionError(msg)

    def reinitialize_command(self, command, reinit_subcommands=0):
        """Reinitializes a command to the state it was in when first
        returned by 'get_command_obj()': ie., initialized but not yet
        finalized.  This provides the opportunity to sneak option
        values in programmatically, overriding or supplementing
        user-supplied values from the config files and command line.
        You'll have to re-finalize the command object (by calling
        'finalize_options()' or 'ensure_finalized()') before using it for
        real.

        'command' should be a command name (string) or command object.  If
        'reinit_subcommands' is true, also reinitializes the command's
        sub-commands, as declared by the 'sub_commands' class attribute (if
        it has one).  See the "install" command for an example.  Only
        reinitializes the sub-commands that actually matter, ie. those
        whose test predicates return true.

        Returns the reinitialized command object.
        """
        from distutils.cmd import Command
        if not isinstance(command, Command):
            command_name = command
            command = self.get_command_obj(command_name)
        else:
            command_name = command.get_command_name()

        if not command.finalized:
            return command
        command.initialize_options()
        command.finalized = 0
        self.have_run[command_name] = 0
        self._set_command_options(command)

        if reinit_subcommands:
            for sub in command.get_sub_commands():
                self.reinitialize_command(sub, reinit_subcommands)

        return command

    # -- Methods that operate on the Distribution ----------------------

    def announce(self, msg, level=log.INFO):
        log.log(level, msg)

    def run_commands(self):
        """Run each command that was seen on the setup script command line.
        Uses the list of commands found and cache of command objects
        created by 'get_command_obj()'.
        """
        for cmd in self.commands:
            self.run_command(cmd)

    # -- Methods that operate on its Commands --------------------------

    def run_command(self, command):
        """Do whatever it takes to run a command (including nothing at all,
        if the command has already been run).  Specifically: if we have
        already created and run the command named by 'command', return
        silently without doing anything.  If the command named by 'command'
        doesn't even have a command object yet, create one.  Then invoke
        'run()' on that command object (or an existing one).
        """
        # Already been here, done that? then return silently.
        if self.have_run.get(command):
            return

        log.info("running %s", command)
        cmd_obj = self.get_command_obj(command)
        cmd_obj.ensure_finalized()
        cmd_obj.run()
        self.have_run[command] = 1

    # -- Distribution query methods ------------------------------------

    def has_pure_modules(self):
        return len(self.packages or self.py_modules or []) > 0

    def has_ext_modules(self):
        return self.ext_modules and len(self.ext_modules) > 0

    def has_c_libraries(self):
        return self.libraries and len(self.libraries) > 0

    def has_modules(self):
        return self.has_pure_modules() or self.has_ext_modules()

    def has_headers(self):
        return self.headers and len(self.headers) > 0

    def has_scripts(self):
        return self.scripts and len(self.scripts) > 0

    def has_data_files(self):
        return self.data_files and len(self.data_files) > 0

    def is_pure(self):
        return (self.has_pure_modules() and
                not self.has_ext_modules() and
                not self.has_c_libraries())

    # -- Metadata query methods ----------------------------------------

    # If you're looking for 'get_name()', 'get_version()', and so forth,
    # they are defined in a sneaky way: the constructor binds self.get_XXX
    # to self.metadata.get_XXX.  The actual code is in the
    # DistributionMetadata class, below.

class DistributionMetadata:
    """Dummy class to hold the distribution meta-data: name, version,
    author, and so forth.
    """

    _METHOD_BASENAMES = ("name", "version", "author", "author_email",
                         "maintainer", "maintainer_email", "url",
                         "license", "description", "long_description",
                         "keywords", "platforms", "fullname", "contact",
                         "contact_email", "classifiers", "download_url",
                         # PEP 314
                         "provides", "requires", "obsoletes",
                         )

    def __init__(self, path=None):
        if path is not None:
            self.read_pkg_file(open(path))
        else:
            self.name = None
            self.version = None
            self.author = None
            self.author_email = None
            self.maintainer = None
            self.maintainer_email = None
            self.url = None
            self.license = None
            self.description = None
            self.long_description = None
            self.keywords = None
            self.platforms = None
            self.classifiers = None
            self.download_url = None
            # PEP 314
            self.provides = None
            self.requires = None
            self.obsoletes = None

    def read_pkg_file(self, file):
        """Reads the metadata values from a file object."""
        msg = message_from_file(file)

        def _read_field(name):
            value = msg[name]
            if value == 'UNKNOWN':
                return None
            return value

        def _read_list(name):
            values = msg.get_all(name, None)
            if values == []:
                return None
            return values

        metadata_version = msg['metadata-version']
        self.name = _read_field('name')
        self.version = _read_field('version')
        self.description = _read_field('summary')
        # we are filling author only.
        self.author = _read_field('author')
        self.maintainer = None
        self.author_email = _read_field('author-email')
        self.maintainer_email = None
        self.url = _read_field('home-page')
        self.license = _read_field('license')

        if 'download-url' in msg:
            self.download_url = _read_field('download-url')
        else:
            self.download_url = None

        self.long_description = _read_field('description')
        self.description = _read_field('summary')

        if 'keywords' in msg:
            self.keywords = _read_field('keywords').split(',')

        self.platforms = _read_list('platform')
        self.classifiers = _read_list('classifier')

        # PEP 314 - these fields only exist in 1.1
        if metadata_version == '1.1':
            self.requires = _read_list('requires')
            self.provides = _read_list('provides')
            self.obsoletes = _read_list('obsoletes')
        else:
            self.requires = None
            self.provides = None
            self.obsoletes = None

    def write_pkg_info(self, base_dir):
        """Write the PKG-INFO file into the release tree.
        """
        with open(os.path.join(base_dir, 'PKG-INFO'), 'w',
                  encoding='UTF-8') as pkg_info:
            self.write_pkg_file(pkg_info)

    def write_pkg_file(self, file):
        """Write the PKG-INFO format data to a file object.
        """
        version = '1.0'
        if (self.provides or self.requires or self.obsoletes or
                self.classifiers or self.download_url):
            version = '1.1'

        file.write('Metadata-Version: %s\n' % version)
        file.write('Name: %s\n' % self.get_name())
        file.write('Version: %s\n' % self.get_version())
        file.write('Summary: %s\n' % self.get_description())
        file.write('Home-page: %s\n' % self.get_url())
        file.write('Author: %s\n' % self.get_contact())
        file.write('Author-email: %s\n' % self.get_contact_email())
        file.write('License: %s\n' % self.get_license())
        if self.download_url:
            file.write('Download-URL: %s\n' % self.download_url)

        long_desc = rfc822_escape(self.get_long_description())
        file.write('Description: %s\n' % long_desc)

        keywords = ','.join(self.get_keywords())
        if keywords:
            file.write('Keywords: %s\n' % keywords)

        self._write_list(file, 'Platform', self.get_platforms())
        self._write_list(file, 'Classifier', self.get_classifiers())

        # PEP 314
        self._write_list(file, 'Requires', self.get_requires())
        self._write_list(file, 'Provides', self.get_provides())
        self._write_list(file, 'Obsoletes', self.get_obsoletes())

    def _write_list(self, file, name, values):
        for value in values:
            file.write('%s: %s\n' % (name, value))

    # -- Metadata query methods ----------------------------------------

    def get_name(self):
        return self.name or "UNKNOWN"

    def get_version(self):
        return self.version or "0.0.0"

    def get_fullname(self):
        return "%s-%s" % (self.get_name(), self.get_version())

    def get_author(self):
        return self.author or "UNKNOWN"

    def get_author_email(self):
        return self.author_email or "UNKNOWN"

    def get_maintainer(self):
        return self.maintainer or "UNKNOWN"

    def get_maintainer_email(self):
        return self.maintainer_email or "UNKNOWN"

    def get_contact(self):
        return self.maintainer or self.author or "UNKNOWN"

    def get_contact_email(self):
        return self.maintainer_email or self.author_email or "UNKNOWN"

    def get_url(self):
        return self.url or "UNKNOWN"

    def get_license(self):
        return self.license or "UNKNOWN"
    get_licence = get_license

    def get_description(self):
        return self.description or "UNKNOWN"

    def get_long_description(self):
        return self.long_description or "UNKNOWN"

    def get_keywords(self):
        return self.keywords or []

    def set_keywords(self, value):
        self.keywords = _ensure_list(value, 'keywords')

    def get_platforms(self):
        return self.platforms or ["UNKNOWN"]

    def set_platforms(self, value):
        self.platforms = _ensure_list(value, 'platforms')

    def get_classifiers(self):
        return self.classifiers or []

    def set_classifiers(self, value):
        self.classifiers = _ensure_list(value, 'classifiers')

    def get_download_url(self):
        return self.download_url or "UNKNOWN"

    # PEP 314
    def get_requires(self):
        return self.requires or []

    def set_requires(self, value):
        import distutils.versionpredicate
        for v in value:
            distutils.versionpredicate.VersionPredicate(v)
        self.requires = list(value)

    def get_provides(self):
        return self.provides or []

    def set_provides(self, value):
        value = [v.strip() for v in value]
        for v in value:
            import distutils.versionpredicate
            distutils.versionpredicate.split_provision(v)
        self.provides = value

    def get_obsoletes(self):
        return self.obsoletes or []

    def set_obsoletes(self, value):
        import distutils.versionpredicate
        for v in value:
            distutils.versionpredicate.VersionPredicate(v)
        self.obsoletes = list(value)

def fix_help_options(options):
    """Convert a 4-tuple 'help_options' list as found in various command
    classes to the 3-tuple form required by FancyGetopt.
    """
    new_options = []
    for help_tuple in options:
        new_options.append(help_tuple[0:3])
    return new_options
