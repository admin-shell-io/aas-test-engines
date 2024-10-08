from typing import Dict, List, Union, Optional, Tuple
from .exception import AasTestToolsException
from .result import AasTestResult, Level, start, abort, write, ResultException
from ._util import b64urlsafe
from .file import map_error

from fences.open_api.open_api import OpenApi, Operation
from fences.open_api.generate import SampleCache, generate_all, generate_one_valid, Request
from fences.core.util import ConfusionMatrix
from json_schema_tool.schema import parse_schema, ParseConfig

import os
from yaml import load
try:
    # This one is faster but not available on all systems
    from yaml import CSafeLoader as Loader
except ImportError:
    from yaml import SafeLoader as Loader

from dataclasses import dataclass
import requests


def _assert(predicate: bool, message):
    if predicate:
        write(f'{message}: OK')
    else:
        abort(f'{message}: Fail')


def _stringify_path(path: List[Union[str, int]]) -> str:
    return "/".join(str(fragment) for fragment in path)


class _NoDefault:
    pass


def _lookup(value: any, path: List[Union[str, int]], default=_NoDefault, idx: int = 0) -> any:
    if idx >= len(path):
        return value

    fragment = path[idx]
    if isinstance(fragment, str):
        if not isinstance(value, dict):
            if default is _NoDefault:
                abort(f"Cannot look up {_stringify_path(path)}: should be an object")
            else:
                return default
        try:
            sub_value = value[fragment]
        except KeyError:
            if default is _NoDefault:
                abort(f"Cannot look up {_stringify_path(path)}: key '{fragment}' does not exist")
            else:
                return default
    elif isinstance(fragment, int):
        if not isinstance(value, list):
            if default is _NoDefault:
                abort(f"Cannot look up {_stringify_path(path)}: should be an array")
            else:
                return default
        try:
            sub_value = value[fragment]
        except IndexError:
            if default is _NoDefault:
                abort(f"Cannot look up {_stringify_path(path)}: array too short")
            else:
                return default
    return _lookup(sub_value, path, default, idx+1)


def _extend(data: Dict[str, List[str]]) -> dict:
    while True:
        all_resolved = True
        for key, values in data.items():
            new_values = []
            for value in values:
                try:
                    new_values.extend(data[value])
                    all_resolved = False
                except KeyError:
                    new_values.append(value)
            data[key] = new_values
        if all_resolved:
            return data


SSP_PREFIX = "https://admin-shell.io/aas/API/3/0/"

