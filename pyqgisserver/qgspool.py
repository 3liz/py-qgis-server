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
import sys
import os
import zmq
import logging
import signal
import time
import traceback
import asyncio

from glob import glob

from multiprocessing import Process
from multiprocessing.util import Finalize

from typing import Callable, Awaitable, Optional, Dict, List

from .zeromq.supervisor import Supervisor
from .zeromq.pool import Pool

from .config import confservice

from .qgsworker import QgsRequestHandler

from pyqgisservercontrib.core.watchfiles import watchfiles

LOGGER=logging.getLogger('SRVLOG')

class _RestartHandler:

    def __init__(self) -> None:
        self._restart = None
        self._watch_files = []

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
            plugins = glob(os.path.join(pluginpath,'*/.update-manifest'))
            self._watch_files.extend(plugins)

        LOGGER.debug("Updated watch files %s", self._watch_files)

    def close(self) -> None:
        if self._restart:
            self._restart.stop()

    def start(self, do_restart: Callable[[None],None]) -> None:
        """ Create a restart handler
        """
        self.update_files()
        
        def callback( *args ):
            do_restart()
            self.update_files()

        check_time = confservice.getint('server','restartmon_check_time', 3000)
        self._restart = watchfiles(self._watch_files, callback, check_time)
        self._restart.start()


class _Server:

    def __init__(self, broadcastaddr: str, pool: Process,  timeout: int,
                 num_workers: int) -> None:

        ctx = zmq.Context.instance()
        pub = ctx.socket(zmq.PUB)
        pub.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
        pub.setsockopt(zmq.SNDHWM, 1)      # Max 1 item on send queue
        pub.bind(broadcastaddr)

        self._timeout = timeout 
        self._sock = pub
        self._num_workers = num_workers

        LOGGER.debug("Started pool server")
        self._pool = pool
        self._supervisor = None
        self._healthcheck = None

        self._restart_handler = _RestartHandler()
        self._restart_handler.start(self.restart)

        # Ensure that pool is terminated is called
        # at process exit
        self._terminate = Finalize(
            self, self._terminate_pool, 
            args=(self._pool,),
            exitpriority=16
        )

    async def healthcheck(self) -> Awaitable[None]:
        while True:
            if self._pool.exitcode is not None and self._pool.exitcode != 0:
                LOGGER.critical("Pool failure, exiting...")
                raise SystemExit("Exiting because of unrecoverable error")
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
        LOGGER.info("Stopping pool server")
        self._restart_handler.close()
        if self._healthcheck:
            self._healthcheck.cancel()
        self._sock.close()
        if self._supervisor:
            self._supervisor.stop()
        LOGGER.info("Stopping worker pool")
        self._terminate()

    def broadcast(self, command: bytes ) -> None:
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

    async def get_reports(self) -> Awaitable[List[Dict]]:
        """ Collect reports
        """
        maxwait=10
        so_far=0
        self._supervisor.clear_reports()
        self.broadcast(b'REPORT')
        while self._supervisor.num_reports() < self._num_workers:
            await asyncio.sleep(1)
            so_far += 1
            if so_far >= maxwait:
                break
        return self._supervisor.reports


def create_poolserver(numworkers: int) -> _Server:
    """ Run workers pool in its own process

        This ensure that sub-processes all always forked from
        the same parent context
    """
    router        = confservice['zmq']['bindaddr']
    broadcastaddr = confservice['zmq']['broadcastaddr']
    timeout       = confservice['server'].getint('timeout')

    maxcycles = confservice.getint('server', 'maxcycles', fallback=None)
    if maxcycles is not None:
        if maxcycles <= 0:
            maxcycles = None
        else:
            LOGGER.info(f"Max cycles limit set to {maxcycles}")

    p = Process(target=run_worker_pool, args=(numworkers, broadcastaddr, router, maxcycles))
    p.start()

    poolserver = _Server(broadcastaddr, p, timeout, numworkers)
    return poolserver


def run_worker_pool(numworkers: int, broadcastaddr: str, router: str, 
                    maxcycles: Optional[int]=None) -> None:
    """ Run a qgis worker pool

        Ensure that child processes run in the main thread
    """
    # Try to exit gracefully
    def term_signal(signum,frames):
        #print("Caught signal: %s" % signum, file=sys.stderr)
        raise SystemExit()

    LOGGER.info("Starting worker pool")
    pool = Pool( numworkers, target=QgsRequestHandler.run, args=(router,),
                 kwargs={ 'broadcastaddr': broadcastaddr, 'maxcycles': maxcycles } )

    # Handle critical failure by sending ABORT to
    # parent process
    def abrt_signal(signum,frames):
        if pool.critical_failure:
            print("Server aborting prematurely !", file=sys.stderr)
            os.kill(os.getppid(), signal.SIGABRT)

    signal.signal(signal.SIGTERM,term_signal)
    signal.signal(signal.SIGABRT,abrt_signal)

    try:
        while True:
            pool.maintain_pool()
            time.sleep(0.1)
    except (KeyboardInterrupt,SystemExit):
        LOGGER.warning("Pool Interrupted")
    finally:
        LOGGER.info("Terminating worker pool")
        pool.terminate()


