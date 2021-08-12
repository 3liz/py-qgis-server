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

from .version import __description__, __manifest__
from .logger import setup_log_handler
from .config import (confservice, read_config_file,
                     validate_config_path, load_configuration)

from .utils.qgis import print_qgis_version
from .runtime import run_server

LOGGER = logging.getLogger('SRVLOG')



def print_version(verbose=False) -> None:
    """ Display version infos
    """
    program = os.path.basename(sys.argv[0])
    print("{program} {version} (build {buildid},commit {commitid})".format(program=program,**__manifest__),
          file=sys.stderr)
    print_qgis_version(verbose=verbose)


def read_configuration(argv: List[str]=None) -> argparse.Namespace:
    """ Parse command line and read configuration file
    """
    if argv is None:
        argv = sys.argv[1:]

    cli_parser = argparse.ArgumentParser(description=__description__)

    cli_parser.add_argument('-d','--debug', action='store_true', default=False, help="debug mode") 
    cli_parser.add_argument('-c','--config', metavar='PATH', nargs='?', dest='config',
                            default=None, help="Configuration file")
    cli_parser.add_argument('--version', action='store_true', 
                            default=False, help="Return version infos and exit")
    cli_parser.add_argument('-p','--port'    , type=int, help="http port", dest='port', default=argparse.SUPPRESS)
    cli_parser.add_argument('-b','--bind'    , metavar='IP',  default=argparse.SUPPRESS, help="interface to bind to", dest='interfaces')
    cli_parser.add_argument('-w','--workers' , metavar='NUM', type=int, default=argparse.SUPPRESS, help="num workers", dest='workers')
    cli_parser.add_argument('-j','--jobs'    , metavar='NUM', type=int, default=1, help="[DEPRECATED] num server instances", dest='jobs')
    cli_parser.add_argument('-u','--setuid'  , default='', help="uid to switch to", dest='setuid')
    cli_parser.add_argument('--rootdir'  , default=argparse.SUPPRESS, metavar='PATH', help='path to qgis projects')
    cli_parser.add_argument('--proxy'    , action='store_true', default=False, help='run only as proxy')

    args = cli_parser.parse_args(argv)

    if args.version:
        print_version(verbose=args.debug)
        sys.exit(1)
    else:
        print_version()

    load_configuration()

    if args.config:
        with open(args.config, mode='rt') as config_file:
            read_config_file(config_file)

    # Override config
    def set_arg( section:str, name:str ) -> None:
        if name in args:
            confservice.set( section, name, str(getattr(args,name)))

    set_arg( 'projects.cache'  , 'rootdir' )
    set_arg( 'server' , 'interfaces')
    set_arg( 'server' , 'port' )
    set_arg( 'server' , 'workers' )

    if args.debug:
        # Force debug mode
        confservice.set('logging', 'level', 'DEBUG')

    # set log level
    setup_log_handler(confservice.get('logging','level'))
    print("Log level set to {}\n".format(logging.getLevelName(LOGGER.level)), file=sys.stderr)

    conf = confservice['server']
    args.port       = conf.getint('port')
    args.workers    = conf.getint('workers')
    args.interfaces = conf.get('interfaces')

    return args


def main() -> None:
    """ Run the server as cli command
    """
    args = read_configuration()

    workers = args.workers
    if not args.proxy:
        validate_config_path('projects.cache','rootdir')
    else:
        # Do not run any qgis workers
        workers = 0

    run_server( port=args.port, address=args.interfaces, jobs=args.jobs, user=args.setuid, workers=workers )

    

