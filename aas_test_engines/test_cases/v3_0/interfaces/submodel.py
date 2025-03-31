from typing import List, Union, Optional, Dict
from dataclasses import dataclass, field
from collections import defaultdict
from aas_test_engines.reflect import reflect
from aas_test_engines.result import Level as ResultLevel
from aas_test_engines.result import abort, AasTestResult, start
from aas_test_engines.http import HttpClient, Request
from .shared import (
    ErrorResult,
    invoke_and_decode,
    r_error_result,
    ApiTestSuite,
    Level,
    Extent,
    PaginationTests,
    PagedResult,
    unpack_enum,
    invoke,
    extract_json,
)
from aas_test_engines.test_cases.v3_0.model import (
    Submodel,
    SubmodelElement,
    ReferenceType,
    Key,
    SubmodelElementCollection,
    SubmodelElementList,
    SubmodelElementCollection,
    SubmodelElementList,
    Entity,
    BasicEventElement,
    Capability,
    Operation,
    Property,
    MultiLanguageProperty,
    Range,
    ReferenceElement,
    RelationshipElement,
    AnnotatedRelationshipElement,
    Blob,
    File,
)

# We omit the prefix '/submodel' for all paths here and add it in the client instead

r_submodel, _ = reflect(Submodel, globals(), locals())


@dataclass
class GetAllSubmodelElementsResponse(PagedResult):
    result: List[SubmodelElement] = field(metadata={"allow_empty": True})


r_get_all_submodel_elements, _ = reflect(GetAllSubmodelElementsResponse, globals(), locals())


@dataclass
class GetAllSubmodelElementsValueOnlyResponse(PagedResult):
    result: List[any] = field(metadata={"allow_empty": True})


r_get_all_submodel_elements_value_only, _ = reflect(GetAllSubmodelElementsValueOnlyResponse, globals(), locals())


@dataclass
class UnconstrainedReference:
    """
    Copy of the Reference class but constraints have been omitted
    """

    type: ReferenceType
    referred_semantic_id: Optional["UnconstrainedReference"]
    keys: List[Key]


r_reference, _ = reflect(UnconstrainedReference, globals(), locals())


@dataclass
class GetAllSubmodelElementsReferenceResponse(PagedResult):
    result: List[UnconstrainedReference] = field(metadata={"allow_empty": True})


r_get_all_submodel_elements_reference, _ = reflect(GetAllSubmodelElementsReferenceResponse, globals(), locals())


@dataclass
class GetAllSubmodelElementsPathResponse(PagedResult):
    result: List[str] = field(metadata={"allow_empty": False})


r_get_all_submodel_elements_path, _ = reflect(GetAllSubmodelElementsPathResponse, globals(), locals())

r_submodel_element, _ = reflect(SubmodelElement, globals(), locals())

PathResponse = List[str]
r_path_response, _ = reflect(PathResponse, globals(), locals())


def get_all_submodel_elements(
    client: HttpClient,
    level: Optional[Level] = None,
    extent: Optional[Level] = None,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
) -> GetAllSubmodelElementsResponse:
    request = Request(
        "/submodel-elements",
        query_parameters={
            "level": unpack_enum(level),
            "extent": unpack_enum(extent),
            "limit": limit,
            "cursor": cursor,
        },
    )
    return invoke_and_decode(client, request, r_get_all_submodel_elements, {200})


