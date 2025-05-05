from unittest import TestCase
from aas_test_engines.config import TestCaseFilter
from aas_test_engines.exception import InvalidFilterException


class TestFilter(TestCase):

    def test_empty(self):
        filter = TestCaseFilter("")
        self.assertEqual(len(filter.includes), 0)
        self.assertEqual(len(filter.excludes), 0)
        self.assertTrue(filter.selects("I am a test"))

    def test_accept_all(self):
        filter = TestCaseFilter("*")
        self.assertEqual(len(filter.includes), 1)
        self.assertEqual(len(filter.excludes), 0)
        self.assertTrue(filter.selects("I am a test"))

    def test_reject_all(self):
        filter = TestCaseFilter("~*")
        self.assertEqual(len(filter.includes), 0)
        self.assertEqual(len(filter.excludes), 1)
        self.assertFalse(filter.selects("I am a test"))

    def test_accept_and_reject_all(self):
        filter = TestCaseFilter("*:~*")
        self.assertEqual(len(filter.includes), 1)
        self.assertEqual(len(filter.excludes), 1)
        self.assertFalse(filter.selects("I am a test"))

    def test_accept_single(self):
        filter = TestCaseFilter("I am a test")
        self.assertEqual(len(filter.includes), 1)
        self.assertEqual(len(filter.excludes), 0)
        self.assertTrue(filter.selects("I am a test"))

    def test_accept_multiple(self):
        filter = TestCaseFilter("I am a test:Test2")
        self.assertEqual(len(filter.includes), 2)
        self.assertEqual(len(filter.excludes), 0)
        self.assertTrue(filter.selects("I am a test"))
        self.assertTrue(filter.selects("Test2"))

    def test_reject_multiple(self):
        filter = TestCaseFilter("~I am a test:Test2")
        self.assertEqual(len(filter.includes), 0)
        self.assertEqual(len(filter.excludes), 2)
        self.assertFalse(filter.selects("I am a test"))
        self.assertFalse(filter.selects("Test2"))

    def test_accept_glob(self):
        filter = TestCaseFilter("*test*")
        self.assertEqual(len(filter.includes), 1)
        self.assertEqual(len(filter.excludes), 0)
        self.assertTrue(filter.selects("I am a test"))
        self.assertTrue(filter.selects("test2"))
        self.assertFalse(filter.selects("Test2"))  # case sensitive

    def test_reject_glob(self):
        filter = TestCaseFilter("~*test*")
        self.assertEqual(len(filter.includes), 0)
        self.assertEqual(len(filter.excludes), 1)
        self.assertFalse(filter.selects("I am a test"))
        self.assertFalse(filter.selects("test2"))
        self.assertTrue(filter.selects("Test2"))  # case sensitive

    def test_complex(self):
        filter = TestCaseFilter("GetAll*:*Submodels~GetAllSubmodels:*Post*")
        self.assertEqual(len(filter.includes), 2)
        self.assertEqual(len(filter.excludes), 2)
        self.assertTrue(filter.selects("GetAllShells"))
        self.assertFalse(filter.selects("GetAllSubmodels"))
        self.assertFalse(filter.selects("PostSubmodels"))
        self.assertTrue(filter.selects("PutSubmodels"))

    def test_invalid(self):
        with self.assertRaises(InvalidFilterException):
            TestCaseFilter("a~b~c")