_available_suites = _extend({
    # APIs
    "Asset Administration Shell API": [
        "GetAssetAdministrationShell",
        "PutAssetAdministrationShell",
        "GetAllSubmodelReferences",
        "PostSubmodelReference",
        "DeleteSubmodelReferenceById",
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
        # "GetSubmodelElementValueByPath", # TODO
        "DeleteSubmodelElementByPath",
        "InvokeOperationSync_AAS",
        "InvokeOperationAsync_AAS",
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
        "GetDescription",
    ],
    # Service Specs
    "Asset Administration Shell Service Specification": [
        "Asset Administration Shell API",
        "Submodel API",  # TODO: via super path
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
        "Submodel Registry API",  # TODO: via super path
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
        "Asset Administration Shell API",  # TODO: via super path
        "Submodel API",  # TODO: via super path
        "Asset Administration Shell Repository API",
        "Submodel Repository API",  # TODO: via super path
        "Serialization API",
        "Description API",
    ],
    "Submodel Repository Service Specification": [
        "Submodel API",  # TODO: via super path
        "Submodel Repository API",  # TODO: via super path
        "Serialization API",
        "Description API",
    ],
    "ConceptDescription Repository Service Specification": [
        "Serialization API",
        "Description API",
        "Concept Description Repository API",
    ],
    # Service Spec Profiles
    f"{SSP_PREFIX}AssetAdministrationShellServiceSpecification/SSP-001": [
        "Asset Administration Shell Service Specification"
    ],
    f"{SSP_PREFIX}AssetAdministrationShellServiceSpecification/SSP-002": [
        # AAS
        "GetAssetAdministrationShell",
        "GetAssetAdministrationShell-Reference",
        "GetAllSubmodelReferences",
        "GetAssetInformation",
        "GetThumbnail",
        # Submodel Repo
        "GetSubmodel_AAS",
        "GetSubmodel-Metadata_AAS",
        "GetSubmodel-ValueOnly_AAS",
        "GetSubmodelMetadata-Reference_AAS",
        "GetSubmodel-Path_AAS",
        # Submodel Elements
        "GetAllSubmodelElements_AAS",
        "GetAllSubmodelElements-Metadata_AAS",
        "GetAllSubmodelElements-ValueOnly_AAS",
        "GetAllSubmodelElementsReference_AAS",
        "GetAllSubmodelElementsPath_AAS",
        # Submodel Element
        "GetSubmodelElementByPath_AAS",
        "GetSubmodelElementByPath-Metadata_AAS",
        "GetSubmodelElementByPath-ValueOnly_AAS",
        "GetSubmodelElementByPath-Reference_AAS",
        "GetSubmodelElementByPath-Path_AAS",
        "GetFileByPath_AAS",
    ],
    f"{SSP_PREFIX}SubmodelServiceSpecification/SSP-001": [
        "Submodel Service Specification",
    ],
    f"{SSP_PREFIX}SubmodelServiceSpecification/SSP-002": [
        # Submodel API
        "GetSubmodel",
        "GetSubmodel-Metadata",
        "GetSubmodel-ValueOnly",
        "GetSubmodel-Reference",
        "GetSubmodel-Path",
        "GetAllSubmodelElements",
        "GetAllSubmodelElements-Metadata",
        "GetAllSubmodelElements-ValueOnly",
        "GetAllSubmodelElements-Reference",
        "GetAllSubmodelElements-Path",
        "GetSubmodelElementByPath",
        "GetSubmodelElementByPath-Metadata",
        "GetSubmodelElementByPath-ValueOnly",
        "GetSubmodelElementByPath-Reference",
        "GetSubmodelElementByPath-Path",
        "GetFileByPath",
        # Serialization API
        "GenerateSerializationByIds",
        # Description API
        "GetDescription",
    ],
    f"{SSP_PREFIX}SubmodelServiceSpecification/SSP-003": [
        "GetSubmodel",
        "InvokeOperation_SubmodelRepo",
        "GetDescription",
    ],
    f"{SSP_PREFIX}AasxFileServerServiceSpecification/SSP-001": [
        "AASX File Server Service Specification"
    ],
    f"{SSP_PREFIX}AssetAdministrationShellRegistryServiceSpecification/SSP-001": [
        "Asset Administration Shell Registry Service Specification",
    ],
    f"{SSP_PREFIX}AssetAdministrationShellRegistryServiceSpecification/SSP-002": [
        "GetAllAssetAdministrationShellDescriptors",
        "GetAssetAdministrationShellDescriptorById",
        "GetAllSubmodelDescriptorsThroughSuperpath",
        "GetSubmodelDescriptorByIdThroughSuperpath",
    ],
    f"{SSP_PREFIX}SubmodelRegistryServiceSpecification/SSP-001": [
        "Submodel Registry Service Specification",
    ],
    f"{SSP_PREFIX}SubmodelRegistryServiceSpecification/SSP-002": [
        "GetAllSubmodelDescriptors",
        "GetSubmodelDescriptorById",
        "GetDescription",
    ],
    f"{SSP_PREFIX}DiscoveryServiceSpecification/SSP-001": [
        "Discovery Service Specification",
    ],
    f"{SSP_PREFIX}AssetAdministrationShellRepositoryServiceSpecification/SSP-001": [
        "Asset Administration Shell Repository Service Specification",
    ],
    f"{SSP_PREFIX}AssetAdministrationShellRepositoryServiceSpecification/SSP-002": [
        # AAS Repository API:
        "GetAllAssetAdministrationShells",
        "GetAllAssetAdministrationShells-Reference",
        "GetAssetAdministrationShellById",
        "GetAssetAdministrationShellById-Reference_AasRepository",
        # AAS API by superpath:
        "GetAllSubmodelReferences_AasRepository",
        "GetAssetInformation_AasRepository",
        "GetThumbnail_AasRepository",
        # Submodel Repository API by superpath:
        "GetSubmodelById_AasRepository",
        "GetSubmodelById-Metadata_AasRepository",
        "GetSubmodelById-ValueOnly_AasRepository",
        "GetSubmodelById-Reference_AasRepository",
        "GetSubmodelById-Path_AasRepository",
        # Submodel API by superpath:
        "GetAllSubmodelElements_AasRepository",
        "GetAllSubmodelElements-Metadata_AasRepository",
        "GetAllSubmodelElements-ValueOnly_AasRepository",
        "GetAllSubmodelElements-Reference_AasRepository",
        "GetAllSubmodelElements-Path_AasRepository",
        "GetSubmodelElementByPath_AasRepository",
        "GetSubmodelElementByPath-Metadata_AasRepository",
        "GetSubmodelElementByPath-ValueOnly_AasRepository",
        "GetSubmodelElementByPath-Reference_AasRepository",
        "GetSubmodelElementByPath-Path_AasRepository",
        "GetFileByPath_AasRepository",
        # Serialization API
        "GenerateSerializationByIds",
        # Description API
        "GetDescription",
    ],
    f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-001": [
        "Submodel Repository Service Specification",
    ],
    f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-002": [
        # Submodel Repository API
        "GetAllSubmodels",
        'GetAllSubmodels-Metadata',
        'GetAllSubmodels-ValueOnly',
        'GetAllSubmodels-Reference',
        'GetAllSubmodels-Path',
        "GetSubmodelById",
        "GetSubmodelById-Metadata",
        "GetSubmodelById-ValueOnly",
        "GetSubmodelById-Reference",
        "GetSubmodelById-Path",
        # Submodel API
        'GetAllSubmodelElements_SubmodelRepository',
        'GetAllSubmodelElements-Metadata_SubmodelRepository',
        'GetAllSubmodelElements-ValueOnly_SubmodelRepo',
        'GetAllSubmodelElements-Reference_SubmodelRepo',
        'GetAllSubmodelElements-Path_SubmodelRepo',
        "GetSubmodelElementByPath_SubmodelRepo",
        "GetSubmodelElementByPath-Metadata_SubmodelRepo",
        "GetSubmodelElementByPath-ValueOnly_SubmodelRepo",
        "GetSubmodelElementByPath-Reference_SubmodelRepo",
        "GetSubmodelElementByPath-Path_SubmodelRepo",
        "GetFileByPath_SubmodelRepo",
        # Serialization API
        "GenerateSerializationByIds",
        # Description API
        "GetDescription"
    ],
    f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-003": [
        f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-001"  # TODO: Constraint AASa-003
    ],
    f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-004": [
        f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-002"  # TODO: Constraint AASa-004
    ],
    f"{SSP_PREFIX}ConceptDescriptionRepositoryServiceSpecification/SSP-001": [
        "ConceptDescription Repository Service Specification"
    ]
})

