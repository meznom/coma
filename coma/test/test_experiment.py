import unittest
from collections import OrderedDict
import os
import shutil
import copy
from coma import Measurement, Experiment, ExperimentError, Config, IndexFile

_EXP_FILE_1='''\
<experiment>
  <info>
    <experiment_id>10</experiment_id>
    <description>Muh</description>
  </info>
</experiment>
'''

_EXP_FILE_2='''\
<experiment>
  <info>
    <experiment_id>20</experiment_id>
    <description>Miau</description>
  </info>
</experiment>
'''

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

def run_example_experiment(e, r=(0,10)):
    e.start()
    s = ExampleSimulation()
    for i in range(*r):
        m = e.new_measurement()
        m.start()
        s.a = i
        s.init()
        s.run()
        m.end()
        m.save(s)
    e.end()
    e.save()

class TestExperiment(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.d = os.path.join(base_dir, 'testexperiment')
        self.fi = os.path.join(self.d, 'coma.index.xml')
        
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

        os.mkdir(self.d)
        i = IndexFile(self.fi, 'experiment')
        i.createfile()
        i.increment()
        i.increment()

        self.c = Config()
        self.c.experiment_index = self.fi

    def tearDown(self):
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

    def test_create_experiment_with_id_in_name(self):
        # create a new experiment
        e = Experiment(self.d, description='Blub', config=self.c)
        
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000003.xml')))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=self.c)

        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000003.xml')))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

    def test_create_experiment_without_id_in_name(self):
        c = copy.copy(self.c)
        c.experiment_file = 'experiment.xml'
        
        # create a new experiment
        e = Experiment(self.d, description='Blub', config=c)
        
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.xml')))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=c)

        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.xml')))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

    def test_create_experiment_with_specific_id(self):
        # create a new experiment
        e = Experiment(self.d, id=42, description='Blub', config=self.c)
        
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000042.xml')))
        self.assertEquals(e.id, 42)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=self.c)

        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000042.xml')))
        self.assertEquals(e.id, 42)
        self.assertEquals(e.description, 'Blub')

    def test_create_experiment_without_index_file(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index.xml'
        
        e = Experiment(self.d,config=c)
        self.assertFalse(os.path.exists(c.experiment_index_path))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.none.xml')))
        self.assertEquals(e.id, None)

        e = Experiment(self.d,id=42,config=c)
        self.assertFalse(os.path.exists(c.experiment_index_path))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000042.xml')))
        self.assertEquals(e.id, 42)

    def test_load_experiment_with_id(self):
        fn = os.path.join(self.d, 'experiment.000010.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_1)
        f.close()

        e = Experiment(self.d, config=self.c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')

    def test_load_experiment_without_id(self):
        c = copy.copy(self.c)
        c.experiment_file = 'experiment.xml'

        fn = os.path.join(self.d, 'experiment.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_1)
        f.close()

        e = Experiment(self.d, config=c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')

    def test_load_experiment_with_wrong_id(self):
        fn = os.path.join(self.d, 'experiment.000010.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_2) # has id 20
        f.close()
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, config=self.c)
        os.remove(fn)
        
        fn = os.path.join(self.d, 'experiment.000020.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_2)
        f.close()
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, id=42, config=self.c)
        os.remove(fn)

        c = copy.copy(self.c)
        c.experiment_file = 'experiment.xml'
        fn = os.path.join(self.d, 'experiment.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_2)
        f.close()
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, id=42, config=c)
        os.remove(fn)

    def test_load_experiment_with_multiple_experiment_files_in_directory(self):
        fn = os.path.join(self.d, 'experiment.000010.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_1)
        f.close()
        fn = os.path.join(self.d, 'experiment.000020.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_2)
        f.close()

        e = Experiment(self.d, id=20, config=self.c)
        self.assertEquals(e.id, 20)
        self.assertEquals(e.description, 'Miau')

        with self.assertRaises(ExperimentError):
            # TODO: maybe, in this case, we should better create a new
            # experiment with id 42?
            e = Experiment(self.d, id=42, config=self.c)
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, config=self.c)

    def test_load_experiment_with_wrong_filename(self):
        c = copy.copy(self.c)
        c.experiment_file = 'experiment.xml'
        fn = os.path.join(self.d, 'experiment.000010.xml')
        f = open(fn, 'w')
        f.write(_EXP_FILE_1)
        f.close()

        # creates a new experiment file
        e = Experiment(self.d, config=c)
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000010.xml')))
    
    def test_standalone_experiment(self):
        e = Experiment(self.d,config=self.c)
        
        self.assertTrue(os.path.exists(self.d))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.index.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000003.xml')))

        e.description = 'Test experiment'
        run_example_experiment(e)

        del(e)
        e = Experiment(self.d,config=self.c)
        self.assertEqual(e.id, 3)
        self.assertEqual(e.description, 'Test experiment')
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)

    def test_experiment_constructor(self):
        e = Experiment(self.d, 1, config=self.c,
                       description='A test experiment',
                       tags=['test','experiment'])
        del(e)
        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.id, 1)
        self.assertEqual(e.description, 'A test experiment')
        self.assertEqual(e.tags, ['test','experiment'])

    def test_resetting_experiment(self):
        e = Experiment(self.d, config=self.c)
        run_example_experiment(e)

        del(e)
        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)
        
        e = Experiment(self.d,config=self.c)
        e.reset()
        run_example_experiment(e, (20,25))
        e.start()

        del(e)
        e = Experiment(self.d,config=self.c)
        self.assertEqual(e.number_of_measurements(), 5)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i+20)

    def test_experiment_with_different_measurement_filename(self):
        c = copy.copy(self.c)
        c.measurement_file = '${measurement_id}.xml'
        e = Experiment(self.d, config=c)
        run_example_experiment(e)

        self.assertTrue(os.path.exists(os.path.join(self.d, '000001.xml')))
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['parameters/a'], i)

        # An invalid measurement_file name: the measurement_id is missing
        # In this case, things can't and won't work properly.
        c = copy.copy(self.c)
        c.measurement_file = 'blah.xml'
        e = Experiment(self.d, config=c)
        run_example_experiment(e)

        self.assertTrue(os.path.exists(os.path.join(self.d, 'blah.xml')))
        self.assertEqual(e.number_of_measurements(), 1)

    def test_continuing_measurements_in_experiment(self):
        e = Experiment(self.d,config=self.c)
        run_example_experiment(e)

        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)

        del(e)
        e = Experiment(self.d,config=self.c)
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)
        
        e = Experiment(self.d,config=self.c)
        run_example_experiment(e, (20,25))

        del(e)
        e = Experiment(self.d,config=self.c)
        self.assertEqual(e.number_of_measurements(), 15)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            if i < 10:
                self.assertEqual(m['parameters/a'], i)
            else:
                self.assertEqual(m['parameters/a'], i+10)

    def test_experiment_with_missing_measurements(self):
        e = Experiment(self.d,config=self.c)
        run_example_experiment(e)

        f1 = os.path.join(self.d, 'measurement.000001.xml')
        f2 = os.path.join(self.d, 'measurement.000007.xml')
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        os.remove(f1)
        os.remove(f2)

        self.assertEqual(e.number_of_measurements(), 8)
        ns = [1,2,3,4,5,7,8,9]
        c = 0
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['parameters/a'], ns[i])
            c += 1
        self.assertEqual(c,8)
