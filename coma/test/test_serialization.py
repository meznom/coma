# Copyright (c) 2013, 2014, Burkhard Ritter
# This code is distributed under the two-clause BSD License.

import unittest
from collections import OrderedDict
from coma import XMLArchive, XMLArchiveError, JsonArchive, JsonArchiveError, \
                 Archive, ArchiveError, archive_exists, Serializer, RecursiveSerializer
import os
import math
import filecmp
import shutil
import numpy
import copy

_SIMPLE_XML='''\
<measurement>
  <info>
    <program>ExamplePythonSimulation</program>
    <version>32ef404-dirty</version>
    <measurement_id>3</measurement_id>
    <measurement_dir>./000005</measurement_dir>
    <empty/>
    <start_date>2013-04-06T04:40:37Z</start_date>
    <end_date>2013-04-06T04:40:37Z</end_date>
  </info>
  <parameters>
    <N>2</N>
    <m>
      <N_row>3</N_row>
      <N_col>5</N_col>
    </m>
  </parameters>
  <results>
    <average>0.5</average>
  </results>
</measurement>
'''

_SIMPLE_JSON='''\
{
  "measurement": {
    "info": {
      "program": "ExamplePythonSimulation",
      "version": "32ef404-dirty",
      "measurement_id": 3,
      "measurement_dir": "./000005",
      "empty": null,
      "start_date": "2013-04-06T04:40:37Z",
      "end_date": "2013-04-06T04:40:37Z"
    },
    "parameters": {
      "N": 2,
      "m": {
        "N_row": 3,
        "N_col": 5
      }
    },
    "results": {
      "average": 0.5
    }
  }
}'''

_INVALID_1_XML='''\
<measurement>
  <info>
    <program>ExamplePythonSimulation</program>
    <version>32ef404-dirty</version>
    <measurement_id>3</measurement_id>
    <measurement_dir>./000005</measurement_dir>
    <start_date>2013-04-06T04:40:37Z</start_date>
    <end_date>2013-04-06T04:40:37Z</end_date>
  </info>
  <parameters>
    <N>2</N>
    <m>
      <N_row>3</N_row>
      <N_col>5</N_col>
    </m>
  </parameters>
  <results>
    <average>0.5</average>
    <a>1</a>
    <a>2</a>
    <a>3</a>
  </results>
</measurement>
'''

_INVALID_1_JSON='''\
{
  "measurement": {
    "info": {
      "program": "ExamplePythonSimulation",
      "version": "32ef404-dirty",
      "measurement_id": 3,
      "measurement_dir": "./000005",
      "empty": null,
      "start_date": "2013-04-06T04:40:37Z",
      "end_date": "2013-04-06T04:40:37Z"
    },
    "parameters": {
      "N": 2,
      "m": {
        "N_row": 3,
        "N_col": 5
      }
    },
    "results": {
      "average": 0.5,
      "a", 1
    }
  }
}'''

_LIST_XML='''\
<measurement>
        <info>
                <date>2013-Apr-08 14:55:42.605198</date>
                <version>ef51159-dirty</version>
                <description>testing</description>
        </info>
        <parameters>
                <nSites>10</nSites>
                <nPhonons>1</nPhonons>
                <lambda>0.2</lambda>
                <omegaKnot>0.1</omegaKnot>
        </parameters>
        <results>
                <Energy>-2</Energy>
                <QuasiParticleResidue>400</QuasiParticleResidue>
                <XExpectationValues>
                        <count>5</count>
                        <item_version>0</item_version>
                        <item>1</item>
                        <item>2</item>
                        <item>3</item>
                        <item>4</item>
                        <item>5</item>
                </XExpectationValues>
                <EmptyList>
                        <count>0</count>
                        <item_version>0</item_version>
                </EmptyList>
                <ListWithDifferentTypes>
                        <count>3</count>
                        <item_version>0</item_version>
                        <item>1</item>
                        <item>text</item>
                        <item>3.1415</item>
                </ListWithDifferentTypes>
        </results>
</measurement>
'''

_LIST_JSON='''\
{
        "measurement": {
                "info": {
                        "date": "2013-Apr-08 14:55:42.605198",
                        "version": "ef51159-dirty",
                        "description": "testing"
                },
                "parameters": {
                        "nSites": 10,
                        "nPhonons": 1,
                        "lambda": 0.2,
                        "omegaKnot": 0.1
                },
                "results": {
                        "Energy": -2,
                        "QuasiParticleResidue": 400,
                        "XExpectationValues": [
                                1,
                                2,
                                3,
                                4,
                                5
                        ],
                        "EmptyList": [],
                        "ListWithDifferentTypes": [
                                1,
                                "text",
                                3.1415
                        ]
                }
        }
}'''

_INVALID_LIST_1_XML='''\
<measurement>
        <info>
                <date>2013-Apr-08 14:55:42.605198</date>
                <version>ef51159-dirty</version>
                <description>testing</description>
        </info>
        <parameters>
                <nSites>10</nSites>
                <nPhonons>1</nPhonons>
                <lambda>0.2</lambda>
                <omegaKnot>0.1</omegaKnot>
        </parameters>
        <results>
                <Energy>-2</Energy>
                <QuasiParticleResidue>400</QuasiParticleResidue>
                <WrongNumberOfElementsInList>
                        <count>5</count>
                        <item_version>0</item_version>
                        <item>1</item>
                        <item>2</item>
                        <item>3</item>
                </WrongNumberOfElementsInList>
        </results>
</measurement>
'''

