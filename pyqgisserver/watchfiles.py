""" Watch file change
"""
import os
import functools
import logging

from tornado import ioloop

LOGGER = logging.getLogger('QGSRV')


def watchfiles(watched_files, updatefunc,  check_time=500):
    """Begins watching source files for changes.
    """
    io_loop = ioloop.IOLoop.current()
    modify_times = {}
    callback = functools.partial(_update_callback, updatefunc, watched_files, modify_times)
    scheduler = ioloop.PeriodicCallback(callback, check_time)
    return scheduler


def _update_callback( updatefunc, watched_files, modify_times ):
    """ Call update funcs when modified files
    """
    modified_files = [path for path in watched_files if _check_file(modify_times, path) is not None]
    if len(modified_files) > 0:
        updatefunc( modified_files )


def _check_file(modify_times, path):
    try:
        modified = os.stat(path).st_mtime
    except Exception:
        return
    if path not in modify_times:
        modify_times[path] = modified
        return
    if modify_times[path] != modified:
        modify_times[path] = modified
        LOGGER.debug("%s modified; running update hook", path)
        return path




