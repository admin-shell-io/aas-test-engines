from typing import Dict, Set
from .exception import AasTestToolsException
from .result import AasTestResult, Level

from fences.open_api.open_api import OpenApi
from fences.open_api.generate import SampleCache, parse_operation, Request

import os
from yaml import safe_load
from dataclasses import dataclass
import requests
import html

_available_suites = {
    # APIs
    "Asset Administration Shell API": [
        "GetAssetAdministrationShell",
        "PutAssetAdministrationShell",
        "GetAllSubmodelReferences",
        "PostSubmodelReference",
        "DeleteSubmodelReference",
        "GetAssetInformation",
        "PutAssetInformation",
        "GetThumbnail",
        "PutThumbnail",
        "DeleteThumbnail"
    ],
    "Submodel API": [
        "GetSubmodel",
        "GetAllSubmodelElements",
        "GetSubmodelElementByPath",
        "GetFileByPath",
        "PutFileByPath",
        "DeleteFileByPath",
        "PutSubmodel",
        "PatchSubmodel",
        "PostSubmodelElement",
        "PostSubmodelElementByPath",
        "PutSubmodelElementByPath",
        "PatchSubmodelElementByPath",
        "GetSubmodelElementValueByPath",
        "DeleteSubmodelElementByPath",
        "InvokeOperationSync",
        "InvokeOperationAsync",
        "GetOperationAsyncStatus",
        "GetOperationAsyncResult",
    ],
    "Serialization API": [
        "GenerateSerializationByIds",
    ],
    "AASX File Server API": [
        "GetAllAASXPackageIds",
        "GetAASXByPackageId",
        "PostAASXPackage",
        "PutAASXByPackageId",
        "DeleteAASXByPackageId",
    ],
    "Asset Administration Shell Registry API": [
        "GetAllAssetAdministrationShellDescriptors",
        "GetAssetAdministrationShellDescriptorById",
        "PostAssetAdministrationShellDescriptor",
        "PutAssetAdministrationShellDescriptorById",
        "DeleteAssetAdministrationShellDescriptorById",
    ],
    "Submodel Registry API": [
        "GetAllSubmodelDescriptors",
        "GetSubmodelDescriptorById",
        "PostSubmodelDescriptor",
        "PutSubmodelDescriptorById",
        "DeleteSubmodelDescriptorById",
    ],
    "Asset Administration Shell Repository API": [
        "GetAllAssetAdministrationShells",
        "GetAllAssetAdministrationShells-Reference",
        "GetAssetAdministrationShellById",
        "GetAllAssetAdministrationShellsByAssetId",
        "GetAllAssetAdministrationShellsByIdShort",
        "PostAssetAdministrationShell",
        "PutAssetAdministrationShellById",
        "DeleteAssetAdministrationShellById",
        "GetAssetAdministrationShellById-Reference_AasRepository",
    ],
    "Submodel Repository API": [
        "GetAllSubmodelDescriptors",
        "GetSubmodelDescriptorById",
        "PostSubmodelDescriptor",
        "PutSubmodelDescriptorById",
        "DeleteSubmodelDescriptorById",
    ],
    "Concept Description Repository API": [
        "GetAllConceptDescriptions",
        "GetConceptDescriptionById",
        "GetAllConceptDescriptionsByIdShort",
        "GetAllConceptDescriptionsByIsCaseOf",
        "GetAllConceptDescriptionsByDataSpecificationReference",
        "PostConceptDescription",
        "PutConceptDescriptionById",
        "DeleteConceptDescriptionById",
    ],
    "Asset Administration Shell Basic Discovery API": [
        "GetAllAssetAdministrationShellIdsByAssetLink",
        "GetAllAssetLinksById",
        "PostAllAssetLinksById",
        "DeleteAllAssetLinksById",
    ],
    "Description API": [
        "GetSelfDescription",
    ],
    # Service Specs
    "Asset Administration Shell Service Specification": [
        "Asset Administration Shell API",
        "Submodel API", # TODO: via super path
        "Serialization API",
        "Description API",
    ],
    "Submodel Service Specification": [
        "Submodel API",
        "Serialization API",
        "Description API",
    ],
    "AASX File Server Service Specification": [
        "AASX File Server API",
        "Description API",
    ],
    "Asset Administration Shell Registry Service Specification": [
        "Asset Administration Shell Registry API",
        "Submodel Registry API", # TODO: via super path
        "Description API",
    ],
    "Submodel Registry Service Specification": [
        "Submodel Registry API",
        "Description API",
    ],
    "Discovery Service Specification": [
        "Asset Administration Shell Basic Discovery API",
        "Description API",
    ],
    "Asset Administration Shell Repository Service Specification": [
        "Asset Administration Shell API", # TODO: via super path
        "Submodel API", # TODO: via super path
        "Asset Administration Shell Repository API",
        "Submodel Repository API", # TODO: via super path
        "Serialization API",
        "Description API",
    ],
    "Submodel Repository Service Specification": [
        "Submodel API", # TODO: via super path
        "Submodel Repository API", # TODO: via super path
        "Serialization API",
        "Description API",
    ],
    "ConceptDescription Repository Service Specification": [
        "Serialization API",
        "Description API",
        "Concept Description Repository API",
    ],
    # Service Spec Profiles
    "AssetAdministrationShellServiceSpecification/SSP-001": [
        "Asset Administration Shell Service Specification"
    ],
    "AssetAdministrationShellServiceSpecification/SSP-002": [
        "GetAssetAdministrationShell",
        "GetAllSubmodelReferences",
        "GetAssetInformation",
        "GetThumbnail",
        "GetSubmodel", # TODO: via super path
        "GetAllSubmodelElements", # TODO: via super path
        "GetSubmodelElementByPath", # TODO: via super path
        "GetFileByPath", # TODO: via super path
    ],
    "SubmodelServiceSpecification/SSP-001": [
        "Submodel Service Specification",
    ],
    "SubmodelServiceSpecification/SSP-002": [
        "GetSubmodel",
        "GetAllSubmodelElements",
        "GetSubmodelElementByPath",
        "GetFileByPath",
        "GenerateSerializationByIds",
        "GetDescription",
    ],
    "SubmodelServiceSpecification/SSP-003": [
        "GetSubmodel",
        "InvokeOperationSync",
        "GetDescription",
    ],
    "AasxFileServerServiceSpecification/SSP-001": [
        "AASX File Server Service Specification"
    ],
    "AssetAdministrationShellRegistryServiceSpecification/SSP-001": [
        "Asset Administration Shell Registry Service Specification",
    ],
    "AssetAdministrationShellRegistryServiceSpecification/SSP-002": [
        "GetAllAssetAdministrationShellDescriptors",
        "GetAssetAdministrationShellDescriptorById",
        "GetAllSubmodelDescriptors", # TODO: via super path
        "GetSubmodelDescriptorById", # TODO: via super path
    ],
    "SubmodelRegistryServiceSpecification/SSP-001": [
        "Submodel Registry Service Specification",
    ],
    "SubmodelRegistryServiceSpecification/SSP-002": [
        "GetAllSubmodelDescriptors",
        "GetSubmodelDescriptorById",
        "GetDescription",
    ],
    "DiscoveryServiceSpecification/SSP-001": [
        "Discovery Service Specification",
    ],
    "AssetAdministrationShellRepositoryServiceSpecification/SSP-001": [
        "Asset Administration Shell Repository Service Specification",
    ],
    "AssetAdministrationShellRepositoryServiceSpecification/SSP-002": [
        "GetAllAssetAdministrationShells",
        "GetAssetAdministrationShellById",
        "GetAllAssetAdministrationShellsByAssetId",
        "GetAllAssetAdministrationShellsByIdShort",
        "GetAssetAdministrationShell", # TODO: via super path
        "GetAllSubmodelReferences", # TODO: via super path
        "GetAssetInformation", # TODO: via super path
        "GetThumbnail", # TODO: via super path
        "GetAllSubmodels", # TODO: via super path
        "GetSubmodelById", # TODO: via super path
        "GetAllSubmodelsBySemanticId", # TODO: via super path
        "GetAllSubmodelsByIdShort", # TODO: via super path
        "GetSubmodel", # TODO: via super path
        "GetAllSubmodelElements", # TODO: via super path
        "GetSubmodelElementByPath", # TODO: via super path
        "GetFileByPath", # TODO: via super path
        "GenerateSerializationByIds",
        "GetDescription",
    ],
    "SubmodelRepositoryServiceSpecification/SSP-001": [
        "Submodel Repository Service Specification",
    ],
    "SubmodelRepositoryServiceSpecification/SSP-002": [
        "GetAllSubmodels",
        "GetSubmodelById",
        "GetAllSubmodelsBySemanticId",
        "GetAllSubmodelsByIdShort",
        "GetSubmodel",
        "GetAllSubmodelElements",
        "GetSubmodelElementByPath",
        "GetFileByPath",
        "GenerateSerializationByIds",
        "GetDescription"
    ],
    "SubmodelRepositoryServiceSpecification/SSP-003": [
        "SubmodelRepositoryServiceSpecification/SSP-001" # TODO: Constraint AASa-003
    ],
    "SubmodelRepositoryServiceSpecification/SSP-004": [
        "SubmodelRepositoryServiceSpecification/SSP-002" # TODO: Constraint AASa-004
    ],
    "ConceptDescriptionRepositoryServiceSpecification/SSP-001": [
        "Concept Description Repository Service Specification"
    ]
}


