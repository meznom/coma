# Copyright (c) 2013, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

import unittest
import os
import shutil
from coma import expand_path, load_config, create_config_file

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
archive_default_format = xml
'''

class TestConfig(unittest.TestCase):
    def test_expand_path_expands_paths_correctly(self):
        open('__pref.conf', 'w').close()
        open('__index.xml', 'w').close()
        open('__index2.json', 'w').close()

        self.assertEqual(expand_path('__pref.conf'), os.path.abspath('__pref.conf'))
        self.assertEqual(expand_path('__index'), os.path.abspath('__index'))
        self.assertEqual(expand_path('__index2'), os.path.abspath('__index2'))
        self.assertEqual(expand_path('__index3'), os.path.expanduser('~/.config/coma/__index3'))

        os.remove('__pref.conf')
        os.remove('__index.xml')
        os.remove('__index2.json')

    def test_create_config_file(self):
        create_config_file('__pref.conf')
        f = open('__pref.conf')
        ls = f.readlines()
        f.close()
        self.assertEqual(len(ls), 8)

        create_config_file('__pref.conf')
        # should print a message

        os.remove('__pref.conf')

    def test_load_config_file(self):
        f = open('__pref1.conf', 'w')
        f.write(_CONFIG_FILE_1)
        f.close()
        f = open('__pref2.conf', 'w')
        f.write(_CONFIG_FILE_2)
        f.close()

        c = load_config('__pref1.conf')
        self.assertEqual(len(c), 2)
        self.assertEqual(c['experiment_file'], 'muh.${experiment_id}')
        self.assertEqual(c['experiment_index'], 'quark')

        c = load_config('__pref2.conf')
        self.assertEqual(len(c), 5)
        self.assertEqual(c['experiment_file'], 'experiment.readme')
        self.assertEqual(c['experiment_index'], '~/experiments.index')
        self.assertEqual(c['measurement_file'], '${measurement_id}')
        self.assertEqual(c['measurement_index'], 'measurements.index')
        self.assertEqual(c['archive_default_format'], 'xml')
        
        os.remove('__pref1.conf')
        os.remove('__pref2.conf')

    def test_load_nonexistent_config_file(self):
        c = load_config('muh')
        self.assertEqual(c, {})
