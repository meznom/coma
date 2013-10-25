import os
from collections import OrderedDict
from .serialization import XMLArchive, MemoryArchive
from .path import access_data_by_path
from .util import current_date_as_string

class Measurement(object):
    def __init__(self, filename, measurement_id=None):
        self.file = filename
        self.id = measurement_id
        self.start_date = None
        self.end_date = None
        self.results = None
        self.data = {}
        if os.path.exists(self.file):
            self.load()

    def start(self):
        self.start_date = current_date_as_string()

    def end(self):
        self.end_date = current_date_as_string()

    def set_results(self, r):
        self.results = r

    def save(self, m):
        i = OrderedDict()
        if hasattr(m, 'program'):
            i['program'] = m.program
        if hasattr(m, 'version'):
            i['version'] = m.version
        i['measurement_id'] = self.id
        i['start_date'] = self.start_date
        i['end_date'] = self.end_date

        a = MemoryArchive()
        o = a.serialize(m)

        if not o.has_key('info'):
            o = OrderedDict([('info', i)] + o.items())
        else:
            i.update(o['info'])
            o['info'] = i
        if not o.has_key('results'):
            o['results'] = self.results

        self.data = o

        f = open(self.file, 'w')
        a = XMLArchive('measurement')
        a.dump(o, f)
        f.close()

    def load(self):
        f = open(self.file)
        a = XMLArchive('measurement')
        self.data = a.load(f)
        f.close()

    def __iter__(self):
        return self.data.itervalues()

    def __getitem__(self, i):
        return access_data_by_path(self.data, i)

    def __str__(self):
        s = 'Measurement {}'.format(self.id)
        if self.data.has_key('info'):
            i = self.data['info']
            keys = ['program', 'version', 'start_date', 'end_date']
            for k in keys:
                if i.has_key(k) and i[k]:
                    s += '\n  {}: {}'.format(k,i[k])
        s += '\n  Fields: {}\n'.format(self.data.keys())
        return s
