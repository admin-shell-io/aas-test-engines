from unittest import TestCase
import os
import zipfile
import io
from xml.etree import ElementTree

from aas_test_tools import file

script_dir = os.path.dirname(os.path.realpath(__file__))


def in_memory_zipfile(path: str):
    buffer = io.BytesIO()
    zip = zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, False)
    for root, subdirs, files in os.walk(path):
        for file in files:
            real_path = os.path.join(root, file)
            archive_path = real_path[len(path)+1:]
            zip.write(real_path, archive_path)
    return zip


class CheckJsonTest(TestCase):

    def test_empty(self):
        result = file.check_json_data({}, '3.0.0')
        self.assertTrue(result.ok())


class CheckXmlTest(TestCase):

    def test_empty(self):
        data = ElementTree.fromstring(
            """<environment xmlns="https://admin-shell.io/aas/3/0">
            </environment>""")
        result = file.check_xml_data(data, '3.0.0')
        self.assertTrue(result.ok())


class CheckAasxTest(TestCase):

    def test_empty(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/empty'))
        result = file.check_aasx_data(z, '3.0.0')
        result.dump()
        self.assertFalse(result.ok())

    def test_no_rels(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/no_rels'))
        result = file.check_aasx_data(z, '3.0.0')
        result.dump()
        self.assertFalse(result.ok())

    def test_invalid_rels(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/invalid_rels'))
        result = file.check_aasx_data(z, '3.0.0')
        result.dump()
        self.assertFalse(result.ok())

    def test_unknown_filetype(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/unknown_filetype'))
        result = file.check_aasx_data(z, '3.0.0')
        result.dump()
        self.assertTrue(result.ok())

    def test_minimal(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/valid/simple'))
        result = file.check_aasx_data(z, '3.0.0')
        result.dump()
        self.assertTrue(result.ok())
