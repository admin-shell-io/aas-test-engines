from unittest import TestCase
import os
import zipfile
import io
from xml.etree import ElementTree

from aas_test_engines import file

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
        result = file.check_json_data({})
        self.assertTrue(result.ok())


class CheckXmlTest(TestCase):

    def test_empty(self):
        data = ElementTree.fromstring(
            """<environment xmlns="https://admin-shell.io/aas/3/0">
            </environment>""")
        result = file.check_xml_data(data)
        self.assertTrue(result.ok())

    def test_invalid_namespace(self):
        data = ElementTree.fromstring(
            """<environment xmlns="invalid">
            </environment>""")
        result = file.check_xml_data(data)
        self.assertFalse(result.ok())
        result.dump()

class CheckAasxTest(TestCase):

    def test_empty(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/empty'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertFalse(result.ok())

    def test_no_rels(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/no_rels'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertFalse(result.ok())

    def test_invalid_rels(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/invalid_rels'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertFalse(result.ok())

    def test_unknown_filetype(self):
        z = in_memory_zipfile(os.path.join(
            script_dir, 'fixtures/aasx/invalid/unknown_filetype'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertFalse(result.ok())

    def test_valid_xml(self):
        z = in_memory_zipfile(os.path.join(script_dir, 'fixtures/aasx/valid/xml'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertTrue(result.ok())

    def test_valid_json(self):
        z = in_memory_zipfile(os.path.join(script_dir, 'fixtures/aasx/valid/json'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertTrue(result.ok())

    def test_invalid_xml(self):
        z = in_memory_zipfile(os.path.join(script_dir, 'fixtures/aasx/invalid/invalid_xml'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertFalse(result.ok())

    def test_invalid_json(self):
        z = in_memory_zipfile(os.path.join(script_dir, 'fixtures/aasx/invalid/invalid_json'))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertFalse(result.ok())


class SupportedVersionTest(TestCase):

    def test_invoke(self):
        s = file.supported_versions()
        for i in s:
            print(i)
        self.assertIn(file.latest_version(), s)

class AasCoreTestCase(TestCase):

    def is_blacklisted(self, path):
        blacklist = [
            'UnexpectedAdditionalProperty',
            'Double/lowest.',
            'Double/max.',
            'Float/largest_normal.',
            'ConstraintViolation/Reference/',
            'ConstraintViolation/reference',
            'ConstraintViolation/SubmodelElementList',
            'ConstraintViolation/submodelElementList',
            'basicEventElement/messageTopic.xml',
            'TypeViolation/langStringNameType/text.xml',
            'TypeViolation/blob/value.xml',
            'TypeViolation/langStringShortNameTypeIec61360/text.xml',
            'TypeViolation/assetInformation/assetType.xml',
            'TypeViolation/assetInformation/globalAssetId.xml',
            'TypeViolation/submodelElementList/orderRelevant.xml',
            'TypeViolation/conceptDescription/administration.xml',
            'TypeViolation/conceptDescription/id.xml',
            'TypeViolation/administrativeInformation/templateId.xml',
            'TypeViolation/specificAssetId/value.xml',
            'TypeViolation/specificAssetId/name.xml',
            'TypeViolation/langStringPreferredNameTypeIec61360/text.xml',
            'TypeViolation/langStringTextType/text.xml',
            'TypeViolation/submodel/administration.xml',
            'TypeViolation/submodel/id.xml',
            'TypeViolation/dataSpecificationIec61360/symbol.xml',
            'TypeViolation/dataSpecificationIec61360/value.xml',
            'TypeViolation/dataSpecificationIec61360/sourceOfDefinition.xml',
            'TypeViolation/dataSpecificationIec61360/valueFormat.xml',
            'TypeViolation/dataSpecificationIec61360/unit.xml',
            'TypeViolation/langStringDefinitionTypeIec61360/text.xml',
            'TypeViolation/assetAdministrationShell/administration.xml',
            'TypeViolation/assetAdministrationShell/id.xml',
            'TypeViolation/key/value.xml',
            'TypeViolation/valueReferencePair/value.xml',
            'TypeViolation/levelType/min.xml',
            'TypeViolation/levelType/max.xml',
            'TypeViolation/levelType/typ.xml',
            'TypeViolation/levelType/nom.xml',
        ]
        for i in blacklist:
            if i in path:
                return True
        return False

    def _run(self, dirname: str, check):
        print(f"Testing {dirname}, this might take a few minutes...")
        valid_accepted = 0
        valid_rejected = 0
        invalid_accepted = 0
        invalid_rejected = 0
        skipped = 0
        for root, dirs, files in os.walk(os.path.join(script_dir, f'fixtures/aas-core3.0-testgen/test_data/{dirname}/ContainedInEnvironment'), topdown=False):
            for name in files:
                path_in = os.path.join(root, name)
                if self.is_blacklisted(path_in):
                    skipped += 1
                    continue
                with open(path_in) as f:
                    errors = check(f)
                if errors.ok():
                    if 'Expected' in path_in:
                        valid_accepted += 1
                    else:
                        invalid_accepted += 1
                else:
                    if 'Expected' in path_in:
                        valid_rejected += 1
                    else:
                        invalid_rejected += 1
        print("valid, accepted",     valid_accepted)
        print("invalid, rejected",   invalid_rejected)
        print("valid, rejected",     valid_rejected)
        print("invalid, accepted",   invalid_accepted)
        print("skipped",             skipped)

    def test_json(self):
        self._run('Json', file.check_json_file)

    def test_xml(self):
        self._run('Xml', file.check_xml_file)
