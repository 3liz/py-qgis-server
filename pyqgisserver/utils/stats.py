#
# Copyright 2021 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from typing import Dict, Optional

try:
    import psutil
    HAVE_PSUTIL = True
except Exception:
    print("WARNING: Failed to load 'PSutil', system metrics will not be collected")
    HAVE_PSUTIL = False


def stats(pid: Optional[int]=None) -> Dict:
    """ Collect stats about process
        see https://psutil.readthedocs.io/en/latest/#processes
    """
    if not HAVE_PSUTIL:
        return {}

    proc = psutil.Process(pid)
    return dict(
        mem_usage=proc.memory_info().rss,
        mem_percent=proc.memory_percent(),
    )    
