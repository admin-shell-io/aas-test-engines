from typing import List, Dict, TextIO, Union, Any, Set
import os
import json
from yaml import safe_load

from .exception import AasTestToolsException
from .result import AasTestResult, Level
from .data_types import validators

from xml.etree import ElementTree
from json_schema_plus.schema import JsonSchemaValidator, ValidatorCollection, ValidationConfig, ParseConfig
from json_schema_plus.types import JsonType
from zipfile import ZipFile

JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


class AasSchema:

    def __init__(self, validator: JsonSchemaValidator):
        self.validator = validator


def _find_schemas() -> Dict[str, any]:
    result = {}
    script_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'file')
    for i in os.listdir(data_dir):
        path = os.path.join(data_dir, i)
        if not i.endswith('.yml'):
            continue
        schema = safe_load(open(path))
        config = ParseConfig(
            format_validators=validators
        )
        validator = JsonSchemaValidator(schema, config)
        result[i[:-4]] = AasSchema(validator)
    return result


_schemas = _find_schemas()
_DEFAULT_VERSION = '3.0'

def supported_versions():
    return list(_schemas.keys())

def latest_version():
    return _DEFAULT_VERSION

def _get_schema(version: str) -> AasSchema:
    try:
        return _schemas[version]
    except KeyError:
        raise AasTestToolsException(
            f"Unknown version {version}, must be one of {supported_versions()}")


def check_json_data(data: any, version: str = _DEFAULT_VERSION) -> AasTestResult:
    schema = _get_schema(version)
    error = schema.validator.get_error(data, ValidationConfig())
    if error:
        return AasTestResult('Invalid', '', Level.ERROR)
    else:
        return AasTestResult('Valid', '', Level.INFO)


def check_json_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    data = json.load(file)
    return check_json_data(data, version)


def check_xml_data(data: ElementTree, version: str = _DEFAULT_VERSION) -> AasTestResult:
    expected_namespace = '{https://admin-shell.io/aas/3/0}'

    def preprocess(data: ElementTree.Element, validator: ValidatorCollection) -> JSON:
        if isinstance(data, (dict, list, str, bool, int, float)) or data is None:
            return data
        types = validator.get_types()
        if types == {JsonType.OBJECT}:
            result = {}
            for child in data:
                if not child.tag.startswith(expected_namespace):
                    raise Exception(f"invalid namespace, got {child.tag}")
                tag = child.tag[len(expected_namespace):]
                result[tag] = child
            result['modelType'] = data.tag[len(
                expected_namespace):].capitalize()
            return result
        elif types == {JsonType.ARRAY}:
            result = []
            for child in data:
                result.append(child)
            return result
        elif types == {JsonType.STRING}:
            return data.text
        elif types == {JsonType.BOOLEAN}:
            return data.text == 'true'
        elif data.tag.endswith('}value') or \
                data.tag.endswith('}min') or \
                data.tag.endswith('}max'):
            return data.text or ""
        else:
            raise Exception(f"Unkown type {types} of {data}")
    schema = _get_schema(version)
    config = ValidationConfig(preprocessor=preprocess)
    error = schema.validator.get_error(data, config)
    if error:
        return AasTestResult('Invalid', '', Level.ERROR)
    else:
        return AasTestResult('Valid', '', Level.INFO)


def check_xml_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    data = ElementTree.fromstring(file.read())
    return check_xml_data(data, version)


NS_CONTENT_TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"
NS_RELATIONSHIPS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

TYPE_AASX_ORIGIN = 'http://www.admin-shell.io/aasx/relationships/aasx-origin'
TYPE_AASX_SPEC = 'http://www.admin-shell.io/aasx/relationships/aas-spec'
TYPE_AASX_SUPPL = 'http://www.admin-shell.io/aasx/relationships/aas-suppl'
TYPE_THUMBNAIL = 'http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail'


class Relationship:

    def __init__(self, type: str, target: str) -> None:
        self.type = type
        self.target = target
        self.sub_rels: List[Relationship] = []

    def sub_rels_by_type(self, type: str) -> List["Relationship"]:
        return [i for i in self.sub_rels if i.type == type]

    def dump(self, indent=0):
        type_suffix = self.type.split("/")[-1]
        print("  " * indent + f"{self.target} [{type_suffix}]")
        for sub_rel in self.sub_rels:
            sub_rel.dump(indent + 1)


