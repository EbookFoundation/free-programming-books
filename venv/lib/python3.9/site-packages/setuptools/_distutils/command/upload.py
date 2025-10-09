"""
distutils.command.upload

Implements the Distutils 'upload' subcommand (upload package to a package
index).
"""

import os
import io
import hashlib
from base64 import standard_b64encode
from urllib.request import urlopen, Request, HTTPError
from urllib.parse import urlparse
from distutils.errors import DistutilsError, DistutilsOptionError
from distutils.core import PyPIRCCommand
from distutils.spawn import spawn
from distutils import log


# PyPI Warehouse supports MD5, SHA256, and Blake2 (blake2-256)
# https://bugs.python.org/issue40698
_FILE_CONTENT_DIGESTS = {
    "md5_digest": getattr(hashlib, "md5", None),
    "sha256_digest": getattr(hashlib, "sha256", None),
    "blake2_256_digest": getattr(hashlib, "blake2b", None),
}


class upload(PyPIRCCommand):

    description = "upload binary package to PyPI"

    user_options = PyPIRCCommand.user_options + [
        ('sign', 's',
         'sign files to upload using gpg'),
        ('identity=', 'i', 'GPG identity used to sign files'),
        ]

    boolean_options = PyPIRCCommand.boolean_options + ['sign']

    def initialize_options(self):
        PyPIRCCommand.initialize_options(self)
        self.username = ''
        self.password = ''
        self.show_response = 0
        self.sign = False
        self.identity = None

    def finalize_options(self):
        PyPIRCCommand.finalize_options(self)
        if self.identity and not self.sign:
            raise DistutilsOptionError(
                "Must use --sign for --identity to have meaning"
            )
        config = self._read_pypirc()
        if config != {}:
            self.username = config['username']
            self.password = config['password']
            self.repository = config['repository']
            self.realm = config['realm']

        # getting the password from the distribution
        # if previously set by the register command
        if not self.password and self.distribution.password:
            self.password = self.distribution.password

    def run(self):
        if not self.distribution.dist_files:
            msg = ("Must create and upload files in one command "
                   "(e.g. setup.py sdist upload)")
            raise DistutilsOptionError(msg)
        for command, pyversion, filename in self.distribution.dist_files:
            self.upload_file(command, pyversion, filename)

    def upload_file(self, command, pyversion, filename):
        # Makes sure the repository URL is compliant
        schema, netloc, url, params, query, fragments = \
            urlparse(self.repository)
        if params or query or fragments:
            raise AssertionError("Incompatible url %s" % self.repository)

        if schema not in ('http', 'https'):
            raise AssertionError("unsupported schema " + schema)

        # Sign if requested
        if self.sign:
            gpg_args = ["gpg", "--detach-sign", "-a", filename]
            if self.identity:
                gpg_args[2:2] = ["--local-user", self.identity]
            spawn(gpg_args,
                  dry_run=self.dry_run)

        # Fill in the data - send all the meta-data in case we need to
        # register a new release
        f = open(filename,'rb')
        try:
            content = f.read()
        finally:
            f.close()

        meta = self.distribution.metadata
        data = {
            # action
            ':action': 'file_upload',
            'protocol_version': '1',

            # identify release
            'name': meta.get_name(),
            'version': meta.get_version(),

            # file content
            'content': (os.path.basename(filename),content),
            'filetype': command,
            'pyversion': pyversion,

            # additional meta-data
            'metadata_version': '1.0',
            'summary': meta.get_description(),
            'home_page': meta.get_url(),
            'author': meta.get_contact(),
            'author_email': meta.get_contact_email(),
            'license': meta.get_licence(),
            'description': meta.get_long_description(),
            'keywords': meta.get_keywords(),
            'platform': meta.get_platforms(),
            'classifiers': meta.get_classifiers(),
            'download_url': meta.get_download_url(),
            # PEP 314
            'provides': meta.get_provides(),
            'requires': meta.get_requires(),
            'obsoletes': meta.get_obsoletes(),
            }

        data['comment'] = ''

        # file content digests
        for digest_name, digest_cons in _FILE_CONTENT_DIGESTS.items():
            if digest_cons is None:
                continue
            try:
                data[digest_name] = digest_cons(content).hexdigest()
            except ValueError:
                # hash digest not available or blocked by security policy
                pass

        if self.sign:
            with open(filename + ".asc", "rb") as f:
                data['gpg_signature'] = (os.path.basename(filename) + ".asc",
                                         f.read())

        # set up the authentication
        user_pass = (self.username + ":" + self.password).encode('ascii')
        # The exact encoding of the authentication string is debated.
        # Anyway PyPI only accepts ascii for both username or password.
        auth = "Basic " + standard_b64encode(user_pass).decode('ascii')

        # Build up the MIME payload for the POST data
        boundary = '--------------GHSKFJDLGDS7543FJKLFHRE75642756743254'
        sep_boundary = b'\r\n--' + boundary.encode('ascii')
        end_boundary = sep_boundary + b'--\r\n'
        body = io.BytesIO()
        for key, value in data.items():
            title = '\r\nContent-Disposition: form-data; name="%s"' % key
            # handle multiple entries for the same name
            if not isinstance(value, list):
                value = [value]
            for value in value:
                if type(value) is tuple:
                    title += '; filename="%s"' % value[0]
                    value = value[1]
                else:
                    value = str(value).encode('utf-8')
                body.write(sep_boundary)
                body.write(title.encode('utf-8'))
                body.write(b"\r\n\r\n")
                body.write(value)
        body.write(end_boundary)
        body = body.getvalue()

        msg = "Submitting %s to %s" % (filename, self.repository)
        self.announce(msg, log.INFO)

        # build the Request
        headers = {
            'Content-type': 'multipart/form-data; boundary=%s' % boundary,
            'Content-length': str(len(body)),
            'Authorization': auth,
        }

        request = Request(self.repository, data=body,
                          headers=headers)
        # send the data
        try:
            result = urlopen(request)
            status = result.getcode()
            reason = result.msg
        except HTTPError as e:
            status = e.code
            reason = e.msg
        except OSError as e:
            self.announce(str(e), log.ERROR)
            raise

        if status == 200:
            self.announce('Server response (%s): %s' % (status, reason),
                          log.INFO)
            if self.show_response:
                text = self._read_pypi_response(result)
                msg = '\n'.join(('-' * 75, text, '-' * 75))
                self.announce(msg, log.INFO)
        else:
            msg = 'Upload failed (%s): %s' % (status, reason)
            self.announce(msg, log.ERROR)
            raise DistutilsError(msg)
