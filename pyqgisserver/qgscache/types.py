#
# Copyright 2020 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Common cache types
"""

from enum import IntEnum


class UpdateState(IntEnum):
    UNCHANGED = 0
    INSERTED = 1
    UPDATED = 2

