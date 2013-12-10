# Copyright (c) 2013, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

import os
import ConfigParser
from .serialization import archive_exists

DEFAULT_CONFIG_FILE='''\
[coma]
; experiment_file = experiment.${experiment_id}
; experiment_index = experiment.index
; measurement_file = measurement.${measurement_id}
; measurement_index = measurement.index
; archive_default_format = json
; archive_pretty_print = yes
; serializer_getstate = coma_getstate
; serializer_setstate = coma_setstate
'''

CONFIG_OPTIONS = [
    ('experiment_file', 'str'),
    ('experiment_index', 'str'),
    ('measurement_file', 'str'),
    ('measurement_index', 'str'),
    ('archive_default_format', 'str'),
    ('archive_pretty_print', 'bool'),
    ('serializer_getstate', 'str'),
    ('serializer_setstate', 'str')
]

def expand_path(f):
    configdir_path = '~/.config/coma'
    f = os.path.expanduser(f)
    if os.path.exists(f) or archive_exists(f):
        f = os.path.abspath(f)
    else:
        p = os.path.expanduser(configdir_path)
        f = os.path.join(p, f)
    return f

def load_config(configfile='preferences.conf'):
    f = expand_path(configfile)
    if not os.path.exists(f):
        return {}

    c = ConfigParser.RawConfigParser()
    c.read(f)
    d = {}
    opts = CONFIG_OPTIONS
    for o,t in opts:
        if c.has_option('coma', o):
            if t == 'str':
                d[o] = c.get('coma', o)
            elif t == 'bool':
                d[o] = c.getboolean('coma', o)
    return d

def create_config_file(configfile):
    if os.path.exists(configfile):
        print('File already exists')
        return
    try:
        print('Creating config file "{}"'.format(configfile))
        f = open(configfile, 'w')
        f.write(DEFAULT_CONFIG_FILE)
        f.close()
    except IOError:
        print('Warning: Could not create config file "{}"'.format(configfile))
