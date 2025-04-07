from typing import Tuple, Optional, Dict, List
from dataclasses import dataclass
from fences.core.util import ConfusionMatrix
from aas_test_engines.exception import AasTestToolsException
from aas_test_engines.reflect import reflect_function
from aas_test_engines.result import write, start, abort, Level, AasTestResult
from aas_test_engines.http import HttpClient, Request
from aas_test_engines.config import CheckApiConfig
import requests
from .interfaces import (
    aas,
    aas_repo,
    submodel_repo,
    submodel,
    description,
    serialization,
)
from .interfaces.shared import ApiTestSuite, Base64String
from .generate import generate_calls


SSP_PREFIX = "https://admin-shell.io/aas/API/3/0/"


def no_prefix(client: HttpClient):
    return ""


def aas_prefix(client: HttpClient):
    return "/aas"


def aas_submodel_prefix(client: HttpClient):
    shell = aas.get_shell(client)
    submodel_id = Base64String(shell.submodels[0].keys[0].value.raw_value)
    return f"/aas/submodels/{submodel_id}"


def aas_repo_prefix(client: HttpClient):
    result = aas_repo.get_all_shells(client, limit=1)
    id = Base64String(result.result[0].id.raw_value)
    return f"/shells/{id}"


def aas_repo_submodel_prefix(client: HttpClient):
    result = aas_repo.get_all_shells(client, limit=1)
    id = Base64String(result.result[0].id.raw_value)
    sid = Base64String(result.result[0].submodels[0].keys[0].value.raw_value)
    return f"/shells/{id}/submodels/{sid}"


def submodel_repo_submodel_prefix(client: HttpClient):
    result = submodel_repo.get_all_submodels(client, limit=1)
    submodel_id = Base64String(result.result[0].id.raw_value)
    return f"/submodels/{submodel_id}"


def submodel_prefix(client: HttpClient):
    return "/submodel"


