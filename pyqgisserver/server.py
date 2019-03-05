#
# Copyright 2018 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import os
import sys
import logging
import argparse

from typing import List

from .version import __description__, __version__
from .logger import setup_log_handler
from .config import (get_config, read_config_file, read_config_dict,
                     validate_config_path)

from .runtime import run_server

LOGGER = logging.getLogger('QGSRV')


def print_version() -> None:
    program = os.path.basename(sys.argv[0])
    print("{name} {version}".format(name=program, version=__version__,file=sys.stderr))


def read_configuration(args: List[str]=None) -> argparse.Namespace:
    """ Parse command line and read configuration file
    """
    if args is None:
        args = sys.argv

    cli_parser = argparse.ArgumentParser(description=__description__)

    config_file = None
    conf = get_config('server')

    cli_parser.add_argument('--logging', choices=['debug', 'info', 'warning', 'error'], 
            default=get_config('logging')['level'].lower(), help="set log level")
    cli_parser.add_argument('-c','--config', metavar='PATH', nargs='?', dest='config',
            default=None, help="Configuration file")
    cli_parser.add_argument('--version', action='store_true', 
            default=False, help="Return version number and exit")
    cli_parser.add_argument('-p','--port'    , type=int, help="http port", dest='port', default=conf.getint('port'))
    cli_parser.add_argument('-b','--bind'    , metavar='IP',  default=conf['interfaces'], help="Interface to bind to", dest='interface')
    cli_parser.add_argument('-w','--workers' , metavar='NUM', type=int, default=conf.getint('workers'), help="Num workers", dest='workers')
    cli_parser.add_argument('-j','--jobs'    , metavar='NUM', type=int, default=1, help="Num server instances", dest='jobs')
    cli_parser.add_argument('-u','--setuid'  , default='', help="uid to switch to", dest='setuid')
    cli_parser.add_argument('--rootdir'  , default=get_config('cache')['rootdir'], metavar='PATH', help='Path to qgis projects')
    cli_parser.add_argument('--proxy'    , action='store_true', default=False, help='Run only as proxy')
    cli_parser.add_argument('--timeout'  , metavar='SECONDS', type=int, default=conf.getint('timeout'), 
            help='Set client timeout in seconds')

    args = cli_parser.parse_args()

    if args.version:
        print_version()
        sys.exit(1)

    log_level = args.logging
    if args.config:
        with open(args.config, mode='rt') as config_file:
            read_config_file(config_file)

    read_config_dict({
        'logging':{ 'level'  : args.logging.upper() },
        'cache'  :{ 'rootdir': args.rootdir },
        'server' :{
            'interfaces': args.interface,
            'port'      : str(args.port),
            'timeout'   : str(args.timeout),
        },
    })

    print_version()

    workers = args.workers

    # set log level
    setup_log_handler(log_level)
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    return args
 

def main() -> None:
    """ Run the server as cli command
    """
    args = read_configuration()

    workers = args.workers
    if not args.proxy:
        validate_config_path('cache','rootdir')
    else:
        # Do not run any qgis workers
        workers = 0

    run_server( port=args.port, address=args.interface, jobs=args.jobs, user=args.setuid, workers=workers )

    

