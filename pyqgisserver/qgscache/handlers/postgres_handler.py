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

from typing import Tuple, Optional
from datetime import datetime

from qgis.core import QgsProject
from pyqgisservercontrib.core import componentmanager

LOGGER = logging.getLogger('SRVLOG')

__all__= []

# List of allowed params in secure mode
ALLOWED_SECURE_PARAMS=('service','project','dbname','schema')

#
# Connect to database and check modification time
# Qgis is silent when failing to read a project from database and really 
# makes it hard to debug.
#
# So we check the timestamp ourselve and makes a consistency check to ensure
# That the project has benn read correctly
#

def _check_unsafe_url( insecure: bool, url: urllib.parse.ParseResult ) -> Tuple[str,datetime]:
    """ Check unsafe url
    """
    if insecure:      
        LOGGER.warning("Setting postgres connexion parameters in insecure mode %s", url.geturl())
        params = { k:v[0] for k,v in parse_qs(url.query).items() }
    else:
        # Secure mode: allow only secure parameter
        params = { k:v[0] for k,v in parse_qs(url.query).items() if k in ALLOWED_SECURE_PARAMS }

    # Support "postgres:<project>" short form
    prjname  = params.pop('project', url.path.strip('/'))
    if not prjname:
        LOGGER.error("Postgres handler: Missing project parameter '%s'", url.geturl()) 
        raise FileNotFoundError(url.geturl())

    schema   = params.pop('schema','public')
    database = params.pop('dbname',None)
 
    connexion_params = dict(host=url.hostname,
                            port=url.port,
                            user=url.username,
                            password=url.password,
                            database=database,
                            # Treats remaining params as supported psql client options
                            **params)
    if insecure:
        netloc = url.netloc
    else:
        netloc = f'{url.username}@' if url.username else ''

    # Create secure url
    params = '&'.join('%s=%s' % (k,v) for k,v in params.items())
    params = f"project={prjname}&schema={schema}&{params}"
    if database:
        params = f"{params}&dbname={database}"

    urlstr = f"postgresql://{netloc}/?{params}"

    try:
        LOGGER.debug("**** Postgresql connection params %s", connexion_params)
        conn   = psycopg2.connect(**connexion_params)
        cursor = conn.cursor()
        cursor.execute(f"select metadata from {schema}.qgis_projects where name='{prjname}'")
        if cursor.rowcount <= 0:
            raise FileNotFoundError(url.geturl())
        metadata = cursor.fetchone()[0]
        LOGGER.debug("**** Postgres metadata for '%s': %s", prjname, metadata)
        conn.close()
    except psycopg2.OperationalError as e:
        LOGGER.error("Postgres handler Connection error: %s", str(e))
        raise FileNotFoundError(urlstr)
    except psycopg2.Error as e:
        LOGGER.error("Postgres handler Connection error: %s", str(e))
        raise RuntimeError("Connection failed: %s", urlstr)

    modified_time = datetime.fromisoformat(metadata['last_modified_time'])

    return urlstr, modified_time
    

@componentmanager.register_factory('@3liz.org/cache/protocol-handler;1?scheme=postgres')
class PostgresProtocolHandler:
    """ Handle postgres protocol
    """
    def __init__(self):
        cnf = componentmanager.get_service('@3liz.org/config-service;1')
        self._insecure = cnf.getboolean('projects.cache','insecure', fallback=False)

    def get_project( self, url: urllib.parse.ParseResult, strict: Optional[bool]=None,
                     project: Optional[QgsProject]=None,
                     timestamp: Optional[datetime]=None) -> Tuple[QgsProject, datetime]:
        """ Create or return a project

            .. versionadded:: 1.3.2

            Supports the postgres:///projectname syntax
        """
        urlstr, modified_time = _check_unsafe_url( self._insecure, url )

        if timestamp is None or timestamp < modified_time:
            cachemngr = componentmanager.get_service('@3liz.org/cache-manager;1')
            project   = cachemngr.read_project(urlstr)
            timestamp = modified_time

        return project, timestamp

