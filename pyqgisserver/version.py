#
# Copyright 2018 3liz
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import sys

from pathlib import Path
from typing import Dict


def read_manifest() -> Dict:
    from importlib import resources

    # Read build manifest
    manifest = {'commitid': 'n/a', 'buildid': 'n/a', 'version': 'n/a'}
    try:
        with Path(str(resources.files('pyqgisserver')), 'build.manifest').open() as f:
            manifest.update(line.strip().split('=')[:2] for line in f.readlines())
    except Exception as e:
        print("WARNING: Failed to read manifest ! %s " % e, file=sys.stderr)  # noqa: T201
    return manifest


__manifest__ = read_manifest()

__version__ = __manifest__['version']
__description__ = "Qgis/HTTP/0MQ scalable server"
