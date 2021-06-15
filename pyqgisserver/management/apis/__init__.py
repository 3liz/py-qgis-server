#
# Copyright 2021 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from pyqgisserver.management.apis import plugins, cache


def register_management_apis( serverIface ):
    """ Return management Qgis server apis
    """
    plugins.register( serverIface )
    cache.register( serverIface )    