class GetSubmodelTestSuite(ApiTestSuite):
    operation = "GetSubmodel"

    def invoke_success(self) -> Submodel:
        request = Request("/")
        return invoke_and_decode(self.client, request, r_submodel, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch submodel
        """
        self.invoke_success()


class GetSubmodelMetaTestSuite(ApiTestSuite):
    operation = "GetSubmodel-Metadata"

    def invoke_success(self) -> Submodel:
        request = Request("/$metadata")
        return invoke_and_decode(self.client, request, r_submodel, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch submodel
        """
        self.invoke_success()


class GetSubmodelValueTestSuite(ApiTestSuite):
    operation = "GetSubmodel-ValueOnly"

    def invoke_success(self) -> any:
        request = Request("/$value")
        result = invoke(self.client, request)
        return extract_json(result)

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch submodel
        """
        self.invoke_success()


class GetSubmodelReferenceTestSuite(ApiTestSuite):
    operation = "GetSubmodel-Reference"

    def invoke_success(self) -> Submodel:
        request = Request("/$reference")
        return invoke_and_decode(self.client, request, r_reference, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch submodel reference
        """
        self.invoke_success()


class GetSubmodelPathTestSuite(ApiTestSuite):
    operation = "GetSubmodel-Path"

    def invoke_success(self) -> PathResponse:
        request = Request("/$path")
        return invoke_and_decode(self.client, request, r_path_response, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch submodel path
        """
        self.invoke_success()


class GetSubmodelElementsTests(ApiTestSuite):
    def setup(self):
        result: PagedResult = self.invoke_success(limit=1)
        self.cursor = result.paging_metadata.cursor

    def test_simple(self):
        """
        Fetch all submodel elements
        """
        self.invoke_success()

    def test_level_core(self):
        """
        Fetch all submodel elements with level=core
        """
        self.invoke_success(level=Level.Core)

    def test_level_deep(self):
        """
        Fetch all submodel elements with level=deep
        """
        self.invoke_success(level=Level.Deep)

    def test_extent_with_blob_value(self):
        """
        Fetch all submodel elements with extent=withBlobValue
        """
        self.invoke_success(extent=Extent.WithBlobValue)

    def test_extent_without_blob_value(self):
        """
        Fetch all submodel elements with extent=withoutBlobValue
        """
        self.invoke_success(extent=Extent.WithoutBlobValue)

    def test_core_without_blob_value(self):
        """
        Fetch all submodel elements with level=core and extend=withoutBlobValue
        """
        self.invoke_success(level=Level.Core, extent=Extent.WithoutBlobValue)

    def test_deep_without_blob_value(self):
        """
        Fetch all submodel elements with level=deep and extend=withoutBlobValue
        """
        self.invoke_success(level=Level.Deep, extent=Extent.WithoutBlobValue)

    def test_core_with_blob_value(self):
        """
        Fetch all submodel elements with level=core and extend=withBlobValue
        """
        self.invoke_success(level=Level.Deep, extent=Extent.WithBlobValue)

    def test_deep_with_blob_value(self):
        """
        Fetch all submodel elements with level=deep and extend=withBlobValue
        """
        self.invoke_success(level=Level.Deep, extent=Extent.WithoutBlobValue)


class GetAllSubmodelElementsValueOnlyTests(ApiTestSuite):
    def setup(self):
        result: PagedResult = self.invoke_success(limit=1)
        self.cursor = result.paging_metadata.cursor

    def test_simple(self):
        """
        Fetch all submodel elements
        """
        self.invoke_success()

    def test_level_core(self):
        """
        Fetch all submodel elements with level=core
        """
        self.invoke_success(level=Level.Core)

    def test_level_deep(self):
        """
        Fetch all submodel elements with level=deep
        """
        self.invoke_success(level=Level.Deep)


class GetAllSubmodelElementsTestSuite(GetSubmodelElementsTests, PaginationTests):
    operation = "GetAllSubmodelElements"

    def invoke_success(
        self,
        level: Optional[Level] = None,
        extent: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> GetAllSubmodelElementsResponse:
        return get_all_submodel_elements(self.client, level, extent, limit, cursor)

    def invoke_error(
        self,
        level: Optional[Level] = None,
        extent: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ErrorResult:
        request = Request(
            "/submodel-elements",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))


class GetAllSubmodelElementsMetaTestSuite(PaginationTests):
    operation = "GetAllSubmodelElements-Metadata"

    def setup(self):
        self.cursor = self.invoke_success(limit=1).paging_metadata.cursor

    def _invoke(self, limit, cursor, reflection, status):
        request = Request(
            "/submodel-elements/$metadata",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> GetAllSubmodelElementsResponse:
        return self._invoke(limit, cursor, r_get_all_submodel_elements, {200})

    def invoke_error(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ErrorResult:
        return self._invoke(limit, cursor, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch all submodel elements (metadata)
        """
        self.invoke_success()


class GetAllSubmodelElementsValueOnlyTestSuite(GetAllSubmodelElementsValueOnlyTests, PaginationTests):
    operation = "GetAllSubmodelElements-ValueOnly"

    def _invoke(self, level, limit, cursor, reflection, status):
        request = Request(
            "/submodel-elements/$value",
            query_parameters={
                "level": unpack_enum(level),
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        level: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> GetAllSubmodelElementsValueOnlyResponse:
        return self._invoke(level, limit, cursor, r_get_all_submodel_elements_value_only, {200})

    def invoke_error(
        self,
        level: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ErrorResult:
        return self._invoke(level, limit, cursor, r_error_result, range(400, 500))


class GetAllSubmodelElementsReferenceTestSuite(GetAllSubmodelElementsValueOnlyTests, PaginationTests):
    operation = "GetAllSubmodelElements-Reference"

    def _invoke(self, level, limit, cursor, reflection, status):
        request = Request(
            "/submodel-elements/$reference",
            query_parameters={
                "level": unpack_enum(level),
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        level: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> GetAllSubmodelElementsValueOnlyResponse:
        return self._invoke(level, limit, cursor, r_get_all_submodel_elements_reference, {200})

    def invoke_error(
        self,
        level: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ErrorResult:
        return self._invoke(level, limit, cursor, r_error_result, range(400, 500))


class GetAllSubmodelElementsPathTestSuite(GetAllSubmodelElementsValueOnlyTests, PaginationTests):
    operation = "GetAllSubmodelElements-Path"

    def _invoke(self, level, limit, cursor, reflection, status):
        request = Request(
            "/submodel-elements/$path",
            query_parameters={
                "level": unpack_enum(level),
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        level: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> GetAllSubmodelElementsPathResponse:
        return self._invoke(level, limit, cursor, r_get_all_submodel_elements_path, {200})

    def invoke_error(
        self,
        level: Optional[Level] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> ErrorResult:
        return self._invoke(level, limit, cursor, r_error_result, range(400, 500))


def _model_type(cls):
    return cls.__name__.split(".")[-1]


def _collect_submodel_elements(elements: List[SubmodelElement], paths: Dict[str, List[str]], path_prefix: str):
    for idx, element in enumerate(elements):
        if not element.id_short:
            continue
        id_short = path_prefix + element.id_short.raw_value
        model_type = _model_type(element.__class__)
        paths[model_type].append(id_short)
        if isinstance(element, SubmodelElementCollection):
            _collect_submodel_elements(element.value, paths, id_short + ".")
        elif isinstance(element, SubmodelElementList):
            _collect_submodel_elements(element.value, paths, str(idx) + ".")


class GetAllSubmodelElementsTestSuiteBase(ApiTestSuite):
    all_submodel_elements = [
        _model_type(SubmodelElementCollection),
        _model_type(SubmodelElementList),
        _model_type(Entity),
        _model_type(BasicEventElement),
        _model_type(Capability),
        _model_type(Operation),
        _model_type(Property),
        _model_type(MultiLanguageProperty),
        _model_type(Range),
        _model_type(ReferenceElement),
        _model_type(RelationshipElement),
        _model_type(AnnotatedRelationshipElement),
        _model_type(Blob),
        _model_type(File),
    ]

    def setup(self):
        result = get_all_submodel_elements(self.client)
        self.paths: Dict[str, List[str]] = defaultdict(list)
        _collect_submodel_elements(result.result, self.paths, "")
        self.valid_arguments["id_short_path"] = next(iter(self.paths.values()))[0]


class GetSubmodelElementTestSuite(GetAllSubmodelElementsTestSuiteBase):
    operation = "GetSubmodelElementByPath"

    supported_submodel_elements = {
        _model_type(SubmodelElementCollection),
        _model_type(SubmodelElementList),
        _model_type(Entity),
        _model_type(BasicEventElement),
        _model_type(Capability),
        _model_type(Operation),
        _model_type(Property),
        _model_type(MultiLanguageProperty),
        _model_type(Range),
        _model_type(ReferenceElement),
        _model_type(RelationshipElement),
        _model_type(AnnotatedRelationshipElement),
        _model_type(Blob),
        _model_type(File),
    }

    def _invoke(self, id_short_path, level, extent, reflection, status):
        request = Request(
            f"/submodel-elements/{id_short_path}",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        id_short_path: str,
        level: Optional[Level] = None,
        extent: Optional[Extent] = None,
    ) -> SubmodelElement:
        return self._invoke(id_short_path, level, extent, r_submodel_element, {200})

    def invoke_error(
        self,
        id_short_path: str,
        level: Optional[Level] = None,
        extent: Optional[Extent] = None,
    ) -> ErrorResult:
        return self._invoke(id_short_path, level, extent, r_error_result, range(400, 500))

    def check_type(self, level: Optional[str] = None, extent: Optional[str] = None):
        for model_type in self.all_submodel_elements:
            with start(f"Checking {model_type}"):
                if model_type not in self.paths:
                    abort(AasTestResult("No such element present", level=ResultLevel.WARNING))
                id_short_path = self.paths[model_type][0]
                if model_type in self.supported_submodel_elements:
                    self.invoke_success(id_short_path=id_short_path, level=level, extent=extent)
                else:
                    self.invoke_error(id_short_path=id_short_path, level=level, extent=extent)

    def test_no_params(self):
        self.check_type()

    def test_level_deep(self):
        self.check_type(level=Level.Deep)

    def test_level_core(self):
        self.check_type(level=Level.Core)

    def test_extend_with_blob_value(self):
        self.check_type(extent=Extent.WithBlobValue)

    def test_extend_without_blob_value(self):
        self.check_type(extent=Extent.WithoutBlobValue)

    def test_core_without_blob_value(self):
        self.check_type(level=Level.Core, extent=Extent.WithoutBlobValue)

    def test_deep_without_blob_value(self):
        self.check_type(level=Level.Deep, extent=Extent.WithoutBlobValue)

    def test_core_with_blob_value(self):
        self.check_type(level=Level.Core, extent=Extent.WithBlobValue)

    def test_deep_with_blob_value(self):
        self.check_type(level=Level.Deep, extent=Extent.WithBlobValue)


class GetSubmodelElementMetaTestSuite(GetAllSubmodelElementsTestSuiteBase):
    operation = "GetSubmodelElementByPath-Metadata"
    supported_submodel_elements = {
        _model_type(SubmodelElementCollection),
        _model_type(SubmodelElementList),
        _model_type(Entity),
        _model_type(BasicEventElement),
        _model_type(Property),
        _model_type(MultiLanguageProperty),
        _model_type(Range),
        _model_type(ReferenceElement),
        _model_type(RelationshipElement),
        _model_type(AnnotatedRelationshipElement),
        _model_type(Blob),
        _model_type(File),
    }

    def invoke_success(self, id_short_path: str) -> any:
        request = Request(f"/submodel-elements/{id_short_path}/$metadata")
        result = invoke(self.client, request)
        return extract_json(result)

    def invoke_error(self, id_short_path: str) -> ErrorResult:
        request = Request(f"/submodel-elements/{id_short_path}/$metadata")
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def check_type(self):
        for model_type in self.all_submodel_elements:
            with start(f"Checking {model_type}"):
                if model_type not in self.paths:
                    abort(AasTestResult("No such element present", level=ResultLevel.WARNING))
                id_short_path = self.paths[model_type][0]
                if model_type in self.supported_submodel_elements:
                    self.invoke_success(id_short_path)
                else:
                    self.invoke_error(id_short_path)

    def test_no_params(self):
        self.check_type()


class GetSubmodelElementValueTestSuite(GetAllSubmodelElementsTestSuiteBase):
    operation = "GetSubmodelElementByPath-ValueOnly"
    supported_submodel_elements = [
        _model_type(SubmodelElementCollection),
        _model_type(SubmodelElementList),
        _model_type(Entity),
        _model_type(BasicEventElement),
        _model_type(Property),
        _model_type(MultiLanguageProperty),
        _model_type(Range),
        _model_type(ReferenceElement),
        _model_type(RelationshipElement),
        _model_type(AnnotatedRelationshipElement),
        _model_type(Blob),
        _model_type(File),
    ]

    def invoke_success(
        self,
        id_short_path: str,
        level: Optional[Level] = None,
        extent: Optional[Extent] = None,
    ) -> any:
        request = Request(
            f"/submodel-elements/{id_short_path}/$value",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
            },
        )
        result = invoke(self.client, request)
        return extract_json(result)

    def invoke_error(
        self,
        id_short_path: str,
        level: Optional[Level] = None,
        extent: Optional[Extent] = None,
    ) -> ErrorResult:
        request = Request(
            f"/submodel-elements/{id_short_path}/$value",
            query_parameters={
                "level": unpack_enum(level),
                "extent": unpack_enum(extent),
            },
        )
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def check_type(self, level: Optional[str] = None, extent: Optional[str] = None):
        for model_type in self.all_submodel_elements:
            with start(f"Checking {model_type}"):
                if model_type not in self.paths:
                    abort(AasTestResult("No such element present", level=ResultLevel.WARNING))
                id_short_path = self.paths[model_type][0]
                self.invoke_success(id_short_path=id_short_path, level=level, extent=extent)

    def test_no_params(self):
        self.check_type()

    def test_level_deep(self):
        self.check_type(level=Level.Deep)

    def test_level_core(self):
        self.check_type(level=Level.Core)

    def test_extend_with_blob_value(self):
        self.check_type(extent=Extent.WithBlobValue)

    def test_extend_without_blob_value(self):
        self.check_type(extent=Extent.WithoutBlobValue)

    def test_core_without_blob_value(self):
        self.check_type(level=Level.Core, extent=Extent.WithoutBlobValue)

    def test_deep_without_blob_value(self):
        self.check_type(level=Level.Deep, extent=Extent.WithoutBlobValue)

    def test_core_with_blob_value(self):
        self.check_type(level=Level.Core, extent=Extent.WithBlobValue)

    def test_deep_with_blob_value(self):
        self.check_type(level=Level.Deep, extent=Extent.WithBlobValue)


class GetSubmodelElementReferenceTestSuite(GetAllSubmodelElementsTestSuiteBase):
    operation = "GetSubmodelElementByPath-Reference"
    supported_submodel_elements = {
        _model_type(SubmodelElementCollection),
        _model_type(SubmodelElementList),
        _model_type(Entity),
        _model_type(BasicEventElement),
        _model_type(Capability),
        _model_type(Operation),
        _model_type(Property),
        _model_type(MultiLanguageProperty),
        _model_type(Range),
        _model_type(ReferenceElement),
        _model_type(RelationshipElement),
        _model_type(AnnotatedRelationshipElement),
        _model_type(Blob),
        _model_type(File),
    }

    def invoke_success(self, id_short_path: str) -> SubmodelElement:
        request = Request(f"/submodel-elements/{id_short_path}/$reference")
        return invoke_and_decode(self.client, request, r_reference, {200})

    def invoke_error(self, id_short_path: str) -> ErrorResult:
        request = Request(f"/submodel-elements/{id_short_path}/$reference")
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def check_type(self):
        for model_type in self.all_submodel_elements:
            with start(f"Checking {model_type}"):
                if model_type not in self.paths:
                    abort(AasTestResult("No such element present", level=ResultLevel.WARNING))
                id_short_path = self.paths[model_type][0]
                if model_type in self.supported_submodel_elements:
                    self.invoke_success(id_short_path)
                else:
                    self.invoke_error(id_short_path)

    def test_no_params(self):
        self.check_type()


GetSubmodelElementPathResponse = List[str]

r_get_submodel_element_path, _ = reflect(GetSubmodelElementPathResponse)


class GetSubmodelElementPathTestSuite(GetAllSubmodelElementsTestSuiteBase):
    operation = "GetSubmodelElementByPath-Path"

    supported_submodel_elements = [
        _model_type(SubmodelElementCollection),
        _model_type(SubmodelElementList),
        _model_type(Entity),
    ]

    def _invoke(self, id_short_path, level, reflection, status):
        request = Request(
            f"/submodel-elements/{id_short_path}/$path",
            query_parameters={
                "level": unpack_enum(level),
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(self, id_short_path: str, level: Optional[Level] = None) -> GetSubmodelElementPathResponse:
        return self._invoke(id_short_path, level, r_get_submodel_element_path, {200})

    def invoke_error(self, id_short_path: str, level: Optional[Level] = None) -> ErrorResult:
        return self._invoke(id_short_path, level, r_error_result, range(400, 500))

    def check_type(self):
        for model_type in self.all_submodel_elements:
            with start(f"Checking {model_type}"):
                if model_type not in self.paths:
                    abort(AasTestResult("No such element present", level=ResultLevel.WARNING))
                id_short_path = self.paths[model_type][0]
                if model_type in self.supported_submodel_elements:
                    self.invoke_success(id_short_path)
                else:
                    self.invoke_error(id_short_path)

    def test_no_params(self):
        self.check_type()


class GetFileByPathTestSuite(GetAllSubmodelElementsTestSuiteBase):
    operation = "GetFileByPath"

    def invoke_success(self, id_short_path: str) -> bytes:
        request = Request(f"/submodel-elements/{id_short_path}/attachment")
        result = invoke(self.client, request)
        return result.content

    def invoke_error(self, id_short_path: str) -> ErrorResult:
        request = Request(f"/submodel-elements/{id_short_path}/attachment")
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_no_params(self):
        try:
            path = self.paths["File"][0]
        except (KeyError, IndexError):
            abort(
                AasTestResult(
                    "No submodel element of type 'File' found, skipping test.",
                    ResultLevel.WARNING,
                )
            )
        self.invoke_success(path)
