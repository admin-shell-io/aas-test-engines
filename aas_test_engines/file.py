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
from .data_types import validators, is_bcp_47_for_english
from ._generate import generate_graph, FlowGraph

from xml.etree import ElementTree
from json_schema_tool.schema import SchemaValidator, SchemaValidator, ValidationConfig, ParseConfig, SchemaValidationResult, KeywordValidationResult, parse_schema
from json_schema_tool.types import JsonType, values_are_equal
from json_schema_tool.exception import PreprocessorException, PostProcessorException
import zipfile

from ._util import un_group, normpath, splitpath

JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]


class AasSchema:

    def __init__(self, validator: SchemaValidator, schema: JSON, submodel_templates: Dict[str, SchemaValidator], submodel_schemas: Dict[str, any]):
        self.validator = validator
        self.schema = schema
        self.submodel_templates = submodel_templates
        self.submodel_schemas = submodel_schemas


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
        submodel_templates = {}
        submodel_schemas = {}
        for key, submodel_schema in schema['$defs']['SubmodelTemplates'].items():
            submodel_schema['$defs'] = schema['$defs']
            submodel_schema['$schema'] = 'https://json-schema.org/draft/2020-12/schema'
            submodel_templates[key] = parse_schema(submodel_schema, config)
            submodel_schemas[key] = submodel_schema
        result[i[:-4]] = AasSchema(validator, schema, submodel_templates, submodel_schemas)
    return result


_schemas = _find_schemas()
_DEFAULT_VERSION = '3.0'


def supported_versions() -> Dict[str, List[str]]:
    return {
        i: list(aas.submodel_templates.keys())
        for i, aas in _schemas.items()
    }


def latest_version():
    return _DEFAULT_VERSION


def _get_schema(version: str, submodel_templates: Set[str]) -> AasSchema:
    try:
        schema = _schemas[version]
    except KeyError:
        raise AasTestToolsException(f"Unknown version {version}, must be one of {supported_versions()}")
    all_templates = schema.submodel_templates.keys()
    unknown = submodel_templates - all_templates
    if unknown:
        raise AasTestToolsException(f"Unknown submodel templates {unknown}, must be in {sorted(all_templates)}")
    return schema


def map_error(parent: AasTestResult, error: SchemaValidationResult):
    for i in error.keyword_results:
        if i.ok():
            continue
        kw_result = AasTestResult(i.error_message, '', Level.ERROR)
        for j in i.sub_schema_results:
            map_error(kw_result, j)
        parent.append(kw_result)


FRAGMENT_KEYS = [
    'FragmentReference',
    'Referable',
    'AnnotatedRelationshipElement',
    'BasicEventElement',
    'Blob',
    'Capability',
    'DataElement',
    'Entity',
    'EventElement',
    'File',
    'MultiLanguageProperty',
    'Operation',
    'Property',
    'Range',
    'ReferenceElement',
    'RelationshipElement',
    'SubmodelElement',
    'SubmodelElementCollection',
    'SubmodelElementList',
]


