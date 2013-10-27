from collections import OrderedDict
import os
import re
from string import Template
from .serialization import XMLArchive
from .util import current_date_as_string
from .indexfile import IndexFile
from .config import Config
from .measurement import Measurement

class ExperimentError(Exception):
    pass

class Experiment(object):
    def __init__(self, dir, id=None, description=None, tags=[], config=Config()):
        self.dir = dir
        self.id = id
        self.file = None
        self.description = description
        self.tags = tags
        self.start_date = None
        self.end_date = None
        self.config = config
        
        self.eindex = None
        if os.path.exists(self.config.experiment_index_path):
            self.eindex = IndexFile(self.config.experiment_index_path, 'experiment')

        if not os.path.exists(self.dir):
            os.mkdir(self.dir)

        # Measurements
        # index file is created if it does not exist
        self.last_mid = 0
        mindexfile = os.path.join(self.dir,self.config.measurement_index)
        self.mindex = IndexFile(mindexfile, 'measurement')
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
            self.file = os.path.join(self.dir,self._experiment_filename())
            self.save()
        elif len(fs) == 1:
            if self.id is None and fs[0][0] != 0:
                self.id = fs[0][0]
            self.file = os.path.join(self.dir, fs[0][1])
        elif len(fs) > 1:
            d = dict(fs)
            if self.id is None or not d.has_key(self.id):
                raise ExperimentError('Found multiple experiment files, non of ' +
                                      'which match the provided experiment id')
            self.file = os.path.join(self.dir, d[self.id])
        self.load()

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
        # Build a regular expression from the experiment_file config variable
        s = pattern
        s = s.replace('.','\.').replace('/','\/')
        s = '^' +  Template(s).substitute({sub: '(\d+)'}) + '$'
        e = re.compile(s)
        
        # All files in current directory that match
        rs = []
        fs = os.listdir(self.dir)
        for f in fs:
            m  = e.match(f)
            if m is not None:
                if len(m.groups()) > 0:
                    rs.append((int(m.group(1)),m.group(0)))
                else:
                    rs.append((0,m.group(0)))
        return rs

    def save(self):
        i = OrderedDict([
            ('info', OrderedDict([
                        ('experiment_id', self.id),
                        ('description', self.description),
                        ('tags', self.tags),
                        ('start_date', self.start_date),
                        ('end_date', self.end_date)]))
            ])
        backupfile = self.file + '.backup'
        if os.path.exists(self.file):
            os.rename(self.file, backupfile)

        f = open(self.file, 'w')
        a = XMLArchive('experiment')
        a.dump(i, f)
        f.close()
        
        if os.path.exists(backupfile):
            os.remove(backupfile)

    def load(self):
        f = open(self.file)
        a = XMLArchive('experiment')
        i = a.load(f)
        i = i['info']
        f.close()

        if self.id is not None and str(self.id) != str(i['experiment_id']):
            raise ExperimentError('Trying to load experiment "{}" from file "{}", '
                    'but this is experiment "{}"'
                    .format(i['experiment_id'], self.file, self.id))
        
        self.id = i['experiment_id']
        for k in ['description','start_date','end_date','tags']:
            if i.has_key(k):
                self.__setattr__(k, i[k])

        self.last_mid = self.mindex.read()

    def start(self):
        self.start_date = current_date_as_string()

    def end (self):
        self.end_date = current_date_as_string()

    def run(self):
        raise NotImplementedError()

    def reset(self):
        self.mindex.createfile()
        self.last_mid = self.mindex.read()
        for _,f in self._matching_measurement_files():
            f = os.path.join(self.dir, f)
            os.remove(f)

    def new_measurement(self):
        mid = self.mindex.increment()
        f = self._measurement_filename(mid)
        f = os.path.join(self.dir, f)
        m = Measurement(f, mid)
        self.last_mid = mid
        return m

    def measurements(self):
        for mid in range(1,self.last_mid+1):
            f = self._measurement_filename(mid)
            f = os.path.join(self.dir, f)
            if os.path.exists(f):
                yield Measurement(f, mid)
            else:
                continue

    def number_of_measurements(self):
        return len(self._matching_measurement_files())

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
