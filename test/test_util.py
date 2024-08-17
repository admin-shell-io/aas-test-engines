from unittest import TestCase
from aas_test_engines._util import group, un_group, normpath, splitpath


class GroupSmcTest(TestCase):

    def test_empty(self):
        result = group({})
        self.assertDictEqual(result, {})
        result = un_group({})
        self.assertDictEqual(result, {})

    def test_simple(self):
        input = {
            'modelType': 'SubmodelElementCollection',
            'value': [
                {
                    'idShort': 'x'
                }
            ]
        }
        result = group(input)
        self.assertDictEqual(result, {
            'modelType': 'SubmodelElementCollection',
            'value': {
                'x': [{'idShort': 'x'}]
            }
        })
        output = un_group(result)
        self.assertDictEqual(input, output)

    def test_multiple(self):
        input = {
            'modelType': 'SubmodelElementCollection',
            'value': [
                {
                    'idShort': 'x',
                    'x': 1
                },
                {
                    'idShort': 'z',
                    'z': 2
                },
                {
                    'idShort': 'x',
                    'x': 3
                }
            ]
        }
        result = group(input)
        self.assertDictEqual(result, {
            'modelType': 'SubmodelElementCollection',
            'value': {
                'x': [{'idShort': 'x', 'x': 1}, {'idShort': 'x', 'x': 3}],
                'z': [{'idShort': 'z', 'z': 2}]
            }
        })
        output = un_group(result)
        self.assertEqual(output['modelType'], 'SubmodelElementCollection')
        self.assertEqual(len(output['value']), 3)

    def test_nested(self):
        input = {
            'modelType': 'SubmodelElementCollection',
            'value': [
                {
                    'modelType': 'SubmodelElementCollection',
                    'idShort': 'foo',
                    'value': [
                        {
                            'idShort': 'x'
                        }
                    ]
                }
            ]
        }
        result = group(input)


class NormPathTest(TestCase):

    def test_empty(self):
        self.assertEqual(normpath(''), '')
        self.assertEqual(normpath('   '), '')

    def test_double_slashes(self):
        self.assertEqual(normpath('//a//b//c'), '/a/b/c')
        self.assertEqual(normpath('//'), '/')

    def test_dot(self):
        self.assertEqual(normpath('.'), '')
        self.assertEqual(normpath('a/./b/./c'), 'a/b/c')
        self.assertEqual(normpath('a/b/.'), 'a/b')

    def test_trailing_slashes(self):
        self.assertEqual(normpath('/abc/def/'), '/abc/def')
        self.assertEqual(normpath('abc/def// //'), 'abc/def')

    def test_double_dot(self):
        self.assertEqual(normpath('foo/../bar'), 'bar')
        self.assertEqual(normpath('/foo/../bar///'), '/bar')
        self.assertEqual(normpath('a/b/../c'), 'a/c')
        self.assertEqual(normpath('a/b/../c/..'), 'a')
        self.assertEqual(normpath('/a/b/../c/..'), '/a')

    def test_illegal_double_dot(self):
        self.assertEqual(normpath('..'), '')
        self.assertEqual(normpath('/..'), '/')
        self.assertEqual(normpath('../x'), 'x')
        self.assertEqual(normpath('/../x'), '/x')


class SplitPathTest(TestCase):

    def test_empty(self):
        self.assertEqual(splitpath(''), ('', ''))

    def test_ends_with_slash(self):
        self.assertEqual(splitpath('a/b.txt/'), ('a/b.txt', ''))
        self.assertEqual(splitpath('/'), ('', ''))
        self.assertEqual(splitpath('/a/b/'), ('/a/b', ''))

    def test_no_slash(self):
        self.assertEqual(splitpath('foo.txt'), ('', 'foo.txt'))