def _check_content_type(zipfile: ZipFile) -> AasTestResult:
    content_types_xml = '[Content_Types].xml'
    result = AasTestResult(f'Checking {content_types_xml}', content_types_xml)
    try:
        with zipfile.open(content_types_xml, 'r') as f:
            content_types = ElementTree.parse(f)
            expected_tag = f'{NS_CONTENT_TYPES}Types'
            if content_types.getroot().tag != expected_tag:
                result.append(
                    AasTestResult(f"root must have tag {expected_tag}, got {content_types.getroot().tag}", content_types_xml, Level.ERROR))
    except KeyError:
        result.append(AasTestResult(
            f"{content_types_xml} not found", content_types_xml, Level.ERROR))

    return result


def _scan_relationships(zipfile: ZipFile, parent_rel: Relationship, rels_file: TextIO, visited_targets: Set[str]) -> AasTestResult:
    relationships = ElementTree.parse(rels_file).getroot()
    expected_tag = f"{NS_RELATIONSHIPS}Relationships"
    if relationships.tag != expected_tag:
        return AasTestResult(f'Invalid root tag {relationships.tag}, expected {expected_tag}', relationships.tag, Level.ERROR)

    result = AasTestResult(f"Checking relationships", relationships.tag)
    for idx, rel in enumerate(relationships):
        if rel.tag != f"{NS_RELATIONSHIPS}Relationship":
            result.append(AasTestResult(
                f'Invalid tag {rel.tag}', str(idx), Level.ERROR))
            continue
        try:
            type = rel.attrib['Type']
            target = rel.attrib['Target']
        except KeyError as e:
            result.append(AasTestResult(
                f'Attribute {e} is missing', str(idx), Level.ERROR))
            continue

        if target.startswith('/'):
            target = target[1:]

        sub_dir, file = os.path.split(target)
        sub_rel = Relationship(type, target)
        parent_rel.sub_rels.append(sub_rel)
        if target in visited_targets:
            result.append(AasTestResult(
                'Recursive relationship', str(idx), Level.ERROR))
            continue
        visited_targets.add(target)
        if target not in zipfile.namelist():
            result.append(AasTestResult(
                f'Relationship has non-existing target {target}', str(idx), Level.ERROR))
            continue
        try:
            with zipfile.open(f"{sub_dir}/_rels/{file}.rels", "r") as f:
                r = _scan_relationships(zipfile, sub_rel, f, visited_targets)
                result.append(r)
        except KeyError:
            # No further sub-relationships
            pass
        result.append(AasTestResult(
            f'Relationship {target} is ok', str(idx), Level.INFO))

    return result


def _check_relationships(zipfile: ZipFile, root_rel: Relationship) -> AasTestResult:
    result = AasTestResult('Checking relationships', '')
    visited_targets = set()
    try:
        ROOT_REL_PATH = "_rels/.rels"
        with zipfile.open(ROOT_REL_PATH, "r") as f:
            r = _scan_relationships(zipfile, root_rel, f, visited_targets)
            result.append(r)
    except KeyError:
        result.append(AasTestResult(
            f"{ROOT_REL_PATH} does not exist", ROOT_REL_PATH, Level.ERROR))
    return result


def _check_files(zipfile: ZipFile, root_rel: Relationship, version: str) -> AasTestResult:
    result = AasTestResult('Checking files', '')
    for aasx_origin in root_rel.sub_rels_by_type(TYPE_AASX_ORIGIN):
        sub_result = AasTestResult(
            f'Checking {aasx_origin.target}', aasx_origin.target)
        for aasx_spec in aasx_origin.sub_rels_by_type(TYPE_AASX_SPEC):
            try:
                with zipfile.open(aasx_spec.target) as f:
                    if aasx_spec.target.endswith('.xml'):
                        check_xml_file(f, version)
                    elif aasx_spec.target.endswith('.json'):
                        check_json_file(f, version)
                    else:
                        sub_result.append(AasTestResult(
                            'Unknown filetype', aasx_spec.target))
            except KeyError:
                return AasTestResult("File does not exist")
        result.append(sub_result)
    return result


def check_aasx_data(zipfile: ZipFile, version: str = _DEFAULT_VERSION) -> AasTestResult:

    result = AasTestResult('Checking AASX package', '')

    result.append(_check_content_type(zipfile))
    if not result.ok():
        return result

    root_rel = Relationship('ROOT', '/')
    result.append(_check_relationships(zipfile, root_rel))
    if not result.ok():
        return result

    result.append(_check_files(zipfile, root_rel, version))
    if not result.ok():
        return result

    return result


def check_aasx_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    zipfile = ZipFile(file)
    return check_json_data(zipfile, version)
