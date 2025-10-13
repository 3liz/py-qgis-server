""" Watch file change
"""
import functools
import logging
import os
import traceback

from typing import Callable, Dict, List, Optional

from tornado.ioloop import PeriodicCallback as Scheduler

LOGGER = logging.getLogger('SRVLOG')

UpdateFunc = Callable[[List[str]], None]


def watchfiles(watched_files: List[str], updatefunc: UpdateFunc, check_time: int = 500) -> Scheduler:
    """Begins watching source files for changes.
    """
    modify_times: Dict[str, float] = {}
    callback = functools.partial(_update_callback, updatefunc, watched_files, modify_times)
    scheduler = Scheduler(callback, check_time)
    return scheduler


def _update_callback(
    updatefunc: UpdateFunc,
    watched_files: List[str],
    modify_times: Dict[str, float],
):
    """ Call update funcs when modified files
    """
    modified_files = [path for path in watched_files if _check_file(modify_times, path) is not None]
    if len(modified_files) > 0:
        LOGGER.debug("running update hook for %s", modified_files)
        updatefunc(modified_files)


def _check_file(modify_times: Dict[str, float], path: str) -> Optional[str]:
    try:
        modified = os.stat(path).st_mtime

        if path not in modify_times:
            modify_times[path] = modified
            return None
        if modify_times[path] != modified:
            modify_times[path] = modified
            return path
    except FileNotFoundError:
        # Do not care if file do not exists
        pass
    except Exception:
        traceback.print_exc()
        LOGGER.error("Error while checking file %s")

    return None
