# -*- coding: utf-8 -*-

import logging

REQ_LOG_TEMPLATE = u"{ip}\t{code}\t{method}\t{url}\t{time}\t{length}\t"
REQ_FORMAT = REQ_LOG_TEMPLATE+u'{agent}\t{referer}'
RREQ_FORMAT = REQ_LOG_TEMPLATE

# Lies between warning and error
REQ = 21
RREQ = 22

def setup_log_handler(log_level, formatstr='%(asctime)s\t%(levelname)s\t[%(process)d]\t%(message)s', logger=None):
    """ Initialize log handler with the given log level
    """
    logging.addLevelName(REQ, "REQ")
    logging.addLevelName(RREQ, "RREQ")

    logger = logger or logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))
    # Init the root logger
    if not logger.handlers:
        channel = logging.StreamHandler()
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


def log_request(handler, logger=None):
    """ Log the current request from the given tornado request handler

        :param handler: The request handler
        :param logger: an optional logger

        :return A tuple (code,reqtime,length) where:
            code: the http retudn code
            reqtime: the request time
            length: the size of the payload
    """
    fmt, code, reqtime, length = format_log_request(handler)
    logger = logger or logging.getLogger()
    logger.log(REQ, fmt)
    return code, reqtime, length


def format_log_rrequest(response):
    """ Format current r-request from the given response

        :param response: The response returned from the request
        :param checksum: Add an md5 checksum for the urlS

        :return A tuple (fmt,code,reqtime,length) where:
            fmt: the log string
            code: the http retudn code
            reqtime: the request time
            length: the size of the payload
    """
    request = response.request
    code    = response.code
    reqtime = response.request_time

    length = -1
    try:
        length = response.headers['Content-Length']
    except KeyError:
        pass

    fmt = RREQ_FORMAT.format(
        ip='',
        method=request.method,
        url=request.url,
        code=code,
        time=int(1000.0 * reqtime),
        length=length)

    return fmt, code, reqtime, length


def log_rrequest(response, logger=None):
    """ Log the current response request from the given response

        :return A tuple (code,reqtime,length) where:
            code: the http retudn code
            reqtime: the request time
            length: the size of the payload
    """
    fmt, code, reqtime, length = format_log_rrequest(response)
    logger = logger or logging.getLogger()
    logger.log(RREQ, fmt)
    return code, reqtime, length

