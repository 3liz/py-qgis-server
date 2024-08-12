#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Dict, NamedTuple, TypeVar

WORKER_READY = b"ready"

Meta = TypeVar("Meta")

# Message structure


class RequestMessage(NamedTuple):
    query: str
    headers: Dict[str, str]
    method: str
    data: bytes


# Generic namedTuple only supported in 3.11
class ReplyMessage(NamedTuple):  # , Generic[Meta]):
    status: int
    headers: Dict[str, str]
    data: bytes
    meta: Meta
