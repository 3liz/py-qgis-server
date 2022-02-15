#
# Copyright 2022 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Cache observer for triggers

    The observer aggregate update notifications from 
    all workers, it prevents triggering the same update
    multiple times.
"""
import os
import asyncio
import zmq.asyncio
import zmq
import traceback
import logging

from datetime import datetime
from typing import Awaitable, Any, NamedTuple

from ..zeromq.utils import _get_ipc
from ..config  import confservice
from .types import UpdateState


LOGGER=logging.getLogger('SRVLOG')


class _CacheUpdate(NamedTuple):
    modified_time: datetime
    status: UpdateState


class Client:

    def __init__(self) -> None:
        """ Cache observer client
        """
        address = _get_ipc('cache_observer')

        ctx = zmq.Context.instance()
        self._sock = ctx.socket(zmq.PUSH)
        self._sock.setsockopt(zmq.IMMEDIATE, 1) # Do no queue if no connection
        self._sock.connect(address)
        self._pid = os.getpid()

    def _send(self, data: Any ) -> None: 
        try:
            self._sock.send_pyobj((self._pid, data), flags=zmq.DONTWAIT)
        except zmq.ZMQError as err:
            if err.errno != zmq.EAGAIN:
                LOGGER.error("%s (%s)", zmq.strerror(err.errno), err.errno)

    def close(self) -> None:
        self._sock.close()

    def observe(self, key: str, modified_time: datetime, state: UpdateState):
        """
        """
        self._send((key,modified_time,state))
        

class Server:

    _declared_observers = []

    @classmethod
    def declare_observers(cls):
        """ Check out observers

            must be done before forking workers since
            we want to make aware of the observers situation
        """
        names = (name.strip() for name in confservice.get('projects.cache','observers', fallback="").split(','))
        cls._declared_observers = list(name for name in names if name)

        confservice.set('projects.cache','has_observers', 'yes' if cls._declared_observers else 'no')

    def __init__(self)-> None:
        """ Run Observer

            :param timeout: timeout delay in seconds
        """
        address = _get_ipc('cache_observer')

        self._observers = []
        self._stopped = True
        self._task = None
        self._last_updates = {}

        if self._declared_observers:
            self._load_observers()
            ctx = zmq.asyncio.Context.instance()
            self._sock = ctx.socket(zmq.PULL)
            self._sock.setsockopt(zmq.RCVTIMEO, 1000)
            self._sock.bind( address )
        else:
            self._sock = None

    def _load_observers(self):
        """ Load registered triggers
        """
        from pyqgisservercontrib.core import componentmanager as cm
        def _load_observers():
            for name in self._declared_observers:
                try:
                    LOGGER.debug("*** Loading cache observer '%s'", name)
                    observer = cm.load_entrypoint('py_qgis_server.cache.observers',name)
                    observer.init()
                    yield observer
                except cm.EntryPointNotFoundError:
                    LOGGER.error("Failed to load cache trigger component: %s", name)

        self._observers = list(_load_observers())

    def run(self) -> None:
        if self._observers:
            self._task = asyncio.ensure_future(self._run_async())

    async def _run_async(self) -> Awaitable[None]:
        """ Run supervisor
        """
        self._stopped = False

        while not self._stopped:
            try:
                pid, (key, modified_time, state) = await self._sock.recv_pyobj()
                LOGGER.debug("*** CACHE OBSERVER: Received update %s for key %s from pid %s", state, key, pid)
               
                # Check if an entry exists already 
                entry = self._last_updates.get(key)
                if entry:
                    do_notify = entry.modified_time < modified_time
                else:
                    # Do trigger in all cases (UPDATED, INSERTED)
                    do_notify = True

                # Update entry
                self._last_updates[key] = _CacheUpdate(modified_time, state)
                   
                if do_notify:
                    self.notify_observers(key, modified_time, state)

            except zmq.ZMQError as err:
                if err.errno != zmq.EAGAIN:
                    LOGGER.error("%s\n%s", zmq.strerror(err.errno), traceback.format_exc())
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.critical("%s", traceback.format_exc())
                raise

    def stop(self) -> None:
        """ Stop the Observer
        """
        if self._stopped:
            return

        LOGGER.info("Stopping cache observer")
        self._stopped = True
        if self._task and not self._task.cancelled():
            self._task.cancel()

    def notify_observers(self, key: str, modified_time: datetime, state = UpdateState ) -> None:
        """ Run registered observers
        """
        for obs in self._observers:
            try:
                obs.observe(key, modified_time, state == UpdateState.INSERTED)
            except Exception:
                LOGGER.critical("Uncaugh error in observer: %s\n%s", obs, traceback.format_exc())


def declare_cache_observers() -> None:
    Server.declare_observers()

def start_cache_observer() -> Server:
    server = Server()
    server.run()
    return server

