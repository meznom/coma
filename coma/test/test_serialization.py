import unittest
from collections import OrderedDict
from coma import XMLArchive, XMLArchiveError
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

class TestXMLArchive(unittest.TestCase):
    def setUp(self):
        self._simple = OrderedDict([
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
            ])
        self._simple_xml=_SIMPLE_XML

        self._invalid_1_xml = _INVALID_1_XML
        
        self._list = OrderedDict([
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
        self._list_xml=_LIST_XML

        self._invalid_list_1_xml = _INVALID_LIST_1_XML
        self._invalid_list_2_xml = _INVALID_LIST_2_XML

    def test_dump_simple(self):
        a = XMLArchive('measurement')
        s = a.dumps(self._simple)
        self.assertEqual(self._simple_xml, s)

    def test_dump_simple_no_pretty_print(self):
        a = XMLArchive('measurement', pretty_print=False)
        s = a.dumps(self._simple)
        self.assertEqual(self._simple_xml.replace('\n','').replace(' ',''), s.replace(' ',''))

    def test_dump_simple_to_file(self):
        name = 'test_serialization.xml'
        
        a = XMLArchive('measurement')
        f = open(name, 'w')
        a.dump(self._simple, f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(self._simple_xml, s)

        a = XMLArchive('measurement', pretty_print=False)
        f = open(name, 'w')
        a.dump(self._simple, f)
        f.close()
        f = open(name)
        s = f.read()
        f.close()
        self.assertEqual(self._simple_xml.replace('\n','').replace(' ',''), s.replace(' ',''))

        os.remove(name)

    def test_dump_list(self):
        a = XMLArchive('measurement', indent=' '*8)
        s = a.dumps(self._list)
        self.assertEqual(self._list_xml, s)

    def test_load_simple(self):
        with self.assertRaises(XMLArchiveError):
            a = XMLArchive('blah')
            a.loads(self._simple_xml)

        a1 = XMLArchive('measurement')
        a2 = XMLArchive()
        d1 = a1.loads(self._simple_xml)
        d2 = a2.loads(self._simple_xml)

        self.assertEqual(d1, d2)
        self.assertEqual(d1, self._simple)

    def test_load_invalid(self):
        a = XMLArchive('measurement')
        self.assertRaises(XMLArchiveError, a.loads, self._invalid_1_xml)

    def test_load_list(self):
        a = XMLArchive('measurement')
        d = a.loads(self._list_xml)
        self.assertEqual(self._list, d)

    def test_load_invalid_list(self):
        a = XMLArchive('measurement')
        self.assertRaises(XMLArchiveError, a.loads, self._invalid_list_1_xml)
        self.assertRaises(XMLArchiveError, a.loads, self._invalid_list_2_xml)

    def test_roundtrip(self):
        a = XMLArchive('measurement')
        s = a.dumps(self._simple)
        d = a.loads(s)
        self.assertEqual(self._simple, d)

        a = XMLArchive('measurement')
        d = a.loads(self._simple_xml)
        s = a.dumps(d)
        self.assertEqual(self._simple_xml, s)

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