@dataclass
class ExecConf:
    server: str = ''
    dry: bool = False
    verify: bool = True


def _check_server(exec_conf: ExecConf) -> AasTestResult:
    result = AasTestResult(f'Check {exec_conf.server}')
    try:
        requests.get(exec_conf.server, verify=exec_conf.verify)
        result.append(AasTestResult('OK', '', Level.INFO))
    except requests.exceptions.RequestException as e:
        result.append(AasTestResult('Failed to reach: {}'.format(e), '', Level.ERROR))
    return result


class AasSpec:

    def __init__(self, open_api: OpenApi) -> None:
        self.open_api = open_api


def _find_specs() -> Dict[str, AasSpec]:
    result = {}
    script_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'api')
    for i in os.listdir(data_dir):
        path = os.path.join(data_dir, i)
        if not i.endswith('.yml'):
            continue
        with open(path, 'rb') as f:
            spec = safe_load(f)
        open_api = OpenApi.from_dict(spec)
        result[i[:-4]] = AasSpec(open_api)
    return result


_specs = _find_specs()

_DEFAULT_VERSION = '3.0'


def _get_spec(version: str) -> AasSpec:
    try:
        return _specs[version]
    except KeyError:
        raise AasTestToolsException(
            f"Unknown version {version}, must be one of {supported_versions()}")

