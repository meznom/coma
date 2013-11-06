from collections import OrderedDict
import xml.etree.ElementTree as ET
from xml.dom import minidom
import json
import re
from importlib import import_module
import math

class Serializer(object):
    def serialize(self, o):
        if hasattr(o, '__getstate__'):
            d = o.__getstate__()
            d['__class__'] = str(o.__class__)
            return d
        raise TypeError('Can\'t serialize ' + repr(o))

    def restore(self, o):
        return o

# note: currently unused and untested
class Restorer(Serializer):
    def restore(self, o):
        if isinstance(o, dict) and '__class__' in o:
            ms,_,cs= o['__class__'].rpartition('.')
            m = import_module(ms)
            c = getattr(m,cs)
            if hasattr(c, '__setstate__'):
                i = c()
                del o['__class__']
                i.__setstate__(o)
                return i
        return o

class MemoryArchive(object):
    def __init__(self, serializer=Serializer):
        self.s = serializer()

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
            return self.encode(self.s.serialize(o))

class XMLArchiveError(Exception):
    pass

class XMLArchive(object):
    def __init__(self, root_tag=None, serializer=Serializer, indent=2):
        self.root_tag = root_tag
        self.s = serializer()
        self.pretty_print = False
        self.indent = ''
        if indent is not None:
            self.pretty_print = True
            self.indent = ' ' * indent
        # this is taken from json.scanner
        self.number_re = re.compile(
            r'^(-?(?:0|[1-9]\d*))(\.\d+)?([eE][-+]?\d+)?$',
            (re.VERBOSE | re.MULTILINE | re.DOTALL))
        
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
            return self.encode(tag, self.s.serialize(o))
        return e

    def decode(self, e):
        if len(e) == 0:
            return self.s.restore(self._parse_string(e.text))
        # Children
        cs = [(c.tag,self.decode(c)) for c in e]
        # Is it a list?
        if cs[0][0] == 'count' and isinstance(cs[0][1],int) and cs[1][0] == 'item_version':
            n = cs[0][1]
            if len(cs) != n+2:
                raise XMLArchiveError('Element "{}" looks like a list, but '
                        'number of items does not match "count"'.format(e.tag))
            if n == 0:
                return self.s.restore([])
            unique_tags = set(zip(*(cs[2:]))[0])
            if len(unique_tags) != 1 or unique_tags.pop() != 'item':
                raise XMLArchiveError('Element "{}" looks like a list, but '
                        'contains invalid child elements'.format(e.tag))
            l = list(zip(*(cs[2:]))[1])
            return self.s.restore(l)
        # Otherwise it's a dictionary
        unique_tags = set(zip(*(cs))[0])
        if len(unique_tags) != len(cs):
            raise XMLArchiveError('Multiple elements with the same tag are not supported')
        d = OrderedDict(cs)
        return self.s.restore(d)

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
    def __init__(self, root_tag=None, serializer=Serializer, indent=2):
        self.root_tag = root_tag
        self.s = serializer()
        self.indent = indent
        self.separators = (',',': ')
        if self.indent is None:
            # no pretty printing
            self.separators = (',',':')

    def dumps(self, o):
        if self.root_tag is not None:
            o = OrderedDict([(self.root_tag, o)])
        return json.dumps(o, default=self.s.serialize, 
                             indent=self.indent, 
                             separators=self.separators)

    def dump(self, o, f):
        if self.root_tag is not None:
            o = OrderedDict([(self.root_tag, o)])
        json.dump(o, f, default=self.s.serialize,
                        indent=self.indent, 
                        separators=self.separators)

    def loads(self, s):
        return self._load(s, json.loads)
        o = json.loads(s, object_pairs_hook=lambda d: self.s.restore(OrderedDict(d)))

    def load(self, f):
        return self._load(f, json.load)

    def _load(self, s_or_f, json_load):
        try:
            o = json_load(s_or_f, object_pairs_hook=lambda d: self.s.restore(OrderedDict(d)))
            if self.root_tag is not None:
                if not isinstance(o, dict) or not o.has_key(self.root_tag):
                    raise JsonArchiveError('Did not find top-level entry "{}" in JSON '
                                           'string'.format(self.root_tag))
                o = o[self.root_tag]
            return o
        except ValueError as e:
            raise JsonArchiveError(e.message)
