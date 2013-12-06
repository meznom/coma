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
; serializer_getstate = coma_getstate
; serializer_setstate = coma_setstate
'''

CONFIG_OPTIONS = [
    'experiment_file',
    'experiment_index',
    'measurement_file',
    'measurement_index',
    'archive_default_format',
    'serializer_getstate',
    'serializer_setstate'
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
    for o in opts:
        if c.has_option('coma', o):
            d[o] = c.get('coma', o)
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

# class Config(object):
#     def __init__(self, configfile='preferences.conf'):
#         self.configfile = expand_path(configfile)
# 
#         # default config settings
#         self._c = {}
#         self._c['experiment_file'] = 'experiment.${experiment_id}'
#         self._c['experiment_index'] = 'experiment.index'
#         self._c['measurement_file'] = 'measurement.${measurement_id}'
#         self._c['measurement_index'] = 'measurement.index'
#         self._c['archive_default_format'] = 'json'
#         self._c['serializer_getstate'] = 'coma_getstate'
#         self._c['serializer_setstate'] = 'coma_setstate'
# 
#         # load file, if it exists
#         self.load()
# 
#     def __getitem__(self, i):
#         return self._c[i]
# 
#     def __setitem__(self, i, v):
#         self._c[i] = v
# 
#     def has_key(self, i):
#         return self._c.has_key(i)
# 
#     def load(self, p=None):
#         if p is None:
#             p = self.configfile
#         if not os.path.exists(p):
#             return
#         
#         # Read config file
#         c = ConfigParser.RawConfigParser()
#         c.read(p)
#         if c.has_option('coma', 'experiment_file'):
#             self._c['experiment_file'] = c.get('coma', 'experiment_file')
#         if c.has_option('coma', 'experiment_index'):
#             self._c['experiment_index'] = c.get('coma', 'experiment_index')
#         if c.has_option('coma', 'measurement_file'):
#             self._c['measurement_file'] = c.get('coma', 'measurement_file')
#         if c.has_option('coma', 'measurement_index'):
#             self._c['measurement_index'] = c.get('coma', 'measurement_index')
#         if c.has_option('coma', 'archive_default_format'):
#             self._c['archive_default_format'] = c.get('coma', 'archive_default_format')
#         if c.has_option('coma', 'serializer_getstate'):
#             self._c['serializer_getstate'] = c.get('coma', 'serializer_getstate')
#         if c.has_option('coma', 'serializer_setstate'):
#             self._c['serializer_setstate'] = c.get('coma', 'serializer_setstate')
# 
#     def create(self,p=None):
#         if p is None:
#             p = self.configfile
#         if os.path.exists(p):
#             print('File already exists')
#             return
#         try:
#             print('Creating config file "{}"'.format(p))
#             f = open(p, 'w')
#             f.write(_CONFIG_FILE)
#             f.close()
#         except IOError:
#             print('Warning: Could not create config file "{}"'.format(p))