available_suites: Dict[str, List[Tuple[callable, ApiTestSuite]]] = {
    f"{SSP_PREFIX}AssetAdministrationShellRepositoryServiceSpecification/SSP-002": [
        (no_prefix, aas_repo.GetAllAasTestSuite),
        (no_prefix, aas_repo.GetAllAasRefsTestSuite),
        (no_prefix, aas_repo.GetAasByIdTestSuite),
        (no_prefix, aas_repo.GetAasByIdReferenceTestSuite),
        (aas_repo_prefix, aas.GetAssetInformationTestSuite),
        (aas_repo_prefix, aas.GetThumbnailTestSuite),
        (aas_repo_prefix, aas.GetAllSubmodelReferencesTestSuite),
        (aas_repo_prefix, submodel_repo.GetSubmodelByIdTestSuite_AAS),
        (aas_repo_prefix, submodel_repo.GetSubmodelByIdMetaTestSuite_AAS),
        (aas_repo_prefix, submodel_repo.GetSubmodelByIdValueTestSuite_AAS),
        (aas_repo_prefix, submodel_repo.GetSubmodelByIdReferenceTestSuite_AAS),
        (aas_repo_prefix, submodel_repo.GetSubmodelByIdPathTestSuite_AAS),
        (aas_repo_submodel_prefix, submodel.GetAllSubmodelElementsTestSuite),
        (aas_repo_submodel_prefix, submodel.GetAllSubmodelElementsMetaTestSuite),
        (aas_repo_submodel_prefix, submodel.GetAllSubmodelElementsValueOnlyTestSuite),
        (aas_repo_submodel_prefix, submodel.GetAllSubmodelElementsReferenceTestSuite),
        (aas_repo_submodel_prefix, submodel.GetAllSubmodelElementsPathTestSuite),
        (aas_repo_submodel_prefix, submodel.GetSubmodelElementTestSuite),
        (aas_repo_submodel_prefix, submodel.GetSubmodelElementMetaTestSuite),
        (aas_repo_submodel_prefix, submodel.GetSubmodelElementValueTestSuite),
        (aas_repo_submodel_prefix, submodel.GetSubmodelElementReferenceTestSuite),
        (aas_repo_submodel_prefix, submodel.GetSubmodelElementPathTestSuite),
        (aas_repo_submodel_prefix, submodel.GetFileByPathTestSuite),
        (no_prefix, serialization.GenerateSerializationSuite),
        (no_prefix, description.GetDescriptionTestSuite),
    ],
    f"{SSP_PREFIX}SubmodelRepositoryServiceSpecification/SSP-002": [
        (no_prefix, submodel_repo.GetAllSubmodelsTestSuite),
        (no_prefix, submodel_repo.GetAllSubmodelsMetadataTestSuite),
        (no_prefix, submodel_repo.GetAllSubmodelsValueTestSuite),
        (no_prefix, submodel_repo.GetAllSubmodelsReferenceTestSuite),
        (no_prefix, submodel_repo.GetAllSubmodelsPathTestSuite),
        (no_prefix, submodel_repo.GetSubmodelByIdTestSuite_Submodel),
        (no_prefix, submodel_repo.GetSubmodelByIdMetaTestSuite_Submodel),
        (no_prefix, submodel_repo.GetSubmodelByIdValueTestSuite_Submodel),
        (no_prefix, submodel_repo.GetSubmodelByIdReferenceTestSuite_Submodel),
        (no_prefix, submodel_repo.GetSubmodelByIdPathTestSuite_Submodel),
        (submodel_repo_submodel_prefix, submodel.GetAllSubmodelElementsTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetAllSubmodelElementsMetaTestSuite),
        (
            submodel_repo_submodel_prefix,
            submodel.GetAllSubmodelElementsValueOnlyTestSuite,
        ),
        (
            submodel_repo_submodel_prefix,
            submodel.GetAllSubmodelElementsReferenceTestSuite,
        ),
        (submodel_repo_submodel_prefix, submodel.GetAllSubmodelElementsPathTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetSubmodelElementTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetSubmodelElementMetaTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetSubmodelElementValueTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetSubmodelElementReferenceTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetSubmodelElementPathTestSuite),
        (submodel_repo_submodel_prefix, submodel.GetFileByPathTestSuite),
        (no_prefix, serialization.GenerateSerializationSuite),
        (no_prefix, description.GetDescriptionTestSuite),
    ],
    f"{SSP_PREFIX}AssetAdministrationShellServiceSpecification/SSP-002": [
        (aas_prefix, aas.GetShellTestSuite),
        (aas_prefix, aas.GetShellReferenceTestSuite),
        (aas_prefix, aas.GetAssetInformationTestSuite),
        (aas_prefix, aas.GetThumbnailTestSuite),
        (aas_prefix, aas.GetAllSubmodelReferencesTestSuite),
        (aas_prefix, submodel_repo.GetSubmodelByIdTestSuite_AAS),
        (aas_prefix, submodel_repo.GetSubmodelByIdMetaTestSuite_AAS),
        (aas_prefix, submodel_repo.GetSubmodelByIdValueTestSuite_AAS),
        (aas_prefix, submodel_repo.GetSubmodelByIdReferenceTestSuite_AAS),
        (aas_prefix, submodel_repo.GetSubmodelByIdPathTestSuite_AAS),
        (aas_submodel_prefix, submodel.GetAllSubmodelElementsTestSuite),
        (aas_submodel_prefix, submodel.GetAllSubmodelElementsMetaTestSuite),
        (aas_submodel_prefix, submodel.GetAllSubmodelElementsValueOnlyTestSuite),
        (aas_submodel_prefix, submodel.GetAllSubmodelElementsReferenceTestSuite),
        (aas_submodel_prefix, submodel.GetAllSubmodelElementsPathTestSuite),
        (aas_submodel_prefix, submodel.GetSubmodelElementTestSuite),
        (aas_submodel_prefix, submodel.GetSubmodelElementMetaTestSuite),
        (aas_submodel_prefix, submodel.GetSubmodelElementValueTestSuite),
        (aas_submodel_prefix, submodel.GetSubmodelElementReferenceTestSuite),
        (aas_submodel_prefix, submodel.GetSubmodelElementPathTestSuite),
        (aas_submodel_prefix, submodel.GetFileByPathTestSuite),
        (aas_prefix, serialization.GenerateSerializationSuite),
        (aas_prefix, description.GetDescriptionTestSuite),
    ],
    f"{SSP_PREFIX}SubmodelServiceSpecification/SSP-002": [
        (submodel_prefix, submodel.GetSubmodelTestSuite),
        (submodel_prefix, submodel.GetSubmodelMetaTestSuite),
        (submodel_prefix, submodel.GetSubmodelValueTestSuite),
        (submodel_prefix, submodel.GetSubmodelReferenceTestSuite),
        (submodel_prefix, submodel.GetSubmodelPathTestSuite),
        (submodel_prefix, submodel.GetAllSubmodelElementsTestSuite),
        (submodel_prefix, submodel.GetAllSubmodelElementsMetaTestSuite),
        (
            submodel_prefix,
            submodel.GetAllSubmodelElementsValueOnlyTestSuite,
        ),
        (
            submodel_prefix,
            submodel.GetAllSubmodelElementsReferenceTestSuite,
        ),
        (submodel_prefix, submodel.GetAllSubmodelElementsPathTestSuite),
        (submodel_prefix, submodel.GetSubmodelElementTestSuite),
        (submodel_prefix, submodel.GetSubmodelElementMetaTestSuite),
        (submodel_prefix, submodel.GetSubmodelElementValueTestSuite),
        (submodel_prefix, submodel.GetSubmodelElementReferenceTestSuite),
        (submodel_prefix, submodel.GetSubmodelElementPathTestSuite),
        (submodel_prefix, submodel.GetFileByPathTestSuite),
        (submodel_prefix, serialization.GenerateSerializationSuite),
        (submodel_prefix, description.GetDescriptionTestSuite),
    ],
}


