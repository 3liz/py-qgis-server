
import zmq
from .watchfiles import watchfiles

# Ask restarting
BCAST_RESTART = b'RESTART'

def create_broadcast_publisher(bindaddr):
    """ Create a command publisher

        This publisher will broadcast message
        to workers
    """
    ctx = zmq.Context().instance()
    pub = ctx.socket(zmq.PUB)
    pub.setsockopt(zmq.LINGER, 500)    # Needed for socket no to wait on close
    pub.setsockopt(zmq.SNDHWM, 1)      # Max 1 item on send queue
    pub.bind(bindaddr)

    return pub

def restart_when_modified(pub, files, check_time):
    """ Broadcast a RESTART if a file is modified from the list is modified
    """
    if isinstance(files,str):
        files = [files]

    def callback( *args ):
        try:
            pub.send(BCAST_RESTART, zmq.NOBLOCK)
        except zmq.ZMQError as err:
            if err.errno != zmq.EAGAIN:
              LOGGER.error("Broadcast Error %s\n%s", exc, traceback.format_exc())

    return watchfiles(files, callback, check_time)