_INVALID_LIST_2_XML='''\
<measurement>
        <info>
                <date>2013-Apr-08 14:55:42.605198</date>
                <version>ef51159-dirty</version>
                <description>testing</description>
        </info>
        <parameters>
                <nSites>10</nSites>
                <nPhonons>1</nPhonons>
                <lambda>0.2</lambda>
                <omegaKnot>0.1</omegaKnot>
        </parameters>
        <results>
                <Energy>-2</Energy>
                <QuasiParticleResidue>400</QuasiParticleResidue>
                <WrongTagsInList>
                        <count>3</count>
                        <item_version>0</item_version>
                        <item>1</item>
                        <blah>2</blah>
                        <blub>3</blub>
                </WrongTagsInList>
        </results>
</measurement>
'''

_HIERARCHY_XML='''\
<testhierarchy>
  <parameters>
    <c>3</c>
    <d>4</d>
    <all>
      <count>2</count>
      <item_version>0</item_version>
      <item>3</item>
      <item>4</item>
    </all>
    <object1>
      <parameters>
        <a>30</a>
        <b>40</b>
        <all>
          <count>2</count>
          <item_version>0</item_version>
          <item>30</item>
          <item>40</item>
        </all>
      </parameters>
      <__class__>coma.test.test_serialization.Class1</__class__>
    </object1>
  </parameters>
  <__class__>coma.test.test_serialization.Class2</__class__>
</testhierarchy>
'''

_HIERARCHY_JSON='''\
{
  "testhierarchy": {
    "parameters": {
      "c": 3,
      "d": 4,
      "all": [
        3,
        4
      ],
      "object1": {
        "parameters": {
          "a": 30,
          "b": 40,
          "all": [
            30,
            40
          ]
        },
        "__class__": "coma.test.test_serialization.Class1"
      }
    },
    "__class__": "coma.test.test_serialization.Class2"
  }
}'''

_NO_PRETTY_PRINTING_XML='<measurement><info><program>ExamplePythonSimulation</program><version>32ef404-dirty</version><measurement_id>3</measurement_id><measurement_dir>./000005</measurement_dir><empty /><start_date>2013-04-06T04:40:37Z</start_date><end_date>2013-04-06T04:40:37Z</end_date></info><parameters><N>2</N><m><N_row>3</N_row><N_col>5</N_col></m></parameters><results><average>0.5</average></results></measurement>'

_NO_PRETTY_PRINTING_JSON='{"measurement":{"info":{"program":"ExamplePythonSimulation","version":"32ef404-dirty","measurement_id":3,"measurement_dir":"./000005","empty":null,"start_date":"2013-04-06T04:40:37Z","end_date":"2013-04-06T04:40:37Z"},"parameters":{"N":2,"m":{"N_row":3,"N_col":5}},"results":{"average":0.5}}}'

_NUMPY_XML='''\
<measurement>
  <info>
    <program>ExamplePythonSimulation</program>
    <version>32ef404-dirty</version>
    <measurement_id>3</measurement_id>
    <measurement_dir>./000005</measurement_dir>
    <empty/>
    <start_date>2013-04-06T04:40:37Z</start_date>
    <end_date>2013-04-06T04:40:37Z</end_date>
  </info>
  <parameters>
    <N>2</N>
    <m>
      <N_row>3</N_row>
      <N_col>5</N_col>
    </m>
  </parameters>
  <results>
    <numpy_array>
      <__type__>numpy.ndarray</__type__>
      <shape>
        <count>2</count>
        <item_version>0</item_version>
        <item>2</item>
        <item>3</item>
      </shape>
      <list>
        <count>6</count>
        <item_version>0</item_version>
        <item>1</item>
        <item>2</item>
        <item>3</item>
        <item>4</item>
        <item>5</item>
        <item>6</item>
      </list>
    </numpy_array>
  </results>
</measurement>
'''

_NUMPY_JSON='''\
{
  "measurement": {
    "info": {
      "program": "ExamplePythonSimulation",
      "version": "32ef404-dirty",
      "measurement_id": 3,
      "measurement_dir": "./000005",
      "empty": null,
      "start_date": "2013-04-06T04:40:37Z",
      "end_date": "2013-04-06T04:40:37Z"
    },
    "parameters": {
      "N": 2,
      "m": {
        "N_row": 3,
        "N_col": 5
      }
    },
    "results": {
      "numpy_array": {
        "__type__": "numpy.ndarray",
        "shape": [
          2,
          3
        ],
        "list": [
          1,
          2,
          3,
          4,
          5,
          6
        ]
      }
    }
  }
}'''

