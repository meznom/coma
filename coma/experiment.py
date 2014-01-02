# Copyright (c) 2013, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

from collections import OrderedDict
import os
import re
from string import Template
import numpy as np
from .serialization import Archive, archive_exists
from .util import current_date_as_string
from .indexfile import IndexFile
from .config import expand_path, load_config
from .measurement import FileMeasurement, MemoryMeasurement

class ExperimentError(Exception):
    pass

class Result(object):
    def __init__(self):
        self.table = np.array([])
        self.table_definition = OrderedDict()
        self.table_columns = ()
        self.parameters = ParameterSet(OrderedDict(),())
        self.measurement_ids = []

    def __repr__(self):
        cols = ','.join(c for c in self.table_columns)
        return 'Result((' + cols + '),' + repr(self.parameters) + ')'

class ResultList(list):
    def filter_results(self, f):
        if len(f) != 2:
            raise TypeError()
        p,v = f
        rs = ResultList()
        for r in self:
            if not r.parameters.has(p):
                continue
            if r.parameters.get(p) == v:
                rs.append(r)
        return rs

    def __getslice__(self, i, j):
        return ResultList(list.__getslice__(self, i, j))

    def __getitem__(self, n):
        if isinstance(n,tuple):
            return self.filter_results(n)
        i = list.__getitem__(self, n)
        if isinstance(i,list):
            return ResultList(i)
        return i

class ParameterSet(object):
    def __init__(self, definition, parameter_tuple):
        if len(definition) != len(parameter_tuple):
            raise ExperimentError('ParameterSet: Parameter set definition and '
                                  'provided parameters do not agree')
        self.definition = definition
        self.ps = parameter_tuple
        self.names = OrderedDict()
        for i,n in enumerate(definition.values()):
            self.names[n] = i
        self.shortnames = OrderedDict()
        for i,n in enumerate(definition.keys()):
            self.shortnames[n] = i

    def has(self, n):
        return self.shortnames.has_key(n) or self.names.has_key(n)

    def get(self, n):
        if self.shortnames.has_key(n):
            return self.ps[ self.shortnames[n] ]
        elif self.names.has_key(n):
            return self.ps[ self.names[n] ]
        else:
            raise ExperimentError('Parameter "{}" does not exist in this parameter set'.format(n))

    def __getattr__(self, n):
        if not self.shortnames.has_key(n):
            raise AttributeError()
        return self.ps[ self.shortnames[n] ]

    def __getitem__(self, n):
        if isinstance(n, int):
            return self.ps[n]
        if not self.names.has_key(n):
            raise IndexError()
        return self.ps[ self.names[n] ]

    def __repr__(self):
        s = '('
        s += ','.join(['{}={}'.format(n,v) for n,v in 
                       zip(self.shortnames.keys(), self.ps)])
        s += ')'
        return s

