import unittest
from collections import OrderedDict
from coma import XMLArchive, XMLArchiveError, JsonArchive, JsonArchiveError
import os
import math

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
            ])
}

test_xml = \
{
    'simple': _SIMPLE_XML,
    'invalid_1': _INVALID_1_XML,
    'list': _LIST_XML,
    'invalid_list_1': _INVALID_LIST_1_XML,
    'invalid_list_2': _INVALID_LIST_2_XML
}

test_json = \
{
    'simple': _SIMPLE_JSON,
    'invalid_1': _INVALID_1_JSON,
    'list': _LIST_JSON
}

class TestXMLArchive(unittest.TestCase):
    def test_dump_simple(self):
        a = XMLArchive('measurement')
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_xml['simple'], s)

    def test_dump_simple_no_pretty_print(self):
        a = XMLArchive('measurement', indent=None)
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_xml['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_simple_to_file(self):
        name = 'test_serialization.xml'
        
        a = XMLArchive('measurement')
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_xml['simple'], s)

        a = XMLArchive('measurement', indent=None)
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_xml['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

        os.remove(name)

    def test_dump_list(self):
        a = XMLArchive('measurement', indent=8)
        s = a.dumps(test_data['list'])
        self.assertEqual(test_xml['list'], s)

    def test_load_simple(self):
        with self.assertRaises(XMLArchiveError):
            a = XMLArchive('blah')
            a.loads(test_xml['simple'])

        a1 = XMLArchive('measurement')
        a2 = XMLArchive()
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
        
        a = XMLArchive('test', indent=None)
        s = a.dumps(d)
        self.assertEqual(xml, s)

        d2 = a.loads(xml)
        self.assertEqual(d[1:], d2[1:])
        self.assertTrue(math.isnan(d[0]))
        self.assertTrue(math.isnan(d2[0]))

class TestJsonArchive(unittest.TestCase):
    def test_dump_simple(self):
        a = JsonArchive('measurement')
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_json['simple'], s)

    def test_dump_simple_no_pretty_print(self):
        a = JsonArchive('measurement', indent=None)
        s = a.dumps(test_data['simple'])
        self.assertEqual(test_json['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_simple_to_file(self):
        name = 'test_serialization.json'
        
        a = JsonArchive('measurement')
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_json['simple'], s)

        a = JsonArchive('measurement', indent=None)
        f = open(name, 'w')
        a.dump(test_data['simple'], f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(test_json['simple'].replace('\n','').replace(' ',''), s.replace(' ',''))

        os.remove(name)

    def test_dump_list(self):
        a = JsonArchive('measurement', indent=8)
        s = a.dumps(test_data['list'])
        self.assertEqual(test_json['list'], s)

    def test_load_simple(self):
        with self.assertRaises(JsonArchiveError):
            a = JsonArchive('blah')
            a.loads(test_json['simple'])

        a1 = JsonArchive('measurement')
        a2 = JsonArchive()
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
        a = JsonArchive()
        s = a.dumps(test_data['simple'])
        d = a.loads(s)
        self.assertEqual(test_data['simple'], d)

        a = JsonArchive()
        d = a.loads(test_json['simple'])
        s = a.dumps(d)
        self.assertEqual(test_json['simple'], s)

    def test_special_numerical_values(self):
        d = [float('nan'), float('inf'), -float('inf')]
        json = '{"test":[NaN,Infinity,-Infinity]}'
        
        a = JsonArchive('test', indent=None)
        s = a.dumps(d)
        self.assertEqual(json, s)

        d2 = a.loads(json)
        self.assertEqual(d[1:], d2[1:])
        self.assertTrue(math.isnan(d[0]))
        self.assertTrue(math.isnan(d2[0]))