_test_suites: Dict[str, "ApiTestSuite"] = {}


def operation(name: str):
    assert name not in _test_suites

    def decorator(fn):
        _test_suites[name] = fn
        return fn
    return decorator


@dataclass
class ExecConf:
    server: str
    dry: bool = False
    verify: bool = True
    remove_path_prefix: str = ""


def _check_server(exec_conf: ExecConf) -> bool:
    with start(f'Trying to reach {exec_conf.server}'):
        if exec_conf.dry:
            write("Skipped due to dry run", Level.WARNING)
            return True

        try:
            requests.get(exec_conf.server, verify=exec_conf.verify)
            write('OK')
            return True
        except requests.exceptions.RequestException as e:
            write('Failed to reach: {}'.format(e), Level.CRITICAL)
            return False


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
            spec = load(f, Loader=Loader)
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


def _shorten(content: bytes, max_len: int = 300) -> str:
    try:
        content = content.decode()
    except UnicodeDecodeError:
        return "<binary-data>"
    if len(content) > max_len:
        return content[:max_len] + "..."
    return content


def _get_json(response: requests.models.Response) -> dict:
    try:
        return response.json()
    except requests.exceptions.JSONDecodeError as e:
        abort(f"Cannot decode as JSON: {e}")


def _invoke(request: Request, conf: ExecConf, positive_test) -> requests.models.Response:
    prepared_request = request.build(conf.server).prepare()
    response = requests.Session().send(prepared_request, verify=conf.verify)
    write(f"Response: ({response.status_code}): {_shorten(response.content)}")
    if response.status_code >= 500:
        abort(f"Got status code {response.status_code}", Level.CRITICAL)
    if positive_test:
        if response.status_code < 200 or response.status_code > 299:
            abort(f"Expected status code 2xx, but got {response.status_code}")
    else:
        if response.status_code < 400 or response.status_code > 499:
            abort(f"Expected status code 4xx, but got {response.status_code}")
    return response


def _invoke_and_decode(request: Request, conf: ExecConf, positive_test: bool) -> dict:
    with start(f"Invoke: {request.operation.method.upper()} {request.make_path()}"):
        response = _invoke(request, conf, positive_test)
        expected_responses = []
        expected_responses += [i for i in request.operation.responses if i.code == response.status_code]
        expected_responses += [i for i in request.operation.responses if i.code is None]
        if not expected_responses:
            abort(f"Invalid status code {response.status_code}")
        data = _get_json(response)
        validator = parse_schema({**expected_responses[0].schema, '$schema': 'https://json-schema.org/draft/2020-12/schema'}, ParseConfig(raise_on_unknown_format=False))
        validation_result = validator.validate(data)
        if validation_result.ok:
            write("Response conforms to schema")
        else:
            result = AasTestResult(f"Invalid response for schema", level=Level.ERROR)
            map_error(result, validation_result)
            raise ResultException(result)
        return data


class ApiTestSuite:

    def __init__(self, operation: Operation, conf: ExecConf, sample_cache: SampleCache, open_api: OpenApi, suite: str):
        self.operation = operation
        self.conf = conf
        self.sample_cache = sample_cache
        self.open_api = open_api
        self.suite = suite
        self.valid_values: Dict[str, List[any]] = {}

    def setup(self):
        pass

    def execute_syntactic_test(self, request: Request):
        _invoke_and_decode(request, self.conf, False)

    def execute_syntactic_tests(self):
        graph = generate_all(self.operation, self.sample_cache, self.valid_values)
        for i in graph.generate_paths():
            request: Request = graph.execute(i.path)
            if not i.is_valid:
                self.execute_syntactic_test(request)

    def execute_semantic_tests(self):
        fns = [getattr(self, i) for i in dir(self) if i.startswith('test_')]
        fns.sort(key=lambda x: x.__code__.co_firstlineno)
        for test_fn in fns:
            with start(test_fn.__doc__ or test_fn.__name__):
                test_fn()

    def execute(self) -> ConfusionMatrix:
        mat = ConfusionMatrix()
        with start("Negative Tests") as result:
            self.execute_syntactic_tests()
        mat.invalid_rejected = len([i for i in result.sub_results if i.ok()])
        mat.invalid_accepted = len(result.sub_results) - mat.invalid_rejected
        with start("Positive Tests") as result:
            self.execute_semantic_tests()
        mat.valid_accepted = len([i for i in result.sub_results if i.ok()])
        mat.valid_rejected = len(result.sub_results) - mat.valid_accepted
        return mat

    def teardown(self):
        pass