test_data = \
{
    'simple': OrderedDict([
            ('info', OrderedDict([
                ('program', 'ExamplePythonSimulation'),
                ('version', '32ef404-dirty'),
                ('measurement_id', 3),
                ('measurement_dir', './000005'),
                ('empty', None),
                ('start_date', '2013-04-06T04:40:37Z'),
                ('end_date', '2013-04-06T04:40:37Z')
                ])),
            ('parameters', OrderedDict([
                ('N', 2),
                ('m', OrderedDict([('N_row', 3),('N_col', 5)]))
                ])),
            ('results', OrderedDict([
                ('average', 0.5)
                ]))
            ]),
    'list': OrderedDict([
            ('info', OrderedDict([
                ('date', '2013-Apr-08 14:55:42.605198'),
                ('version', 'ef51159-dirty'),
                ('description', 'testing')
                ])),
            ('parameters', OrderedDict([
                ('nSites', 10),
                ('nPhonons', 1),
                ('lambda', 0.20000000000000001),
                ('omegaKnot', 0.10000000000000001)
                ])),
            ('results', OrderedDict([
                ('Energy', -2),
                ('QuasiParticleResidue', 400),
                ('XExpectationValues', [1,2,3,4,5]),
                ('EmptyList', []),
                ('ListWithDifferentTypes', [1,'text',3.1415]),
                ]))
            ]),
    'numpy': OrderedDict([
            ('info', OrderedDict([
                ('program', 'ExamplePythonSimulation'),
                ('version', '32ef404-dirty'),
                ('measurement_id', 3),
                ('measurement_dir', './000005'),
                ('empty', None),
                ('start_date', '2013-04-06T04:40:37Z'),
                ('end_date', '2013-04-06T04:40:37Z')
                ])),
            ('parameters', OrderedDict([
                ('N', 2),
                ('m', OrderedDict([('N_row', 3),('N_col', 5)]))
                ])),
            ('results', OrderedDict([
                ('numpy_array', numpy.array([[1,2,3],[4,5,6]]))
                ]))
            ]),
}

test_xml = \
{
    'simple': _SIMPLE_XML,
    'invalid_1': _INVALID_1_XML,
    'list': _LIST_XML,
    'invalid_list_1': _INVALID_LIST_1_XML,
    'invalid_list_2': _INVALID_LIST_2_XML,
    'hierarchy': _HIERARCHY_XML,
    'no_pretty_printing': _NO_PRETTY_PRINTING_XML,
    'numpy': _NUMPY_XML
}

test_json = \
{
    'simple': _SIMPLE_JSON,
    'invalid_1': _INVALID_1_JSON,
    'list': _LIST_JSON,
    'hierarchy': _HIERARCHY_JSON,
    'no_pretty_printing': _NO_PRETTY_PRINTING_JSON,
    'numpy': _NUMPY_JSON
}

# TODO: These tests could certainly be simplified. E.g. TestXMLArchive and
# TestJsonArchive are mostly equivalent and even overlap with TestArchive.

class Class1(object):
    def __init__(self, a=0, b=0):
        self.a = a
        self.b = b

    def __getstate__(self):
        o = OrderedDict()
        o['parameters'] = OrderedDict()
        o['parameters']['a'] = self.a
        o['parameters']['b'] = self.b
        o['parameters']['all'] = [self.a,self.b]
        return o
    
    def __setstate__(self, o):
        self.a = o['parameters']['a']
        self.b = o['parameters']['b']

class Class2(object):
    def __init__(self, c=0, d=0):
        self.c = c
        self.d = d
        self.object1 = Class1()

    def __getstate__(self):
        o = OrderedDict()
        o['parameters'] = OrderedDict()
        o['parameters']['c'] = self.c
        o['parameters']['d'] = self.d
        o['parameters']['all'] = [self.c,self.d]
        o['parameters']['object1'] = self.object1
        return o

    def __setstate__(self, o):
        self.c = o['parameters']['c']
        self.d = o['parameters']['d']
        self.object1 = o['parameters']['object1']

class Class3(object):
    def __init__(self, a=0, b=0):
        self.a = a
        self.b = b

    def coma_getstate(self):
        o = OrderedDict()
        o['parameters'] = OrderedDict()
        o['parameters']['a'] = self.a
        o['parameters']['b'] = self.b
        o['parameters']['all'] = [self.a,self.b]
        return o

