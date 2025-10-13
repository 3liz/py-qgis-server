""" AMQP monitor for qgis requests
"""
import logging

from typing import Optional

from .config import confservice
from .monitors.base import MonitorABC

LOGGER = logging.getLogger('SRVLOG')


class Monitor:

    @classmethod
    def instance(cls) -> Optional[MonitorABC]:

        if hasattr(cls, '_instance'):
            return cls._instance

        name = confservice.get('server', 'monitor', fallback=None)
        service = None
        if name:
            from pyqgisservercontrib.core import componentmanager as cm
            try:
                service = cm.load_entrypoint('py_qgis_server.monitors', name).initialize()
                setattr(cls, '_instance', service)
                LOGGER.info("Using '%s' monitor service", name)
            except cm.EntryPointNotFoundError:
                LOGGER.error("Failed to load monitor component: %s", name)

        return service
