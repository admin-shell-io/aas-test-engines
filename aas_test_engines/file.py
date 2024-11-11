from typing import List, Dict, TextIO, Union, Any, Set, Optional, Generator
import os
import json
from yaml import load
try:
    # This one is faster but not available on all systems
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

from .exception import AasTestToolsException
from .result import AasTestResult, Level
from .data_types import validators
from ._generate import generate_graph

from xml.etree import ElementTree
from json_schema_tool.schema import SchemaValidator, SchemaValidator, ParseConfig, parse_schema
import zipfile

from aas_test_engines.test_cases.v3_0 import json_to_env, xml_to_env
from aas_test_engines.test_cases.v3_0.submodel_templates import supported_templates

from ._util import un_group, normpath, splitpath

JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


class AasSchema:

    def __init__(self, validator: SchemaValidator, schema: JSON):
        self.validator = validator
        self.schema = schema


def _find_schemas() -> Dict[str, AasSchema]:
    result = {}
    script_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'file')
    for i in os.listdir(data_dir):
        path = os.path.join(data_dir, i)
        if not i.endswith('.yml'):
            continue
        schema = load(open(path, "rb"), Loader=Loader)
        config = ParseConfig(
            format_validators=validators
        )
        validator = parse_schema(schema, config)
        result[i[:-4]] = AasSchema(validator, schema)
    return result


_schemas = _find_schemas()
_DEFAULT_VERSION = '3.0'


def supported_versions() -> Dict[str, List[str]]:
    return {'3.0': supported_templates()}


def latest_version():
    return _DEFAULT_VERSION


def _get_schema(version: str) -> AasSchema:
    try:
        schema = _schemas[version]
    except KeyError:
        raise AasTestToolsException(f"Unknown version {version}, must be one of {supported_versions()}")
    return schema


def check_json_data(data: any, version: str = _DEFAULT_VERSION) -> AasTestResult:
    result, env = json_to_env(data)
    return result


def check_json_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    try:
        data = json.load(file)
    except json.decoder.JSONDecodeError as e:
        return AasTestResult(f"Invalid JSON: {e}", Level.ERROR)
    return check_json_data(data, version)


def check_xml_data(data: ElementTree, version: str = _DEFAULT_VERSION, submodel_templates: Set[str] = set()) -> AasTestResult:
    result, env = xml_to_env(data)
    return result


def check_xml_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    try:
        data = ElementTree.fromstring(file.read())
    except ElementTree.ParseError as e:
        return AasTestResult(f"Invalid xml: {e}", Level.ERROR)
    return check_xml_data(data, version)


NS_CONTENT_TYPES = "{http://schemas.openxmlformats.org/package/2006/content-types}"
NS_RELATIONSHIPS = "{http://schemas.openxmlformats.org/package/2006/relationships}"

TYPE_AASX_ORIGIN = 'http://admin-shell.io/aasx/relationships/aasx-origin'
TYPE_AASX_SPEC = 'http://admin-shell.io/aasx/relationships/aas-spec'
TYPE_AASX_SUPPL = 'http://admin-shell.io/aasx/relationships/aas-suppl'
DEPRECATED_TYPES = {
    'http://www.admin-shell.io/aasx/relationships/aasx-origin': TYPE_AASX_ORIGIN,
    'http://www.admin-shell.io/aasx/relationships/aas-spec': TYPE_AASX_SPEC,
    'http://www.admin-shell.io/aasx/relationships/aas-suppl': TYPE_AASX_SUPPL
}
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


def _check_content_type(zipfile: zipfile.ZipFile) -> AasTestResult:
    content_types_xml = '[Content_Types].xml'
    result = AasTestResult(f'Checking {content_types_xml}')
    try:
        with zipfile.open(content_types_xml, 'r') as f:
            content_types = ElementTree.parse(f)
            expected_tag = f'{NS_CONTENT_TYPES}Types'
            if content_types.getroot().tag != expected_tag:
                result.append(
                    AasTestResult(f"root must have tag {expected_tag}, got {content_types.getroot().tag}", Level.ERROR))
    except KeyError:
        result.append(AasTestResult(f"{content_types_xml} not found", Level.ERROR))

    return result


