# Copyright (c) 2013, 2014, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

from collections import OrderedDict
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from importlib import import_module
import math
import os
import numpy

class Serializer(object):
    # TODO: '__class__' is part of the serialization / de-serialization
    # protocol, just as 'coma_getstate' and 'coma_setstate' and should
    # probably be configurable as well
    def __init__(self, restore_objects=False, getstate='coma_getstate', 
                 setstate='coma_setstate', config=None):
        self.restore_objects = restore_objects
        self.getstate = getstate
        self.setstate = setstate
        if config is not None:
            if config.has_key('serializer_getstate'):
                self.getstate = config['serializer_getstate']
            if config.has_key('serializer_setstate'):
                self.setstate = config['serializer_setstate']

    def serialize(self, o):
        # Special case for numpy array. In principle this could be a more
        # general, extensible system to allow serialization of arbitrary types.
        if isinstance(o, numpy.ndarray):
            return self.serialize_numpy_ndarray(o)
        if not hasattr(o, self.getstate):
            raise AttributeError('Can\'t serialize ' + repr(o))
        f = getattr(o, self.getstate)
        d = f()
        d['__class__'] = o.__class__.__module__ + '.' + o.__class__.__name__
        return d

    def restore(self, o):
        if isinstance(o, dict) and '__type__' in o:
            if o['__type__'] == 'numpy.ndarray':
                return self.restore_numpy_ndarray(o)
        if not self.restore_objects:
            return o
        if not isinstance(o, dict) or not '__class__' in o:
            return o

        # I believe that __module__ can never be empty, so __class__
        # should always be of the form some_module.class
        ms,_,cs= o['__class__'].rpartition('.')
        m = import_module(ms)
        c = getattr(m,cs)
        
        if not hasattr(c, self.setstate):
            raise AttributeError('Can\'t restore object ' + repr(o))
        
        i = c()
        del o['__class__']
        f = getattr(c, self.setstate)
        f(i,o)
        return i

    def serialize_numpy_ndarray(self, o):
        d = OrderedDict()
        d['__type__'] = 'numpy.ndarray'
        d['shape'] = o.shape
        d['list'] = o.flatten().tolist()
        return d

    def restore_numpy_ndarray(self, d):
        o = numpy.array(d['list'])
        o.shape = d['shape']
        return o

# Maybe just merge this class with Serializer and have a flag recursive.
# It might make sense to always use RecursiveSerializer for all serialization,
# right now the same serialization functionality is implemented in different
# ways in XMLArchive and JsonArchive.
class RecursiveSerializer(object):
    def __init__(self, restore_objects=False, getstate='coma_getstate', 
                 setstate='coma_setstate', config=None):
        self.serializer = Serializer(restore_objects=restore_objects,
                                     getstate=getstate,
                                     setstate=setstate,
                                     config=config)

    def serialize(self, o):
        if isinstance(o, (basestring,bool,int,long,float)) or o is None:
            return o
        elif isinstance(o, (list, tuple)):
            return [self.serialize(i) for i in o]
        elif isinstance(o, dict):
            return OrderedDict([(self.serialize(k), self.serialize(v)) for k,v in o.iteritems()])
        else:
            return self.serialize(self.serializer.serialize(o))

    def restore(self, d):
        o = None
        if isinstance(d, (basestring,bool,int,long,float)) or d is None:
            o = d
        elif isinstance(d, dict):
            o = OrderedDict()
            for k,v in d.iteritems():
                o[self.restore(k)] = self.restore(v)
        elif isinstance(d, (list, tuple)):
            o = []
            for v in d:
                o.append(self.restore(v))
        else:
            o = d
        return self.serializer.restore(o)

class XMLArchiveError(Exception):
    pass

