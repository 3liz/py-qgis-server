# -*- encoding=utf-8 -*-
#
# Copyrights 2106 3Liz  
# Author: David Marteau (dmarteau@3liz.com)
#
from __future__ import print_function

import os
import sys
from ..config import parse_commandline, parse_configuration, read_property_file
from ..version import __version__

default_config = dict(
    worker_key="map.service.%(workspace)s",
    notify_key="map.notify.%(workspace)s",
    notify_exchange="map.exchange.notify",
    qgis_python_path="/usr/local/share/qgis/python",
    manifest="/MANIFEST",
    qgis_manifest="/QGIS_MANIFEST",
    logger_exchange='qgis_logger'
)


def read_configuration():
    """ Set up configuration
    """
    import argparse

    # Get the configuration from
    # the environnment variable SWARM_CONFIG
    version_tag = "Qgis server worker/{}".format(__version__)
    parser = argparse.ArgumentParser(description=version_tag)
    parser.add_argument("--workspace",nargs='?',default=None, help="worker workspace") 
    parser.add_argument("--noop", action='store_true', default=False, help="Dump config and exit") 

    args = parse_commandline(cli_parser=parser)

    workspace = args.workspace or os.environ.get("WORKSPACE")
    assert workspace is not None, "workspace is not defined"

    default_config.update(workspace=workspace)
    config = parse_configuration(args, config_var="WORKER_CONFIG", default_config=default_config)

    # Read manifests
    if os.path.exists(config.manifest):
        read_property_file(config.manifest, parser=config, section="manifest")
    if os.path.exists(config.qgis_manifest):
        read_property_file(config.qgis_manifest, parser=config, section="qgis_manifest")

    if args.noop:
        print("\n#### Configuration:\n")
        print(config.dumps())
        sys.exit(1)

    return config


