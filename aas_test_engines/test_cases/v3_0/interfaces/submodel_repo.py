from typing import List, Union, Optional
from dataclasses import dataclass, field
from aas_test_engines.reflect import reflect
from aas_test_engines.http import HttpClient, Request
from .shared import (
    ErrorResult,
    invoke_and_decode,
    invoke,
    extract_json,
    r_error_result,
    Base64String,
    PagedResult,
    ApiTestSuite,
    _assert,
    PaginationTests,
    Level,
    Extent,
    unpack_enum,
)
from aas_test_engines.test_cases.v3_0.model import Submodel, Reference
from .aas import get_all_submodel_references


@dataclass
class GetAllSubmodelReferencesResponse(PagedResult):
    result: List[Reference]


GetSubmodelPathsResponse = List[str]

r_submodel, _ = reflect(Submodel, globals(), locals())
r_submodel_references, _ = reflect(GetAllSubmodelReferencesResponse, globals(), locals())

r_submodel, _ = reflect(Submodel, globals(), locals())
r_reference, _ = reflect(Reference, globals(), locals())
r_get_submodel_paths, _ = reflect(GetSubmodelPathsResponse)


@dataclass
class GetAllSubmodelsResponse(PagedResult):
    result: List[Submodel] = field(metadata={"allow_empty": True})


r_get_all_submodels, _ = reflect(GetAllSubmodelsResponse, globals(), locals())


@dataclass
class GetAllSubmodelsValueResponse(PagedResult):
    result: List[any] = field(metadata={"allow_empty": True})


r_get_all_submodels_value, _ = reflect(GetAllSubmodelsValueResponse, globals(), locals())


@dataclass
class GetAllSubmodelsPathResponse(PagedResult):
    result: List[str] = field(metadata={"allow_empty": True})


r_get_all_submodels_path, _ = reflect(GetAllSubmodelsPathResponse, globals(), locals())


def get_all_submodels(
    client: HttpClient, limit: Optional[int] = None, cursor: Optional[str] = None
) -> GetAllSubmodelsResponse:
    request = Request(
        path=f"/submodels",
        query_parameters={
            "limit": limit,
            "cursor": cursor,
        },
    )
    return invoke_and_decode(client, request, r_get_all_submodels, {200})


