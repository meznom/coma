import os
from collections import OrderedDict
from .serialization import XMLArchive, MemoryArchive
from .path import access_data_by_path
from .util import current_date_as_string

# Works, but makes a copy of everything we access
# class DictAsObject(dict):
#     def __init__(self, *args, **kwargs):
#         super(DictAsObject, self).__init__(*args, **kwargs)
#         self.__dict__ = self
# 
#     def __getattribute__(self, name):
#          a = super(DictAsObject, self).__getattribute__(name)
#          if isinstance(a,dict):
#              return DictAsObject(a)
#          else:
#              return a

class DictAsObject(object):
    def __init__(self, d):
        self.__dict__ = d

    def __getattribute__(self, name):
         a = super(DictAsObject, self).__getattribute__(name)
         if isinstance(a,dict):
             return DictAsObject(a)
         else:
             return a

class Measurement(object):
    def __init__(self, file, id=None):
        self.file = file
        self.id = id
        self.start_date = None
        self.end_date = None
        self.data = {}
        if os.path.exists(self.file):
            self.load()

    def start(self):
        self.start_date = current_date_as_string()

    def end(self):
        self.end_date = current_date_as_string()

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

        i = self.data['info']
        if i.has_key('measurement_id'):
            self.id = i['measurement_id']
        ks = ['start_date', 'end_date']
        for k in ks:
            if i.has_key(k):
                self.__setattr__(k, i[k])

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

    # This is experimental, a convenience method for accessing the data
    # dictionary like an object: E.g. m.data['parameters']['layout']['V1']
    # should be accessible as m.parameters.layout.V1 (where m is an instance of
    # Measurement)
    def __getattr__(self, name):
        if not self.data.has_key(name):
            raise AttributeError()
        if isinstance(self.data[name], dict):
            return DictAsObject(self.data[name])
        else:
            return self.data[name]
