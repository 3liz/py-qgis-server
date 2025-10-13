#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Dict, Mapping, NamedTuple, Optional

WORKER_READY = b"ready"

# Message structure


class RequestMessage(NamedTuple):
    query: str
    headers: Mapping[str, str]
    method: str
    data: Optional[bytes]


class ReplyMessage(NamedTuple):
    status: int
    headers: Dict[str, str]
    data: bytes
    meta: Optional[Dict[str, str]]
