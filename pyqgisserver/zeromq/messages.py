#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from collections import namedtuple

WORKER_READY=b"ready"

# Message structure

RequestMessage = namedtuple( "RequestMessage", (
    "query",
    "headers",
    "method",
    "data"
))


ReplyMessage = namedtuple( "ReplyMessage", (
    "status",
    "headers",
    "data",
))