# /shells
class GetAllAasTestSuiteBase(ApiTestSuite):

    def setup(self):
        self.cursor: Optional[str] = None
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 2})
        data = _invoke_and_decode(request, self.conf, True)
        self.valid_id_short: str = _lookup(data, ['result', 0, 'idShort'])
        self.second_id_short: Optional[str] = _lookup(data, ['result', 1, 'idShort'], None)
        self.cursor = _lookup(data, ['paging_metadata', 'cursor'], None)

    def test_no_parameters(self):
        """
        Invoke without parameters
        """
        request = generate_one_valid(self.operation, self.sample_cache)
        _invoke_and_decode(request, self.conf, True)

    def test_get_one(self):
        """
        Fetch only one
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        data = _lookup(data, ['result'])
        _assert(len(data) == 1, 'Has exactly one result entry')

    def test_filter_by_non_existing_idshort(self):
        """
        Filter by non-existing idShort
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'idShort': 'does-not-exist'})
        data = _invoke_and_decode(request, self.conf, True)
        data = _lookup(data, ['result'])
        _assert(len(data) == 0, 'Result is empty')

    def test_pagination(self):
        """
        Test pagination
        """
        if self.cursor is None or self.second_id_short is None:
            abort("Cannot check pagination, there must be at least 2 shells", level=Level.WARNING)
        request = generate_one_valid(self.operation, self.sample_cache, {'cursor': self.cursor, 'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        data = _lookup(data, ['result'])
        _assert(len(data) == 1, 'Exactly one entry')
        data = _lookup(data, [0, 'idShort'])
        _assert(self.second_id_short == data, 'Returns second')


@operation("GetAllAssetAdministrationShells")
class GetAllAasTestSuite(GetAllAasTestSuiteBase):
    def test_filter_by_idshort(self):
        """
        Filter by idShort
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'idShort': self.valid_id_short})
        data = _invoke_and_decode(request, self.conf, True)
        id_short = _lookup(data, ['result', 0, 'idShort'])
        _assert(id_short == self.valid_id_short, 'Result has the requested idShort')


@operation("GetAllAssetAdministrationShells-Reference")
class GetAllAasRefsTestSuite(GetAllAasTestSuiteBase):
    def test_filter_by_idshort(self):
        """
        Filter by idShort
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'idShort': self.valid_id_short})
        _invoke_and_decode(request, self.conf, True)

# /shells/<AAS>


@operation("GetAssetAdministrationShellById")
class GetAasById(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        self.valid_id: str = _lookup(data, ['result', 0, 'id'])

    def test_get(self):
        """
        Fetch AAS by id
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'aasIdentifier': b64urlsafe(self.valid_id)})
        data = _invoke_and_decode(request, self.conf, True)
        data = _lookup(data, ['id'])
        _assert(data == self.valid_id, 'Returned the correct one')


@operation('GetAssetAdministrationShellById-Reference_AasRepository')
class GetAasReferenceById(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        self.valid_id: str = _lookup(data, ['result', 0, 'id'])

    def test_simple(self):
        """
        Fetch AAS reference by id
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'aasIdentifier': b64urlsafe(self.valid_id)})
        data = _invoke_and_decode(request, self.conf, True)
        data = _lookup(data, ['keys', 0, 'value'])
        _assert(data == self.valid_id, 'Returned the correct one')

# /shells/<AAS>/submodels
# /shells/<AAS>/submodel-refs


