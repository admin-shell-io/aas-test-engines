from unittest import TestCase
from aas_test_engines._util import group, un_group


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