class TestXMLArchive(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.d = os.path.join(base_dir, 'testxmlarchive')
        
        if os.path.exists(self.d):
            shutil.rmtree(self.d)
        os.mkdir(self.d)

    def tearDown(self):
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

    def filename(self, f):
        return os.path.join(self.d, f)

    def test_dump_simple(self):
        a = XMLArchive('measurement')
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_xml['simple'], s)

    def test_dump_simple_no_pretty_print(self):
        a = XMLArchive('measurement', pretty_print=False)
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_xml['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_simple_to_file(self):
        name = self.filename('test_serialization.xml')
        
        a = XMLArchive('measurement')
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_xml['simple'], s)

        a = XMLArchive('measurement', pretty_print=False)
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_xml['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_list(self):
        a = XMLArchive('measurement', indent=8)
        s = a.dumps(test_data['list'])
        self.assertEqual(test_xml['list'], s)

    def test_dump_numpy(self):
        a = XMLArchive('measurement')
        s = a.dumps(test_data['numpy'])
        self.assertEqual(test_xml['numpy'], s)

    def test_load_simple(self):
        with self.assertRaises(XMLArchiveError):
            a = XMLArchive('blah')
            a.loads(test_xml['simple'])

        a1 = XMLArchive('measurement')
        # 'None' works for any root_tag, generally not recommended
        a2 = XMLArchive(None)
        d1 = a1.loads(test_xml['simple'])
        d2 = a2.loads(test_xml['simple'])

        self.assertEqual(d1, d2)
        self.assertEqual(d1, test_data['simple'])

    def test_load_invalid(self):
        a = XMLArchive('measurement')
        self.assertRaises(XMLArchiveError, a.loads, test_xml['invalid_1'])

    def test_load_list(self):
        a = XMLArchive('measurement')
        d = a.loads(test_xml['list'])
        self.assertEqual(test_data['list'], d)

    def test_load_invalid_list(self):
        a = XMLArchive('measurement')
        self.assertRaises(XMLArchiveError, a.loads, test_xml['invalid_list_1'])
        self.assertRaises(XMLArchiveError, a.loads, test_xml['invalid_list_2'])

    def test_load_numpy(self):
        a = XMLArchive('measurement')
        d = a.loads(test_xml['numpy'])
        d_ = copy.deepcopy(test_data['numpy'])
        self.assertTrue((d_['results']['numpy_array'] == 
                          d['results']['numpy_array']).all())
        del d['results']['numpy_array']
        del d_['results']['numpy_array']
        self.assertEqual(d, d_)

    def test_roundtrip(self):
        a = XMLArchive('measurement')
        s = a.dumps(test_data['simple'])
        d = a.loads(s)
        self.assertEqual(test_data['simple'], d)

        a = XMLArchive('measurement')
        d = a.loads(test_xml['simple'])
        s = a.dumps(d)
        self.assertEqual(test_xml['simple'], s)

    def test_special_numerical_values(self):
        d = [float('nan'), float('inf'), -float('inf')]
        xml = '<test><count>3</count><item_version>0</item_version><item>NaN</item><item>Infinity</item><item>-Infinity</item></test>'
        
        a = XMLArchive('test', pretty_print=False)
        s = a.dumps(d)
        self.assertEqual(xml, s)

        d2 = a.loads(xml)
        self.assertEqual(d[1:], d2[1:])
        self.assertTrue(math.isnan(d[0]))
        self.assertTrue(math.isnan(d2[0]))

    def test_serialize_and_dump_class_hierarchy(self):
        o = Class2(3,4)
        o.object1.a = 30
        o.object1.b = 40

        c = {'serializer_getstate': '__getstate__'}
        a = XMLArchive('testhierarchy', config=c)
        s = a.dumps(o)
        self.assertEqual(test_xml['hierarchy'], s)

    def test_load_but_do_not_restore_class_hierarchy(self):
        a = XMLArchive('testhierarchy')
        o = a.loads(test_xml['hierarchy'])
        self.assertEquals(o['parameters']['c'], 3)
        self.assertEquals(o['parameters']['d'], 4)
        self.assertEquals(o['parameters']['object1']['parameters']['a'], 30)
        self.assertEquals(o['parameters']['object1']['parameters']['b'], 40)

    def test_load_and_restore_class_hierarchy(self):
        # At least for the time being, we need to set the serializer by hand;
        # full object restore is not supported via the config dictionary
        c = {
            'serializer_getstate': '__getstate__',
            'serializer_setstate': '__setstate__'
        }
        s = Serializer(restore_objects=True, config=c)
        a = XMLArchive('testhierarchy')
        a.serializer = s
        o = a.loads(test_xml['hierarchy'])
        self.assertEquals(o.c, 3)
        self.assertEquals(o.d, 4)
        self.assertEquals(o.object1.a, 30)
        self.assertEquals(o.object1.b, 40)

    def test_no_pretty_printing_with_config_object(self):
        f1 = self.filename('testarchive1.xml')
        f1_ref = self.filename('testarchive1_reference.xml')
        f = open(f1_ref, 'w')
        f.write(test_xml['no_pretty_printing'])
        f.close()
        
        c = {'archive_default_format': 'xml', 'archive_pretty_print': False}
        a = XMLArchive('measurement', config=c)
        f = open(f1, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))
        
    def test_no_pretty_printing_with_invalid_config_object(self):
        f1 = self.filename('testarchive1.xml')
        f1_ref = self.filename('testarchive1_reference.xml')
        f = open(f1_ref, 'w')
        f.write(test_xml['simple'])
        f.close()

        # Invalid value for option. Does not throw an error right now, just
        # does not do anything.
        c = {'archive_default_format': 'xml', 'archive_pretty_print': 'muh'}
        a = XMLArchive('measurement', config=c)
        f = open(f1, 'w')
        a.dump(test_data['simple'], f)
        f.close()

        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))

