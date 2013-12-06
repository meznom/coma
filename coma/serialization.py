from collections import OrderedDict
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from importlib import import_module
import math
import os

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
        if not hasattr(o, self.getstate):
            raise AttributeError('Can\'t serialize ' + repr(o))
        f = getattr(o, self.getstate)
        d = f()
        d['__class__'] = o.__class__.__module__ + '.' + o.__class__.__name__
        return d

    def restore(self, o):
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

class MemoryArchive(object):
    def __init__(self, config=None):
        self.serializer = Serializer(config=config)

    def serialize(self, o):
        return self.encode(o)

    def encode(self, o):
        if isinstance(o, (basestring,bool,int,long,float)) or o is None:
            return o
        elif isinstance(o, (list, tuple)):
            return [self.encode(i) for i in o]
        elif isinstance(o, dict):
            return OrderedDict([(self.encode(k), self.encode(v)) for k,v in o.iteritems()])
        else:
            return self.encode(self.serializer.serialize(o))

class XMLArchiveError(Exception):
    pass

class XMLArchive(object):
    def __init__(self, root_tag=None, indent=2, config=None):
        self.root_tag = root_tag
        self.serializer = Serializer(config=config)
        self.pretty_print = False
        self.indent = ''
        if indent is not None:
            self.pretty_print = True
            self.indent = ' ' * indent
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
        tag = self.root_tag
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
        if self.root_tag is not None and e.tag != self.root_tag:
            raise XMLArchiveError('Expected XML root element "{}", but found "{}"'
                    .format(self.root_tag, e.tag))
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
    def __init__(self, root_tag=None, indent=2, config=None):
        self.root_tag = root_tag
        self.serializer = Serializer(config=config)
        self.indent = indent
        self.separators = (',',': ')
        if self.indent is None:
            # no pretty printing
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
        if self.root_tag is not None:
            o = OrderedDict([(self.root_tag, o)])
        return json.dumps(o, default=self.serializer.serialize, 
                             indent=self.indent, 
                             separators=self.separators)

    def dump(self, o, f):
        if self.root_tag is not None:
            o = OrderedDict([(self.root_tag, o)])
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
            if self.root_tag is not None:
                if not isinstance(o, dict) or not o.has_key(self.root_tag):
                    raise JsonArchiveError('Did not find top-level entry "{}" in JSON '
                                           'string'.format(self.root_tag))
                o = o[self.root_tag]
            return o
        except ValueError as e:
            raise JsonArchiveError(e.message)

class ArchiveError(Exception):
    pass

class Archive(object):
    formats = ['json','xml']
    classes = {'json': JsonArchive, 'xml': XMLArchive}

    def __init__(self, basename, archive_name=None, indent=2,
                 default_format='json', config=None):
        self.basename = basename
        self.name = archive_name
        self.default_format = default_format
        self.indent = indent
        self.config = config
        if config is not None:
            if config.has_key('archive_default_format'):
                self.default_format = config['archive_default_format']

        self.format = self._infer_format()
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
        return A(self.name, self.indent, config=self.config)
    
    def _infer_format(self):
        fs = []
        for f in self.formats:
            if os.path.exists(self.basename + '.' + f):
                fs.append(f)
        if len(fs) > 1:
            raise ArchiveError('Found multiple files for archive "{}"'
                               .format(self.basename))
        elif len(fs) == 1:
            return fs[0]
        else:
            return self.default_format

def archive_exists(basename):
    fs = []
    for f in Archive.formats:
        if os.path.exists(basename + '.' + f):
            return True
    return False
