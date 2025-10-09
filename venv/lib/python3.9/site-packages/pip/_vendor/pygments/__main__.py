"""
    pygments.__main__
    ~~~~~~~~~~~~~~~~~

    Main entry point for ``python -m pygments``.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
from pip._vendor.pygments.cmdline import main

try:
    sys.exit(main(sys.argv))
except KeyboardInterrupt:
    sys.exit(1)
