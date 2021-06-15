#
# Copyright 2018 3liz
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
""" Logging handlers
"""
import logging

REQ_LOG_TEMPLATE = "{ip}\t{code}\t{method}\t{url}\t{time}\t{length}\t"
REQ_FORMAT = REQ_LOG_TEMPLATE+'{agent}\t{referer}'
RREQ_FORMAT = REQ_LOG_TEMPLATE

# Lies between warning and error
REQ = 21
RREQ = 22

LOGGER=logging.getLogger('SRVLOG')

def setup_log_handler(log_level, formatstr='%(asctime)s\t%(levelname)s\t[%(process)d]\t%(message)s',
                      stream = None ):
    """ Initialize log handler with the given log level
    """
    logging.addLevelName(REQ, "REQ")
    logging.addLevelName(RREQ, "RREQ")

    logger = LOGGER
    logger.setLevel(getattr(logging, log_level.upper()))
    # Init the root logger
    if not logger.handlers:
        channel = logging.StreamHandler(stream=stream)
        formatter = logging.Formatter(formatstr)
        channel.setFormatter(formatter)
        logger.addHandler(channel)
        return True
    return False

def format_log_request(handler):
    """ Format current request from the given tornado request handler

        :return a tuple (fmt,code,reqtime,length) where:
            fmt: the log string
            code: the http return code
            reqtime: the request time
            length: the size of the payload
    """
    request = handler.request
    code    = handler.get_status()
    reqtime = request.request_time()

    length  = handler._headers.get('Content-Length') or -1
    agent   = request.headers.get('User-Agent') or ""
    referer = request.headers.get('Referer')  or ""

    fmt = REQ_FORMAT.format(
        ip=request.remote_ip,
        method=request.method,
        url=request.uri,
        code=code,
        time=int(1000.0 * reqtime),
        length=length,
        referer=referer,
        agent=agent)

    return fmt, code, reqtime, length


def log_request(handler):
    """ Log the current request from the given tornado request handler

        :param handler: The request handler
        :param logger: an optional logger

        :return A tuple (code,reqtime,length) where:
            code: the http retudn code
            reqtime: the request time
            length: the size of the payload
    """
    fmt, code, reqtime, length = format_log_request(handler)
    LOGGER.log(REQ, fmt)
    return code, reqtime, length


def format_log_rrequest(path, code, method, query, reqtime, headers, addr=''):
    """ Format current r-request from the given response

        :param response: The response returned from the request
        :return A tuple (fmt,code,reqtime,length) where:
            fmt: the log string
            code: the http retudn code
            reqtime: the request time
            length: the size of the payload
    """
    length = -1
    try:
        length = headers['Content-Length']
    except KeyError:
        pass

    fmt = RREQ_FORMAT.format(
        ip=addr,
        method=method,
        url=f"{path.rstrip('/')}/{query}",
        code=code,
        time=int(1000.0 * reqtime),
        length=length)

    return fmt


def log_rrequest(*args, **kwargs):
    """ Log the current response request from the given response

        :return A tuple (code,reqtime,length) where:
            code: the http retudn code
            reqtime: the request time
            length: the size of the payload
    """
    fmt = format_log_rrequest(*args, **kwargs)
    LOGGER.log(RREQ, fmt)

