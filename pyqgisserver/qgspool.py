#
# Copyright 2018 3liz
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Qgis worker pool
"""
import logging
import threading
import time

from functools import partial

from multiprocessing import Process, cpu_count
from multiprocessing.util import Finalize

from .qgsworker import QgsRequestHandler

RUN = 0
CLOSE = 1
TERMINATE = 2


LOGGER = logging.getLogger('QGSRV')

class Pool:

    def __init__(self, router, num_workers):
        self._router = router
        self._num_workers = num_workers
        self._pool = []
        self._repopulate_pool()

        self._worker_handler = threading.Thread(
             target=Pool._handle_workers,
             args=(self, )
        )
        self._worker_handler._state = RUN
        self._worker_handler.daemon = True
        self._worker_handler.start()

        # Ensure that pool is terminated is called
        # at process exit
        self._terminate = Finalize(
            self, self._terminate_pool, 
            args=(self._pool, self._worker_handler),
            exitpriority=15
        )

    def _join_exited_workers(self):
        """Cleanup after any worker processes which have exited due to reaching
        their specified lifetime.  Returns True if any workers were cleaned up.
        """
        cleaned = False
        for i in reversed(range(len(self._pool))):
            worker = self._pool[i]
            if worker.exitcode is not None:
                if worker.exitcode != 0:
                    LOGGER.warning("Qgis Worker exited with code %s", worker.exitcode) 
                # worker exited
                worker.join()
                cleaned = True
                del self._pool[i]
        return cleaned

    def _repopulate_pool(self):
        """Bring the number of pool processes up to the specified number,
        for use after reaping workers which have exited.
        """
        for _ in range(self._num_workers - len(self._pool)):
            w = Process(target=QgsRequestHandler.run, args=(self._router,))
            self._pool.append(w)
            w.name = w.name.replace('Process', 'QgisWorker')
            w.daemon = True
            w.start()

    def _maintain_pool(self):
        """Clean up any exited workers and start replacements for them.
        """
        if self._join_exited_workers():
            self._repopulate_pool()

    @classmethod
    def _terminate_pool(cls, pool, worker_handler):

        worker_handler._state = TERMINATE
        # We must wait for the worker handler to exit before terminating
        # workers because we don't want workers to be restarted behind our back.
        if threading.current_thread() is not worker_handler:
            worker_handler.join()

        if pool and hasattr(pool[0], 'terminate'):
            for p in pool:
                if p.exitcode is None:
                    p.terminate()

        # Join pool workers
        if pool and hasattr(pool[0], 'terminate'):
            for p in pool:
                if p.is_alive():
                    # worker has not yet exited
                    p.join()

    @staticmethod
    def _handle_workers(pool):
        thread = threading.current_thread()
        while thread._state == RUN:
            pool._maintain_pool()
            time.sleep(0.1)

    def __reduce__(self):
        raise NotImplementedError(
            'cluster objects cannot be passed between processes or pickled'
        )

    def terminate(self):
        self._worker_handler._state = TERMINATE
        self._terminate()




