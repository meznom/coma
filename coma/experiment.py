from collections import OrderedDict
import os
import re
from string import Template
import numpy as np
from .serialization import Archive, archive_exists
from .util import current_date_as_string
from .indexfile import IndexFile
from .config import Config
from .measurement import Measurement

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
    def __init__(self, dir, id=None, description=None, tags=[], config=Config()):
        self.dir = dir
        self.id = id
        self.archive = None
        self.description = description
        self.tags = tags
        self.start_date = None
        self.end_date = None
        self.config = config

        self.pset_definition = OrderedDict()
        self.psets = []
        
        self.eindex = None
        if archive_exists(self.config.experiment_index_path):
            self.eindex = IndexFile(self.config.experiment_index_path, 'experiment', 
                                    default_format=self.config.default_format)

        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        # Measurements
        # index file is created if it does not exist
        self.last_mid = 0
        mindexfile = os.path.join(self.dir,self.config.measurement_index)
        self.mindex = IndexFile(mindexfile, 'measurement', 
                                default_format=self.config.default_format)
        self.last_mid = self.mindex.read()

        # Retrieve files matching the experiment_file config variable.
        #
        # If there are no matching files, we create a new experiment, using the
        # supplied experiment id or retrieving the id from the global counter
        # (stored in the config directory).
        #
        # If there is one matching file, then we load this experiment, if the
        # filename contains the experiment id, then we retrieve it.
        #
        # If there are multiple matching files, then we load the one matching
        # the provided experiment id. 
        fs = self._matching_experiment_files()
        if len(fs) == 0:
            if self.id is None and self.eindex is not None:
                self.id = self.eindex.increment()
            f = os.path.join(self.dir,self._experiment_filename())
            self.archive = Archive(f, 'experiment', default_format=self.config.default_format)
            self.save()
            self.load()
        elif len(fs) == 1:
            if self.id is None and fs[0][0] != 0:
                self.id = fs[0][0]
            f = os.path.join(self.dir, fs[0][1])
            self.archive = Archive(f, 'experiment', default_format=self.config.default_format)
            self.load()
        elif len(fs) > 1:
            d = dict(fs)
            if self.id is None or not d.has_key(self.id):
                raise ExperimentError('Found multiple experiment files, non of ' +
                                      'which match the provided experiment id')
            f = os.path.join(self.dir, d[self.id])
            self.archive = Archive(f, 'experiment', default_format=self.config.default_format)
            self.load()

    def save(self):
        i = OrderedDict([
            ('info', OrderedDict([
                        ('experiment_id', self.id),
                        ('description', self.description),
                        ('tags', self.tags),
                        ('start_date', self.start_date),
                        ('end_date', self.end_date)]))
            ])
        f = self.archive.filename
        backupfile = f + '.backup'
        if os.path.exists(f):
            os.rename(f, backupfile)

        self.archive.save(i)
        
        if os.path.exists(backupfile):
            os.remove(backupfile)

    def load(self):
        i = self.archive.load()
        i = i['info']

        if self.id is not None and str(self.id) != str(i['experiment_id']):
            raise ExperimentError('Trying to load experiment "{}" from file "{}", '
                    'but this is experiment "{}"'
                    .format(i['experiment_id'], self.archive.filename, self.id))
        
        self.id = i['experiment_id']
        for k in ['description','start_date','end_date','tags']:
            if i.has_key(k):
                self.__setattr__(k, i[k])

        self.last_mid = self.mindex.read()

    def start(self):
        self.start_date = current_date_as_string()

    def end (self):
        self.end_date = current_date_as_string()

    def reset(self):
        self.mindex.createfile()
        self.last_mid = self.mindex.read()
        for _,f in self._matching_measurement_files():
            f = os.path.join(self.dir, f)
            # TODO: maybe move functionality to archive, i.e. a method
            # Archive.delete
            a = Archive(f)
            os.remove(a.filename)

    def new_measurement(self):
        mid = self.mindex.increment()
        f = self._measurement_filename(mid)
        f = os.path.join(self.dir, f)
        m = Measurement(f, mid, config=self.config)
        self.last_mid = mid
        return m

    def measurements(self):
        for mid in range(1,self.last_mid+1):
            f = self._measurement_filename(mid)
            f = os.path.join(self.dir, f)
            if archive_exists(f):
                yield Measurement(f, mid, config=self.config)
            else:
                continue

    def number_of_measurements(self):
        return len(self._matching_measurement_files())

    def define_parameter_set(self, *args):
        self.pset_definition = OrderedDict(args)

    def add_parameter_set(self, *args):
        p = tuple(args)
        self.psets.append(p)

    def run(self, run_measurement=None):
        if run_measurement is None:
            run_measurement = self.run_measurement

        existing = self._get_existing_psets()
        todo = [p for p in self.psets if p not in existing]

        self.start()
        for p in todo:
            run_measurement(ParameterSet(self.pset_definition, p))
        self.end()

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
                        t.extend(v)
                        c.extend([name + '_' + str(i+1) for i in range(len(v))])
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
        s = self.config.experiment_file
        s = Template(s)
        s = s.substitute(experiment_id=idstr)
        return s

    def _measurement_filename(self, mid):
        idstr = 'none'
        if isinstance(mid, int):
            idstr = '{:06d}'.format(mid)
        s = self.config.measurement_file
        s = Template(s)
        s = s.substitute(measurement_id=idstr)
        return s

    def _matching_experiment_files(self):
        return self._matching_files(self.config.experiment_file, 'experiment_id')

    def _matching_measurement_files(self):
        return self._matching_files(self.config.measurement_file, 'measurement_id')

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
