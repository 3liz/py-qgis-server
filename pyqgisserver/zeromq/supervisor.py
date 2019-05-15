#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Supervisor implementation for controlling lifetime and restart of workers

    This supervisor will not work for distributed workers because it needs to know
    the pid of the worker processes to send abort signal to. 
"""

#
# Client
#

import os
import asyncio
import signal
import zmq.asyncio
import zmq
import traceback
import logging

from typing import Callable

LOGGER=logging.getLogger('QGSRV')


def _get_supervisor_addr() -> str:
    """ Create ipc address for supervisor/client communication
    """
    ipc_path = '/tmp/qgssrv/supervisor0'
    os.makedirs(os.path.dirname(ipc_path), exist_ok=True)
    return 'ipc://'+ipc_path


class Client:

    def __init__(self) -> None:
        """ Supervised client notifier
        """
        address = _get_supervisor_addr()

        ctx = zmq.Context.instance()
        self._sock = ctx.socket(zmq.PUSH)
        self._sock.setsockopt(zmq.IMMEDIATE, 1) # Do no queue if no connection
        self._sock.connect(address)
        self._pid = os.getpid()
        self._busy = False

    def _send(self, data: bytes ) -> None: 
        try:
            self._sock.send_pyobj((self._pid, data), flags=zmq.DONTWAIT)
        except zmq.ZMQError as err:
            if err.errno != zmq.EAGAIN:
                LOGGER.error("%s (%s)", zmq.strerror(err.errno), err.errno)

    def notify_done(self) -> None:
        """ Send 'ready' notification
        """
        if self._busy:
            self._busy = False
            self._send(b'DONE')

    def notify_busy(self) -> None:
        """ send 'busy' notification
        """
        if not self._busy:
            self._busy = True
            self._send(b'BUSY')

    def close(self) -> None:
        self._sock.close()



class Supervisor:

    def __init__(self, timeout: int,  killfunc: Callable[[int],None])-> None:
        """ Run supervisor

            :param timeout: timeout delay in seconds
        """
        address = _get_supervisor_addr()

        ctx = zmq.asyncio.Context.instance()
        self._sock = ctx.socket(zmq.PULL)
        self._sock.setsockopt(zmq.RCVTIMEO, 1000)
        self._sock.bind( address )

        self._timeout = timeout
        self._busy = {}
        self._stopped = True
        self._killfunc = killfunc


    async def run(self) -> None:
        """ Run supervisor
        """
        LOGGER.debug("Starting supervisor")

        loop = asyncio.get_event_loop()

        def kill(pid:int) -> None:
            LOGGER.critical("Killing stalled process %s", pid)
            del self._busy[pid]
            self._killfunc(pid)

        self._stopped = False

        while not self._stopped:
            try:
                pid, notif = await self._sock.recv_pyobj()
                if notif == b'BUSY':
                    self._busy[pid] = loop.call_later(self._timeout,kill,pid)
                elif notif == b'DONE':
                    try:
                        self._busy.pop(pid).cancel()
                    except KeyError:
                        pass
            except zmq.ZMQError as err:
                if err.errno != zmq.EAGAIN:
                    LOGGER.error("%s\n%s", zmq.strerror(err.errno), traceback.format_exc())
            except Exception:
                LOGGER.critical("%s", traceback.format_exc())

    def stop(self) -> None:
        """ Stop the supervisor
        """
        self._stopped = True
        for th in self._busy.values():
            th.cancel()
        self._busy.clear()


