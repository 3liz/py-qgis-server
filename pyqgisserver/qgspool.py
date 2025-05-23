#
# Copyright 2020 3liz
# Author: David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
"""
The fork serve will ensure that forking processes
occurs from [almost] the same state.
"""
import asyncio
import logging
import os
import signal
import time
import traceback

from glob import glob
from multiprocessing import Process
from multiprocessing.util import Finalize
from typing import (
    Awaitable,
    Callable,
    Iterator,
    Optional,
    Union,
    cast,
)

import psutil
import zmq

from pyqgisservercontrib.core.watchfiles import Scheduler, watchfiles

from .config import confservice
from .qgsworker import QgsRequestHandler
from .zeromq.pool import Pool
from .zeromq.supervisor import Supervisor

LOGGER = logging.getLogger('SRVLOG')


class _RestartHandler:

    def __init__(self) -> None:
        self._restart: Optional[Scheduler] = None
        self._watch_files: list[str] = []

    def update_files(self) -> None:
        """ update files to watch
        """
        conf = confservice['server']

        self._watch_files.clear()
        restartmon = conf.get('restartmon')
        if restartmon:
            self._watch_files.append(restartmon)

        # Check for plugins
        pluginpath = conf.get('pluginpath')
        if pluginpath:
            plugins = glob(os.path.join(pluginpath, '*/.update-manifest'))
            self._watch_files.extend(plugins)

        LOGGER.debug("Updated watch files %s", self._watch_files)

    def close(self) -> None:
        if self._restart:
            self._restart.stop()

    def start(self, do_restart: Callable[[None], None]) -> None:
        """ Create a restart handler
        """
        self.update_files()

        def callback(*args):
            do_restart()
            self.update_files()

        check_time = confservice.getint('server', 'restartmon_check_time', 3000)
        self._restart = watchfiles(self._watch_files, callback, check_time)
        self._restart.start()  # type: ignore [attr-defined]


