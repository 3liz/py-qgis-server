
from collections import namedtuple
from enum import Enum

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


