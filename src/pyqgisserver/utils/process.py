#
# Copyright 2026 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Multiprocessing helpers

    Starting with Python 3.14, the default multiprocessing start method
    on POSIX platforms is 'forkserver' instead of 'fork'.

    The server relies on 'fork' semantics (inherited state, non-picklable
    targets and arguments), so we force the 'fork' start method.
"""
import multiprocessing
import sys

if sys.version_info >= (3, 14):
    Process = multiprocessing.get_context('fork').Process
else:
    from multiprocessing import Process

__all__ = ['Process']