@operation("GetAllSubmodelReferences_AasRepository")
@operation("GetAllSubmodels_AasRepository")
@operation("GetAllSubmodels_AasRepository Metadata")
@operation("GetAllSubmodels_AasRepository-ValueOnly")
@operation("GetAllSubmodels_AasRepository-Reference")
@operation("GetAllSubmodels_AasRepository-Path")
@operation("GetAssetInformation_AasRepository")
class AasBySuperpathSuite(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        self.valid_id = _lookup(data, ['result', 0, 'id'])
        self.valid_values = {
            'aasIdentifier': [b64urlsafe(self.valid_id)]
        }

    def test_simple(self):
        """
        Fetch by id
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'aasIdentifier': b64urlsafe(self.valid_id)})
        _invoke_and_decode(request, self.conf, True)

# /shells/<AAS>/asset-information


@operation('GetThumbnail_AasRepository')
class AasThumbnailBySuperpathSuite(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        self.valid_id: str = _lookup(data, ['result', 0, 'id'])

    def test_simple(self):
        """
        Fetch thumbnail by id
        """
        request = generate_one_valid(self.operation, self.sample_cache, {
            'aasIdentifier': b64urlsafe(self.valid_id),
        })
        _invoke(request, self.conf, True)

# /shells/<AAS>/submodels/<SM>


class SubmodelBySuperpathSuiteBase(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        self.valid_id: str = _lookup(data, ['result', 0, 'id'])
        self.valid_submodel_id: str = _lookup(data, ['result', 0, 'submodels', 0, 'keys', 0, 'value'])


@operation("GetSubmodelById_AasRepository")
@operation("GetSubmodelById-Metadata_AasRepository")
class SubmodelBySuperpathSuite(SubmodelBySuperpathSuiteBase):
    def test_simple(self):
        """
        Fetch submodel by id
        """
        request = generate_one_valid(self.operation, self.sample_cache, {
            'aasIdentifier': b64urlsafe(self.valid_id),
            'submodelIdentifier': b64urlsafe(self.valid_submodel_id),
        })
        data = _invoke_and_decode(request, self.conf, True)
        data = _lookup(data, ['id'])
        _assert(data == self.valid_submodel_id, 'Returns the correct one')



@operation("GetSubmodelById-ValueOnly_AasRepository")
@operation("GetSubmodelById-Reference_AasRepository")
@operation("GetSubmodelById-Path_AasRepository")
class SubmodelRefBySuperpathSuite(SubmodelBySuperpathSuiteBase):
    def test_simple(self):
        """
        Fetch submodel by id
        """
        request = generate_one_valid(self.operation, self.sample_cache, {
            'aasIdentifier': b64urlsafe(self.valid_id),
            'submodelIdentifier': b64urlsafe(self.valid_submodel_id),
        })
        _invoke_and_decode(request, self.conf, True)

# /shells/<AAS>/submodels/<SM>/submodel-elements

@operation("GetAllSubmodelElements_AasRepository")
@operation("GetAllSubmodelElements-Metadata_AasRepository")
@operation("GetAllSubmodelElements-ValueOnly_AasRepository")
@operation("GetAllSubmodelElements-Reference_AasRepository")
@operation("GetAllSubmodelElements-Path_AasRepository")
class GetAllSubmodelElementsBySuperpathSuite(SubmodelBySuperpathSuiteBase):
    def test_simple(self):
        """
        Fetch all submodel elements
        """
        request = generate_one_valid(self.operation, self.sample_cache, {
            'aasIdentifier': b64urlsafe(self.valid_id),
            'submodelIdentifier': b64urlsafe(self.valid_submodel_id),
        })
        _invoke_and_decode(request, self.conf, True)

# /shells/<AAS>/submodels/<SM>/submodel-elements/<ID>


def _collect_submodel_elements(data: list, paths: Dict[str, List[str]], path_prefix: str):
    for i in data:
        id_short = path_prefix + _lookup(i, ['idShort'])
        model_type = _lookup(i, ['modelType'])
        try:
            paths[model_type].append(id_short)
        except KeyError:
            paths[model_type] = [id_short]
        if model_type == 'SubmodelElementCollection':
            value = _lookup(i, ['value'])
            _collect_submodel_elements(value, paths, id_short + ".")


@operation("GetSubmodelElementByPath_AasRepository")
@operation("GetSubmodelElementByPath-Reference_AasRepository")
class SubmodelElementBySuperpathSuite(ApiTestSuite):
    supported_submodel_elements = [
        'SubmodelElementCollection',
        'SubmodelElementList',
        'Entity',
        'BasicEventElement',
        'Capability',
        'Operation',
        'Property',
        'MultiLanguageProperty',
        'Range',
        'ReferenceElement',
        'RelationshipElement',
        'AnnotatedRelationshipElement',
        'Blob',
        'File',
    ]

    def setup(self):
        self.paths = {}
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        valid_id = _lookup(data, ['result', 0, 'id'])
        valid_submodel_id = _lookup(data, ['result', 0, 'submodels', 0, 'keys', 0, 'value'])
        overwrites = {
            'aasIdentifier': [b64urlsafe(valid_id)],
            'submodelIdentifier': [b64urlsafe(valid_submodel_id)],
        }
        op = self.open_api.operations["GetAllSubmodelElements_AasRepository"]
        request = generate_one_valid(op, self.sample_cache, overwrites)
        data = _invoke_and_decode(request, self.conf, True)
        elements = _lookup(data, ['result'])
        _collect_submodel_elements(elements, self.paths, '')
        overwrites['idShortPath'] = [i[0] for i in self.paths.values()]
        self.valid_values = overwrites

    def check_type(self, model_type: str):
        if model_type not in self.paths:
            abort("No such element present", level=Level.WARNING)
        id_short_path = self.paths[model_type][0]
        valid_values = self.valid_values.copy()
        valid_values['idShortPath'] = [id_short_path]
        graph = generate_all(self.operation, self.sample_cache, valid_values)
        for i in graph.generate_paths():
            request: Request = graph.execute(i.path)
            if i.is_valid:
                has_extend = 'extend' in request.query_parameters
                has_level = 'level' in request.query_parameters
                if (not has_extend and not has_level) or \
                        model_type in ['SubmodelElementCollection', 'SubmodelElementList', 'Entity'] or \
                        model_type in ['Blob'] and not has_level:
                    _invoke(request, self.conf, True)
                else:
                    self.execute_syntactic_test(request)

    def execute_semantic_tests(self):
        # TODO: for unsupported elements, check if 4xx is returned
        for model_type in self.supported_submodel_elements:
            with start(f"Checking {model_type}"):
                self.check_type(model_type)


@operation("GetSubmodelElementByPath-Metadata_AasRepository")
@operation("GetSubmodelElementByPath-ValueOnly_AasRepository")
class SubmodelElementMetadataBySuperpathSuite(SubmodelElementBySuperpathSuite):
    supported_submodel_elements = [
        'SubmodelElementCollection',
        'SubmodelElementList',
        'Entity',
        'BasicEventElement',
        'Property',
        'MultiLanguageProperty',
        'Range',
        'ReferenceElement',
        'RelationshipElement',
        'AnnotatedRelationshipElement',
        'Blob',
        'File',
    ]


@operation("GetSubmodelElementByPath-Path_AasRepository")
class SubmodelElementPathBySuperpathSuite(SubmodelElementBySuperpathSuite):
    supported_submodel_elements = [
        'SubmodelElementCollection',
        'SubmodelElementList',
        'Entity',
    ]


@operation("GetFileByPath_AasRepository")
class GetFileByPathSuperpathSuite(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        valid_id = _lookup(data, ['result', 0, 'id'])
        valid_submodel_id = _lookup(data, ['result', 0, 'submodels', 0, 'keys', 0, 'value'])
        overwrites = {
            'aasIdentifier': [b64urlsafe(valid_id)],
            'submodelIdentifier': [b64urlsafe(valid_submodel_id)],
        }
        op = self.open_api.operations["GetAllSubmodelElements_AasRepository"]
        request = generate_one_valid(op, self.sample_cache, overwrites)
        data = _invoke_and_decode(request, self.conf, True)
        paths = {}
        _collect_submodel_elements(_lookup(data, ['result']), paths, '')
        try:
            overwrites['idShortPath'] = [paths['File']]
        except KeyError:
            abort("No submodel element of type 'File' found, skipping test.")
        self.valid_values = overwrites


# /serialization

@operation("GenerateSerializationByIds")
class GenerateSerializationSuite(ApiTestSuite):
    def setup(self):
        op = self.open_api.operations["GetAllAssetAdministrationShells"]
        request = generate_one_valid(op, self.sample_cache, {'limit': 1})
        data = _invoke_and_decode(request, self.conf, True)
        valid_id = _lookup(data, ['result', 0, 'id'])
        valid_submodel_id = _lookup(data, ['result', 0, 'submodels', 0, 'keys', 0, 'value'])
        self.valid_aas_id = b64urlsafe(valid_id)
        self.valid_submod_id = b64urlsafe(valid_submodel_id)

    def test_filter_by_aasids(self):
        """
        Filter by aas ids
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'aasIds': self.valid_aas_id})
        _invoke_and_decode(request, self.conf, True)

    def test_filter_by_(self):
        """
        Filter by submodel ids
        """
        request = generate_one_valid(self.operation, self.sample_cache, {'submodelIds': self.valid_submod_id})
        _invoke_and_decode(request, self.conf, True)