def _html_safe(content: bytes, max_len: int = 100) -> str:
    content = content.decode()
    if len(content) > max_len:
        content = content[:max_len]
    return html.escape(content)

def execute_tests(version: str = _DEFAULT_VERSION, suites: Set[str] = None, conf: ExecConf = ExecConf()) -> AasTestResult:
    spec = _get_spec(version)
    if suites is None:
        suites = set(_available_suites.keys())
    operations = set()
    for suite in suites:
        try:
            operations.update(_available_suites[suite])
        except KeyError:
            all_suites = "\n".join(sorted(_available_suites.keys()))
            raise AasTestToolsException(f"Unknown suite {suite}, must be one of:\n{all_suites}")
    sample_cache = SampleCache()
    result_root = AasTestResult("Checking api")
    for operation in spec.open_api.operations.values():
        if operation.operation_id not in operations:
            continue
        result_op = AasTestResult(f"Checking {operation.operation_id}")
        result_negative = AasTestResult("Negative tests")
        result_positive = AasTestResult("Positive tests")

        graph = parse_operation(operation, sample_cache)
        for i in graph.generate_paths():
            request: Request = graph.execute(i.path)
            result_request = AasTestResult(f"Invoke: {request.operation.method.upper()} {request.path}")
            response = request.execute(conf.server)
            if response.status_code >= 400 and response.status_code < 500:
                if i.is_valid:
                    result_request.append(AasTestResult(f"Got bad status code {response.status_code}: {_html_safe(response.content)}", level=Level.ERROR))
                else:
                    result_request.append(AasTestResult(f"Ok ({response.status_code})"))
            elif response.status_code >= 200 and response.status_code < 300:
                if i.is_valid:
                    result_request.append(AasTestResult(f"Ok ({response.status_code})"))
                else:
                    result_request.append(AasTestResult(f"Got good status code {response.status_code}: {_html_safe(response.content)}", level=Level.ERROR))
            else:
                result_request.append(AasTestResult(f"Got unexpected status code {response.status_code}: {_html_safe(response.content)}", level=Level.ERROR))
            parent = result_positive if i.is_valid else result_negative
            parent.append(result_request)
        result_op.append(result_negative)
        result_op.append(result_positive)
        result_root.append(result_op)
    return result_root


def supported_versions():
    return {ver: spec.tags for ver, spec in _specs.items()}


def latest_version():
    return _DEFAULT_VERSION
