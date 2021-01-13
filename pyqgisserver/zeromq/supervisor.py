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
import signal
import asyncio
import zmq.asyncio
import zmq
import traceback
import logging

from .utils import _get_ipc

from typing import Awaitable

LOGGER=logging.getLogger('SRVLOG')


class Client:

    def __init__(self) -> None:
        """ Supervised client notifier
        """
        address = _get_ipc('supervisor')

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

    def __init__(self, timeout: int)-> None:
        """ Run supervisor

            :param timeout: timeout delay in seconds
        """
        address = _get_ipc('supervisor')

        ctx = zmq.asyncio.Context.instance()
        self._sock = ctx.socket(zmq.PULL)
        self._sock.setsockopt(zmq.RCVTIMEO, 1000)
        self._sock.bind( address )

        self._timeout = timeout
        self._busy = {}
        self._stopped = True
        self._task = None

    def run(self) -> None:
        self._task = asyncio.ensure_future(self._run_async())

    async def _run_async(self) -> Awaitable[None]:
        """ Run supervisor
        """
        loop = asyncio.get_event_loop()

        def kill(pid:int) -> None:
            del self._busy[pid]
            try:
                os.kill(pid, signal.SIGKILL)
                LOGGER.critical("Killed stalled process %s", pid)
            except ProcessLookupError:
                # Process was already terminated/crashed
                pass

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
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.critical("%s", traceback.format_exc())
                raise

    def stop(self) -> None:
        """ Stop the supervisor
        """
        LOGGER.info("Stopping supervisor")
        self._stopped = True
        if self._task and not self._task.cancelled():
            self._task.cancel()
        for th in self._busy.values():
            th.cancel()
        self._busy.clear()


