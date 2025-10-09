# -*- coding: utf-8 -*-
#
# Copyright (C) 2012-2024 Vinay Sajip.
# Licensed to the Python Software Foundation under a contributor agreement.
# See LICENSE.txt and CONTRIBUTORS.txt.
#
import logging

__version__ = '0.4.0'


class DistlibException(Exception):
    pass


try:
    from logging import NullHandler
except ImportError:  # pragma: no cover

    class NullHandler(logging.Handler):

        def handle(self, record):
            pass

        def emit(self, record):
            pass

        def createLock(self):
            self.lock = None


logger = logging.getLogger(__name__)
logger.addHandler(NullHandler())