# /description

@operation("GetDescription")
class GetDescriptionTestSuite(ApiTestSuite):
    def test_contains_suite(self):
        """
        Returned profiles must contain suite
        """
        request = generate_one_valid(self.operation, self.sample_cache)
        data = _invoke_and_decode(request, self.conf, True)
        suites = _lookup(data, ['profiles'])
        _assert(self.suite in suites, f"Contains {self.suite}")


@operation('PostAssetAdministrationShell')
@operation('PutAssetAdministrationShellById')
@operation('DeleteAssetAdministrationShellById')
@operation('PutAssetInformation_AasRepository')
@operation('PutThumbnail_AasRepository')
@operation('DeleteThumbnail_AasRepository')
@operation('PostSubmodelReference_AasRepository')
@operation('DeleteSubmodelReferenceById_AasRepository')
@operation('PutSubmodelById_AasRepository')
@operation('DeleteSubmodelById_AasRepository')
@operation('PatchSubmodel_AasRepository')
@operation('PatchSubmodelById-Metadata_AasRepository')
@operation('PatchSubmodelById-ValueOnly_AasRepository')
@operation("PostSubmodelElement_AasRepository")
@operation('PutSubmodelElementByPath_AasRepository')
@operation('PostSubmodelElementByPath_AasRepository')
@operation('DeleteSubmodelElementByPath_AasRepository')
@operation('PatchSubmodelElementValueByPath_AasRepository')
@operation('PatchSubmodelElementValueByPath-Metadata')
@operation('PatchSubmodelElementValueByPath-ValueOnly')
@operation('PutFileByPath_AasRepository')
@operation('DeleteFileByPath_AasRepository')
@operation('InvokeOperation_AasRepository')
@operation('InvokeOperation-ValueOnly_AasRepository')
@operation('InvokeOperationAsync_AasRepository')
@operation('InvokeOperationAsync-ValueOnly_AasRepository')
@operation('GetOperationAsyncStatus_AasRepository')
@operation('GetOperationAsyncResult_AasRepository')
@operation('GetOperationAsyncResult-ValueOnly_AasRepository')
# /aas
@operation('GetAssetAdministrationShell')
@operation('PutAssetAdministrationShell')
@operation('GetAssetAdministrationShell-Reference')
@operation('GetAssetInformation')
@operation('PutAssetInformation')
@operation('GetThumbnail')
@operation('PutThumbnail')
@operation('DeleteThumbnail')
# /aas/submodel-refs
@operation('GetAllSubmodelReferences')
@operation('GetAllSubmodelReferences')
@operation('PostSubmodelReference')
@operation('DeleteSubmodelReferenceById')
# /aas/submodels/<SM>
@operation('GetSubmodel_AAS')
@operation('PutSubmodel_AAS')
@operation('DeleteSubmodelById_AAS')
@operation('PatchSubmodel_AAS')
@operation('GetSubmodel-Metadata_AAS')
@operation('PatchSubmodelMetadata_AAS')
@operation('GetSubmodel-ValueOnly_AAS')
@operation('PatchSubmodel-ValueOnly_AAS')
@operation('GetSubmodelMetadata-Reference_AAS')
@operation('GetSubmodel-Path_AAS')
# /aas/submodels/<SM>/submodel-elements
@operation('GetAllSubmodelElements_AAS')
@operation('PostSubmodelElement_AAS')
@operation('GetAllSubmodelElements-Metadata_AAS')
@operation('GetAllSubmodelElements-ValueOnly_AAS')
@operation('GetAllSubmodelElementsReference_AAS')
@operation('GetAllSubmodelElementsPath_AAS')
@operation('GetSubmodelElementByPath_AAS')
@operation('PutSubmodelElementByPath_AAS')
@operation('PostSubmodelElementByPath_AAS')
@operation('DeleteSubmodelElementByPath_AAS')
@operation('PatchSubmodelElementValueByPath_AAS')
@operation('GetSubmodelElementByPath-Metadata_AAS')
@operation('PatchSubmodelElementValueByPath-Metadata_AAS')
@operation('GetSubmodelElementByPath-ValueOnly_AAS')
@operation('PatchSubmodelElementValueByPathValueOnly_AAS')
@operation('GetSubmodelElementByPath-Reference_AAS')
@operation('GetSubmodelElementByPath-Path_AAS')
@operation('GetFileByPath_AAS')
@operation('PutFileByPath_AAS')
@operation('DeleteFileByPath_AAS')
@operation('InvokeOperationSync_AAS')
@operation('InvokeOperationSync-ValueOnly_AAS')
@operation('InvokeOperationAsync_AAS')
@operation('InvokeOperationAsync-ValueOnly_AAS')
@operation('GetOperationAsyncStatus_AAS')
@operation('GetOperationAsyncResult_AAS')
@operation('GetOperationAsyncResult-ValueOnly_AAS')
# /submodel
@operation('GetSubmodel')
@operation('PutSubmodel')
@operation('PatchSubmodel')
@operation('GetSubmodel-Metadata')
@operation('PatchSubmodel-Metadata')
@operation('GetSubmodel-ValueOnly')
@operation('PatchSubmodel-ValueOnly')
@operation('GetSubmodel-Reference')
@operation('GetSubmodel-Path')
# /submodel/submodel-elements
@operation('GetAllSubmodelElements')
@operation('PostSubmodelElement')
@operation('GetAllSubmodelElements-Metadata')
@operation('GetAllSubmodelElements-ValueOnly')
@operation('GetAllSubmodelElements-Reference')
@operation('GetAllSubmodelElements-Path')
@operation('GetSubmodelElementByPath')
@operation('PutSubmodelElementByPath')
@operation('PostSubmodelElementByPath')
@operation('DeleteSubmodelElementByPath')
@operation('PatchSubmodelElementByPath')
@operation('GetSubmodelElementByPath-Metadata')
@operation('PatchSubmodelElementByPath-Metadata')
@operation('GetSubmodelElementByPath-ValueOnly')
@operation('PatchSubmodelElementByPath-ValueOnly')
@operation('GetSubmodelElementByPath-Reference')
@operation('GetSubmodelElementByPath-Path')
@operation('GetFileByPath')
@operation('PutFileByPath')
@operation('DeleteFileByPath')
@operation('InvokeOperation')
@operation('InvokeOperationAsync')
@operation('InvokeOperationSync-ValueOnly')
@operation('InvokeOperationAsync-ValueOnly')
@operation('GetOperationAsyncStatus')
@operation('GetOperationAsyncResult')
@operation('GetOperationAsyncResult-ValueOnly')
# /submodels
@operation('GetAllSubmodels')
@operation('PostSubmodel')
@operation('GetAllSubmodels-Metadata')
@operation('GetAllSubmodels-ValueOnly')
@operation('GetAllSubmodels-Reference')
@operation('GetAllSubmodels-Path')
# /submodels/<SM>
@operation('GetSubmodelById')
@operation('PutSubmodelById')
@operation('DeleteSubmodelById')
@operation('PatchSubmodelById')
@operation('GetSubmodelById-Metadata')
@operation('PatchSubmodelById-Metadata')
@operation('GetSubmodelById-ValueOnly')
@operation('PatchSubmodelById-ValueOnly')
@operation('GetSubmodelById-Reference')
@operation('GetSubmodelById-Path')
# /submodels/<SM>/submodel-elements
@operation('GetAllSubmodelElements_SubmodelRepository')
@operation('PostSubmodelElement_SubmodelRepository')
@operation('GetAllSubmodelElements-Metadata_SubmodelRepository')
@operation('GetAllSubmodelElements-ValueOnly_SubmodelRepo')
@operation('GetAllSubmodelElements-Reference_SubmodelRepo')
@operation('GetAllSubmodelElements-Path_SubmodelRepo')
@operation('GetSubmodelElementByPath_SubmodelRepo')
@operation('PutSubmodelElementByPath_SubmodelRepo')
@operation('PostSubmodelElementByPath_SubmodelRepo')
@operation('DeleteSubmodelElementByPath_SubmodelRepo')
@operation('PatchSubmodelElementByPath_SubmodelRepo')
@operation('GetSubmodelElementByPath-Metadata_SubmodelRepo')
@operation('PatchSubmodelElementByPath-Metadata_SubmodelRepo')
@operation('GetSubmodelElementByPath-ValueOnly_SubmodelRepo')
@operation('PatchSubmodelElementByPath-ValueOnly_SubmodelRepo')
@operation('GetSubmodelElementByPath-Reference_SubmodelRepo')
@operation('GetSubmodelElementByPath-Path_SubmodelRepo')
@operation('GetFileByPath_SubmodelRepo')
@operation('PutFileByPath_SubmodelRepo')
@operation('DeleteFileByPath_SubmodelRepo')
@operation('InvokeOperation_SubmodelRepo')
@operation('InvokeOperation-ValueOnly_SubmodelRepo')
@operation('InvokeOperationAsync_SubmodelRepo')
@operation('InvokeOperationAsync-ValueOnly_SubmodelRepo')
@operation('GetOperationAsyncStatus_SubmodelRepo')
@operation('GetOperationAsyncResult_SubmodelRepo')
@operation('GetOperationAsyncResult-ValueOnly_SubmodelRepo')
@operation('GetAllConceptDescriptions')
@operation('PostConceptDescription')
@operation('GetConceptDescriptionById')
@operation('PutConceptDescriptionById')
@operation('DeleteConceptDescriptionById')
# /shell-descriptors
@operation('GetAllAssetAdministrationShellDescriptors')
@operation('PostAssetAdministrationShellDescriptor')
@operation('GetAssetAdministrationShellDescriptorById')
@operation('PutAssetAdministrationShellDescriptorById')
@operation('DeleteAssetAdministrationShellDescriptorById')
# /shell-descriptors/<AAS>/submodel-descriptors
@operation('GetAllSubmodelDescriptorsThroughSuperpath')
@operation('PostSubmodelDescriptor-ThroughSuperpath')
@operation('GetSubmodelDescriptorByIdThroughSuperpath')
@operation('PutSubmodelDescriptorByIdThroughSuperpath')
@operation('DeleteSubmodelDescriptorByIdThroughSuperpath')
# /submodel-descriptors
@operation('GetAllSubmodelDescriptors')
@operation('PostSubmodelDescriptor')
@operation('GetSubmodelDescriptorById')
@operation('PutSubmodelDescriptorById')
@operation('DeleteSubmodelDescriptorById')
# /lookup/shells
@operation('GetAllAssetAdministrationShellIdsByAssetLink')
@operation('GetAllAssetLinksById')
@operation('PostAllAssetLinksById')
@operation('DeleteAllAssetLinksById')
# /packages
@operation('GetAllAASXPackageIds')
@operation('PostAASXPackage')
@operation('GetAASXByPackageId')
@operation('PutAASXByPackageId')
@operation('DeleteAASXByPackageId')
class SimpleSemanticTestSuite(ApiTestSuite):
    def test_semantic(self):
        """
        Perform a simple semantic test
        """
        request = generate_one_valid(self.operation, self.sample_cache)
        _invoke_and_decode(request, self.conf, True)


