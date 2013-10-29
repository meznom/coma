import unittest
from collections import OrderedDict
import os
import shutil
import copy
from coma import Measurement, Experiment, ExperimentError, Config, IndexFile, ParameterSet

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
        self.t = 2
        self.V1 = 100
        self.boa = 2.2
        self.energies = [1,2,3,4]

    def init(self):
        pass

    def run(self):
        pass

    def __getstate__(self):
        i = OrderedDict([
            ('parameters', OrderedDict([
                        ('a', self.a),
                        ('t', self.t),
                        ('layout', OrderedDict([('V1', self.V1),('boa', self.boa)]))])),
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

    def test_construct_and_use_a_parameter_set(self):
        d = OrderedDict([('t','parameters/t'),('V1','parameters/layout/V1')])
        ps = [1,2]

        p = ParameterSet(d,ps)
        self.assertEqual(p.t, 1)
        self.assertEqual(p.V1, 2)
        self.assertEqual(p['parameters/t'], 1)
        self.assertEqual(p['parameters/layout/V1'], 2)
        self.assertEqual(p[0], 1)
        self.assertEqual(p[1], 2)
        with self.assertRaises(IndexError):
            a = p['t']
        with self.assertRaises(IndexError):
            a = p['V1']
        with self.assertRaises(IndexError):
            a = p[2]
        with self.assertRaises(AttributeError):
            a = p.parameters

    def test_construct_an_invalid_parameter_set_fails(self):
        d = OrderedDict([('t','parameters/t'),('V1','parameters/layout/V1')])
        ps = [1,2,3]
        with self.assertRaises(ExperimentError):
            ParameterSet(d,ps)

        # Construction with an invalid short name does not through an error...
        d = OrderedDict([('t','parameters/t'),('V1','parameters/layout/V1'),
                         ('a.b','parameters/a/b')])
        ps = [1,2,3]
        p = ParameterSet(d,ps)
        with self.assertRaises(AttributeError):
            a = p.a.b

    def test_use_parameter_sets(self):
        e = Experiment(self.d,config=self.c)
        e.define_parameter_set(
            ('t','parameters/t'),
            ('V1','parameters/layout/V1'))
        for t in [1,2]:
            for V1 in range(100,200):
                e.add_parameter_set(t,V1)

        def run_measurement(p):
            m = e.new_measurement()
            m.start()

            s = ExampleSimulation()
            s.t = p.t
            s.V1 = p.V1
            s.init()
            s.run()

            m.end()
            m.save(s)

        r,t = e.run(run_measurement)

        self.assertEqual(r, 200)
        self.assertEqual(t, 200)

        self.assertEqual(e.number_of_measurements(), 200)
        i = 0
        for m in e.measurements():
            if i<100:
                self.assertEqual(m['parameters/t'], 1)
            else:
                self.assertEqual(m['parameters/t'], 2)
            self.assertEqual(m['parameters/layout/V1'], i%100+100)
            i += 1

    def test_use_parameter_sets_with_a_subclass_of_experiment(self):
        class MyExperiment(Experiment):
            def init(self):
                self.define_parameter_set(
                    ('t','parameters/t'),
                    ('V1','parameters/layout/V1'))
                for t in [1,2]:
                    for V1 in range(100,200):
                        self.add_parameter_set(t,V1)

            def run_measurement(self, p):
                m = self.new_measurement()
                m.start()

                s = ExampleSimulation()
                s.t = p.t
                s.V1 = p.V1
                s.init()
                s.run()

                m.end()
                m.save(s)

        e = MyExperiment(self.d,config=self.c)
        e.init()
        r,t = e.run()

        self.assertEqual(r, 200)
        self.assertEqual(t, 200)

        self.assertEqual(e.number_of_measurements(), 200)
        i = 0
        for m in e.measurements():
            if i<100:
                self.assertEqual(m['parameters/t'], 1)
            else:
                self.assertEqual(m['parameters/t'], 2)
            self.assertEqual(m['parameters/layout/V1'], i%100+100)
            i += 1

    def test_running_the_experiment_only_computes_missing_parameter_sets(self):
        e = Experiment(self.d,config=self.c)
        e.define_parameter_set(
            ('t','parameters/t'),
            ('V1','parameters/layout/V1'))
        for t in [1]:
            for V1 in range(100,200):
                e.add_parameter_set(t,V1)

        def run_measurement(p):
            m = e.new_measurement()
            m.start()

            s = ExampleSimulation()
            s.t = p.t
            s.V1 = p.V1
            s.init()
            s.run()

            m.end()
            m.save(s)

        r,t = e.run(run_measurement)
        self.assertEqual(r, 100)
        self.assertEqual(t, 100)
        self.assertEqual(e.number_of_measurements(), 100)

        # add some additional parameter sets
        for t in [2]:
            for V1 in range(100,200):
                e.add_parameter_set(t,V1)

        # delete some existing measurements
        f1 = os.path.join(self.d, 'measurement.000011.xml')
        f2 = os.path.join(self.d, 'measurement.000042.xml')
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))
        os.remove(f1)
        os.remove(f2)

        # and run again
        r,t = e.run(run_measurement)
        self.assertEqual(r, 102)
        self.assertEqual(t, 200)
        self.assertEqual(e.number_of_measurements(), 200)

        ps = []
        for m in e.measurements():
            ps.append((m['parameters/t'], m['parameters/layout/V1']))
        self.assertEqual(len(ps), 200)
        ps.sort()
        i = 0
        for p in ps:
            if i<100:
                self.assertEqual(p[0], 1)
            else:
                self.assertEqual(p[0], 2)
            self.assertEqual(p[1], i%100+100)
            i += 1

    def run_example_experiment_2(self):
        e = Experiment(self.d,config=self.c)

        def run_measurement(p):
            m = e.new_measurement()
            m.start()

            s = ExampleSimulation()
            s.t = p.t
            s.V1 = p.V1
            s.init()
            s.run()
            s.results = OrderedDict()
            s.results['P'] = [s.V1*10,s.V1*20]
            s.results['N'] = OrderedDict()
            s.results['N']['all'] = s.t * 100

            m.end()
            m.save(s)

        e.define_parameter_set(
            ('t','parameters/t'),
            ('a','parameters/a'),
            ('V1','parameters/layout/V1'))
        for t in [1,2]:
            for a in [10,20,30]:
                for V1 in range(100,200):
                    e.add_parameter_set(t,V1)
        r,t = e.run(run_measurement)

    def test_retrieve_results(self):
        self.run_example_experiment_2()

        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 600)

        d = OrderedDict((('V1','parameters/layout/V1'),('P','results/P')))
        rs = e.retrieve_results(
                (('V1','parameters/layout/V1'),('P','results/P')),
                (('t','parameters/t'),('a','parameters/a')))

        self.assertEqual(len(rs),6)
        i = 0
        for r in rs:
            self.assertEqual(r.table.shape, (200,3))
            self.assertEqual(r.table_definition, d)
            self.assertEqual(r.table_columns, ['V1', 'P_1', 'P_2'])
            self.assertEqual(len(r.measurement_ids), 200)
            i += 1
        self.assertEqual(i,6)

        r = rs[0]
        self.assertEqual(r.parameters.t, 1)
        self.assertEqual(r.parameters.a, 10)
        # TODO: more tests on r go here

        # Retrieve a Results object (similar to a list of results), i.e. this is a filter
        # Don't implement this for now
        # rs2 = rs.where() ?

        # Should retrieve exactly one result object
        r = rs.get({'t':1, 'a':10})
        # or
        r = rs.get(('t', 1), ('a', 10))
