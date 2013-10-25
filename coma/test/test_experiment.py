import unittest
from collections import OrderedDict
import os
import shutil
from coma import Measurement, Experiment, Config, IndexFile

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

        self.c = Config()
        self.c.experiment_index = self.fi

    # def tearDown(self):
    #     if os.path.exists(self.d):
    #         shutil.rmtree(self.d)

    def test_create_experiment(self):
        e = Experiment(self.d, config=self.c)
        print(e.file)


###    def setUp(self):
###        base_dir = os.path.dirname(__file__)
###        self.f = os.path.join(base_dir, 'testmeasurement.xml')
###        self.d = os.path.join(base_dir, 'testexperiment')
###        self.ed = os.path.join(base_dir, 'testexperimentsdirectory')
###
###        if os.path.exists(self.f):
###            os.remove(self.f)
###        if os.path.exists(self.d):
###            shutil.rmtree(self.d)
###        if os.path.exists(self.ed):
###            shutil.rmtree(self.ed)
###
###    def tearDown(self):
###        if os.path.exists(self.f):
###            os.remove(self.f)
###        if os.path.exists(self.d):
###            shutil.rmtree(self.d)
###        if os.path.exists(self.ed):
###            shutil.rmtree(self.ed)
###    
###    def test_standalone_measurement(self):
###        m = Measurement(self.f)
###        s = ExampleSimulation()
###        
###        m.start()
###        s.init()
###        s.run()
###        m.end()
###        m.save(s)
###
###        self.assertEqual(m['info/measurement_id'], None)
###        self.assertEqual(m['info/program'], 'ExampleSimulation')
###        self.assertEqual(m['info/version'], 0.1)
###        self.assertEqual(m['parameters/a'], 1)
###        self.assertEqual(m['parameters/b'], 2)
###        self.assertEqual(m['results/energies'], [1,2,3,4])
###
###        del(m)
###        m = Measurement(self.f)
###        self.assertEqual(m['info/measurement_id'], None)
###        self.assertEqual(m['info/program'], 'ExampleSimulation')
###        self.assertEqual(m['info/version'], 0.1)
###        self.assertEqual(m['parameters/a'], 1)
###        self.assertEqual(m['parameters/b'], 2)
###        self.assertEqual(m['results/energies'], [1,2,3,4])
###
###    def test_standalone_experiment(self):
###        e = Experiment(self.d)
###        
###        self.assertTrue(os.path.exists(self.d))
###        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurements.index.xml')))
###        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.readme.xml')))
###
###        e.description = 'Test experiment'
###
###        e.start()
###        s = ExampleSimulation()
###
###        for i in range(10):
###            m = e.new_measurement()
###            m.start()
###            s.a = i
###            s.init()
###            s.run()
###            m.end()
###            m.save(s)
###
###        e.end()
###        e.save()
###
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(e['info/experiment_id'], None)
###        self.assertEqual(e['info/description'], 'Test experiment')
###        self.assertEqual(len(e.measurements), 10)
###        for i in range(1,11):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i-1)
###
###    def test_experiment_constructor(self):
###        e = Experiment(self.d, 1,
###                       description='A test experiment',
###                       tags=['test','experiment'])
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(e['info/experiment_id'], 1)
###        self.assertEqual(e['info/description'], 'A test experiment')
###        self.assertEqual(e['info/tags'], ['test','experiment'])
###
###    def test_resetting_experiment(self):
###        e = Experiment(self.d)
###        e.start()
###        s = ExampleSimulation()
###        for i in range(10):
###            m = e.new_measurement()
###            m.start()
###            s.a = i
###            s.init()
###            s.run()
###            m.end()
###            m.save(s)
###        e.end()
###        e.save()
###
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(len(e.measurements), 10)
###        for i in range(1,11):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i-1)
###        
###        e = Experiment(self.d)
###        e.reset()
###        e.start()
###        s = ExampleSimulation()
###        for i in range(20,25):
###            m = e.new_measurement()
###            m.start()
###            s.a = i
###            s.init()
###            s.run()
###            m.end()
###            m.save(s)
###        e.end()
###        e.save()
###
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(len(e.measurements), 5)
###        for i in range(1,6):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i+19)
###
###    def test_continuing_measurements_in_experiment(self):
###        e = Experiment(self.d)
###        e.start()
###        s = ExampleSimulation()
###        for i in range(10):
###            m = e.new_measurement()
###            m.start()
###            s.a = i
###            s.init()
###            s.run()
###            m.end()
###            m.save(s)
###        e.end()
###        e.save()
###
###        self.assertEqual(len(e.measurements), 10)
###        for i in range(1,11):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i-1)
###
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(len(e.measurements), 10)
###        for i in range(1,11):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i-1)
###        
###        e = Experiment(self.d)
###        e.start()
###        s = ExampleSimulation()
###        for i in range(20,25):
###            m = e.new_measurement()
###            m.start()
###            s.a = i
###            s.init()
###            s.run()
###            m.end()
###            m.save(s)
###        e.end()
###        e.save()
###
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(len(e.measurements), 15)
###        for i in range(1,11):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i-1)
###        for i in range(11,16):
###            self.assertEqual(e['measurements'][i]['info/measurement_id'], i)
###            self.assertEqual(e['measurements'][i]['info/program'], 'ExampleSimulation')
###            self.assertEqual(e['measurements'][i]['parameters/a'], i+9)
###
###    def test_experiment_templates(self):
###        template_dir = os.path.join(os.path.dirname(__file__), 'test_template')
###        
###        e = Experiment(self.d,
###                       from_template=template_dir,
###                       description='A test experiment',
###                       experiment_id='101')
###        self.assertTrue(os.path.exists(os.path.join(self.d,'runexperiment.py')))
###        self.assertTrue(os.path.exists(os.path.join(self.d,'measurements.index.xml')))
###        self.assertTrue(os.path.exists(os.path.join(self.d,'experiment.readme.xml')))
###
###        del(e)
###        e = Experiment(self.d)
###        self.assertEqual(e['info/experiment_id'], 101)
###        self.assertEqual(e['info/description'], 'A test experiment')
###        with self.assertRaises(KeyError):
###            x = e['info/data']
###
###    def test_experiments_directory(self):
###        ed = ExperimentsDirectory(self.ed)
###
###        self.assertTrue(os.path.exists(self.ed))
###        self.assertTrue(os.path.exists(os.path.join(self.ed, 'experiments.index.xml')))
###        self.assertTrue(os.path.exists(os.path.join(self.ed, 'templates')))
###        self.assertTrue(os.path.exists(os.path.join(self.ed, 'templates', 'default')))
###        self.assertTrue(os.path.exists(os.path.join(self.ed, 'templates', 'python')))
###
###        e1 = ed.new_experiment(description='Test 1', tags=['test'])
###        e2 = ed.new_experiment(description='Test 2', tags=['test'])
###        e3 = ed.new_experiment(description='Test 3', tags=['test'], from_template='python')
###
###        self.assertTrue(os.path.exists(os.path.join(self.ed, '000001')))
###        self.assertTrue(os.path.exists(os.path.join(self.ed, '000002')))
###        self.assertTrue(os.path.exists(os.path.join(self.ed, '000003')))
###
###        e2.start()
###        s = ExampleSimulation()
###
###        for i in range(10):
###            m = e2.new_measurement()
###            m.start()
###            s.a = i
###            s.init()
###            s.run()
###            m.end()
###            m.save(s)
###
###        e2.end()
###        e2.save()
###
###        self.assertEqual(len(ed),3)
###        self.assertEqual(ed['1/info/experiment_id'], 1)
###        self.assertEqual(ed['1/info/description'], 'Test 1')
###        self.assertEqual(ed['1/info/tags'], ['test'])
###        self.assertEqual(ed['2/info/experiment_id'], 2)
###        self.assertEqual(ed['2/info/description'], 'Test 2')
###        self.assertEqual(ed['2/info/tags'], ['test'])
###        self.assertEqual(ed['3/info/experiment_id'], 3)
###        self.assertEqual(ed['3/info/description'], 'Test 3')
###        self.assertEqual(ed['3/info/tags'], ['test'])
###        self.assertEqual(len(ed['1/measurements']), 0)
###        self.assertEqual(len(ed['2/measurements']), 10)
###        self.assertEqual(len(ed['3/measurements']), 0)
###
###        del(ed)
###        ed = ExperimentsDirectory(self.ed)
###        self.assertEqual(len(ed),3)
###        self.assertEqual(ed['1/info/experiment_id'], 1)
###        self.assertEqual(ed['1/info/description'], 'Test 1')
###        self.assertEqual(ed['1/info/tags'], ['test'])
###        self.assertEqual(ed['2/info/experiment_id'], 2)
###        self.assertEqual(ed['2/info/description'], 'Test 2')
###        self.assertEqual(ed['2/info/tags'], ['test'])
###        self.assertEqual(ed['3/info/experiment_id'], 3)
###        self.assertEqual(ed['3/info/description'], 'Test 3')
###        self.assertEqual(ed['3/info/tags'], ['test'])
###        self.assertEqual(len(ed['1/measurements']), 0)
###        self.assertEqual(len(ed['2/measurements']), 10)
###        self.assertEqual(len(ed['3/measurements']), 0)
###
###        e4 = ed.new_experiment(description='Test 4', tags=['test'])
###        self.assertTrue(os.path.exists(os.path.join(self.ed, '000004')))
###        self.assertEqual(ed['4/info/experiment_id'], 4)
###        self.assertEqual(ed['4/info/description'], 'Test 4')
###        self.assertEqual(ed['4/info/tags'], ['test'])