def check_constraints(instance: any, validator: SchemaValidator):
    for check in validator.schema.get('check', []):
        if check == 'Constraint_AASd-107':
            try:
                semantic_id = instance['semanticIdListElement']
            except KeyError:
                continue
            for i in instance.get('value', []):
                try:
                    if not values_are_equal(i['semanticId'], semantic_id):
                        raise PostProcessorException(f"AASd-107: Invalid semantic id")
                except KeyError:
                    pass
        elif check == 'Constraint_AASd-108':
            type_value = instance['typeValueListElement']
            for i in instance.get('value', []):
                if i['modelType'] != type_value:
                    raise PostProcessorException(f"AASd-108: Expected modelType {type_value}")
        elif check == 'Constraint_AASd-109':
            if instance['typeValueListElement'] in ['Property', 'Range']:
                try:
                    value_type = instance['valueTypeListElement']
                except KeyError as e:
                    raise PostProcessorException("AASd-109: valueTypeListElement must be set")
                for i in instance.get('value', []):
                    if i['valueType'] != value_type:
                        raise PostProcessorException("Invalid valueType")
        elif check == 'Constraint_AASd-114':
            last_semantic_id = None
            for i in instance.get('value', []):
                try:
                    semantic_id = i['semanticId']
                except KeyError:
                    continue
                if last_semantic_id and not values_are_equal(last_semantic_id, semantic_id):
                    raise PostProcessorException(f"AASd-114: Invalid semanticId")
                last_semantic_id = semantic_id
        elif check == 'Constraint_AASd-124':
            if not isinstance(instance, dict) or 'keys' not in instance:
                continue
            keys = instance['keys']
            if not isinstance(keys, list) or len(keys) == 0:
                continue
            last_key = keys[-1]
            if not isinstance(last_key, dict) or 'type' not in last_key:
                continue
            if last_key['type'] not in ['GlobalReference', 'FragmentReference']:
                raise PostProcessorException(f"AASd-125: invalid last key")
        elif check == 'Constraint_AASd-125':
            if not isinstance(instance, dict) or 'keys' not in instance:
                continue
            keys = instance['keys']
            if not isinstance(keys, list):
                continue
            for idx, key in enumerate(keys):
                if idx == 0:
                    continue
                if not isinstance(key, dict) or 'type' not in key:
                    continue
                if key['type'] not in FRAGMENT_KEYS:
                    raise PostProcessorException("AASd-125: Not a fragment key")
        elif check == 'Constraint_AASd-127':
            if not isinstance(instance, dict) or 'keys' not in instance:
                continue
            keys = instance['keys']
            if not isinstance(keys, list):
                continue
            for idx, key in enumerate(keys):
                if not isinstance(key, dict) or 'type' not in key:
                    continue
                if key['type'] == 'FragmentReference':
                    if idx == 0 or keys[idx-1]['type'] not in ['File', 'Blob']:
                        raise PostProcessorException("AASd-127: FragmentReference not preceded by File or Blob")
                # TODO
                # else:
                #     raise PostProcessorException("AASd-127: FragmentReference not allowed")
        elif check == 'Constraint_AASd-128':
            if not isinstance(instance, dict) or 'keys' not in instance:
                continue
            keys = instance['keys']
            if not isinstance(keys, list):
                continue
            for idx, key in enumerate(keys):
                if not isinstance(key, dict) or 'type' not in key:
                    continue
                if key['type'] != 'SubmodelElementList':
                    continue
                if idx + 1 == len(keys) or not keys[idx+1]['value'].isdigit():
                    raise PostProcessorException("AASd-128: SubmodelElementList must be succeeded by an integer")
        elif check == 'Constraint_AASd-119':
            if not isinstance(instance, dict):
                continue
            qualifiers = instance.get('qualifiers', [])
            if not isinstance(qualifiers, list):
                continue
            if any(qualifier.get('kind') == 'TemplateQualifier' for qualifier in qualifiers):
                if instance.get('kind') != 'Template':
                    raise PostProcessorException("AASd-129: kind must be Template as at least one qualifier is a TemplateQualifier")
        elif check == 'Constraint_AASd-129':
            if not isinstance(instance, dict):
                continue
            elements = instance.get('submodelElements')
            if not isinstance(elements, list):
                continue
            for element in elements:
                qualifiers = element.get('qualifiers')
                if not isinstance(qualifiers, list):
                    continue
                if any(qualifier.get('kind') == 'TemplateQualifier' for qualifier in qualifiers):
                    if instance.get('kind') != 'Template':
                        raise PostProcessorException("AASd-129: kind must be Template as at least one qualifier is a TemplateQualifier")
        elif check == 'Constraint_AASd-134':
            # TODO
            pass
        elif check == 'Constraint_AASc-3a-002':
            try:
                if not any(is_bcp_47_for_english(name.get('language')) for name in instance['preferredName']):
                    raise PostProcessorException("AASc-3a-008: preferredName must be provided at least in english")
            except (KeyError, TypeError, AttributeError):
                pass
        elif check == 'Constraint_AASc-3a-008':
            try:
                if 'value' not in instance:
                    if not any(is_bcp_47_for_english(definition.get('language')) for definition in instance['definition']):
                        raise PostProcessorException("AASc-3a-008: definition must be provided at least in english")
            except (KeyError, TypeError, AttributeError):
                pass
        else:
            # This should not happen
            raise RuntimeError(f"Invalid check {check}")


def _check_json_data(data: any, validator: SchemaValidator, short_circuit: bool) -> AasTestResult:
    result = AasTestResult('Check JSON', '', Level.INFO)
    config = ValidationConfig(
        postprocessor=check_constraints,
        short_circuit_evaluation=short_circuit,
    )

    error = validator.validate(data, config)
    map_error(result, error)
    return result


