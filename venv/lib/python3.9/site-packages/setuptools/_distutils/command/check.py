"""distutils.command.check

Implements the Distutils 'check' command.
"""
from distutils.core import Command
from distutils.errors import DistutilsSetupError

try:
    # docutils is installed
    from docutils.utils import Reporter
    from docutils.parsers.rst import Parser
    from docutils import frontend
    from docutils import nodes

    class SilentReporter(Reporter):

        def __init__(self, source, report_level, halt_level, stream=None,
                     debug=0, encoding='ascii', error_handler='replace'):
            self.messages = []
            Reporter.__init__(self, source, report_level, halt_level, stream,
                              debug, encoding, error_handler)

        def system_message(self, level, message, *children, **kwargs):
            self.messages.append((level, message, children, kwargs))
            return nodes.system_message(message, level=level,
                                        type=self.levels[level],
                                        *children, **kwargs)

    HAS_DOCUTILS = True
except Exception:
    # Catch all exceptions because exceptions besides ImportError probably
    # indicate that docutils is not ported to Py3k.
    HAS_DOCUTILS = False

class check(Command):
    """This command checks the meta-data of the package.
    """
    description = ("perform some checks on the package")
    user_options = [('metadata', 'm', 'Verify meta-data'),
                    ('restructuredtext', 'r',
                     ('Checks if long string meta-data syntax '
                      'are reStructuredText-compliant')),
                    ('strict', 's',
                     'Will exit with an error if a check fails')]

    boolean_options = ['metadata', 'restructuredtext', 'strict']

    def initialize_options(self):
        """Sets default values for options."""
        self.restructuredtext = 0
        self.metadata = 1
        self.strict = 0
        self._warnings = 0

    def finalize_options(self):
        pass

    def warn(self, msg):
        """Counts the number of warnings that occurs."""
        self._warnings += 1
        return Command.warn(self, msg)

    def run(self):
        """Runs the command."""
        # perform the various tests
        if self.metadata:
            self.check_metadata()
        if self.restructuredtext:
            if HAS_DOCUTILS:
                self.check_restructuredtext()
            elif self.strict:
                raise DistutilsSetupError('The docutils package is needed.')

        # let's raise an error in strict mode, if we have at least
        # one warning
        if self.strict and self._warnings > 0:
            raise DistutilsSetupError('Please correct your package.')

    def check_metadata(self):
        """Ensures that all required elements of meta-data are supplied.

        Required fields:
            name, version, URL

        Recommended fields:
            (author and author_email) or (maintainer and maintainer_email))

        Warns if any are missing.
        """
        metadata = self.distribution.metadata

        missing = []
        for attr in ('name', 'version', 'url'):
            if not (hasattr(metadata, attr) and getattr(metadata, attr)):
                missing.append(attr)

        if missing:
            self.warn("missing required meta-data: %s"  % ', '.join(missing))
        if metadata.author:
            if not metadata.author_email:
                self.warn("missing meta-data: if 'author' supplied, " +
                          "'author_email' should be supplied too")
        elif metadata.maintainer:
            if not metadata.maintainer_email:
                self.warn("missing meta-data: if 'maintainer' supplied, " +
                          "'maintainer_email' should be supplied too")
        else:
            self.warn("missing meta-data: either (author and author_email) " +
                      "or (maintainer and maintainer_email) " +
                      "should be supplied")

    def check_restructuredtext(self):
        """Checks if the long string fields are reST-compliant."""
        data = self.distribution.get_long_description()
        for warning in self._check_rst_data(data):
            line = warning[-1].get('line')
            if line is None:
                warning = warning[1]
            else:
                warning = '%s (line %s)' % (warning[1], line)
            self.warn(warning)

    def _check_rst_data(self, data):
        """Returns warnings when the provided data doesn't compile."""
        # the include and csv_table directives need this to be a path
        source_path = self.distribution.script_name or 'setup.py'
        parser = Parser()
        settings = frontend.OptionParser(components=(Parser,)).get_default_values()
        settings.tab_width = 4
        settings.pep_references = None
        settings.rfc_references = None
        reporter = SilentReporter(source_path,
                          settings.report_level,
                          settings.halt_level,
                          stream=settings.warning_stream,
                          debug=settings.debug,
                          encoding=settings.error_encoding,
                          error_handler=settings.error_encoding_error_handler)

        document = nodes.document(settings, reporter, source=source_path)
        document.note_source(source_path, -1)
        try:
            parser.parse(data, document)
        except AttributeError as e:
            reporter.messages.append(
                (-1, 'Could not finish the parsing: %s.' % e, '', {}))

        return reporter.messages