class GetAllSubmodelsTestSuite(PaginationTests, ApiTestSuite):
    operation = "GetAllSubmodels"

    def setup(self):
        result = get_all_submodels(self.client, limit=1)
        self.cursor = result.paging_metadata.cursor

    def invoke_success(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> GetAllSubmodelsResponse:
        return get_all_submodels(self.client, limit, cursor)

    def invoke_error(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> ErrorResult:
        request = Request(
            path=f"/submodels",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_no_params(self):
        """
        Invoke without parameters
        """
        self.invoke_success()


class GetAllSubmodelsMetadataTestSuite(PaginationTests, ApiTestSuite):
    operation = "GetAllSubmodels-Metadata"

    def setup(self):
        result = get_all_submodels(self.client, limit=1)
        self.cursor = result.paging_metadata.cursor

    def _invoke(self, limit, cursor, reflection, status):
        request = Request(
            path=f"/submodels/$metadata",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> GetAllSubmodelsResponse:
        return self._invoke(limit, cursor, r_get_all_submodels, {200})

    def invoke_error(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> ErrorResult:
        return self._invoke(limit, cursor, r_error_result, range(400, 500))

    def test_no_params(self):
        """
        Invoke without parameters
        """
        self.invoke_success()


class GetAllSubmodelsValueTestSuite(PaginationTests, ApiTestSuite):
    operation = "GetAllSubmodels-ValueOnly"

    def setup(self):
        result = get_all_submodels(self.client, limit=1)
        self.cursor = result.paging_metadata.cursor

    def _invoke(self, limit, cursor, reflection, status):
        request = Request(
            path=f"/submodels/$value",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> GetAllSubmodelsValueResponse:
        return self._invoke(limit, cursor, r_get_all_submodels_value, {200})

    def invoke_error(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> ErrorResult:
        return self._invoke(limit, cursor, r_error_result, range(400, 500))

    def test_no_params(self):
        """
        Invoke without parameters
        """
        self.invoke_success()


class GetAllSubmodelsReferenceTestSuite(PaginationTests, ApiTestSuite):
    operation = "GetAllSubmodels-Reference"

    def setup(self):
        result = get_all_submodels(self.client, limit=1)
        self.cursor = result.paging_metadata.cursor

    def _invoke(self, limit, cursor, reflection, status):
        request = Request(
            path=f"/submodels/$reference",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> GetAllSubmodelReferencesResponse:
        return self._invoke(limit, cursor, r_submodel_references, {200})

    def invoke_error(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> ErrorResult:
        return self._invoke(limit, cursor, r_error_result, range(400, 500))

    def test_no_params(self):
        """
        Invoke without parameters
        """
        self.invoke_success()


class GetAllSubmodelsPathTestSuite(PaginationTests, ApiTestSuite):
    operation = "GetAllSubmodels-Path"

    def setup(self):
        result = get_all_submodels(self.client, limit=1)
        self.cursor = result.paging_metadata.cursor

    def _invoke(self, limit, cursor, reflection, status):
        request = Request(
            path=f"/submodels/$path",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> GetAllSubmodelsResponse:
        return self._invoke(limit, cursor, r_get_all_submodels_path, {200})

    def invoke_error(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> ErrorResult:
        return self._invoke(limit, cursor, r_error_result, range(400, 500))

    def test_no_params(self):
        """
        Invoke without parameters
        """
        self.invoke_success()


# For test execution of the GetSubmodelById operations we need a valid submodel id
# To fetch it, we have to options
# - For a single submodel or a submodel repo, we can query the list of submodels directly
#   using /submodels
# - For a single AAS service or an AAS repo, we can either query the whole shell or
#   or a list of submodel references /submodel-refs. We use the latter for efficiency


class SetupForAas(ApiTestSuite):
    def setup(self):
        result = get_all_submodel_references(self.client, limit=1)
        self.valid_id = result.result[0].keys[0].value.raw_value
        self.valid_arguments["submodel_id"] = Base64String(self.valid_id)


class SetupForSubmodel(ApiTestSuite):
    def setup(self):
        result = get_all_submodels(self.client, limit=1)
        self.valid_id = result.result[0].id.raw_value
        self.valid_arguments["submodel_id"] = Base64String(self.valid_id)


class GetSubmodelByIdTests(ApiTestSuite):
    operation = "GetSubmodelById"

    def _invoke(self, submodel_id, level, extent, reflection, status):
        request = Request(
            path=f"/submodels/{submodel_id}",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self, submodel_id: Base64String, level: Optional[Level] = None, extent: Optional[Extent] = None
    ) -> Submodel:
        return self._invoke(submodel_id, level, extent, r_submodel, {200})

    def invoke_error(
        self, submodel_id: Base64String, level: Optional[Level] = None, extent: Optional[Extent] = None
    ) -> ErrorResult:
        return self._invoke(submodel_id, level, extent, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch submodel by id
        """
        result = self.invoke_success(Base64String(self.valid_id))
        _assert(result.id.raw_value == self.valid_id, "Returns the right one")


class GetSubmodelByIdTestSuite_AAS(GetSubmodelByIdTests, SetupForAas):
    pass


class GetSubmodelByIdTestSuite_Submodel(GetSubmodelByIdTests, SetupForSubmodel):
    pass


class GetSubmodelByIdMetaTests(ApiTestSuite):
    operation = "GetSubmodelById-Metadata"

    def _invoke(self, submodel_id, reflection, status):
        request = Request(path=f"/submodels/{submodel_id}/$metadata")
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, submodel_id: Base64String) -> Submodel:
        return self._invoke(submodel_id, r_submodel, {200})

    def invoke_error(self, submodel_id: Base64String) -> ErrorResult:
        return self._invoke(submodel_id, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch submodel by id
        """
        result = self.invoke_success(Base64String(self.valid_id))
        _assert(result.id.raw_value == self.valid_id, "Returns the right one")


class GetSubmodelByIdMetaTestSuite_AAS(GetSubmodelByIdMetaTests, SetupForAas):
    pass


class GetSubmodelByIdMetaTestSuite_Submodel(GetSubmodelByIdMetaTests, SetupForSubmodel):
    pass


class GetSubmodelByIdValueTests(ApiTestSuite):
    operation = "GetSubmodelById-ValueOnly"

    def invoke_success(
        self, submodel_id: Base64String, level: Optional[Level] = None, extent: Optional[Extent] = None
    ) -> any:
        request = Request(
            path=f"/submodels/{submodel_id}/$value",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
            },
        )
        response = invoke(self.client, request)
        return extract_json(response)

    def invoke_error(
        self, submodel_id: Base64String, level: Optional[Level] = None, extent: Optional[Extent] = None
    ) -> ErrorResult:
        request = Request(
            path=f"/submodels/{submodel_id}/$value",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
            },
        )
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch submodel by id
        """
        self.invoke_success(Base64String(self.valid_id))
        # TODO: check value only serialization


class GetSubmodelByIdReferenceTestSuite_AAS(GetSubmodelByIdValueTests, SetupForAas):
    pass


class GetSubmodelByIdReferenceTestSuite_Submodel(GetSubmodelByIdValueTests, SetupForSubmodel):
    pass


class GetSubmodelByIdReferenceTests(ApiTestSuite):
    operation = "GetSubmodelById-Reference"

    def _invoke(self, submodel_id, reflection, status):
        request = Request(path=f"/submodels/{submodel_id}/$reference")
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, submodel_id: Base64String) -> Reference:
        return self._invoke(submodel_id, r_reference, {200})

    def invoke_error(self, submodel_id: Base64String) -> ErrorResult:
        return self._invoke(submodel_id, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch submodel by id
        """
        result = self.invoke_success(Base64String(self.valid_id))
        _assert(result.keys[0].value.raw_value == self.valid_id, "Returns the right one")


class GetSubmodelByIdValueTestSuite_AAS(GetSubmodelByIdReferenceTests, SetupForAas):
    pass


class GetSubmodelByIdValueTestSuite_Submodel(GetSubmodelByIdReferenceTests, SetupForSubmodel):
    pass


class GetSubmodelByIdPathTests(ApiTestSuite):
    operation = "GetSubmodelById-Path"

    def _invoke(self, submodel_id, level, reflection, status):
        request = Request(path=f"/submodels/{submodel_id}/$path", query_parameters={"level": unpack_enum(level)})
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, submodel_id: Base64String, level: Optional[Level] = None) -> GetSubmodelPathsResponse:
        return self._invoke(submodel_id, level, r_get_submodel_paths, {200})

    def invoke_error(self, submodel_id: Base64String, level: Optional[Level] = None) -> ErrorResult:
        return self._invoke(submodel_id, level, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch submodel by id
        """
        self.invoke_success(Base64String(self.valid_id))


class GetSubmodelByIdPathTestSuite_AAS(GetSubmodelByIdPathTests, SetupForAas):
    pass


class GetSubmodelByIdPathTestSuite_Submodel(GetSubmodelByIdPathTests, SetupForSubmodel):
    pass
