""" Request logger

    Detailled log of all *incoming* requests as:
    ```
        timestamp: int
        method: str
        uri: str
        body: bytes
        headers: Dict[str, str]
    ```
"""
import json
import logging
import os

from base64 import b64encode
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from time import time
from typing import List, Optional, Tuple

from tornado.httputil import HTTPServerRequest

from pyqgisservercontrib.core.filters import policy_filter

logger = logging.getLogger('SRVLOG.request_logger')


class DataclassEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, bytes):
            return b64encode(o).decode()
        if is_dataclass(o):
            return asdict(o)
        return super().default(o)


@dataclass
class RequestData:
    timestamp: float
    method: Optional[str]
    uri: Optional[str]
    body: Optional[bytes]
    headers: List[Tuple[str, str]]


def register_filters(policy_service, *args, **kwargs):

    env = os.getenv("PY_QGIS_SERVER_REQUEST_LOG")
    if env:
        fp = Path(env).open('a')
    else:
        return

    @policy_filter()
    def request_logger(request: HTTPServerRequest) -> None:
        data = RequestData(
            timestamp=time(),
            method=request.method,
            uri=request.uri,
            body=request.body,
            headers=list(request.headers.get_all()),
        )
        print(json.dumps(data, cls=DataclassEncoder), file=fp)

    policy_service.add_filters([request_logger], pri=10000)
