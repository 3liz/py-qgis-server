""" Handle fork

    The code is derived from the tornado implementation:
    see http://www.tornadoweb.org/en/stable/_modules/tornado/process.html#fork_processes
"""
import sys
import os
import logging
import signal

_task_id  = None
_ppid     = None
_children = {}

def _start_child(i):

    global _children

    pid = os.fork()
    if pid == 0:
        # child process
        global _task_id
        _task_id = i
        return i
    else:
        _children[pid] = i
        return None


def fork_processes(num_processes):
    """Starts multiple worker processes.

    In each child process, ``fork_processes`` returns its *task id*, a
    number between 0 and ``num_processes``.  
    
    """
    global _ppid
    assert _ppid is None

    global _task_id
    assert _task_id is None

    global _children

    _ppid = os.getpid()    

    for i in range(num_processes):
        id = _start_child(i)
        if id is not None:
            _children.clear()
            return id

    return None


def manage_processes( max_restarts, logger = None ):
    """ Manage child processes 

    Processes that exit
    abnormally (due to a signal or non-zero exit status) are restarted
    with the same id (up to ``max_restarts`` times).  In the parent
    process, ``fork_processes`` returns None if all child processes
    have exited normally, but will otherwise only exit by throwing an
    exception.
    """

    assert _ppid == os.getpid(), "can only manage processes created in the current process"

    num_restarts = 0

    logger = logger or logger.getLogger()

    global _children

    while _children:
        try:
            pid, status = os.wait()
        except OSError as e:
            if errno_from_exception(e) == errno.EINTR:
                continue
            raise
        if pid not in _children:
            continue
        id = _children.pop(pid)
        if os.WIFSIGNALED(status):
            logger.warning("child %d (pid %d) killed by signal %d, restarting",
                            id, pid, os.WTERMSIG(status))
        elif os.WEXITSTATUS(status) != 0:
            logger.warning("child %d (pid %d) exited with status %d, restarting",
                            id, pid, os.WEXITSTATUS(status))
        else:
            logger.debug("child %d (pid %d) exited normally", id, pid)
            continue
        num_restarts += 1
        if num_restarts > max_restarts:
            raise RuntimeError("Too many child restarts, giving up")
        new_id = _start_child(id)
        if new_id is not None:
            return new_id
    # All child processes exited cleanly, so exit the master process
    # instead of just returning to right after the call to
    # fork_processes (which will probably just start up another IOLoop
    # unless the caller checks the return value).
    sys.exit(0)


def task_id():
    """Returns the current task id, if any.

    Returns None if this process was not created by `fork_processes`.
    """
    global _task_id
    return _task_id


def terminate_childs():
    """ Terminate all childs
    """
    assert _ppid == os.getpid(), "can only terminate processes created in the current process"
    global _children
    for pid in _children:
        os.kill(pid, signal.SIGTERM)