class WorkerPoolServer:

    def __init__(
        self,
        broadcastaddr: str,
        pool: Process,
        timeout: int,
        num_workers: int,
        high_water_mark: float,
    ) -> None:

        ctx = zmq.Context.instance()
        pub = ctx.socket(zmq.PUB)
        pub.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
        pub.setsockopt(zmq.SNDHWM, 1)      # Max 1 item on send queue
        pub.bind(broadcastaddr)

        self._timeout = timeout
        self._sock = pub
        self._num_workers = num_workers

        self._high_water_mark = high_water_mark

        LOGGER.debug("Started pool server")
        self._pool = pool
        self._supervisor: Union[Supervisor, None] = None
        self._healthcheck = None

        self._restart_handler = _RestartHandler()

        # Ensure that pool is terminated is called
        # at process exit
        self._terminate = Finalize(
            self, self._terminate_pool,
            args=(self._pool,),
            exitpriority=16,
        )

    async def healthcheck(self) -> Awaitable[None]:
        while True:
            # Check for exitcode
            if self._pool.exitcode is not None and self._pool.exitcode != 0:
                LOGGER.critical("Pool failure, exiting because of unrecoverable error...")
                raise SystemExit(1)
            # Check high water mark
            try:
                self.check_oom_status()
            except Exception:
                LOGGER.error(traceback.format_exc())
            await asyncio.sleep(5)

    def start_supervisor(self):
        """ Start supervisor independently

            Note: It is no recommended to run supervisor before asyncio loop
            has been properly set - for exemple when using a custom loop.
        """
        if self._supervisor is None:
            LOGGER.info("Initializing supervisor")
            self._supervisor = Supervisor(self._timeout)
            self._supervisor.run()

        if self._healthcheck is None:
            LOGGER.info("Initializing pool healthcheck")
            self._healthcheck = asyncio.ensure_future(self.healthcheck())

        self._restart_handler.start(self.restart)

    @classmethod
    def _terminate_pool(cls, p: Process) -> None:
        if p and hasattr(p, 'terminate'):
            if p.exitcode is None:
                p.terminate()
            if p.is_alive():
                p.join()

    def terminate(self):
        """ Terminate handler
        """
        self._restart_handler.close()
        if self._healthcheck:
            self._healthcheck.cancel()
        self._sock.close()
        if self._supervisor:
            self._supervisor.stop()
        self._terminate()

    def broadcast(self, command: bytes) -> None:
        """ Broadcast notification to workers
        """
        try:
            self._sock.send(command, zmq.NOBLOCK)
        except zmq.ZMQError as err:

            if err.errno != zmq.EAGAIN:
                LOGGER.error("Broadcast Error %s\n%s", err, traceback.format_exc())

    def restart(self) -> None:
        """ Send restart command
        """
        self.broadcast(b'RESTART')

    @property
    def num_workers(self) -> int:
        return self._num_workers

    async def get_reports(self) -> list[dict]:
        """ Collect reports
        """
        if self._supervisor is None:
            return []

        supervisor = cast(Supervisor, self._supervisor)

        maxwait = 10
        so_far = 0
        supervisor.clear_reports()
        self.broadcast(b'REPORT')
        while supervisor.num_reports() < self._num_workers:
            await asyncio.sleep(1)
            so_far += 1
            if so_far >= maxwait:
                break
        return supervisor.reports

    def check_oom_status(self):
        """Kill out-of-memory children

        This will kill the children using the most memory
        until the memory goes below high water mark
        """
        # Compute memory used for all childs
        def _mem_usage() -> Iterator[tuple[psutil.Process, float]]:
            for p in psutil.Process(self._pool.pid).children():
                mem = p.memory_percent()
                mem += sum(pp.memory_percent() for pp in p.children(recursive=True))
                yield (p, mem / 100.0)

        childs = list(_mem_usage())

        # Total mem
        memory_fraction = sum(t[1] for t in childs)
        if memory_fraction > self._high_water_mark:
            LOGGER.critical(
                "High memory water mark reached (%s)",
                self._high_water_mark,
            )

            # Sort childs process in descending order
            # kill child processes until memory get low
            childs.sort(key=lambda t: t[1], reverse=True)
            for (p, mem) in childs:
                LOGGER.critical("OOM: killing worker: %s (mem usage: %s)", p.pid, mem)
                p.kill()
                memory_fraction -= mem
                if memory_fraction < self._high_water_mark:
                    break


def create_poolserver(numworkers: int) -> WorkerPoolServer:
    """ Run workers pool in its own process

        This ensure that sub-processes all always forked from
        the same parent context
    """
    router = confservice['zmq']['bindaddr']
    broadcastaddr = confservice['zmq']['broadcastaddr']
    timeout = confservice['server'].getint('timeout')

    high_water_mark = float(confservice['server']['memory_high_water_mark'])

    p = Process(target=run_worker_pool, args=(numworkers, broadcastaddr, router))
    p.start()

    poolserver = WorkerPoolServer(
        broadcastaddr,
        p,
        timeout,
        numworkers,
        high_water_mark=high_water_mark,
    )
    return poolserver


def run_worker_pool(numworkers: int, broadcastaddr: str, router: str) -> None:
    """ Run a qgis worker pool

        Ensure that child processes run in the main thread
    """

    # Try to exit gracefully
    def term_signal(signum, frames):
        # print("Caught signal: %s" % signum, file=sys.stderr)
        raise SystemExit()

    LOGGER.info("Starting worker pool")
    pool = Pool(
        numworkers,
        target=QgsRequestHandler.run,
        args=(router,),
        kwargs={'broadcastaddr': broadcastaddr},
    )

    signal.signal(signal.SIGTERM, term_signal)

    try:
        while True:
            if pool.critical_failure:
                raise RuntimeError("Server aborting prematurely !")
            pool.maintain_pool()
            time.sleep(0.1)
    except (KeyboardInterrupt, SystemExit):
        LOGGER.warning("Pool Interrupted")
    finally:
        LOGGER.info("Terminating worker pool")
        pool.terminate()
