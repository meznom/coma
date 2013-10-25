import os
from .serialization import XMLArchive
from .path import access_data_by_path
from .util import create_lockfile, remove_lockfile, DirectoryError
from .measurement import Measurement

class MeasurementsDirectory(object):
    def __init__(self, measurement_dir):
        self.dir = measurement_dir
        self.indexfile = os.path.join(self.dir, 'measurements.index.xml')
        self.indexfile_mtime = None
        self.last_measurement_id = 0
        self._iter_i = 1
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        if not os.path.exists(self.indexfile):
            self.create_empty_indexfile()
        self.read_indexfile()

    def create_empty_indexfile(self):
        o = {'last_measurement_id': 0}
        if os.path.exists(self.indexfile):
            raise DirectoryError('Can\'t create index file: File already exists')
        f = open(self.indexfile, 'w')
        a = XMLArchive('measurements')
        a.dump(o,f)
        f.close()

    def reload(self):
        if self.indexfile_mtime != os.path.getmtime(self.indexfile):
            self.read_indexfile()

    def read_indexfile(self):
        self.indexfile_mtime = os.path.getmtime(self.indexfile)
        f = open(self.indexfile)
        a = XMLArchive('measurements')
        o = a.load(f)
        f.close()
        self.last_measurement_id = o['last_measurement_id']

    def reset(self):
        create_lockfile(self.indexfile)
        
        f = open(self.indexfile, 'r+')
        a = XMLArchive('measurements')
        o = a.load(f)
        o['last_measurement_id'] = 0
        
        f.truncate(0)
        f.seek(0)
        a.dump(o,f)
        f.close()
        
        remove_lockfile(self.indexfile)

    def measurement_filename(self, id_):
        return os.path.join(self.dir, '{:06d}.xml'.format(id_))

    def new_measurement(self):
        # Read and increment id of the last measurement
        create_lockfile(self.indexfile)
        
        f = open(self.indexfile, 'r+')
        a = XMLArchive('measurements')
        o = a.load(f)
        o['last_measurement_id'] += 1
        mid = o['last_measurement_id']
        
        f.truncate(0)
        f.seek(0)
        a.dump(o,f)
        f.close()
        
        remove_lockfile(self.indexfile)

        m = Measurement(self.measurement_filename(mid), mid)
        self.last_measurement_id = mid
        return m

    def __iter__(self):
        self._iter_i = 0
        return self

    def next(self):
        self._iter_i += 1
        if self._iter_i > self.last_measurement_id:
            raise StopIteration()
        mid = self._iter_i
        return Measurement(self.measurement_filename(mid), mid)

    def __len__(self):
        return self.last_measurement_id

    def __getitem__(self, i):
        if isinstance(i,int):
            if i<1 or i>self.last_measurement_id:
                raise IndexError()
            return Measurement(self.measurement_filename(i), i)
        elif isinstance(i,basestring) and (i.find('/') != -1 or i.isdigit() or i == '*' or i == ''):
            return access_data_by_path(self, i)
        else:
            raise KeyError(i)

    def __str__(self):
        s = 'Measurements directory "{}" with {} measurements'.format(
                self.dir, self.last_measurement_id)
        return s
