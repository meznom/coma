# Copyright (c) 2013, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

import datetime

def current_date_as_string():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