def check_json_data(data: any, version: str = _DEFAULT_VERSION, submodel_templates: Set = set()) -> AasTestResult:
    schema = _get_schema(version, submodel_templates)
    result = _check_json_data(data, schema.validator, False)

    if submodel_templates and result.ok():

        def preprocess(data: ElementTree.Element, validator: SchemaValidator) -> JSON:
            try:
                group_by = validator.schema['groupBy']
            except KeyError:
                return data
            result: Dict[str, List[any]] = {}
            if not isinstance(data, list):
                raise PreprocessorException("Expected an array")
            for idx, value in enumerate(data):
                try:
                    key = value[group_by]
                except KeyError:
                    raise PreprocessorException(f"Property {group_by} is missing at idx {idx}")
                if not isinstance(key, str):
                    raise PreprocessorException(f"{key} must be a string at idx {idx}")
                try:
                    result[key].append(value)
                except KeyError:
                    result[key] = [value]
            return result

        submodels_result = AasTestResult('Checking submodel templates')
        for name in submodel_templates:
            submodel_result = AasTestResult(f"Checking for {name}")
            validator = schema.submodel_templates[name]
            config = ValidationConfig(
                preprocessor=preprocess
            )
            error = validator.validate(data, config)
            map_error(submodel_result, error)
            submodels_result.append(submodel_result)
        result.append(submodels_result)
    return result


def check_json_file(file: TextIO, version: str = _DEFAULT_VERSION, submodel_templates: Set = set()) -> AasTestResult:
    try:
        data = json.load(file)
    except json.decoder.JSONDecodeError as e:
        return AasTestResult(f"Invalid JSON: {e}", '', Level.ERROR)
    return check_json_data(data, version, submodel_templates)


def _get_model_type(el: ElementTree.Element, expected_namespace: str):
    model_type = el.tag[len(expected_namespace):]
    model_type = model_type[0].upper() + model_type[1:]
    return model_type


def _get_single_child(el: ElementTree.Element) -> ElementTree.Element:
    if len(el) != 1:
        raise PreprocessorException("DataSpecificationContent must have exactly one child")
    return el[0]


def _is_json(data: any) -> bool:
    if data is None:
        return True
    return isinstance(data, (dict, list, str, bool, int, float))


def _assert_no_children(el: ElementTree.Element):
    if next(iter(el), None):
        raise PreprocessorException("No child elements allowed")


def _assert_no_text(el: ElementTree.Element):
    if el.text is None:
        return
    if el.text.strip():
        raise PreprocessorException("No inline text allowed")


def check_xml_data(data: ElementTree, version: str = _DEFAULT_VERSION, submodel_templates: Set[str] = set()) -> AasTestResult:
    expected_namespace = '{https://admin-shell.io/aas/3/0}'

    def preprocess(data: ElementTree.Element, validator: SchemaValidator) -> JSON:

        if _is_json(data):
            return data

        if not data.tag.startswith(expected_namespace):
            raise PreprocessorException(f"invalid namespace, got '{data.tag}'")

        types = validator.get_types()

        if types == {JsonType.OBJECT}:

            _assert_no_text(data)

            # Special handling for data specification content
            if data.tag.endswith('dataSpecificationContent'):
                data = _get_single_child(data)

            result = {}
            result['modelType'] = _get_model_type(data, expected_namespace)
            for child in data:
                if not child.tag.startswith(expected_namespace):
                    raise PreprocessorException(f"invalid namespace, got {child.tag}")
                tag = child.tag[len(expected_namespace):]
                if result['modelType'] == 'OperationVariable' and tag == 'value':
                    result[tag] = _get_single_child(child)
                else:
                    result[tag] = child
            return result
        elif types == {JsonType.ARRAY}:
            result = []
            for child in data:
                result.append(child)
            return result
        elif types == {JsonType.STRING}:
            _assert_no_children(data)
            return data.text or ""
        elif types == {JsonType.BOOLEAN}:
            _assert_no_children(data)
            return data.text == 'true'
        else:
            raise Exception(f"Unknown type {types} at {validator.pointer}")
    schema = _get_schema(version, submodel_templates)
    config = ValidationConfig(
        preprocessor=preprocess,
    )
    error = schema.validator.validate(data, config)
    result = AasTestResult('Check XML', '', Level.INFO)
    map_error(result, error)
    return result


