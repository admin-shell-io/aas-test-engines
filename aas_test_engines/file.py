from typing import List, Dict, TextIO, Union, Any, Set, Optional
import json

from .result import AasTestResult, Level
from .opc import Relationship, read_opc

from xml.etree import ElementTree
import zipfile

from aas_test_engines.test_cases.v3_0 import json_to_env, xml_to_env
from aas_test_engines.test_cases.v3_0.submodel_templates import supported_templates

JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]

_DEFAULT_VERSION = "3.0"


def supported_versions() -> Dict[str, List[str]]:
    return {"3.0": supported_templates()}


def latest_version():
    return _DEFAULT_VERSION


def check_json_data(data: any, version: str = _DEFAULT_VERSION) -> AasTestResult:
    result, env = json_to_env(data)
    return result


def check_json_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    try:
        data = json.load(file)
    except json.decoder.JSONDecodeError as e:
        return AasTestResult(f"Invalid JSON: {e}", Level.ERROR)
    return check_json_data(data, version)


def check_xml_data(
    data: ElementTree,
    version: str = _DEFAULT_VERSION,
    submodel_templates: Set[str] = set(),
) -> AasTestResult:
    result, env = xml_to_env(data)
    return result


def check_xml_file(file: TextIO, version: str = _DEFAULT_VERSION) -> AasTestResult:
    try:
        data = ElementTree.fromstring(file.read())
    except ElementTree.ParseError as e:
        return AasTestResult(f"Invalid xml: {e}", Level.ERROR)
    return check_xml_data(data, version)


TYPE_AASX_ORIGIN = "http://admin-shell.io/aasx/relationships/aasx-origin"
TYPE_AASX_SPEC = "http://admin-shell.io/aasx/relationships/aas-spec"
TYPE_AASX_SUPPL = "http://admin-shell.io/aasx/relationships/aas-suppl"
DEPRECATED_TYPES = {
    "http://www.admin-shell.io/aasx/relationships/aasx-origin": TYPE_AASX_ORIGIN,
    "http://www.admin-shell.io/aasx/relationships/aas-spec": TYPE_AASX_SPEC,
    "http://www.admin-shell.io/aasx/relationships/aas-suppl": TYPE_AASX_SUPPL,
}
TYPE_THUMBNAIL = "http://schemas.openxmlformats.org/package/2006/relationships/metadata/thumbnail"


def _check_files(zipfile: zipfile.ZipFile, root_rel: Relationship, version: str) -> AasTestResult:
    result = AasTestResult("Checking files")
    origin_rels = root_rel.sub_rels_by_type(TYPE_AASX_ORIGIN)
    if len(origin_rels) != 1:
        result.append(
            AasTestResult(
                f"Expected exactly one aas origin, but found {len(origin_rels)}",
                level=Level.WARNING,
            )
        )
    for aasx_origin in origin_rels:
        spec_rels = aasx_origin.sub_rels_by_type(TYPE_AASX_SPEC)
        if not spec_rels:
            result.append(AasTestResult("No aas spec found", level=Level.WARNING))
        for aasx_spec in spec_rels:
            sub_result = AasTestResult(f"Checking {aasx_spec.target}")
            try:
                with zipfile.open(aasx_spec.target) as f:
                    if aasx_spec.target.endswith(".xml"):
                        r = check_xml_file(f, version)
                    elif aasx_spec.target.endswith(".json"):
                        r = check_json_file(f, version)
                    else:
                        r = AasTestResult("Unknown filetype", Level.WARNING)
                    sub_result.append(r)
            except KeyError:
                return AasTestResult("File does not exist")
            result.append(sub_result)
    return result


def check_aasx_data(zipfile: zipfile.ZipFile, version: str = _DEFAULT_VERSION) -> AasTestResult:

    result = AasTestResult("Checking AASX package")
    root_rel = Relationship("ROOT", "/")
    read_opc(zipfile, root_rel, result, DEPRECATED_TYPES)
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