class XMLArchive(object):
    def __init__(self, archive_name, pretty_print=None, indent=None, config=None):
        # defaults for pretty_print and indent
        _pretty_print = True
        _indent = 2
        
        # read relevant config options
        if config is not None:
            if config.has_key('archive_pretty_print'):
                p = config['archive_pretty_print']
                if p is True or p is False:
                    _pretty_print = p
        
        # __init__ arguments---if specified (i.e. not None)---overwrite config
        # options
        if pretty_print is not None:
            _pretty_print = pretty_print
        if indent is not None:
            _indent = indent
        
        if _pretty_print is False:
            _indent = 0

        self.archive_name = archive_name
        self.serializer = Serializer(config=config)
        self.pretty_print = _pretty_print
        self.indent = ' ' * _indent
        # this is taken from json.scanner
        self.number_re = re.compile(
            r'^(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?$',
            (re.VERBOSE | re.MULTILINE | re.DOTALL))

    def dumpfile(self, o, filename):
        f = open(filename, 'w')
        self.dump(o, f)
        f.close()

    def loadfile(self, filename):
        f = open(filename)
        o = self.load(f)
        f.close()
        return o
        
    def dumps(self, o):
        s = ET.tostring(self._dump_to_element(o))
        if self.pretty_print:
            # This is a hack to get rid of the xml header
            header = minidom.Document().toprettyxml(indent=self.indent)
            s = minidom.parseString(s).toprettyxml(indent=self.indent)
            s = s[len(header):]
        return s

    def dump(self, o, f):
        if self.pretty_print:
            #s = ET.tostring(self._dump_to_element(o))
            #minidom.parseString(s).writexml(f, addindent=self.indent, newl='\n', encoding='utf-8')
            s = self.dumps(o)
            f.write(s)
        else:
            et = ET.ElementTree(self._dump_to_element(o))
            et.write(f)

    def _dump_to_element(self, o):
        tag = self.archive_name
        if tag is None:
            tag = 'serialization'
        return self.encode(tag, o)

    def loads(self, s):
        e = ET.fromstring(s)
        return self._load_from_element(e)

    def load(self, f):
        et = ET.parse(f)
        e = et.getroot()
        return self._load_from_element(e)

    def _load_from_element(self, e):
        if self.archive_name is not None and e.tag != self.archive_name:
            raise XMLArchiveError('Expected XML root element "{}", but found "{}"'
                    .format(self.archive_name, e.tag))
        return self.decode(e)

    def encode(self, tag, o):
        e = ET.Element(tag)
        if isinstance(o, (basestring,bool,int,long)):
            e.text = str(o)
        elif o is None:
            e.text = ''
        elif isinstance(o, float):
            if math.isnan(o):
                e.text = 'NaN'
            elif o == float('inf'):
                e.text = 'Infinity'
            elif o == -float('inf'):
                e.text = '-Infinity'
            else:
                e.text = str(o)
        elif isinstance(o, (list, tuple)):
            f = ET.Element('count')
            f.text = str(len(o))
            g = ET.Element('item_version')
            g.text = str(0)
            e.append(f)
            e.append(g)
            for i in o:
                e.append(self.encode('item', i))
        elif isinstance(o, dict):
            for k,v in o.iteritems():
                e.append(self.encode(k, v))
        else:
            return self.encode(tag, self.serializer.serialize(o))
        return e

    def decode(self, e):
        if len(e) == 0:
            return self.serializer.restore(self._parse_string(e.text))
        # Children
        cs = [(c.tag,self.decode(c)) for c in e]
        # Is it a list?
        if cs[0][0] == 'count' and isinstance(cs[0][1],int) and cs[1][0] == 'item_version':
            n = cs[0][1]
            if len(cs) != n+2:
                raise XMLArchiveError('Element "{}" looks like a list, but '
                        'number of items does not match "count"'.format(e.tag))
            if n == 0:
                return self.serializer.restore([])
            unique_tags = set(zip(*(cs[2:]))[0])
            if len(unique_tags) != 1 or unique_tags.pop() != 'item':
                raise XMLArchiveError('Element "{}" looks like a list, but '
                        'contains invalid child elements'.format(e.tag))
            l = list(zip(*(cs[2:]))[1])
            return self.serializer.restore(l)
        # Otherwise it's a dictionary
        unique_tags = set(zip(*(cs))[0])
        if len(unique_tags) != len(cs):
            raise XMLArchiveError('Multiple elements with the same tag are not supported')
        d = OrderedDict(cs)
        return self.serializer.restore(d)

    def _parse_string(self, s):
        if s is None:
            return s
        if s == 'NaN':
            return float('nan')
        if s == 'Infinity':
            return float('inf')
        if s == '-Infinity':
            return -float('inf')
        m = self.number_re.match(s)
        if m is None:
            return s
        else:
            i,f,e = m.groups() #integer, fraction, exponent
            if f or e:
                return float(i + (f or '') + (e or ''))
            else:
                return int(i)

class JsonArchiveError(Exception):
    pass

