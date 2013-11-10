import unittest
from collections import OrderedDict
import os
import shutil
import copy
from coma import Measurement, Config

class ExampleSimulation(object):
    def __init__(self):
        self.program = 'ExampleSimulation'
        self.version = 0.1
        self.a = 1
        self.b = 2
        self.energies = [1,2,3,4]

    def init(self):
        pass

    def run(self):
        pass

    def __getstate__(self):
        i = OrderedDict([
            ('parameters', OrderedDict([
                        ('a', self.a),
                        ('b', self.b)])),
            ('results', OrderedDict([
                        ('energies', self.energies)]))
            ])
        return i

class TestMeasurement():
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.f = os.path.join(base_dir, 'testmeasurement')
        self.fn = os.path.join(base_dir, 'testmeasurement.' + self.format)

        self.c = Config()
        self.c.default_format = self.format
        
        if os.path.exists(self.fn):
            os.remove(self.fn)

    def tearDown(self):
        if os.path.exists(self.fn):
            os.remove(self.fn)

    def test_create_measurement_without_id(self):
        m = Measurement(self.f, config=self.c)
        s = ExampleSimulation()
        
        m.start()
        s.init()
        s.run()
        m.end()
        m.save(s)

        self.assertEqual(m['info/measurement_id'], None)
        self.assertTrue(m['info/start_date'] is not None)
        self.assertTrue(m['info/end_date'] is not None)
        self.assertEqual(m['info/program'], 'ExampleSimulation')
        self.assertEqual(m['info/version'], 0.1)
        self.assertEqual(m['parameters/a'], 1)
        self.assertEqual(m['parameters/b'], 2)
        self.assertEqual(m['results/energies'], [1,2,3,4])
        # general measurement properties can be accessed directly
        self.assertEqual(m.id, None)
        self.assertTrue(m.start_date is not None)
        self.assertTrue(m.end_date is not None)
        

        m = Measurement(self.f, config=self.c)
        self.assertEqual(m['info/measurement_id'], None)
        self.assertTrue(m['info/start_date'] is not None)
        self.assertTrue(m['info/end_date'] is not None)
        self.assertEqual(m['info/program'], 'ExampleSimulation')
        self.assertEqual(m['info/version'], 0.1)
        self.assertEqual(m['parameters/a'], 1)
        self.assertEqual(m['parameters/b'], 2)
        self.assertEqual(m['results/energies'], [1,2,3,4])
        # general measurement properties can be accessed directly
        self.assertEqual(m.id, None)
        self.assertTrue(m.start_date is not None)
        self.assertTrue(m.end_date is not None)

    def test_create_measurement_with_id(self):
        m = Measurement(self.f, id=10, config=self.c)
        s = ExampleSimulation()
        
        m.start()
        s.init()
        s.run()
        m.end()
        m.save(s)

        self.assertEqual(m['info/measurement_id'], 10)
        self.assertTrue(m['info/start_date'] is not None)
        self.assertTrue(m['info/end_date'] is not None)
        self.assertEqual(m['info/program'], 'ExampleSimulation')
        self.assertEqual(m['info/version'], 0.1)
        self.assertEqual(m['parameters/a'], 1)
        self.assertEqual(m['parameters/b'], 2)
        self.assertEqual(m['results/energies'], [1,2,3,4])
        # general measurement properties can be accessed directly
        self.assertEqual(m.id, 10)
        self.assertTrue(m.start_date is not None)
        self.assertTrue(m.end_date is not None)

        m = Measurement(self.f, config=self.c)
        self.assertEqual(m['info/measurement_id'], 10)
        self.assertTrue(m['info/start_date'] is not None)
        self.assertTrue(m['info/end_date'] is not None)
        self.assertEqual(m['info/program'], 'ExampleSimulation')
        self.assertEqual(m['info/version'], 0.1)
        self.assertEqual(m['parameters/a'], 1)
        self.assertEqual(m['parameters/b'], 2)
        self.assertEqual(m['results/energies'], [1,2,3,4])
        # general measurement properties can be accessed directly
        self.assertEqual(m.id, 10)
        self.assertTrue(m.start_date is not None)
        self.assertTrue(m.end_date is not None)

    def test_different_ways_to_access_measurement_data(self):
        i = OrderedDict([('program', 'TestProgram'), ('version', '0.0.0.1')])
        l = OrderedDict([('V1', 40), ('type', 'wire'), ('boas', [1,2,3,4,5])])
        p = OrderedDict([('t', 1), ('T', 0.1), ('layout', l), ('cs', [6,7,8])])
        a = OrderedDict([('info', i), ('parameters', p)])

        m = Measurement(self.f, config=self.c)
        m.save(a)

        # direct access
        self.assertEqual(m['info']['program'], 'TestProgram')
        self.assertEqual(m['info']['version'], '0.0.0.1')
        self.assertEqual(m['parameters']['t'], 1)
        self.assertEqual(m['parameters']['T'], 0.1)
        self.assertEqual(m['parameters']['cs'], [6,7,8])
        self.assertEqual(m['parameters']['layout']['V1'], 40)
        self.assertEqual(m['parameters']['layout']['type'], 'wire')
        self.assertEqual(m['parameters']['layout']['boas'], [1,2,3,4,5])

        # path style access
        self.assertEqual(m['info/program'], 'TestProgram')
        self.assertEqual(m['info/version'], '0.0.0.1')
        self.assertEqual(m['parameters/t'], 1)
        self.assertEqual(m['parameters/T'], 0.1)
        self.assertEqual(m['parameters/cs'], [6,7,8])
        self.assertEqual(m['parameters/layout/V1'], 40)
        self.assertEqual(m['parameters/layout/type'], 'wire')
        self.assertEqual(m['parameters/layout/boas'], [1,2,3,4,5])

        # object style access
        self.assertEqual(m.info.program, 'TestProgram')
        self.assertEqual(m.info.version, '0.0.0.1')
        self.assertEqual(m.parameters.t, 1)
        self.assertEqual(m.parameters.T, 0.1)
        self.assertEqual(m.parameters.cs, [6,7,8])
        self.assertEqual(m.parameters.layout.V1, 40)
        self.assertEqual(m.parameters.layout.type, 'wire')
        self.assertEqual(m.parameters.layout.boas, [1,2,3,4,5])

        # Write access works, but is not recommended
        m.parameters.layout.boas = 'muh'
        self.assertEqual(m['parameters/layout/boas'], 'muh')

class TestMeasurementXML(TestMeasurement, unittest.TestCase):
    def __init__(self, method='runTest'):
        super(TestMeasurementXML, self).__init__(method)
        self.format = 'xml'

class TestMeasurementJson(TestMeasurement, unittest.TestCase):
    def __init__(self, method='runTest'):
        super(TestMeasurementJson, self).__init__(method)
        self.format = 'json'