# Used by unit test
def check_in_sync():
    for version, suites in supported_versions().items():
        spec = _get_spec(version)
        for suite in suites:
            operations = _available_suites[suite]
            for op in operations:
                if op not in spec.open_api.operations:
                    raise AasTestToolsException(f"Unknown operation {op}")


def execute_tests(conf: ExecConf, suite: str, version: str = _DEFAULT_VERSION) -> Tuple[AasTestResult, ConfusionMatrix]:
    spec = _get_spec(version)
    try:
        operation_ids = _available_suites[suite]
    except KeyError:
        all_suites = "\n".join(sorted(_available_suites.keys()))
        raise AasTestToolsException(f"Unknown suite {suite}, must be one of:\n{all_suites}")

    sample_cache = SampleCache()
    mat = ConfusionMatrix()

    with start(f"Checking compliance to {suite}") as result_root:

        # Initial connection check
        if not _check_server(conf):
            return result_root, mat

        for operation in spec.open_api.operations.values():
            if operation.path.startswith(conf.remove_path_prefix):
                # TODO: this will be permanent so that you cannot call this function again
                operation.path = operation.path[len(conf.remove_path_prefix):]

        # Check individual operations
        for operation in spec.open_api.operations.values():
            if operation.operation_id not in operation_ids:
                continue
            with start(f"Checking {operation.method.upper()} {operation.path} ({operation.operation_id})"):
                if conf.dry:
                    continue

                ctr = _test_suites[operation.operation_id]
                test_suite: ApiTestSuite = ctr(operation, conf, sample_cache, spec.open_api, suite)

                with start("Setup") as result_setup:
                    test_suite.setup()

                if result_setup.ok():
                    sub_mat = test_suite.execute()
                    mat += sub_mat
        with start("Summary:"):
            write(f"Negative tests passed: {mat.invalid_rejected} / {mat.invalid_accepted + mat.invalid_rejected}")
            write(f"Positive tests passed: {mat.valid_accepted} / {mat.valid_accepted + mat.valid_rejected}")
    return result_root, mat


def supported_versions() -> Dict[str, List[str]]:
    return {ver: _available_suites.keys() for ver, spec in _specs.items()}


def latest_version():
    return _DEFAULT_VERSION
