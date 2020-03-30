#
# Copyright 2020 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

""" Postgres protocol handler

    See 
      * http://www.bostongis.com/blog/index.php?/archives/271-New-in-QGIS-3.2-Save-Project-to-PostgreSQL.html
      * https://github.com/qgis/QGIS-Enhancement-Proposals/issues/118

    project filename syntax for posgresql

    ```
    postgres://[user[:pass]@]host[:port]/?dbname=X&schema=Y&project=Z
    ```

    How does QGIS store the project?

    QGIS creates a table called qgis_projects in whatever schema you had specified, each project is stored as a separate row.
    
    columns are: 'name', 'metadata', 'content'

    Metadata is a json data that contains the 'last_modified_time' field. 


"""
import logging
import urllib.parse

import psycopg2

from urllib.parse import parse_qs

from typing import Tuple
from datetime import datetime

from qgis.core import QgsProject
from pyqgisservercontrib.core import componentmanager

LOGGER = logging.getLogger('SRVLOG')

__all__= []

@componentmanager.register_factory('@3liz.org/cache/protocol-handler;1?scheme=postgres')
class PostgresProtocolHandler:
    """ Handle postgres protocol
    """
    def __init__(self):
        pass

    def get_project( self, url: urllib.parse.ParseResult, project: QgsProject=None,
                     timestamp: datetime=None) -> Tuple[QgsProject, datetime]:
        """ Create or return a proect
        """
        params = { k:v[0] for k,v in parse_qs(url.query).items() }

        try:
            project  = params.pop('project')
            schema   = params.pop('schema','public')
            database = params.pop('dbname',None)
        except KeyError as exc:
            LOGGER.error("Postgres handler: Missing parameter %s: %s", url.geturl(), str(exc)) 
            raise FileNotFoundError(url.geturl())

        connexion_params = dict(
           host=url.hostname,
           port=url.port,
           user=url.username,
           password=url.password,
           database=database,
           # Treats remaining params as supported psql client options
           **params 
        )

        # Connect to database and check modification time
        try:
            LOGGER.debug("**** Postgresql connection params %s", connexion_params)
            conn   = psycopg2.connect(**connexion_params)
            cursor = conn.cursor()
            cursor.execute("select metadata from %s.qgis_projects where name='%s'" % (schema,project))
            if cursor.rowcount <= 0:
                raise FileNotFoundError(url.geturl())
            metadata = cursor.fetchone()[0]
            LOGGER.debug("**** Postgres metadata for '%s': %s", project, metadata)
            conn.close()
        except psycopg2.OperationalError as e:
            LOGGER.error("Postgres handler Connection error: %s", str(e))
            raise FileNotFoundError(url.geturl())
        except psycopg2.Error as e:
            LOGGER.error("Postgres handler Connection error: %s", str(e))
            raise RuntimeError("Connection failed: %s", url.geturl())

        modified_time = datetime.fromisoformat(metadata['last_modified_time'])
        if timestamp is None or timestamp < modified_time:
            cachmngr  = componentmanager.get_service('@3liz.org/cache-manager;1')
            project   = cachmngr.read_project(url.geturl())
            timestamp = modified_time

        return project, timestamp

