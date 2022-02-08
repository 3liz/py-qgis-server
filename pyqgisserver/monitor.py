""" AMQP monitor for qgis requests
"""
import logging

from .config  import confservice

LOGGER = logging.getLogger('SRVLOG')

class Monitor:

    @classmethod
    def initialize(cls) -> 'Monitor':

        if hasattr(cls,'_instance'):
            return cls._instance

        name = confservice.get('server','monitor', fallback=None)
        service = None
        if name:
            from pyqgisservercontrib.core import componentmanager as cm
            try:
                service = cm.load_entrypoint('py_qgis_server.monitors',name).initialize()
                setattr(cls,'_instance', service)
                LOGGER.info("Using '%s' monitor service", name)
                return service
            except cm.EntryPointNotFoundError:
                LOGGER.error("Failed to load monitor component: %s", name)