def check_xml_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    try:
        data = ElementTree.fromstring(file.read())
    except ElementTree.ParseError as e:
        return AasTestResult(f"Invalid xml: {e}", '', Level.ERROR)
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


def _scan_relationships(zipfile: zipfile.ZipFile, parent_rel: Relationship, dir: str, file: str, visited_targets: Set[str]) -> Optional[AasTestResult]:
    try:
        with zipfile.open(f"{dir}_rels/{file}.rels", "r") as f:
            relationships = ElementTree.parse(f).getroot()
    except KeyError:
        # file does not exist
        return None
    expected_tag = f"{NS_RELATIONSHIPS}Relationships"
    if relationships.tag != expected_tag:
        return AasTestResult(f'Invalid root tag {relationships.tag}, expected {expected_tag}', relationships.tag, Level.ERROR)

    if dir:
        result = AasTestResult(f"Checking relationships of {dir}{file}", relationships.tag)
    else:
        result = AasTestResult(f"Checking root relationship", relationships.tag)
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
        result.append(AasTestResult(f'Relationship {sub_rel.target} is of type {sub_rel.type}', str(idx), Level.INFO))
        parent_rel.sub_rels.append(sub_rel)
        if target in visited_targets:
            result.append(AasTestResult(f'Already checked {target}', str(idx), Level.INFO))
            continue
        visited_targets.add(target)
        if target not in zipfile.namelist():
            result.append(AasTestResult(
                f'Relationship has non-existing target {target}', str(idx), Level.ERROR))
            continue
        r = _scan_relationships(zipfile, sub_rel, sub_dir + '/', file, visited_targets)
        if r:
            result.append(r)

    return result


def _check_relationships(zipfile: zipfile.ZipFile, root_rel: Relationship) -> AasTestResult:
    result = AasTestResult('Checking relationships', '')
    visited_targets = set()
    r = _scan_relationships(zipfile, root_rel, '', '', visited_targets)
    if r:
        result.append(r)
    else:
        result.append(AasTestResult(f"Root relationship does not exist", '', Level.ERROR))
    return result


def _check_files(zipfile: zipfile.ZipFile, root_rel: Relationship, version: str) -> AasTestResult:
    result = AasTestResult('Checking files', '')
    origin_rels = root_rel.sub_rels_by_type(TYPE_AASX_ORIGIN)
    if len(origin_rels) != 1:
        result.append(AasTestResult(f"Expected exactly one aas origin, but found {len(origin_rels)}", level=Level.WARNING))
    for aasx_origin in origin_rels:
        spec_rels = aasx_origin.sub_rels_by_type(TYPE_AASX_SPEC)
        if not spec_rels:
            result.append(AasTestResult("No aas spec found", level=Level.WARNING))
        for aasx_spec in spec_rels:
            sub_result = AasTestResult(f'Checking {aasx_spec.target}', aasx_spec.target)
            try:
                with zipfile.open(aasx_spec.target) as f:
                    if aasx_spec.target.endswith('.xml'):
                        r = check_xml_file(f, version)
                    elif aasx_spec.target.endswith('.json'):
                        r = check_json_file(f, version)
                    else:
                        r = AasTestResult('Unknown filetype', aasx_spec.target, Level.WARNING)
                    sub_result.append(r)
            except KeyError:
                return AasTestResult("File does not exist")
            result.append(sub_result)
    return result


def check_aasx_data(zipfile: zipfile.ZipFile, version: str = _DEFAULT_VERSION) -> AasTestResult:

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
    try:
        zip = zipfile.ZipFile(file)
    except zipfile.BadZipFile as e:
        return AasTestResult(f"Cannot read: {e}", level=Level.ERROR)

    return check_aasx_data(zip, version)


def generate(version: str = _DEFAULT_VERSION, submodel_template: Optional[str] = None) -> Generator[str, None, None]:
    if submodel_template is None:
        aas = _get_schema(version, set())
        graph = generate_graph(aas.schema)
        for i in graph.generate_paths():
            sample = graph.execute(i.path)
            if i.is_valid:
                valid = True
            else:
                valid = _check_json_data(sample, aas.validator, True).ok()
            yield valid, sample
    else:
        aas = _get_schema(version, set([submodel_template]))
        graph = generate_graph(aas.submodel_schemas[submodel_template])
        for i in graph.generate_paths():
            sample = graph.execute(i.path)
            sample = un_group(sample)
            yield i.is_valid, sample