class TestJsonArchive(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.d = os.path.join(base_dir, 'testjsonarchive')
        
        if os.path.exists(self.d):
            shutil.rmtree(self.d)
        os.mkdir(self.d)

    def tearDown(self):
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

    def filename(self, f):
        return os.path.join(self.d, f)

    def test_dump_simple(self):
        a = JsonArchive('measurement')
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_json['simple'], s)

    def test_dump_simple_no_pretty_print(self):
        a = JsonArchive('measurement', pretty_print=False)
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_json['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_simple_to_file(self):
        name = self.filename('test_serialization.json')
        
        a = JsonArchive('measurement')
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_json['simple'], s)

        a = JsonArchive('measurement', pretty_print=False)
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_json['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_list(self):
        a = JsonArchive('measurement', indent=8)
        s = a.dumps(test_data['list'])
        self.assertEqual(test_json['list'], s)

    def test_dump_numpy(self):
        a = JsonArchive('measurement')
        s = a.dumps(test_data['numpy'])
        self.assertEqual(test_json['numpy'], s)

    def test_load_simple(self):
        with self.assertRaises(JsonArchiveError):
            a = JsonArchive('blah')
            a.loads(test_json['simple'])

        a1 = JsonArchive('measurement')
        # Use 'None' to read any JSON file, regardless of top level "tag";
        # generally it's not recommended to use this.
        a2 = JsonArchive(None)
        d1 = a1.loads(test_json['simple'])
        d2 = a2.loads(test_json['simple'])

        self.assertEqual(d1, d2['measurement'])
        self.assertEqual(d1, test_data['simple'])

    def test_load_invalid(self):
        a = JsonArchive('measurement')
        with self.assertRaises(JsonArchiveError):
            a.loads(test_json['invalid_1']);

    def test_load_list(self):
        a = JsonArchive('measurement')
        d = a.loads(test_json['list'])
        self.assertEqual(test_data['list'], d)

    def test_load_numpy(self):
        a = JsonArchive('measurement')
        d = a.loads(test_json['numpy'])
        d_ = copy.deepcopy(test_data['numpy'])
        self.assertTrue((d_['results']['numpy_array'] == 
                          d['results']['numpy_array']).all())
        del d['results']['numpy_array']
        del d_['results']['numpy_array']
        self.assertEqual(d, d_)

    def test_roundtrip(self):
        a = JsonArchive('measurement')
        s = a.dumps(test_data['simple'])
        d = a.loads(s)
        self.assertEqual(test_data['simple'], d)

        a = JsonArchive('measurement')
        d = a.loads(test_json['simple'])
        s = a.dumps(d)
        self.assertEqual(test_json['simple'], s)

        # now without root_tag
        a = JsonArchive(None)
        s = a.dumps(test_data['simple'])
        d = a.loads(s)
        self.assertEqual(test_data['simple'], d)

        a = JsonArchive(None)
        d = a.loads(test_json['simple'])
        s = a.dumps(d)
        self.assertEqual(test_json['simple'], s)

    def test_special_numerical_values(self):
        d = [float('nan'), float('inf'), -float('inf')]
        json = '{"test":[NaN,Infinity,-Infinity]}'
        
        a = JsonArchive('test', pretty_print=False)
        s = a.dumps(d)
        self.assertEqual(json, s)

        d2 = a.loads(json)
        self.assertEqual(d[1:], d2[1:])
        self.assertTrue(math.isnan(d[0]))
        self.assertTrue(math.isnan(d2[0]))

    def test_serialize_and_dump_class_hierarchy(self):
        o = Class2(3,4)
        o.object1.a = 30
        o.object1.b = 40

        c = {'serializer_getstate': '__getstate__'}
        a = JsonArchive('testhierarchy', config=c)
        s = a.dumps(o)
        self.assertEqual(test_json['hierarchy'], s)

    def test_load_but_do_not_restore_class_hierarchy(self):
        a = JsonArchive('testhierarchy')
        o = a.loads(test_json['hierarchy'])
        self.assertEquals(o['parameters']['c'], 3)
        self.assertEquals(o['parameters']['d'], 4)
        self.assertEquals(o['parameters']['object1']['parameters']['a'], 30)
        self.assertEquals(o['parameters']['object1']['parameters']['b'], 40)

    def test_load_and_restore_class_hierarchy(self):
        # At least for the time being, we need to set the serializer by hand;
        # full object restore is not supported via the config dictionary
        c = {
            'serializer_getstate': '__getstate__',
            'serializer_setstate': '__setstate__'
        }
        s = Serializer(restore_objects=True, config=c)
        a = JsonArchive('testhierarchy')
        a.serializer = s
        o = a.loads(test_json['hierarchy'])
        self.assertEquals(o.c, 3)
        self.assertEquals(o.d, 4)
        self.assertEquals(o.object1.a, 30)
        self.assertEquals(o.object1.b, 40)

    def test_no_pretty_printing_with_config_object(self):
        f1 = self.filename('testarchive1.json')
        f1_ref = self.filename('testarchive1_reference.json')
        f = open(f1_ref, 'w')
        f.write(test_xml['no_pretty_printing'])
        f.close()
        
        c = {'archive_default_format': 'json', 'archive_pretty_print': False}
        a = XMLArchive('measurement', config=c)
        f = open(f1, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))
        
    def test_no_pretty_printing_with_invalid_config_object(self):
        f1 = self.filename('testarchive1.json')
        f1_ref = self.filename('testarchive1_reference.json')
        f = open(f1_ref, 'w')
        f.write(test_xml['simple'])
        f.close()

        # Invalid value for option. Does not throw an error right now, just
        # does not do anything.
        c = {'archive_default_format': 'json', 'archive_pretty_print': 'muh'}
        a = XMLArchive('measurement', config=c)
        f = open(f1, 'w')
        a.dump(test_data['simple'], f)
        f.close()

        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))

