#
# Copyright 2021 3liz
# Author David Marteau
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
    Collect global stats
"""
from time import time
from datetime import datetime, timedelta

class Stats:

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self.num_requests = 0
        self.num_errors   = 0
        self.start_time   = time()
       
    def json(self):
        """ Return a json payload
        """
        return dict(
            num_request = self.num_requests,
            num_errors  = self.num_errors,
            start_date  = datetime.fromtimestamp(self.start_time).isoformat(),
            uptime      = timedelta(seconds=time() - self.start_time).total_seconds(),
        )