def _scan_relationships(zipfile: zipfile.ZipFile, parent_rel: Relationship, dir: str, file: str, visited_targets: Set[str]) -> Optional[AasTestResult]:
    try:
        with zipfile.open(f"{dir}_rels/{file}.rels", "r") as f:
            relationships = ElementTree.parse(f).getroot()
    except KeyError:
        # file does not exist
        return None
    expected_tag = f"{NS_RELATIONSHIPS}Relationships"
    if relationships.tag != expected_tag:
        return AasTestResult(f'Invalid root tag {relationships.tag}, expected {expected_tag}', Level.ERROR)

    if dir:
        result = AasTestResult(f"Checking relationships of {dir}{file}")
    else:
        result = AasTestResult(f"Checking root relationship")
    for idx, rel in enumerate(relationships):
        if rel.tag != f"{NS_RELATIONSHIPS}Relationship":
            result.append(AasTestResult(
                f'Invalid tag {rel.tag}', Level.ERROR))
            continue
        try:
            type = rel.attrib['Type']
            target = rel.attrib['Target']
        except KeyError as e:
            result.append(AasTestResult(f'Attribute {e} is missing', Level.ERROR))
            continue

        if type in DEPRECATED_TYPES:
            new_type = DEPRECATED_TYPES[type]
            result.append(AasTestResult(f"Deprecated type {type}, considering as {new_type}", level=Level.WARNING))
            type = new_type

        if target.startswith('/'):
            target = target[1:]
        else:
            target = dir + target
        target = normpath(target)

        sub_dir, file = splitpath(target)
        sub_rel = Relationship(type, target)
        result.append(AasTestResult(f'Relationship {sub_rel.target} is of type {sub_rel.type}', Level.INFO))
        parent_rel.sub_rels.append(sub_rel)
        if target in visited_targets:
            result.append(AasTestResult(f'Already checked {target}', Level.INFO))
            continue
        visited_targets.add(target)
        if target not in zipfile.namelist():
            result.append(AasTestResult(f'Relationship has non-existing target {target}', Level.ERROR))
            continue
        r = _scan_relationships(zipfile, sub_rel, sub_dir + '/', file, visited_targets)
        if r:
            result.append(r)

    return result


def _check_relationships(zipfile: zipfile.ZipFile, root_rel: Relationship) -> AasTestResult:
    result = AasTestResult('Checking relationships')
    visited_targets = set()
    r = _scan_relationships(zipfile, root_rel, '', '', visited_targets)
    if r:
        result.append(r)
    else:
        result.append(AasTestResult(f"Root relationship does not exist", Level.ERROR))
    return result


def _check_files(zipfile: zipfile.ZipFile, root_rel: Relationship, version: str) -> AasTestResult:
    result = AasTestResult('Checking files')
    origin_rels = root_rel.sub_rels_by_type(TYPE_AASX_ORIGIN)
    if len(origin_rels) != 1:
        result.append(AasTestResult(f"Expected exactly one aas origin, but found {len(origin_rels)}", level=Level.WARNING))
    for aasx_origin in origin_rels:
        spec_rels = aasx_origin.sub_rels_by_type(TYPE_AASX_SPEC)
        if not spec_rels:
            result.append(AasTestResult("No aas spec found", level=Level.WARNING))
        for aasx_spec in spec_rels:
            sub_result = AasTestResult(f'Checking {aasx_spec.target}')
            try:
                with zipfile.open(aasx_spec.target) as f:
                    if aasx_spec.target.endswith('.xml'):
                        r = check_xml_file(f, version)
                    elif aasx_spec.target.endswith('.json'):
                        r = check_json_file(f, version)
                    else:
                        r = AasTestResult('Unknown filetype', Level.WARNING)
                    sub_result.append(r)
            except KeyError:
                return AasTestResult("File does not exist")
            result.append(sub_result)
    return result


def check_aasx_data(zipfile: zipfile.ZipFile, version: str = _DEFAULT_VERSION) -> AasTestResult:

    result = AasTestResult('Checking AASX package')

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
    try:
        zip = zipfile.ZipFile(file)
    except zipfile.BadZipFile as e:
        return AasTestResult(f"Cannot read: {e}", level=Level.ERROR)

    return check_aasx_data(zip, version)


def generate(version: str = _DEFAULT_VERSION) -> Generator[str, None, None]:
    aas = _get_schema(version)
    graph = generate_graph(aas.schema)
    for i in graph.generate_paths():
        sample = graph.execute(i.path)
        if i.is_valid:
            valid = True
        else:
            valid = check_json_data(sample, version).ok()
        yield valid, sample
