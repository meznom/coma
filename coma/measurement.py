from collections import OrderedDict
from .serialization import Archive, MemoryArchive, archive_exists
from .config import Config
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
    def __init__(self):
        self.id = None
        self.start_date = None
        self.end_date = None
        self._data = OrderedDict()

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, o):
        # ensures that some standard fields are always defined and in a
        # specific order
        i = OrderedDict([
            ('measurement_id', self.id),
            ('start_date', self.start_date),
            ('end_date',self.end_date)])
        if not o.has_key('info'):
            o = OrderedDict([('info', i)] + o.items())
        else:
            i.update(o['info'])
            o['info'] = i
        self._data = o

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

class MemoryMeasurement(Measurement):
    def __init__(self, data):
        Measurement.__init__(self)
        self.data = data
        self.id = self.data['info']['measurement_id']
        self.start_date = self.data['info']['start_date']
        self.end_date = self.data['info']['end_date']

class FileMeasurement(Measurement):
    def __init__(self, filename, id=None, config=Config()):
        Measurement.__init__(self)
        self.id = id
        self.archive = Archive(filename, 'measurement', default_format=config.default_format)
        if archive_exists(filename):
            self.load()

    def start(self):
        self.start_date = current_date_as_string()

    def end(self):
        self.end_date = current_date_as_string()

    def save(self, m=None):
        if m is not None:
            a = MemoryArchive()
            o = a.serialize(m)
            i = OrderedDict()
            if hasattr(m, 'program'):
                i['program'] = m.program
            if hasattr(m, 'version'):
                i['version'] = m.version
            if not o.has_key('info'):
                o = OrderedDict([('info', i)] + o.items())
            else:
                i.update(o['info'])
                o['info'] = i
            self.data = o
        self.archive.save(self.data)

    def load(self):
        self.data = self.archive.load()
        i = self.data['info']
        self.id = i['measurement_id']
        self.start_date = i['start_date']
        self.end_date = i['end_date']
