import unittest
from collections import OrderedDict
import os
import shutil
import copy
import glob
from coma import Experiment, ExperimentError, Config, IndexFile, \
                 ParameterSet, ResultList, Result, Archive

XML_FILE_1='''\
<experiment>
  <info>
    <experiment_id>10</experiment_id>
    <description>Muh</description>
  </info>
</experiment>
'''

JSON_FILE_1='''\
{
  "experiment": {
    "info": {
      "experiment_id": 10,
      "description": "Muh"
    }
  }
}'''

XML_FILE_2='''\
<experiment>
  <info>
    <experiment_id>20</experiment_id>
    <description>Miau</description>
  </info>
</experiment>
'''

JSON_FILE_2='''\
{
  "experiment": {
    "info": {
      "experiment_id": 20,
      "description": "Miau"
    }
  }
}'''

files = {
    'xml': [XML_FILE_1,XML_FILE_2],
    'json': [JSON_FILE_1,JSON_FILE_2]
}

class ExampleSimulation(object):
    def __init__(self):
        self.program = 'ExampleSimulation'
        self.version = 0.1
        self.a = 1
        self.t = 2
        self.V1 = 100
        self.N = None
        self.boa = 2.2
        self.results = OrderedDict()

    def init(self):
        pass

    def run(self):
        pass

    def __getstate__(self):
        i = OrderedDict()
        i['parameters'] = OrderedDict()
        if self.a is not None:
            i['parameters']['a'] = self.a
        i['parameters']['t'] = self.t
        i['parameters']['layout'] = OrderedDict()
        i['parameters']['layout']['V1'] = self.V1
        i['parameters']['layout']['boa'] = self.boa
        i['parameters']['layout']['N'] = self.N
        i['results'] = self.results
        return i

