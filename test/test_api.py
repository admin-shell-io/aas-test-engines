from unittest import TestCase

from aas_test_engines import api
from aas_test_engines.test_cases.v3_0.api import check_in_sync


class SupportedVersionsTest(TestCase):

    def test_list(self):
        s = api.supported_versions()
        for i in s:
            print(i)
        self.assertIn(api.latest_version(), s)

    def test_in_sync(self):
        check_in_sync()
