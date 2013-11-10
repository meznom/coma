import unittest
import os
import shutil
from coma import Config

_CONFIG_FILE_1='''\
[coma]
experiment_file = muh.${experiment_id}
experiment_index = quark
'''

_CONFIG_FILE_2='''\
[coma]
experiment_file = experiment.readme
experiment_index = ~/experiments.index
measurement_file = ${measurement_id}
measurement_index = measurements.index
default_format = xml
'''

class TestConfig(unittest.TestCase):
    def test_default_config(self):
        c = Config()
        self.assertEqual(c.configfile, 'preferences.conf')
        self.assertEqual(c.experiment_index, 'experiment.index')
        self.assertEqual(c.configfile_path, 
                         os.path.expanduser('~/.config/coma/preferences.conf'))
        self.assertEqual(c.experiment_index_path, 
                         os.path.expanduser('~/.config/coma/experiment.index'))
        self.assertEqual(c.default_format, 'json')
        
    def test_expands_paths_correctly(self):
        open('__pref.conf', 'w').close()
        open('__index.xml', 'w').close()
        open('__index2.json', 'w').close()

        c = Config()
        c.configfile = '__pref.conf'
        c.experiment_index = '__index'

        self.assertEqual(c.configfile_path,
                         os.path.abspath('__pref.conf'))
        self.assertEqual(c.experiment_index_path,
                         os.path.abspath('__index'))

        c.experiment_index = '__index2'
        self.assertEqual(c.experiment_index_path,
                         os.path.abspath('__index2'))

        c.experiment_index = '__index3'
        self.assertEqual(c.experiment_index_path,
                         os.path.expanduser('~/.config/coma/__index3'))

        os.remove('__pref.conf')
        os.remove('__index.xml')
        os.remove('__index2.json')

    def test_create_config_file(self):
        c = Config()
        c.create('__pref.conf')
        f = open('__pref.conf')
        ls = f.readlines()
        f.close()
        self.assertEqual(len(ls), 6)

        c = Config('__pref.conf')
        c.create()
        # should print a message

        os.remove('__pref.conf')

    def test_load_config_file(self):
        f = open('__pref1.conf', 'w')
        f.write(_CONFIG_FILE_1)
        f.close()
        f = open('__pref2.conf', 'w')
        f.write(_CONFIG_FILE_2)
        f.close()

        c = Config('__pref1.conf')
        self.assertEqual(c.experiment_file, 'muh.${experiment_id}')
        self.assertEqual(c.experiment_index, 'quark')
        self.assertEqual(c.experiment_index_path, 
                         os.path.expanduser('~/.config/coma/quark'))
        self.assertEqual(c.default_format, 'json')

        c.configfile = '__pref2.conf'
        c.load()
        self.assertEqual(c.experiment_file, 'experiment.readme')
        self.assertEqual(c.experiment_index, '~/experiments.index')
        self.assertEqual(c.measurement_file, '${measurement_id}')
        self.assertEqual(c.measurement_index, 'measurements.index')
        self.assertEqual(c.experiment_index_path, 
                         os.path.expanduser('~/experiments.index'))
        self.assertEqual(c.default_format, 'xml')
        
        os.remove('__pref1.conf')
        os.remove('__pref2.conf')