def _check_server(dry: bool, client: HttpClient) -> bool:
    with start(f"Trying to reach {client.host}"):
        if dry:
            write(AasTestResult("Skipped due to dry run", Level.WARNING))
            return True
        try:
            client.send(Request(path=""))
            write("OK")
            return True
        except requests.exceptions.RequestException as e:
            write(AasTestResult("Failed to reach: {}".format(e), level=Level.CRITICAL))
            return False


def _execute_syntactic_tests(suite: ApiTestSuite):
    # make this ForwardReference resolvable
    from .model import Reference

    func_type = reflect_function(suite.invoke_error, globals(), locals())
    func_type2 = reflect_function(suite.invoke_success, globals(), locals())
    assert func_type == func_type2, suite
    generate_calls(func_type, suite.operation, suite.valid_arguments)


def _execute_semantic_tests(suite: ApiTestSuite):
    fns = [getattr(suite, i) for i in dir(suite) if i.startswith("test_")]
    fns.sort(key=lambda x: x.__code__.co_firstlineno)
    for test_fn in fns:
        with start(test_fn.__doc__ or test_fn.__name__):
            test_fn()


def _execute(suite: ApiTestSuite) -> ConfusionMatrix:
    mat = ConfusionMatrix()
    with start("Negative Tests") as result:
        _execute_syntactic_tests(suite)
    mat.invalid_rejected = len([i for i in result.sub_results if i.ok()])
    mat.invalid_accepted = len(result.sub_results) - mat.invalid_rejected
    with start("Positive Tests") as result:
        _execute_semantic_tests(suite)
    mat.valid_accepted = len([i for i in result.sub_results if i.ok()])
    mat.valid_rejected = len(result.sub_results) - mat.valid_accepted
    return mat


def execute_tests(client: HttpClient, conf: CheckApiConfig) -> Tuple[AasTestResult, ConfusionMatrix]:
    try:
        test_suites = available_suites[conf.suite]
    except KeyError:
        all_suites = "\n".join(sorted(available_suites.keys()))
        raise AasTestToolsException(f"Unknown suite {conf.suite}, must be one of:\n{all_suites}")

    mat = ConfusionMatrix()

    with start(f"Checking compliance to {conf.suite}") as result_root:

        # Initial connection check
        if not _check_server(conf.dry, client):
            return result_root, mat

        # Check individual operations
        for prefix_provider, test_suite_class in test_suites:
            with start(
                # f"Checking {operation.method.upper()} {operation.path} ({operation.operation_id})",
                f"Checking {test_suite_class.operation}",
                False,
            ):
                if conf.dry:
                    continue

                with start("Setup") as result_setup:
                    prefix = prefix_provider(client)
                    sub_client = client.descend(prefix)
                    test_suite: ApiTestSuite = test_suite_class(sub_client, conf.suite)
                    test_suite.setup()

                if result_setup.ok():
                    sub_mat = _execute(test_suite)
                    mat += sub_mat

        with start("Summary:"):
            write(f"Negative tests passed: {mat.invalid_rejected} / {mat.invalid_accepted + mat.invalid_rejected}")
            write(f"Positive tests passed: {mat.valid_accepted} / {mat.valid_accepted + mat.valid_rejected}")
    return result_root, mat
