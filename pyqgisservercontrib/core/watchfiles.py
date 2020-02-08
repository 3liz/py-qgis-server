""" Watch file change
"""
import os
import functools
import logging
import traceback

from typing import Callable, Mapping, Union, List
from tornado import ioloop

LOGGER = logging.getLogger('SRVLOG')

UpdateFunc = Callable[[List[str]],None]


def watchfiles(watched_files: List[str], updatefunc: UpdateFunc,  check_time: int=500) -> ioloop.PeriodicCallback:
    """Begins watching source files for changes.
    """
    io_loop = ioloop.IOLoop.current()
    modify_times = {}
    callback = functools.partial(_update_callback, updatefunc, watched_files, modify_times)
    scheduler = ioloop.PeriodicCallback(callback, check_time)
    return scheduler


def _update_callback( updatefunc: UpdateFunc, watched_files: List[str], modify_times: Mapping[float,str]) -> None:
    """ Call update funcs when modified files
    """
    modified_files = [path for path in watched_files if _check_file(modify_times, path) is not None]
    if len(modified_files) > 0:
        LOGGER.debug("running update hook for %s", modified_files)
        updatefunc( modified_files )


def _check_file(modify_times: Mapping[float,str], path: str) -> Union[str,None]:
    try:
        modified = os.stat(path).st_mtime
    except FileNotFoundError:
        # Do not care if file do not exists
        return
    except Exception:
        traceback.print_exc()
        LOGGER.error("Error while checking file %s")
        return
    if path not in modify_times:
        modify_times[path] = modified
        return
    if modify_times[path] != modified:
        modify_times[path] = modified
        return path




