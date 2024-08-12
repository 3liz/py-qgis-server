#
# Copyright 2020 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Components are a way to register objects using
    contract ids. A contract id is attached to an interface or a set
    of interface.

    It is designed to have a general way about passing objects or behaviors to plugins
    or extension or other modules. It then enables for these modules or extensions to rely on the calling
    module behaviors without the need for these to do explicit imports
"""

import logging

from collections import namedtuple
from importlib import metadata
from typing import Any, Callable, Optional, Sequence


class ComponentManagerError(Exception):
    pass


class FactoryNotFoundError(ComponentManagerError):
    pass


class NoRegisteredFactoryError(ComponentManagerError):
    pass


class EntryPointNotFoundError(ComponentManagerError):
    pass


LOGGER = logging.getLogger('SRVLOG')

FactoryEntry = namedtuple('FactoryEntry', ('create_instance', 'service'))


def _entry_points(group: str, name: Optional[str] = None) -> Sequence[metadata.EntryPoint]:
    """ Return entry points
    """
    # See https://docs.python.org/3.10/library/importlib.metadata.html
    entry_points = metadata.entry_points()
    if name:
        return entry_points.select(group=group, name=name)
    else:
        return entry_points.select(group=group)


class ComponentManager:

    def __init__(self):
        """ Component Manager
        """
        self._contractIDs = {}

    def register_entrypoints(self, category, *args, **kwargs):
        """ Load extension modules

            Loaded modules will do self-registration
        """
        for ep in _entry_points(category):
            LOGGER.info("Loading module: %s:%s", category, ep.name)
            ep.load()(*args, **kwargs)

    def load_entrypoint(self, category: str, name: str) -> Any:
        for ep in _entry_points(category, name):
            return ep.load()
        raise EntryPointNotFoundError(name)

    def register_factory(self, contractID: str, factory: Callable[[], None]):
        """ Register a factory for the given contract ID
        """
        if not callable(factory):
            raise ValueError('factory must be a callable object')

        LOGGER.debug("Registering factory: %s", contractID)
        self._contractIDs[contractID] = FactoryEntry(factory, None)

    def register_service(self, contractID: str, service: Any):
        """ Register an instance object as singleton service
        """
        def nullFactory():
            raise NoRegisteredFactoryError(contractID)

        LOGGER.debug("Registering service: %s", contractID)
        self._contractIDs[contractID] = FactoryEntry(nullFactory, service)

    def create_instance(self, contractID: str) -> Any:
        """ Create an instance of the object referenced by its
            contract id.
        """
        fe = self._contractIDs.get(contractID)
        if fe:
            return fe.create_instance()
        else:
            raise FactoryNotFoundError(contractID)

    def get_service(self, contractID: str) -> Any:
        """ Return instance object as singleton
        """
        fe = self._contractIDs.get(contractID)
        if fe is None:
            raise FactoryNotFoundError(contractID)
        if fe.service is None:
            fe = fe._replace(service=fe.create_instance())
            self._contractIDs[contractID] = fe
        return fe.service


gComponentManager = ComponentManager()


def get_service(contractID: str) -> Any:
    """ Alias to component_manager.get_service
    """
    return gComponentManager.get_service(contractID)


def create_instance(contractID: str) -> Any:
    """ Alias to component_manager.create_instance
    """
    return gComponentManager.create_instance(contractID)


def register_entrypoints(category: str, *args, **kwargs):
    """ Alias to component_manager.register_components
    """
    gComponentManager.register_entrypoints(category, *args, **kwargs)


def load_entrypoint(category: str, name: str) -> Any:
    """ Alias to component_manager.load_entrypoint
    """
    return gComponentManager.load_entrypoint(category, name)

#
# Declare factories or services with decorators
#


def register_service(contractID: str) -> Callable:
    def wrapper(obj):
        gComponentManager.register_service(contractID, obj)
        return obj
    return wrapper


def register_factory(contractID: str) -> Callable:
    def wrapper(obj):
        gComponentManager.register_factory(contractID, obj)
        return obj
    return wrapper
