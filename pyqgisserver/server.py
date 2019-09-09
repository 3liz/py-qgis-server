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

    manifest = { 'commitid':'n/a', 'buildid':'n/a', 'version':__version__ }

    # Read build manifest
    mnpath = os.path.join(os.getenv('QGSRV_DATA_PATH','/'),'build.manifest')
    if mnpath and os.path.exists(mnpath):
        with open(mnpath) as fd:
            manifest.update(l.strip().split('=')[:2] for l in fd.readlines())
    if manifest['version'] != __version__:
        print("WARNING: manifest version does not match current version", file=sys.stderr)

    program = os.path.basename(sys.argv[0])
    print("{program} {version} (build {buildid},commit {commitid})".format(program=program,**manifest),
          file=sys.stderr)
    if mnpath:
        print("build manifest: %s" % mnpath, file=sys.stderr)


def read_configuration(argv: List[str]=None) -> None:
    """ Parse command line and read configuration file
    """
    if argv is None:
        argv = sys.argv[1:]

    cli_parser = argparse.ArgumentParser(description=__description__)

    cli_parser.add_argument('--logging', choices=['debug', 'info', 'warning', 'error'], 
            default=argparse.SUPPRESS, help="set log level")
    cli_parser.add_argument('-c','--config', metavar='PATH', nargs='?', dest='config',
            default=None, help="Configuration file")
    cli_parser.add_argument('--version', action='store_true', 
            default=False, help="Return version number and exit")
    cli_parser.add_argument('-p','--port'    , type=int, help="http port", dest='port', default=argparse.SUPPRESS)
    cli_parser.add_argument('-b','--bind'    , metavar='IP',  default=argparse.SUPPRESS, help="Interface to bind to", dest='interface')
    cli_parser.add_argument('-w','--workers' , metavar='NUM', type=int, default=argparse.SUPPRESS, help="Num workers", dest='workers')
    cli_parser.add_argument('-j','--jobs'    , metavar='NUM', type=int, default=1, help="Num server instances", dest='jobs')
    cli_parser.add_argument('-u','--setuid'  , default='', help="uid to switch to", dest='setuid')
    cli_parser.add_argument('--rootdir'  , default=argparse.SUPPRESS, metavar='PATH', help='Path to qgis projects')
    cli_parser.add_argument('--proxy'    , action='store_true', default=False, help='Run only as proxy')

    args = cli_parser.parse_args(argv)

    if args.version:
        print_version()
        sys.exit(1)

    if args.config:
        with open(args.config, mode='rt') as config_file:
            read_config_file(config_file)

    config_dict = { 'logging': {}, 'cache': {}, 'server':{}, }

    conf = get_config('server')

    # Override with cli arguments
    if 'logging' in args: 
        config_dict['logging']['level'] = args.logging.upper()
    if 'rootdir' in args:
        config_dict['cache']['rootdir'] = args.rootdir
    if 'interface' in args:
        config_dict['server']['interfaces'] = args.interface
    else:
        args.interface = conf['interfaces']
    if 'port' in args:
        config_dict['server']['port']  = str(args.port)
    else:
        args.port =  conf.getint('port')
    if 'workers' in args:
        config_dict['server']['workers'] = str(args.workers)
    else:
        args.workers = conf.getint('workers')

    read_config_dict(config_dict)

    print_version()

    # set log level
    setup_log_handler(get_config('logging')['level'])
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

    

