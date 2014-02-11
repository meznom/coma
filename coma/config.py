# Copyright (c) 2013, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

import os
import ConfigParser
from .serialization import archive_exists
from .indexfile import IndexFile

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

CONFIG_DIR = '~/.config/coma'

def expand_path(f):
    f = os.path.expanduser(f)
    if os.path.exists(f) or archive_exists(f):
        f = os.path.abspath(f)
    else:
        p = os.path.expanduser(CONFIG_DIR)
        f = os.path.join(p, f)
    return f

def load_config(configfile='preferences.conf'):
    """Load config from a file.

    The configuration is returned as a dictionary. If no filename is specified
    the default config file in "~/.config/coma/preferences.conf" is used.
    """
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
    configfile = os.path.expanduser(configfile)
    if os.path.exists(configfile):
        print('Config file "{}" already exists'.format(configfile))
        return
    try:
        print('Creating config file "{}"'.format(configfile))
        f = open(configfile, 'w')
        f.write(DEFAULT_CONFIG_FILE)
        f.close()
    except IOError:
        print('Warning: Could not create config file "{}"'.format(configfile))

def create_default_config(create_experiment_index=True):
    """Create a default config file and experiment index file in ~/.config/coma."""
    p = os.path.expanduser(CONFIG_DIR)
    cfile = os.path.join(p, 'preferences.conf')
    ifile = os.path.join(p, 'experiment.index')
    if not os.path.exists(p):
        print('Creating directory {}'.format(p))
        os.mkdir(p)
    create_config_file(cfile)
    if create_experiment_index:
        i = IndexFile(ifile, 'experiment')
        if i.exists():
            print('Experiment index "{}" already exists'.format(ifile))
        else:
            print('Creating experiment index "{}"'.format(ifile))
            i.create()
