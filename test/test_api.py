from unittest import TestCase

from aas_test_engines import api


class ApiTestCase(TestCase):

    def test_simple(self):
        pass


class SupportedVersionsTest(TestCase):

    def test_list(self):
        s = api.supported_versions()
        for i in s:
            print(i)
        self.assertIn(api.latest_version(), s)