class Experiment(object):
    def __init__(self, dir, id=None, description=None, tags=[], config=None):
        self.dir = dir
        self.id = id
        self.archive = None
        self.description = description
        self.tags = tags
        self.start_date = None
        self.end_date = None
        self._measurements = None
        self.pset_definition = OrderedDict()
        self.psets = []

        # Default values for configurable properties
        self.experiment_file = 'experiment.${experiment_id}'
        self.experiment_index = 'experiment.index'
        self.measurement_file = 'measurement.${measurement_id}'
        self.measurement_index = 'measurement.index'

        if config is None:
            config = load_config()

        self._configure(config)
        self.config = config

        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        
        eindexfile = expand_path(self.experiment_index)
        self.eindex = IndexFile(eindexfile, 'experiment', config=config)
        mindexfile = os.path.join(self.dir, self.measurement_index)
        self.mindex = IndexFile(mindexfile, 'measurement', config=config)

        # Retrieve files matching the experiment_file config variable.
        #
        # If there are no matching files, we create a new experiment, using the
        # supplied experiment id or retrieving the id from the global counter
        # (stored in the config directory). Creates a new measurement index
        # file.
        #
        # If there is one matching file, then we load this experiment, if the
        # filename contains the experiment id, then we retrieve it. Loads the
        # measurement index file, if it exists.
        #
        # If there are multiple matching files, then we load the one matching
        # the provided experiment id. Never loads a measurement index file.
        fs = self._matching_experiment_files()
        if len(fs) == 0:
            if self.id is None and self.eindex.exists():
                self.id = self.eindex.increment()
            f = os.path.join(self.dir,self._experiment_filename())
            self.archive = Archive(f, 'experiment', config=config)
            self.mindex.create()
            self.save()
            self.load()
        elif len(fs) == 1:
            if self.id is None and fs[0][0] != 0:
                self.id = fs[0][0]
            f = os.path.join(self.dir, fs[0][1])
            self.archive = Archive(f, 'experiment', config=config)
            self.load()
        else:
            d = dict(fs)
            if self.id is None or not d.has_key(self.id):
                raise ExperimentError('Found multiple experiment files, non of ' +
                                      'which match the provided experiment id')
            f = os.path.join(self.dir, d[self.id])
            self.archive = Archive(f, 'experiment', config=config)
            self.load()

    def _configure(self, config):
        props = ['experiment_index','measurement_index',
                 'experiment_file','measurement_file']
        for p in props:
            if config.has_key(p):
                setattr(self, p, config[p])

    def save(self):
        o = OrderedDict()
        o['info'] = OrderedDict([
                        ('experiment_id', self.id),
                        ('description', self.description),
                        ('tags', self.tags),
                        ('start_date', self.start_date),
                        ('end_date', self.end_date)])
        if self._measurements is not None:
            o['measurements'] = self._measurements

        f = self.archive.filename
        backupfile = f + '.backup'
        if os.path.exists(f):
            os.rename(f, backupfile)

        self.archive.save(o)
        
        if os.path.exists(backupfile):
            os.remove(backupfile)

    def load(self):
        o = self.archive.load()
        i = o['info']

        if self.id is not None and str(self.id) != str(i['experiment_id']):
            raise ExperimentError('Trying to load experiment "{}" from file "{}", '
                    'but this is experiment "{}"'
                    .format(i['experiment_id'], self.archive.filename, self.id))
        
        self.id = i['experiment_id']
        for k in ['description','start_date','end_date','tags']:
            if i.has_key(k):
                self.__setattr__(k, i[k])

        self._measurements = None
        if o.has_key('measurements'):
            self._measurements = o['measurements']

    def activate(self):
        if self.isactive():
            raise ExperimentError('Experiment already is active')
        last_mid = 0
        for m in self._memory_measurements():
            f = self._measurement_filename(m.id)
            f = os.path.join(self.dir, f)
            if archive_exists(f):
                raise ExperimentError('Cannot create measurement with id {}: The '
                                      'measurement already exists.'.format(m.id))
            fm = FileMeasurement(f, m.id, config=self.config)
            fm.data = m.data
            fm.save()
            if m.id is not None and m.id > last_mid:
                last_mid = m.id
        self.mindex.create()
        self.mindex.set(last_mid)

        # Read back and verify everything got written correctly.
        equal = True
        if self._number_of_file_measurements() != self._number_of_memory_measurements():
            equal = False
        for m1,m2 in zip(self._file_measurements(), self._memory_measurements()):
            if m1.data != m2.data:
                equal = False
        if not equal:
            raise ExperimentError('Could not activate experiment. Leaving '
                                  'experiment in inconsistent state. Please '
                                  'investigate by hand.')

        self._measurements = None
        self.save()
        self.load()

    def deactivate(self):
        if not self.isactive():
            raise ExperimentError('Experiment already is inactive')
        ms = []
        for m in self._file_measurements():
            ms.append(m.data)
        self._measurements = ms
        self.save()

        # Read back and verify everything got written correctly.
        self.load()
        equal = True
        if self._number_of_file_measurements() != self._number_of_memory_measurements():
            equal = False
        for m1,m2 in zip(self._file_measurements(), self._memory_measurements()):
            if m1.data != m2.data:
                equal = False
        if not equal:
            raise ExperimentError('Could not deactivate experiment. Leaving '
                                  'experiment in inconsistent state. Please '
                                  'investigate by hand.')

        for m in self._file_measurements():
            os.remove(m.archive.filename)
        self.mindex.remove()

    def isactive(self):
        return self._measurements is None

    def start(self):
        self.start_date = current_date_as_string()

    def end(self):
        self.end_date = current_date_as_string()

    def reset(self):
        self.start_date = None
        self.end_date = None
        if self.isactive():
            last_mid = self.mindex.get()
            self.mindex.create()
            for mid,f in self._matching_measurement_files():
                if mid < 1 or mid>last_mid:
                    continue
                f = os.path.join(self.dir, f)
                a = Archive(f,'measurement')
                os.remove(a.filename)
        else:
            self._measurements = []
        self.save()

    def new_measurement(self):
        if not self.isactive():
            raise ExperimentError('Cannot create a new measurement for an '
                                  'inactive experiment.')
        mid = self.mindex.increment()
        f = self._measurement_filename(mid)
        f = os.path.join(self.dir, f)
        if archive_exists(f):
            raise ExperimentError('Cannot create measurement with id {}: The '
                                  'measurement already exists.'.format(mid))
        m = FileMeasurement(f, mid, config=self.config)
        return m

    def measurements(self):
        if self.isactive():
            return self._file_measurements()
        else:
            return self._memory_measurements()

    def _file_measurements(self):
        for mid in range(1,self.mindex.get()+1):
            f = self._measurement_filename(mid)
            f = os.path.join(self.dir, f)
            if archive_exists(f):
                yield FileMeasurement(f, mid, config=self.config)
            else:
                continue

    def _memory_measurements(self):
        for m in self._measurements:
            yield MemoryMeasurement(m)

    def number_of_measurements(self):
        if self.isactive():
            return self._number_of_file_measurements()
        else:
            return self._number_of_memory_measurements()

    def _number_of_file_measurements(self):
        fs = self._matching_measurement_files()
        ls = [(1 if (mid!=0 and mid<=self.mindex.get()) else 0) for mid,f in fs]
        return sum(ls)

    def _number_of_memory_measurements(self):
        return len(self._measurements)

    def define_parameter_set(self, *args):
        self.pset_definition = OrderedDict(args)

    def add_parameter_set(self, *args):
        p = tuple(args)
        self.psets.append(p)

    def run(self, run_measurement=None):
        run_m = self.run_measurement
        if run_measurement is not None:
            run_m = lambda p: run_measurement(self, p)

        existing = self._get_existing_psets()
        todo = [p for p in self.psets if p not in existing]

        self.start()
        for p in todo:
            run_m(ParameterSet(self.pset_definition, p))
        self.end()
        self.save()

        return (len(todo),len(self.psets))

    def run_measurement(self, parameter_set):
        raise NotImplementedError()

    def retrieve_results(self, table_definition, parameter_set_definition=()):
        tdef = OrderedDict(table_definition)
        pdef = OrderedDict(parameter_set_definition)
        
        ts = OrderedDict()
        for m in self.measurements():
            try:
                p,t,c = [],[],[]
                for name,path in pdef.iteritems():
                    p.append(m[path])
                p = tuple(p)
                for name,path in tdef.iteritems():
                    v = m[path]
                    if isinstance(v,list):
                        ns,vs = self._flatten_list(name,v)
                        t.extend(vs)
                        c.extend(ns)
                    else:
                        t.append(v)
                        c.append(name)
                c = tuple(c)
                if not ts.has_key(p):
                    ts[p] = (c,[],[])
                if ts[p][0] != c:
                    raise ExperimentError('Different number of columns in results '
                                          'table for the same set of parameters')
                ts[p][1].append(t)
                ts[p][2].append(m.id)
            except KeyError:
                pass

        rs = ResultList()
        for p,(c,t,ids) in ts.iteritems():
            r = Result()
            r.parameters = ParameterSet(pdef,p)
            r.table = np.array(t)
            r.table_definition = tdef
            r.table_columns = c
            r.measurement_ids = ids
            rs.append(r)
        return rs

    def _flatten_list(self, n, l):
        """Flattens the list, returning a list of names and a list of values."""
        ns = []
        vs = []
        for i,v in enumerate(l):
            nn = n + '_' + str(i+1)
            if isinstance(v,list):
                ns_,vs_ = self._flatten_list(nn,v)
                ns.extend(ns_)
                vs.extend(vs_)
            else:
                ns.append(nn)
                vs.append(v)
        return ns,vs

    def _get_existing_psets(self):
        ps = []
        for m in self.measurements():
            try:
                p = []
                for name,path in self.pset_definition.iteritems():
                    p.append(m[path])
                ps.append(tuple(p))
            except KeyError:
                pass
        return ps

    def _experiment_filename(self):
        idstr = 'none'
        if isinstance(self.id, int):
            idstr = '{:06d}'.format(self.id)
        s = self.experiment_file
        s = Template(s)
        s = s.substitute(experiment_id=idstr)
        return s

    def _measurement_filename(self, mid):
        idstr = 'none'
        if isinstance(mid, int):
            idstr = '{:06d}'.format(mid)
        s = self.measurement_file
        s = Template(s)
        s = s.substitute(measurement_id=idstr)
        return s

    def _matching_experiment_files(self):
        return self._matching_files(self.experiment_file, 'experiment_id')

    def _matching_measurement_files(self):
        return self._matching_files(self.measurement_file, 'measurement_id')

    def _matching_files(self, pattern, sub):
        # Build a regular expression from pattern
        s = pattern
        s = s.replace('.','\.').replace('/','\/')
        fs = '|'.join(Archive.formats) # string 'json|xml', or similar
        s = '^(' +  Template(s).substitute({sub: '(\d+|none)'}) + ')\.(?:' + fs + ')$'
        e = re.compile(s)

        # All files in current directory that match
        rs = []
        fs = os.listdir(self.dir)
        for f in fs:
            m  = e.match(f)
            if m is not None:
                if len(m.groups()) == 2 and m.group(2) != 'none':
                    rs.append((int(m.group(2)),m.group(1)))
                else:
                    rs.append((0,m.group(1)))
        return rs

    def __str__(self):
        s = 'Experiment {}'.format(self.id)
        if self.data.has_key('info'):
            i = self.data['info']
            for k,v in i.iteritems():
                if k != 'experiment_id' and v:
                    s += '\n  {}: {}'.format(k,v)
        s += '\n  Fields: {}'.format(self.data.keys())
        s += '\n  {} measurements\n'.format(len(self.number_of_measurements()))
        return s