class TestArchive(unittest.TestCase):
    def setUp(self):
        base_dir = os.path.dirname(__file__)
        self.d = os.path.join(base_dir, 'testarchive')
        
        if os.path.exists(self.d):
            shutil.rmtree(self.d)
        os.mkdir(self.d)

    def tearDown(self):
        if os.path.exists(self.d):
            shutil.rmtree(self.d)

    def filename(self, f):
        return os.path.join(self.d, f)

    def test_archive_cannot_be_constructed_when_multiple_archive_files_are_present(self):
        f1 = self.filename('testarchive.xml')
        f = open(f1, 'w')
        f.write(test_xml['simple'])
        f.close()
        f2 = self.filename('testarchive.json')
        f = open(f2, 'w')
        f.write(test_json['simple'])
        f.close()

        with self.assertRaises(ArchiveError):
            Archive(self.filename('testarchive'), 'measurement')

    def test_archive_cannot_be_constructed_with_invalid_format(self):
        with self.assertRaises(ArchiveError):
            Archive(self.filename('testarchive'), 'test', default_format='txt')

        with self.assertRaises(ArchiveError):
            Archive(self.filename('testarchive'), 'test', default_format='.xml')

    def test_archive_exists(self):
        n = self.filename('testarchive')
        
        self.assertFalse(archive_exists(n))

        f = self.filename('testarchive')
        open(f,'w').close()
        self.assertFalse(archive_exists(n))
        os.remove(f)

        f = self.filename('testarchive.txt')
        open(f,'w').close()
        self.assertFalse(archive_exists(n))
        self.assertFalse(archive_exists(f))
        os.remove(f)

        f = self.filename('testarchive.xml')
        open(f,'w').close()
        self.assertTrue(archive_exists(n))
        self.assertTrue(archive_exists(f))
        os.remove(f)

        f = self.filename('testarchive.json')
        open(f,'w').close()
        self.assertTrue(archive_exists(n))
        self.assertTrue(archive_exists(f))
        os.remove(f)

        f1 = self.filename('testarchive.xml')
        f2 = self.filename('testarchive.json')
        open(f1,'w').close()
        open(f2,'w').close()
        self.assertTrue(archive_exists(n))
        self.assertTrue(archive_exists(f1))
        self.assertTrue(archive_exists(f2))
        os.remove(f1)
        os.remove(f2)

    def test_save_to_xml_and_json(self):
        f1 = self.filename('testarchive1.xml')
        f1_ref = self.filename('testarchive1_reference.xml')
        f2 = self.filename('testarchive2.json')
        f2_ref = self.filename('testarchive2_reference.json')
        f = open(f1_ref, 'w')
        f.write(test_xml['list'])
        f.close()
        f = open(f2_ref, 'w')
        f.write(test_json['list'])
        f.close()
        
        a = Archive(self.filename('testarchive1'), 'measurement', indent=8, default_format='xml')
        a.save(test_data['list'])
        a = Archive(self.filename('testarchive2'), 'measurement', indent=8, default_format='json')
        a.save(test_data['list'])

        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))

        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))
        self.assertTrue(filecmp.cmp(f2, f2_ref, shallow=False))

    def test_load_from_xml_and_json(self):
        f1 = self.filename('testarchive1.xml')
        f2 = self.filename('testarchive2.json')
        f = open(f1, 'w')
        f.write(test_xml['simple'])
        f.close()
        f = open(f2, 'w')
        f.write(test_json['simple'])
        f.close()

        a = Archive(self.filename('testarchive1'), 'measurement')
        o1 = a.load()
        a = Archive(self.filename('testarchive2'), 'measurement')
        o2 = a.load()

        self.assertEqual(o1, test_data['simple'])
        self.assertEqual(o2, test_data['simple'])

    def test_load_archive_with_full_filename(self):
        f1 = self.filename('testarchive1.xml')
        f2 = self.filename('testarchive1.json')
        f = open(f1, 'w')
        f.write(test_xml['simple'])
        f.close()
        f = open(f2, 'w')
        f.write(test_json['list'])
        f.close()

        a = Archive(self.filename('testarchive1.xml'), 'measurement')
        o1 = a.load()
        a = Archive(self.filename('testarchive1.json'), 'measurement')
        o2 = a.load()

        self.assertEqual(o1, test_data['simple'])
        self.assertEqual(o2, test_data['list'])

    def test_default_format_is_used_if_no_archive_file_exists(self):
        a = Archive(self.filename('testarchive'), 'measurement', default_format='xml')
        a.save(test_data['simple'])
        self.assertTrue(os.path.exists(self.filename('testarchive.xml')))

    def test_default_format_is_overridden_by_exisiting_archive_file_format(self):
        f = open(self.filename('testarchive.json'), 'w')
        f.write(test_json['simple'])
        f.close()
        
        a = Archive(self.filename('testarchive'), 'measurement', default_format='xml')
        a.save(test_data['list'])
        
        self.assertTrue(os.path.exists(self.filename('testarchive.json')))
        self.assertFalse(os.path.exists(self.filename('testarchive.xml')))

        a = Archive(self.filename('testarchive'), 'measurement', default_format='xml')
        o = a.load()

        self.assertEqual(o, test_data['list'])

    def test_save_archive_to_different_format(self):
        f1 = self.filename('testarchive1.xml')
        f2 = self.filename('testarchive1.json')
        f2_ref = self.filename('testarchive1_reference.json')
        f = open(f1, 'w')
        f.write(test_xml['simple'])
        f.close()
        f = open(f2_ref, 'w')
        f.write(test_json['simple'])
        f.close()

        # Note: This should be mainly useful for format conversions.
        a = Archive(self.filename('testarchive1'), 'measurement')
        a.save(a.load(), format='json')
        
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(os.path.exists(f2))

        with self.assertRaises(ArchiveError):
            a = Archive(self.filename('testarchive1'), 'measurement')

        os.remove(f1)
        a = Archive(self.filename('testarchive1'), 'measurement')
        o = a.load()

        self.assertEqual(o, test_data['simple'])
        self.assertTrue(filecmp.cmp(f2, f2_ref, shallow=False))

    def test_save_archive_to_different_format_with_invalid_format_fails(self):
        f1 = self.filename('testarchive1.xml')
        f = open(f1, 'w')
        f.write(test_xml['simple'])
        f.close()

        a = Archive(self.filename('testarchive1'), 'measurement')
        with self.assertRaises(ArchiveError):
            a.save(a.load(), format='invalid')

    def test_use_archive_with_config_object_1(self):
        f1 = self.filename('testarchive1.xml')
        f1_ref = self.filename('testarchive1_reference.xml')
        f = open(f1_ref, 'w')
        f.write(test_xml['list'])
        f.close()
        
        c = {'archive_default_format': 'xml'}
        a = Archive(self.filename('testarchive1'), 'measurement', indent=8, config=c)
        a.save(test_data['list'])
        
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))

    def test_use_archive_with_config_object_2(self):
        f1 = self.filename('testarchive1.json')
        f1_ref = self.filename('testarchive1_reference.json')
        f = open(f1_ref, 'w')
        f.write(test_json['no_pretty_printing'])
        f.close()
        
        # arguments to constructor overwrite config options
        c = {'archive_default_format': 'xml', 'archive_pretty_print': False}
        a = Archive(self.filename('testarchive1'), 'measurement', default_format='json', indent=8, config=c)
        a.save(test_data['simple'])
        
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))

    def test_use_archive_with_config_object_3(self):
        f1 = self.filename('testarchive1.json')
        f1_ref = self.filename('testarchive1_reference.json')
        f = open(f1_ref, 'w')
        f.write(test_json['no_pretty_printing'])
        f.close()
        
        # arguments to constructor overwrite config options
        c = {'archive_default_format': 'xml', 'archive_pretty_print': True}
        a = Archive(self.filename('testarchive1'), 'measurement', default_format='json', pretty_print=False, indent=8, config=c)
        a.save(test_data['simple'])
        
        self.assertTrue(os.path.exists(f1))
        self.assertTrue(filecmp.cmp(f1, f1_ref, shallow=False))