class JsonArchive(object):
    def __init__(self, archive_name, pretty_print=None, indent=None, config=None):
        # defaults for pretty_print and indent
        _pretty_print = True
        _indent = 2
        
        # read relevant config options
        if config is not None:
            if config.has_key('archive_pretty_print'):
                p = config['archive_pretty_print']
                if p is True or p is False:
                    _pretty_print = p
        
        # __init__ arguments---if specified (i.e. not None)---overwrite config
        # options
        if pretty_print is not None:
            _pretty_print = pretty_print
        if indent is not None:
            _indent = indent

        self.archive_name = archive_name
        self.serializer = Serializer(config=config)
        self.indent = _indent
        self.separators = (',',': ')
        if _pretty_print is False:
            self.indent = None
            self.separators = (',',':')

    def dumpfile(self, o, filename):
        f = open(filename, 'w')
        self.dump(o, f)
        f.close()

    def loadfile(self, filename):
        f = open(filename)
        o = self.load(f)
        f.close()
        return o
        
    def dumps(self, o):
        if self.archive_name is not None:
            o = OrderedDict([(self.archive_name, o)])
        return json.dumps(o, default=self.serializer.serialize, 
                             indent=self.indent, 
                             separators=self.separators)

    def dump(self, o, f):
        if self.archive_name is not None:
            o = OrderedDict([(self.archive_name, o)])
        json.dump(o, f, default=self.serializer.serialize,
                        indent=self.indent, 
                        separators=self.separators)

    def loads(self, s):
        return self._load(s, json.loads)
        o = json.loads(s, object_pairs_hook=lambda d: self.serializer.restore(OrderedDict(d)))

    def load(self, f):
        return self._load(f, json.load)

    def _load(self, s_or_f, json_load):
        try:
            o = json_load(s_or_f, object_pairs_hook=lambda d: self.serializer.restore(OrderedDict(d)))
            if self.archive_name is not None:
                if not isinstance(o, dict) or not o.has_key(self.archive_name):
                    raise JsonArchiveError('Did not find top-level entry "{}" in JSON '
                                           'string'.format(self.archive_name))
                o = o[self.archive_name]
            return o
        except ValueError as e:
            raise JsonArchiveError(e.message)

class ArchiveError(Exception):
    pass

class Archive(object):
    formats = ['json','xml']
    classes = {'json': JsonArchive, 'xml': XMLArchive}

    def __init__(self, filename, archive_name, pretty_print=None, indent=None,
                 default_format=None, config=None):
        _default_format = 'json'
        if config is not None:
            if config.has_key('archive_default_format'):
                _default_format = config['archive_default_format']
        if default_format is not None:
            _default_format = default_format
        
        self.name = archive_name
        self.default_format = _default_format
        self.pretty_print = pretty_print
        self.indent = indent
        self.config = config

        self.basename,self.format = self._basename_and_format(filename)
        self.filename = self.basename + '.' + self.format
        self._a = self._archive_factory(self.format)

    def save(self, o, format=None):
        if format is None or format == self.format:
            self._a.dumpfile(o, self.filename)
            return
        filename = self.basename + '.' + format
        a = self._archive_factory(format)
        a.dumpfile(o, filename)

    def load(self):
        return self._a.loadfile(self.filename)

    def _archive_factory(self, format):
        if not self.classes.has_key(format):
            raise ArchiveError('Unsupported archive format: {}'.format(format))
        A = self.classes[format]
        return A(self.name, self.pretty_print, self.indent, config=self.config)
    
    def _basename_and_format(self, filename):
        # If filename ends with a supported format, return basename and format
        # accordingly, otherwise treat filename as the basename and see whether
        # an archive with one of the supported formats already exists.
        # Otherwise return default format.
        for f in self.formats:
            if filename.endswith('.' + f):
                return filename[:-(len(f)+1)],f
        fs = []
        for f in self.formats:
            if os.path.exists(filename + '.' + f):
                fs.append(f)
        if len(fs) > 1:
            raise ArchiveError('Found multiple files for archive "{}"'
                               .format(filename))
        elif len(fs) == 1:
            return filename,fs[0]
        else:
            return filename,self.default_format

def archive_exists(filename):
    fs = []
    for f in Archive.formats:
        if filename.endswith('.' + f) and os.path.exists(filename):
            return True
        if os.path.exists(filename + '.' + f):
            return True
    return False
