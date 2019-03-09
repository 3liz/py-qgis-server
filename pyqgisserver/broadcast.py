
import os
import zmq
import logging

from glob import glob

from .watchfiles import watchfiles
from .config import get_config

# Ask restarting
BCAST_RESTART = b'RESTART'

LOGGER = logging.getLogger('QGSRV')

class Broadcast:

    def __init__(self):
        self._sock = None
        self._restart = None
        self._watch_files = []
        self._config = get_config('server')

    def close(self):
        if self._restart:
            self._restart.stop()
        if self._sock:
            self._sock.close()

    def update_files(self):
        """ update files to watch
        """
        self._watch_files.clear()
        restartmon = self._config['restartmon']
        if restartmon:
            self._watch_files.append(restartmon)

        # Check for plugins
        pluginpath = self._config['pluginpath']
        if pluginpath:
            plugins = glob(os.path.join(pluginpath,'*/.update-manifest'))
            self._watch_files.extend(plugins)

        LOGGER.debug("Updated watch files %s", self._watch_files)

    def init(self):
        """ Create a command publisher

            This publisher will broadcast message
            to workers
        """
        bindaddr = get_config('zmq')['broadcastaddr']

        ctx = zmq.Context().instance()
        pub = ctx.socket(zmq.PUB)
        pub.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
        pub.setsockopt(zmq.SNDHWM, 1)      # Max 1 item on send queue
        pub.bind(bindaddr)

        self._sock = pub

        self.update_files()

        def callback( *args ):
            try:
                pub.send(BCAST_RESTART, zmq.NOBLOCK)
            except zmq.ZMQError as err:
                if err.errno != zmq.EAGAIN:
                  LOGGER.error("Broadcast Error %s\n%s", exc, traceback.format_exc())
            # Update files to watch
            self.update_files()

        check_time = get_config('server').get('restartmon_check_time', 3000)
        self._restart = watchfiles(self._watch_files, callback, check_time)
        self._restart.start()

