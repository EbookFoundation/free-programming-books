"""distutils

The main package for the Python Module Distribution Utilities.  Normally
used from a setup script as

   from distutils.core import setup

   setup (...)
"""

import sys

__version__ = sys.version[:sys.version.index(' ')]

local = True
