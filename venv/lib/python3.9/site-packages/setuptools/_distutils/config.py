"""distutils.pypirc

Provides the PyPIRCCommand class, the base class for the command classes
that uses .pypirc in the distutils.command package.
"""
import os
from configparser import RawConfigParser

from distutils.cmd import Command

DEFAULT_PYPIRC = """\
[distutils]
index-servers =
    pypi

[pypi]
username:%s
password:%s
"""

class PyPIRCCommand(Command):
    """Base command that knows how to handle the .pypirc file
    """
    DEFAULT_REPOSITORY = 'https://upload.pypi.org/legacy/'
    DEFAULT_REALM = 'pypi'
    repository = None
    realm = None

    user_options = [
        ('repository=', 'r',
         "url of repository [default: %s]" % \
            DEFAULT_REPOSITORY),
        ('show-response', None,
         'display full response text from server')]

    boolean_options = ['show-response']

    def _get_rc_file(self):
        """Returns rc file path."""
        return os.path.join(os.path.expanduser('~'), '.pypirc')

    def _store_pypirc(self, username, password):
        """Creates a default .pypirc file."""
        rc = self._get_rc_file()
        with os.fdopen(os.open(rc, os.O_CREAT | os.O_WRONLY, 0o600), 'w') as f:
            f.write(DEFAULT_PYPIRC % (username, password))

    def _read_pypirc(self):
        """Reads the .pypirc file."""
        rc = self._get_rc_file()
        if os.path.exists(rc):
            self.announce('Using PyPI login from %s' % rc)
            repository = self.repository or self.DEFAULT_REPOSITORY

            config = RawConfigParser()
            config.read(rc)
            sections = config.sections()
            if 'distutils' in sections:
                # let's get the list of servers
                index_servers = config.get('distutils', 'index-servers')
                _servers = [server.strip() for server in
                            index_servers.split('\n')
                            if server.strip() != '']
                if _servers == []:
                    # nothing set, let's try to get the default pypi
                    if 'pypi' in sections:
                        _servers = ['pypi']
                    else:
                        # the file is not properly defined, returning
                        # an empty dict
                        return {}
                for server in _servers:
                    current = {'server': server}
                    current['username'] = config.get(server, 'username')

                    # optional params
                    for key, default in (('repository',
                                          self.DEFAULT_REPOSITORY),
                                         ('realm', self.DEFAULT_REALM),
                                         ('password', None)):
                        if config.has_option(server, key):
                            current[key] = config.get(server, key)
                        else:
                            current[key] = default

                    # work around people having "repository" for the "pypi"
                    # section of their config set to the HTTP (rather than
                    # HTTPS) URL
                    if (server == 'pypi' and
                        repository in (self.DEFAULT_REPOSITORY, 'pypi')):
                        current['repository'] = self.DEFAULT_REPOSITORY
                        return current

                    if (current['server'] == repository or
                        current['repository'] == repository):
                        return current
            elif 'server-login' in sections:
                # old format
                server = 'server-login'
                if config.has_option(server, 'repository'):
                    repository = config.get(server, 'repository')
                else:
                    repository = self.DEFAULT_REPOSITORY
                return {'username': config.get(server, 'username'),
                        'password': config.get(server, 'password'),
                        'repository': repository,
                        'server': server,
                        'realm': self.DEFAULT_REALM}

        return {}

    def _read_pypi_response(self, response):
        """Read and decode a PyPI HTTP response."""
        import cgi
        content_type = response.getheader('content-type', 'text/plain')
        encoding = cgi.parse_header(content_type)[1].get('charset', 'ascii')
        return response.read().decode(encoding)

    def initialize_options(self):
        """Initialize options."""
        self.repository = None
        self.realm = None
        self.show_response = 0

    def finalize_options(self):
        """Finalizes options."""
        if self.repository is None:
            self.repository = self.DEFAULT_REPOSITORY
        if self.realm is None:
            self.realm = self.DEFAULT_REALM
