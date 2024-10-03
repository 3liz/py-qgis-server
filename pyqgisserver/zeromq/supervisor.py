#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
""" Supervisor implementation for controlling lifetime and restart of workers

    This supervisor will not work for distributed workers because it needs to know
    the pid of the worker processes to send abort signal to.
"""

#
# Client
#

import asyncio
import logging
import os
import signal
import traceback

from typing import (
    Any,
    Dict,
    NamedTuple,
    Optional,
    Union,
)

import zmq
import zmq.asyncio

from .utils import _get_ipc

LOGGER = logging.getLogger('SRVLOG')


class _Report(NamedTuple):
    data: Any


class Client:

    def __init__(self):
        """ Supervised client notifier
        """
        try:
            address = _get_ipc('supervisor')
        except KeyError:
            self._sock = None
            LOGGER.warning("Supervisor disabled")
        else:
            ctx = zmq.Context.instance()
            self._sock = ctx.socket(zmq.PUSH)
            self._sock.setsockopt(zmq.IMMEDIATE, 1)  # Do no queue if no connection
            self._sock.connect(address)

        self._pid = os.getpid()
        self._busy = False

    def _send(self, data: Union[bytes, _Report]):
        if not self._sock:
            return
        try:
            self._sock.send_pyobj((self._pid, data), flags=zmq.DONTWAIT)
        except zmq.ZMQError as err:
            if err.errno != zmq.EAGAIN:
                LOGGER.error("%s (%s)", zmq.strerror(err.errno), err.errno)

    def notify_done(self):
        """ Send 'ready' notification
        """
        if self._busy:
            self._busy = False
            self._send(b'DONE')

    def notify_busy(self):
        """ send 'busy' notification
        """
        if not self._busy:
            self._busy = True
            self._send(b'BUSY')

    def close(self):
        if self._sock:
            self._sock.close()

    def send_report(self, data: Any):  # noqa: ANN401
        self._send(_Report(data=data))


class Supervisor:

    def __init__(self, timeout: int):
        """ Run supervisor

            :param timeout: timeout delay in seconds
        """
        address = _get_ipc('supervisor')

        ctx = zmq.asyncio.Context.instance()
        self._sock = ctx.socket(zmq.PULL)
        self._sock.setsockopt(zmq.RCVTIMEO, 1000)
        self._sock.bind(address)

        self._timeout = timeout
        self._busy: Dict[int, asyncio.Task] = {}
        self._stopped = True
        self._task: Optional[asyncio.Task] = None
        self._reports: Dict[int, Any] = {}

    def run(self):
        self._task = asyncio.create_task(self._run_async())

    async def _run_async(self):
        """ Run supervisor
        """
        loop = asyncio.get_running_loop()

        def kill(pid: int):
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
                pid, msg = await self._sock.recv_pyobj()
                if msg == b'BUSY':
                    self._busy[pid] = loop.call_later(self._timeout, kill, pid)
                elif msg == b'DONE':
                    try:
                        self._busy.pop(pid).cancel()
                    except KeyError:
                        pass
                elif isinstance(msg, _Report):
                    self._reports[pid] = msg.data
            except zmq.ZMQError as err:
                if err.errno != zmq.EAGAIN:
                    LOGGER.error("%s\n%s", zmq.strerror(err.errno), traceback.format_exc())
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.critical("%s", traceback.format_exc())
                raise

    @property
    def reports(self):
        return list(self._reports.values())

    def num_reports(self) -> int:
        return len(self._reports)

    def clear_reports(self):
        self._reports = {}

    def stop(self):
        """ Stop the supervisor
        """
        LOGGER.info("Stopping supervisor")
        self._stopped = True
        if self._task and not self._task.cancelled():
            self._task.cancel()
        for th in self._busy.values():
            th.cancel()
        self._busy.clear()