class TestSerializer(unittest.TestCase):
    def test_serialize_an_object(self):
        o = Class3(3,4)
        s = Serializer()
        d = s.serialize(o)

        self.assertTrue(d.has_key('parameters'));
        self.assertTrue(d.has_key('__class__'));
        self.assertEqual(d['__class__'], 'coma.test.test_serialization.Class3');
        p = d['parameters']
        self.assertTrue(p.has_key('a'));
        self.assertTrue(p.has_key('b'));
        self.assertTrue(p.has_key('all'));
        self.assertEqual(p['a'], 3);
        self.assertEqual(p['b'], 4);
        self.assertEqual(p['all'], [3,4]);

    def test_serialize_an_object_with_a_different_serialization_method(self):
        o = Class2(5,6)
        s = Serializer(getstate='__getstate__')
        d = s.serialize(o)

        self.assertTrue(d.has_key('parameters'));
        self.assertTrue(d.has_key('__class__'));
        self.assertEqual(d['__class__'], 'coma.test.test_serialization.Class2');
        p = d['parameters']
        self.assertTrue(p.has_key('c'));
        self.assertTrue(p.has_key('d'));
        self.assertTrue(p.has_key('object1'));
        self.assertTrue(p.has_key('all'));
        self.assertEqual(p['c'], 5);
        self.assertEqual(p['d'], 6);
        self.assertEqual(p['all'], [5,6]);
        self.assertTrue(isinstance(p['object1'], Class1));

    def test_serialize_an_object_with_wrong_serialization_method_fails(self):
        o = Class3(3,4)
        s = Serializer(getstate='__getstate__')
        with self.assertRaises(AttributeError):
            s.serialize(o)

    def test_restore_by_default_does_nothing(self):
        d = OrderedDict([('parameters',OrderedDict([('a',10),('b',20)]))])
        s = Serializer()
        o = s.restore(d)
        self.assertTrue(o == d)
        self.assertTrue(o is d)

    def test_restore_an_object(self):
        d = OrderedDict([
            ('parameters',OrderedDict([('c',50),('d',90),('object1','placeholder')])),
            ('__class__', 'coma.test.test_serialization.Class2')
        ])
        s = Serializer(restore_objects=True, getstate='__getstate__', setstate='__setstate__')
        o = s.restore(d)
        self.assertTrue(isinstance(o, Class2))
        self.assertEqual(o.c, 50)
        self.assertEqual(o.d, 90)

    def test_restore_an_object_from_incorrect_or_incomplete_dict(self):
        s = Serializer(restore_objects=True, getstate='__getstate__', setstate='__setstate__')
        
        # If the dict does not have '__class__' field, it is just passed through
        d = OrderedDict([('parameters',OrderedDict([('a',10),('b',20)]))])
        o = s.restore(d)
        self.assertTrue(o == d)
        self.assertTrue(o is d)

        # Nonexistent module fails
        d = OrderedDict([
            ('parameters', OrderedDict([('a',10),('b',20)])),
            ('__class__', 'blub.Muh')
        ])
        with self.assertRaises(ImportError):
            s.restore(d)
        
        # Nonexistent class fails
        d = OrderedDict([
            ('parameters', OrderedDict([('a',10),('b',20)])),
            ('__class__', '__main__.Muh')
        ])
        with self.assertRaises(AttributeError):
            s.restore(d)
        
        # Correct class, but wrong / nonexistent serialization method fails
        d = OrderedDict([
            ('parameters', OrderedDict([('a',10),('b',20)])),
            ('__class__', 'coma.test.test_serialization.Class3')
        ])
        with self.assertRaises(AttributeError):
            s.restore(d)
    
    def test_serialize_and_restore_an_object(self):
        s = Serializer(restore_objects=True, getstate='__getstate__', setstate='__setstate__')
        o1 = Class2(8,9)
        d = s.serialize(o1)
        o2 = s.restore(d)
        
        # Note that here object1 was never serialized, it was just passed
        # around as is. Serializing / restoring a whole object tree recursively
        # is not Serializer's job.
        self.assertTrue(isinstance(o1.object1, Class1))
        self.assertTrue(isinstance(o2.object1, Class1))
        self.assertEqual(o1.__dict__, o2.__dict__)

    def test_use_serializer_with_config_object(self):
        d = OrderedDict([
            ('parameters',OrderedDict([('c',50),('d',90),('object1','placeholder')])),
            ('__class__', 'coma.test.test_serialization.Class2')
        ])
        c = {
            'serializer_getstate': '__getstate__',
            'serializer_setstate': '__setstate__'
        }
        s = Serializer(restore_objects=True, config=c)
        o = s.restore(d)
        self.assertTrue(isinstance(o, Class2))
        self.assertEqual(o.c, 50)
        self.assertEqual(o.d, 90)

    def test_serialize_numpy_arrays(self):
        a = numpy.array([[1,2,3],[4,5,6]])
        s = Serializer()
        d = s.serialize(a)

        self.assertTrue(d.has_key('__type__'))
        self.assertTrue(d.has_key('shape'))
        self.assertTrue(d.has_key('list'))
        self.assertEquals(d['__type__'], 'numpy.ndarray')
        self.assertEquals(d['shape'], (2,3))
        self.assertEquals(d['list'], [1,2,3,4,5,6])

    def test_restore_numpy_arrays(self):
        d = OrderedDict([
            ('__type__', 'numpy.ndarray'),
            ('shape', [2,3]),
            ('list', [1,2,3,4,5,6])
        ])
        s = Serializer()
        o = s.restore(d)
        self.assertTrue(isinstance(o, numpy.ndarray))
        self.assertTrue((o == numpy.array([[1,2,3],[4,5,6]])).all())

        with self.assertRaises(ValueError):
            d = OrderedDict([
                ('__type__', 'numpy.ndarray'),
                ('shape', (2,3)),
                ('list', [1,2,3,4,5])
            ])
            s = Serializer()
            o = s.restore(d)

