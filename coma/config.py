import os
import ConfigParser
from . import xdgbasedirectory as xdg

_CONFIG_FILE='''\
[coma]
; experiment_file = experiment.${experiment_id}.xml
; experiment_index = experiment.index.xml
; measurement_file = measurement.${measurement_id}.xml
; measurement_index = measurement.index.xml
'''

class Config(object):
    def __init__(self, configfile='preferences.conf'):
        # full path to config file and experiment index
        self.configfile_path = ''
        self.experiment_index_path = ''

        self._experiment_index = ''
        self._configfile = ''
        
        # default config settings
        self.configfile = configfile
        self.experiment_file = 'experiment.${experiment_id}.xml'
        self.experiment_index = 'experiment.index.xml'
        self.measurement_file = 'measurement.${measurement_id}.xml'
        self.measurement_index = 'measurement.index.xml'

        # load file, if it exists
        self.load()

    @property
    def experiment_index(self):
        return self._experiment_index

    @experiment_index.setter
    def experiment_index(self, ei_):
        self._experiment_index = ei_
        self.experiment_index_path = self._expand_filename(ei_)

    @property
    def configfile(self):
        return self._configfile

    @configfile.setter
    def configfile(self, cf_):
        self._configfile = cf_
        self.configfile_path = self._expand_filename(cf_)

    def _expand_filename(self, f):
        f = os.path.expanduser(f)
        if os.path.exists(f):
            return os.path.abspath(f)
        p = xdg.save_config_path('coma')
        f = os.path.join(p, f)
        return f

    def load(self, p=None):
        if p is None:
            p = self.configfile_path
        if not os.path.exists(p):
            return
        
        # Read config file
        c = ConfigParser.RawConfigParser()
        c.read(p)
        if c.has_option('coma', 'experiment_file'):
            self.experiment_file = c.get('coma', 'experiment_file')
        if c.has_option('coma', 'experiment_index'):
            self.experiment_index = c.get('coma', 'experiment_index')
        if c.has_option('coma', 'measurement_file'):
            self.measurement_file = c.get('coma', 'measurement_file')
        if c.has_option('coma', 'measurement_index'):
            self.measurement_index = c.get('coma', 'measurement_index')

    def create(self,p=None):
        if p is None:
            p = self.configfile_path
        if os.path.exists(p):
            print('File already exists')
            return
        try:
            print('Creating config file "{}"'.format(p))
            f = open(p, 'w')
            f.write(_CONFIG_FILE)
            f.close()
        except IOError:
            print('Warning: Could not create config file "{}"'.format(p))
