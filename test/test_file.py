from unittest import TestCase
import os
import zipfile
import io
import json
from xml.etree import ElementTree

from aas_test_engines import file, exception
from aas_test_engines.result import Level

script_dir = os.path.dirname(os.path.realpath(__file__))


def in_memory_zipfile(path: str):
    buffer = io.BytesIO()
    zip = zipfile.ZipFile(buffer, "a", zipfile.ZIP_DEFLATED, False)
    for root, subdirs, files in os.walk(path):
        for file in files:
            real_path = os.path.join(root, file)
            archive_path = real_path[len(path) + 1 :]
            zip.write(real_path, archive_path)
    return zip


class CheckJsonTest(TestCase):

    def test_empty(self):
        result = file.check_json_data({})
        self.assertTrue(result.ok())

    def test_no_json(self):
        result = file.check_json_file(io.StringIO("no json"))
        self.assertFalse(result.ok())

    def test_id_short_path(self):
        result = file.check_json_data(
            {
                "submodels": [
                    {
                        "id": "https://example.com/some-submodel",
                        "idShort": "someSubmodel",
                        "modelType": "Submodel",
                        "submodelElements": [
                            {
                                "modelType": "SubmodelElementCollection",
                                "idShort": "SMC",
                                "value": [
                                    {
                                        "modelType": "SubmodelElementList",
                                        "idShort": "SML",
                                        "valueTypeListElement": "xs:int",
                                        "typeValueListElement": "Property",
                                        "value": [
                                            {
                                                "modelType": "Property",
                                                "valueType": "xs:int",
                                                "value": "foo",
                                            }
                                        ],
                                    }
                                ],
                            }
                        ],
                    }
                ]
            }
        )
        result.dump()
        self.assertFalse(result.ok())
        self.assertTrue(
            any(
                "SMC.SML.0 in Submodel someSubmodel[https://example.com/some-submodel]" in line
                for line in result.to_lines()
            )
        )


class CheckXmlTest(TestCase):

    def test_empty(self):
        data = ElementTree.fromstring(
            """<environment xmlns="https://admin-shell.io/aas/3/0">
            </environment>"""
        )
        result = file.check_xml_data(data)
        self.assertTrue(result.ok())

    def test_invalid_namespace(self):
        data = ElementTree.fromstring(
            """<environment xmlns="invalid">
            </environment>"""
        )
        result = file.check_xml_data(data)
        self.assertFalse(result.ok())
        result.dump()

    def test_no_xml(self):
        result = file.check_xml_file(io.StringIO("no xml"))
        self.assertFalse(result.ok())

    def test_namespaces(self):
        data = ElementTree.fromstring(
            """<aas:environment xmlns:aas="https://admin-shell.io/aas/3/0">
                <aas:assetAdministrationShells>
                    <aas:assetAdministrationShell>
                        <aas:administration/>
                        <aas:id>something_142922d6</aas:id>
                        <aas:assetInformation>
                            <aas:assetKind>NotApplicable</aas:assetKind>
                            <aas:globalAssetId>something_eea66fa1</aas:globalAssetId>
                        </aas:assetInformation>
                    </aas:assetAdministrationShell>
                </aas:assetAdministrationShells>
            </aas:environment>"""
        )
        result = file.check_xml_data(data)
        result.dump()
        self.assertTrue(result.ok())


class CheckAasxTest(TestCase):

    def test_not_a_zip(self):
        with open(
            os.path.join(script_dir, "fixtures/aasx/invalid/invalid_json/[Content_Types].xml"),
            "rb",
        ) as f:
            result = file.check_aasx_file(f)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)

    def test_empty(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/empty"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)

    def test_no_rels(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/no_rels"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)

    def test_invalid_rels(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/invalid_rels"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)

    def test_unknown_filetype(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/unknown_filetype"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.WARNING)

    def test_rel_target_not_exists(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/rel_target_not_exists"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)
        self.assertTrue(any("Relationship has non-existing target aasx/aasx-origin" in i for i in result.to_lines()))

    def test_no_aas(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/no_aas1"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.WARNING)
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/no_aas2"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.WARNING)

    def test_valid_xml(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/xml"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.INFO)

    def test_valid_json(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/json"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.INFO)

    def test_invalid_xml(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/invalid_xml"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)

    def test_invalid_json(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/invalid/invalid_json"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.ERROR)

    def test_relative_paths(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/relative_paths"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.INFO)

    def test_recursive(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/recursive"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertEqual(result.level, Level.WARNING)

    def test_deprecated_rel(self):
        z = in_memory_zipfile(os.path.join(script_dir, "fixtures/aasx/valid/deprecated_rel"))
        result = file.check_aasx_data(z)
        result.dump()
        self.assertTrue(any("Deprecated type http://www.admin-shell.io/" in line for line in result.to_lines()))
        self.assertEqual(result.level, Level.WARNING)


class SupportedVersionTest(TestCase):

    def test_invoke(self):
        s = file.supported_versions()
        for version, templates in s.items():
            print(f"{version}: {', '.join(templates)}")
        self.assertIn(file.latest_version(), s)


class CheckSubmodelTemplate(TestCase):

    def test_contact_info(self):
        with open(os.path.join(script_dir, "fixtures", "submodel_templates", "contact_information.json")) as f:
            data = json.load(f)
        result = file.check_json_data(data)
        result.dump()
        self.assertTrue(result.ok())
        data["submodels"][0]["submodelElements"][0]["value"][0]["value"] = "invalid"
        result = file.check_json_data(data)
        result.dump()
        self.assertFalse(result.ok())

    def test_digital_nameplate(self):
        with open(os.path.join(script_dir, "fixtures", "submodel_templates", "digital_nameplate.json")) as f:
            data = json.load(f)
        result = file.check_json_data(data)
        result.dump()
        self.assertTrue(result.ok())
        # either family or type must be present
        elements = data["submodels"][0]["submodelElements"]
        indices = [
            idx
            for idx, value in enumerate(elements)
            if value["idShort"] in ["ManufacturerProductFamily", "ManufacturerProductType"]
        ]
        for idx in indices:
            del elements[idx]["semanticId"]
        result = file.check_json_data(data)
        result.dump()
        self.assertFalse(result.ok())

    def test_no_submodels(self):
        data = {}
        # is compliant to meta-model...
        result = file.check_json_data(data)
        result.dump()
        self.assertTrue(result.ok())