class TestRecursiveSerializer(unittest.TestCase):
    def setUp(self):
        self.hierarchy = OrderedDict([
            ('parameters', OrderedDict([
                ('c',3),
                ('d',4),
                ('all', [3,4]),
                ('object1', OrderedDict([
                    ('parameters', OrderedDict([
                        ('a',30),
                        ('b',40),
                        ('all', [30,40])
                    ])),
                    ('__class__', 'coma.test.test_serialization.Class1')
                ]))
            ])),
            ('__class__', 'coma.test.test_serialization.Class2')
        ])
        self.d_numpy_array = OrderedDict([
            ('__type__', 'numpy.ndarray'),
            ('shape', [2,3]),
            ('list', [1,2,3,4,5,6])
        ])
        self.numpy_array = numpy.array([[1,2,3],[4,5,6]])

    def test_serialize_class_hierarchy(self):
        o = Class2(3,4)
        o.object1.a = 30
        o.object1.b = 40

        c = {'serializer_getstate': '__getstate__'}
        a = RecursiveSerializer(config=c)
        s = a.serialize(o)
        self.assertEqual(s, self.hierarchy)

    def test_restore_class_hierarchy_without_restoring_objects(self):
        a = RecursiveSerializer()
        o = a.restore(self.hierarchy)
        self.assertEquals(o['parameters']['c'], 3)
        self.assertEquals(o['parameters']['d'], 4)
        self.assertEquals(o['parameters']['all'], [3,4])
        self.assertEquals(o['parameters']['object1']['parameters']['a'], 30)
        self.assertEquals(o['parameters']['object1']['parameters']['b'], 40)
        self.assertEquals(o['parameters']['object1']['parameters']['all'], [30,40])

    def test_restore_class_hierarchy_with_restoring_objects(self):
        c = {
            'serializer_getstate': '__getstate__',
            'serializer_setstate': '__setstate__'
        }
        a = RecursiveSerializer(restore_objects=True, config=c)
        o = a.restore(self.hierarchy)
        self.assertTrue(isinstance(o,Class2))
        self.assertEquals(o.c, 3)
        self.assertEquals(o.d, 4)
        self.assertTrue(isinstance(o.object1,Class1))
        self.assertEquals(o.object1.a, 30)
        self.assertEquals(o.object1.b, 40)

    def test_serialize_numpy_arrays(self):
        o = Class3(self.numpy_array,3)
        s = RecursiveSerializer()
        d = s.serialize(o)

        self.assertTrue(d.has_key('parameters'));
        self.assertTrue(d.has_key('__class__'));
        self.assertEqual(d['__class__'], 'coma.test.test_serialization.Class3');
        p = d['parameters']
        self.assertTrue(p.has_key('a'));
        self.assertTrue(p.has_key('b'));
        self.assertTrue(p.has_key('all'));
        self.assertEquals(p['all'][0], p['a'])
        self.assertEqual(p['a'], self.d_numpy_array)

    def test_restore_numpy_arrays(self):
        d = OrderedDict([('parameters',OrderedDict([
            ('a',self.d_numpy_array),
            ('b',20)]))])
        s = RecursiveSerializer()
        o = s.restore(d)
        self.assertTrue(o.has_key('parameters'))
        self.assertTrue(o['parameters'].has_key('a'))
        self.assertTrue(o['parameters'].has_key('b'))
        self.assertTrue(isinstance(o['parameters']['a'],numpy.ndarray))
        self.assertTrue((o['parameters']['a'] == self.numpy_array).all())

        with self.assertRaises(ValueError):
            r = self.d_numpy_array
            r['list'] = r['list'][:-1]
            d = OrderedDict([('parameters',OrderedDict([('a',r),('b',20)]))])
            s = RecursiveSerializer()
            o = s.restore(d)
