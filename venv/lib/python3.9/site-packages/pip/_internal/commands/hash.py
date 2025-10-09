import hashlib
import logging
import sys
from optparse import Values

from pip._internal.cli.base_command import Command
from pip._internal.cli.status_codes import ERROR, SUCCESS
from pip._internal.utils.hashes import FAVORITE_HASH, STRONG_HASHES
from pip._internal.utils.misc import read_chunks, write_output

logger = logging.getLogger(__name__)


class HashCommand(Command):
    """
    Compute a hash of a local package archive.

    These can be used with --hash in a requirements file to do repeatable
    installs.
    """

    usage = "%prog [options] <file> ..."
    ignore_require_venv = True

    def add_options(self) -> None:
        self.cmd_opts.add_option(
            "-a",
            "--algorithm",
            dest="algorithm",
            choices=STRONG_HASHES,
            action="store",
            default=FAVORITE_HASH,
            help="The hash algorithm to use: one of {}".format(
                ", ".join(STRONG_HASHES)
            ),
        )
        self.parser.insert_option_group(0, self.cmd_opts)

    def run(self, options: Values, args: list[str]) -> int:
        if not args:
            self.parser.print_usage(sys.stderr)
            return ERROR

        algorithm = options.algorithm
        for path in args:
            write_output(
                "%s:\n--hash=%s:%s", path, algorithm, _hash_of_file(path, algorithm)
            )
        return SUCCESS


def _hash_of_file(path: str, algorithm: str) -> str:
    """Return the hash digest of a file."""
    with open(path, "rb") as archive:
        hash = hashlib.new(algorithm)
        for chunk in read_chunks(archive):
            hash.update(chunk)
    return hash.hexdigest()
