""" Monitor utilities
"""
import os

from abc import ABC, abstractmethod
from typing import (
    Any,
    Dict,
    Iterator,
    Tuple,
)

TAG_PREFIX_LEGACY = 'AMQP_GLOBAL_TAG_'
TAG_PREFIX = 'QGSRV_MONITOR_TAG_'


def _get_tags(prefix: str) -> Iterator[Tuple[str, str]]:
    return ((e.partition(prefix)[2], os.environ[e]) for e in os.environ if e.startswith(prefix))


class MonitorABC(ABC):

    def __init__(self):
        """ Return tags defined in environment
        """
        # Get global tags
        tags = {t: v for (t, v) in _get_tags(TAG_PREFIX) if t}
        tags.update((t, v) for (t, v) in _get_tags(TAG_PREFIX_LEGACY) if t)
        self.global_tags = tags

    @abstractmethod
    def emit(self, params: Dict[str, Any], meta: Dict[str, str]) -> None:
        raise NotImplementedError("Subclasses must implement this")