class TestExperiment(object):
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.d = os.path.join(base_dir, 'testexperiment')
        self.fi = os.path.join(self.d, 'coma.index')
        
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

        os.mkdir(self.d)
        i = IndexFile(self.fi, 'experiment', default_format=self.format)
        i.createfile()
        i.increment()
        i.increment()

        self.c = Config()
        self.c.experiment_index = self.fi
        self.c.default_format = self.format

    def tearDown(self):
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

    def filename(self, basename):
        return os.path.join(self.d, basename + '.' + self.format)

    def exists(self, basename):
        return os.path.exists(self.filename(basename))

    def test_create_experiment_with_id_in_name(self):
        # create a new experiment
        e = Experiment(self.d, description='Blub', config=self.c)
        
        self.assertTrue(self.exists('experiment.000003'))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=self.c)

        self.assertTrue(self.exists('experiment.000003'))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

    def test_create_experiment_without_id_in_name(self):
        c = copy.copy(self.c)
        c.experiment_file = 'experiment'
        
        # create a new experiment
        e = Experiment(self.d, description='Blub', config=c)
        
        self.assertTrue(self.exists('experiment'))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=c)

        self.assertTrue(self.exists('experiment'))
        self.assertEquals(e.id, 3)
        self.assertEquals(e.description, 'Blub')

    def test_create_experiment_with_specific_id(self):
        # create a new experiment
        e = Experiment(self.d, id=42, description='Blub', config=self.c)
        
        self.assertTrue(self.exists('experiment.000042'))
        self.assertEquals(e.id, 42)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=self.c)

        self.assertTrue(self.exists('experiment.000042'))
        self.assertEquals(e.id, 42)
        self.assertEquals(e.description, 'Blub')

    def test_create_experiment_without_index_file_1(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index'
        
        e = Experiment(self.d,config=c)
        self.assertFalse(os.path.exists(c.experiment_index_path))
        self.assertTrue(self.exists('experiment.none'))
        self.assertEquals(e.id, None)

        with self.assertRaises(ExperimentError):
            Experiment(self.d,id=42,config=c)

    def test_create_experiment_without_index_file_2(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index'

        e = Experiment(self.d,id=42,config=c)
        self.assertFalse(os.path.exists(c.experiment_index_path))
        self.assertTrue(self.exists('experiment.000042'))
        self.assertEquals(e.id, 42)

    def test_load_experiment_with_id(self):
        fn = self.filename('experiment.000010')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()

        e = Experiment(self.d, config=self.c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')

    def test_load_experiment_without_id(self):
        c = copy.copy(self.c)
        c.experiment_file = 'experiment'

        fn = self.filename('experiment')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()

        e = Experiment(self.d, config=c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')

    def test_load_experiment_with_wrong_id(self):
        fn = self.filename('experiment.000010')
        f = open(fn, 'w')
        f.write(files[self.format][1]) # has id 20
        f.close()
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, config=self.c)
        os.remove(fn)
        
        fn = self.filename('experiment.000020')
        f = open(fn, 'w')
        f.write(files[self.format][1])
        f.close()
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, id=42, config=self.c)
        os.remove(fn)

        c = copy.copy(self.c)
        c.experiment_file = 'experiment'
        fn = self.filename('experiment')
        f = open(fn, 'w')
        f.write(files[self.format][1])
        f.close()
        with self.assertRaises(ExperimentError):
            e = Experiment(self.d, id=42, config=c)
        os.remove(fn)

    def test_load_experiment_with_multiple_experiment_files_in_directory(self):
        fn = self.filename('experiment.000010')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()
        fn = self.filename('experiment.000020')
        f = open(fn, 'w')
        f.write(files[self.format][1])
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

    def test_load_experiment_without_index_file_1(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index'

        fn = self.filename('experiment.000010')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()
        
        e = Experiment(self.d,config=c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')

    def test_load_experiment_without_index_file_2(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index'
        c.experiment_file = 'experiment'
        
        fn = self.filename('experiment')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()
        
        e = Experiment(self.d,config=c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')
    
    def test_load_experiment_without_index_file_3(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index'
        
        fn = self.filename('experiment.none')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()
        
        e = Experiment(self.d,config=c)
        self.assertEquals(e.id, 10)
        self.assertEquals(e.description, 'Muh')

    def test_load_experiment_with_wrong_filename(self):
        c = copy.copy(self.c)
        c.experiment_file = 'experiment'
        fn = self.filename('experiment.000010')
        f = open(fn, 'w')
        f.write(files[self.format][0])
        f.close()

        # creates a new experiment file
        e = Experiment(self.d, config=c)
        self.assertTrue(self.exists('experiment'))
        self.assertTrue(self.exists('experiment.000010'))

    def run_example_experiment_1(self, e, r=(0,10)):
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
    
    def test_standalone_experiment(self):
        e = Experiment(self.d,config=self.c)
        
        self.assertTrue(os.path.exists(self.d))
        self.assertTrue(self.exists('measurement.index'))
        self.assertTrue(self.exists('experiment.000003'))

        e.description = 'Test experiment'
        self.run_example_experiment_1(e)

        del(e)
        e = Experiment(self.d,config=self.c)
        self.assertEqual(e.id, 3)
        self.assertEqual(e.description, 'Test experiment')
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)

    def test_standalone_experiment_without_index_file(self):
        c = copy.copy(self.c)
        c.experiment_index = '__experimenttest.index'

        e = Experiment(self.d,config=c)
        
        self.assertTrue(os.path.exists(self.d))
        self.assertTrue(self.exists('measurement.index'))
        self.assertTrue(self.exists('experiment.none'))

        e.description = 'Test experiment'
        self.run_example_experiment_1(e)

        del(e)
        e = Experiment(self.d,config=c)
        self.assertEqual(e.id, None)
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
        self.run_example_experiment_1(e)

        del(e)
        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)
        
        e = Experiment(self.d,config=self.c)
        e.reset()
        self.run_example_experiment_1(e, (20,25))
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
        c.measurement_file = '${measurement_id}'
        e = Experiment(self.d, config=c)
        self.run_example_experiment_1(e)

        self.assertTrue(self.exists('000001'))
        self.assertEqual(e.number_of_measurements(), 10)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['parameters/a'], i)

        # An invalid measurement_file name: the measurement_id is missing
        # In this case, things can't and won't work properly.
        c = copy.copy(self.c)
        c.measurement_file = 'blah'
        e = Experiment(self.d, config=c)
        self.run_example_experiment_1(e)

        self.assertTrue(self.exists('blah'))
        self.assertEqual(e.number_of_measurements(), 1)

    def test_continuing_measurements_in_experiment(self):
        e = Experiment(self.d,config=self.c)
        self.run_example_experiment_1(e)

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
        self.run_example_experiment_1(e, (20,25))

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
        self.run_example_experiment_1(e)

        f1 = self.filename('measurement.000001')
        f2 = self.filename('measurement.000007')
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
        self.assertTrue(p.has('t'))
        self.assertTrue(p.has('parameters/t'))
        self.assertTrue(p.has('V1'))
        self.assertTrue(p.has('parameters/layout/V1'))
        self.assertFalse(p.has('parameters/quark'))
        self.assertEqual(p.get('t'), 1)
        self.assertEqual(p.get('parameters/t'), 1)
        self.assertEqual(p.get('V1'), 2)
        self.assertEqual(p.get('parameters/layout/V1'), 2)
        with self.assertRaises(IndexError):
            a = p['t']
        with self.assertRaises(IndexError):
            a = p['V1']
        with self.assertRaises(IndexError):
            a = p[2]
        with self.assertRaises(AttributeError):
            a = p.parameters
        with self.assertRaises(ExperimentError):
            a = p.get('parameters/quark')
        with self.assertRaises(ExperimentError):
            a = p.get('V2')

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
        f1 = self.filename('measurement.000011')
        f2 = self.filename('measurement.000042')
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

    def create_example_result_list(self):
        d1 = OrderedDict([('t','parameters/t'),('V1','parameters/layout/V1')])
        d2 = OrderedDict([('t','parameters/t'),('V1','parameters/layout/V1'),('a','parameters/a')])
        rs = ResultList()
        r = Result()
        r.parameters = ParameterSet(d1,[1,100])
        r.table_columns = ('boa', 'P_1', 'P_2')
        rs.append(r)
        r = Result()
        r.parameters = ParameterSet(d1,[2,100])
        r.table_columns = ('boa', 'P_1', 'P_2')
        rs.append(r)
        r = Result()
        r.parameters = ParameterSet(d1,[1,200])
        r.table_columns = ('boa', 'P_1', 'P_2')
        rs.append(r)
        r = Result()
        r.parameters = ParameterSet(d1,[2,200])
        r.table_columns = ('boa', 'P_1', 'P_2')
        rs.append(r)
        r = Result()
        r.parameters = ParameterSet(d2,[1,250,10])
        r.table_columns = ('boa', 'P_1', 'P_2')
        rs.append(r)
        r = Result()
        r.parameters = ParameterSet(d2,[1,150,20])
        r.table_columns = ('boa', 'P_1', 'P_2')
        rs.append(r)
        return rs

    def test_result_list(self):
        rs = self.create_example_result_list()

        self.assertEqual(len(rs), 6)
        self.assertEqual(len(rs['t',1]),4)
        self.assertEqual(len(rs['V1',200]),2)
        self.assertEqual(len(rs['a',10]),1)
        self.assertEqual(len(rs['a',30]),0)

        self.assertEqual(len(rs['t',1]['a',10]),1)
        self.assertEqual(len(rs['t',1]['V1',200]),1)
        self.assertEqual(len(rs['a',30]['t',1]),0)
        
        self.assertTrue(rs['t',1]['V1',100][0] is rs[0])
        self.assertTrue(rs['t',1]['V1',150][0] is rs[5])
        
        self.assertEqual(len(rs['t',1][1:3]),2)
        self.assertEqual(len(rs[0:4]['t',1]),2)
        self.assertEqual(len(rs[:]['t',1]),4)
        self.assertEqual(len(rs[0:5:2]['t',1]),3)

        self.assertEqual(len(rs['parameters/t',1]),4)
        self.assertEqual(len(rs['parameters/layout/V1',100]),2)

        # a bit unrelated: demonstrate that sorting works
        # note: rs['t',1].sort(f) does not work, because the [] operator
        # creates a new copy of the list
        f = lambda x,y: -1 if x.parameters.V1<y.parameters.V1 else 0
        rs2 = rs['t',1]
        rs2.sort(f)
        rs3 = sorted(rs['t',1], f)
        self.assertEqual(rs2,rs3)
        self.assertEqual(len(rs2), 4)
        self.assertTrue(rs2[0] is rs[0])
        self.assertTrue(rs2[1] is rs[5])
        self.assertTrue(rs2[2] is rs[2])
        self.assertTrue(rs2[3] is rs[4])

        # Does not throw an exception, but does not do anything useful
        self.assertEqual(len(rs[1,2]), 0)
        # Nonexisting parameter
        self.assertEqual(len(rs['blub',2]), 0)
        # Bogus parameter values
        self.assertEqual(len(rs['t','muh']), 0)

        # Invalid usage
        with self.assertRaises(TypeError):
            r = rs['t',1,'V1',100]
        with self.assertRaises(TypeError):
            r = rs['t',1,2]
        with self.assertRaises(TypeError):
            r = rs['t']
        with self.assertRaises(TypeError):
            r = rs['quark']

    def test_print_results(self):
        # no unit tests, just looking at the output
        rs = self.create_example_result_list()
        #print(rs)
        for r in rs:
            #print(r)
            pass

    def run_example_experiment_2(self):
        e = Experiment(self.d,config=self.c)

        def run_measurement(p):
            m = e.new_measurement()
            m.start()

            s = ExampleSimulation()
            s.t = p.t
            s.V1 = p.V1
            # artificially create some measurements with missing parameter N
            if p.a != 10:
                s.a = p.a
            else:
                s.a = None
            s.N = p.N
            s.init()
            s.run()
            s.results = OrderedDict()
            if p.N == 2:
                s.results['P'] = [s.V1*10,s.V1*20]
            elif p.N == 3:
                s.results['P'] = [s.V1*10,s.V1*20,s.V1*30]
            else:
                s.results['P'] = [s.V1*10,s.V1*20,s.V1*30,s.V1*40]
            s.results['N'] = OrderedDict()
            s.results['N']['all'] = s.t * 100

            m.end()
            m.save(s)

        e.define_parameter_set(
            ('t','parameters/t'),
            ('a','parameters/a'),
            ('V1','parameters/layout/V1'),
            ('N','parameters/layout/N'))
        for N in [2,3,4]:
            for t in [1,2]:
                for a in [10,20,30]:
                    for V1 in range(100,110):
                        e.add_parameter_set(t,a,V1,N)
        r,t = e.run(run_measurement)

    def test_retrieve_results(self):
        self.run_example_experiment_2()

        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 180)

        d = OrderedDict((('V1','parameters/layout/V1'),('P','results/P')))
        rs = e.retrieve_results(
                (('V1','parameters/layout/V1'),('P','results/P')),
                (('t','parameters/t'),('N','parameters/layout/N')))

        #print(rs)
        
        # Tests for all parameter sets
        self.assertEqual(len(rs),6)
        i = 0
        for r in rs:
            self.assertEqual(r.table_definition, d)
            self.assertEqual(len(r.measurement_ids), 30)
            i += 1
        self.assertEqual(i,6)

        # Tests that differ, depending on the parameter set
        for r in rs['N',2]:
            self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2'))
            self.assertEqual(r.table.shape, (30,3))
        for r in rs['N',3]:
            self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2', 'P_3'))
            self.assertEqual(r.table.shape, (30,4))
        for r in rs['N',4]:
            self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2', 'P_3', 'P_4'))
            self.assertEqual(r.table.shape, (30,5))
        
        r = rs[0]
        self.assertEqual(r.parameters.t, 1)
        self.assertEqual(r.parameters.N, 2)
        # a is not directly accessible
        with self.assertRaises(AttributeError):
            r.parameters.a
        with self.assertRaises(IndexError):
            r.parameters['parameters/a']
        for i,id in enumerate(r.measurement_ids):
            self.assertEqual(id,i+1)
            self.assertEqual(r.table[i,0], 100+i%10)
            self.assertEqual(r.table[i,1], (100+i%10)*10)

    def test_retrieve_results_with_only_some_measurements_matching(self):
        self.run_example_experiment_2()

        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 180)

        tdef = [('V1','parameters/layout/V1'),
                ('P','results/P')]
        pdef = [('t','parameters/t'),
                ('N','parameters/layout/N'),
                ('a','parameters/a')]
        rs = e.retrieve_results(tdef,pdef)

        self.assertEqual(len(rs), 12)
        for r in rs['N',2]:
            self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2'))
            self.assertEqual(r.table.shape, (10,3))
            self.assertEqual(len(r.measurement_ids),10)
        for r in rs['N',3]:
            self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2', 'P_3'))
            self.assertEqual(r.table.shape, (10,4))
            self.assertEqual(len(r.measurement_ids),10)
        for r in rs['N',4]:
            self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2', 'P_3', 'P_4'))
            self.assertEqual(r.table.shape, (10,5))
            self.assertEqual(len(r.measurement_ids),10)

        r = rs[0]
        self.assertEqual(r.parameters.t, 1)
        self.assertEqual(r.parameters.N, 2)
        self.assertEqual(r.parameters.a, 20)
        self.assertEqual(r.parameters['parameters/a'], 20)
        for i,id in enumerate(r.measurement_ids):
            self.assertEqual(id,i+11)
            self.assertEqual(r.table[i,0], 100+i)

    def test_retrieve_results_with_variable_number_of_columns_in_result_table_fails(self):
        self.run_example_experiment_2()

        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 180)

        # Tries to put different number of columns (for different N values)
        # into to the result table, which fails
        with self.assertRaises(ExperimentError):
            rs = e.retrieve_results(
                    table_definition = [('V1','parameters/layout/V1'),
                                        ('P','results/P')],
                    parameter_set_definition = [('t','parameters/t'),
                                                ('a','parameters/a')])

    def run_example_experiment_3(self):
        e = Experiment(self.d,config=self.c)

        def run_measurement(p):
            m = e.new_measurement()
            m.start()

            s = ExampleSimulation()
            s.V1 = p.V1
            s.init()
            s.run()
            s.results = OrderedDict()
            s.results['P'] = [s.V1*10,s.V1*20]
            s.results['N'] = OrderedDict()
            s.results['N']['all'] = s.t * 100

            m.end()
            m.save(s)

        e.define_parameter_set((('V1','parameters/layout/V1')))
        for V1 in range(100,200):
            e.add_parameter_set(V1)
        r,t = e.run(run_measurement)
    
    def test_retrieve_results_for_a_simple_experiment(self):
        self.run_example_experiment_3()

        e = Experiment(self.d, config=self.c)
        self.assertEqual(e.number_of_measurements(), 100)

        tdef = [('V1','parameters/layout/V1'),
                ('P','results/P'),
                ('N','results/N/all')]
        rs = e.retrieve_results(tdef)

        self.assertEqual(len(rs), 1)
        r = rs[0]
        self.assertEqual(r.table.shape,(100,4))
        self.assertEqual(len(r.measurement_ids),100)
        self.assertEqual(r.table_columns, ('V1', 'P_1', 'P_2', 'N'))

        # This works, but does not really make sense. It would be better if it
        # failed, i.e. threw an exception.
        tdef = [('V1','parameters/layout/V1'),
                ('P','results/P'),
                ('N','results/N')]
        rs = e.retrieve_results(tdef)
        self.assertEqual(rs[0].table.shape, (100,4))
        #print(rs[0].table)

class TestExperimentXML(TestExperiment,unittest.TestCase):
    def __init__(self, method='runTest'):
        super(TestExperimentXML, self).__init__(method)
        self.format = 'xml'

class TestExperimentJson(TestExperiment,unittest.TestCase):
    def __init__(self, method='runTest'):
        super(TestExperimentJson, self).__init__(method)
        self.format = 'json'

class TestExperimentXMLAndJsonMixed(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.d = os.path.join(base_dir, 'testexperiment')
        self.fi = os.path.join(self.d, 'coma.index')
        
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

        os.mkdir(self.d)

    def tearDown(self):
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

    def test_default_format_is_json(self):
        i = IndexFile(self.fi, 'experiment')
        i.createfile()

        c = Config()
        c.experiment_index = self.fi
        
        e = Experiment(self.d, description='Blub', config=c)
        
        self.assertTrue(os.path.exists(os.path.join(self.d, 'coma.index.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000001.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.index.json')))
        self.assertEquals(e.id, 1)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=c)

        self.assertTrue(os.path.exists(os.path.join(self.d, 'coma.index.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000001.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.index.json')))
        self.assertEquals(e.id, 1)
        self.assertEquals(e.description, 'Blub')

    def test_can_use_xml_format(self):
        i = IndexFile(self.fi, 'experiment', default_format='xml')
        i.createfile()

        c = Config()
        c.experiment_index = self.fi
        c.default_format = 'xml'
        
        e = Experiment(self.d, description='Blub', config=c)
        
        self.assertTrue(os.path.exists(os.path.join(self.d, 'coma.index.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000001.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.index.xml')))
        self.assertEquals(e.id, 1)
        self.assertEquals(e.description, 'Blub')

        # reopen the same experiment
        e = Experiment(self.d, config=c)

        self.assertTrue(os.path.exists(os.path.join(self.d, 'coma.index.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.000001.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.index.xml')))
        self.assertEquals(e.id, 1)
        self.assertEquals(e.description, 'Blub')

    def run_example_experiment_xml_and_json(self, e, r=(0,10)):
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

        j = 0
        fs = glob.glob(os.path.join(self.d, 'measurement.*.json'))
        fs.sort()
        for f in fs[:-1]:
            j += 1
            if j%2 == 0:
                continue
            a = Archive(f[:-5], 'measurement')
            o = a.load()
            os.remove(f)
            a = Archive(f[:-5], 'measurement', default_format='xml')
            a.save(o)
    
    def test_load_experiment_with_xml_and_json_files(self):
        c = Config()
        c.experiment_index = self.fi
        
        e = Experiment(self.d,config=c)
        
        self.assertTrue(os.path.exists(self.d))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.index.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'experiment.none.json')))

        e.description = 'Test experiment'
        self.run_example_experiment_xml_and_json(e,(0,6))

        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.000001.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.000002.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.000003.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.000004.json')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.000005.xml')))
        self.assertTrue(os.path.exists(os.path.join(self.d, 'measurement.000006.json')))

        del(e)
        e = Experiment(self.d,config=c)
        self.assertEqual(e.id, None)
        self.assertEqual(e.description, 'Test experiment')
        self.assertEqual(e.number_of_measurements(), 6)
        for i,m in enumerate(e.measurements()):
            self.assertEqual(m['info/measurement_id'], i+1)
            self.assertEqual(m['info/program'], 'ExampleSimulation')
            self.assertEqual(m['parameters/a'], i)
