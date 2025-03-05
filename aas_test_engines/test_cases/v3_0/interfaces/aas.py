from typing import List, Optional
from dataclasses import dataclass
from aas_test_engines.reflect import reflect
from aas_test_engines.http import HttpClient, Request
from .shared import (
    ErrorResult,
    invoke_and_decode,
    r_error_result,
    ApiTestSuite,
    invoke,
    PagedResult,
    Base64String,
    PaginationTests,
)
from aas_test_engines.test_cases.v3_0.model import (
    AssetInformation,
    Reference,
    Submodel,
    AssetAdministrationShell,
)

# We omit the prefix '/aas' for all paths here and add it in the client instead


@dataclass
class GetAllSubmodelReferencesResponse(PagedResult):
    result: List[Reference]


r_submodel_references, _ = reflect(GetAllSubmodelReferencesResponse, globals(), locals())


r_asset_information, _ = reflect(AssetInformation, globals(), locals())
r_asset_administration_shell, _ = reflect(AssetAdministrationShell, globals(), locals())
r_reference, _ = reflect(Reference, globals(), locals())


def get_shell(client: HttpClient) -> AssetAdministrationShell:
    request = Request("/")
    return invoke_and_decode(client, request, r_asset_administration_shell, {200})


def get_all_submodel_references(
    client: HttpClient, limit: Optional[int] = None, cursor: Optional[str] = None
) -> GetAllSubmodelReferencesResponse:
    request = Request(
        path=f"/submodel-refs",
        query_parameters={
            "limit": limit,
            "cursor": cursor,
        },
    )
    return invoke_and_decode(client, request, r_submodel_references, {200})


class GetShellTestSuite(ApiTestSuite):
    operation = "GetAssetAdministrationShell"

    def invoke_success(self) -> AssetAdministrationShell:
        return get_shell(self.client)

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch Shell
        """
        self.invoke_success()


class GetShellReferenceTestSuite(ApiTestSuite):
    operation = "GetAssetAdministrationShell-Reference"

    def invoke_success(self) -> Reference:
        request = Request("/$reference")
        return invoke_and_decode(self.client, request, r_reference, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_no_params(self):
        """
        Fetch Shell Reference
        """
        self.invoke_success()


class GetAllSubmodelReferencesTestSuite(PaginationTests, ApiTestSuite):
    operation = "GetAllSubmodelReferences"

    def setup(self):
        refs = get_all_submodel_references(self.client, limit=1)
        self.cursor = refs.paging_metadata.cursor

    def invoke_success(
        self, limit: Optional[int] = None, cursor: Optional[str] = None
    ) -> GetAllSubmodelReferencesResponse:
        return get_all_submodel_references(self.client, limit, cursor)

    def invoke_error(self, limit: Optional[int] = None, cursor: Optional[str] = None) -> ErrorResult:
        request = Request(
            path=f"/submodel-refs",
            query_parameters={
                "limit": limit,
                "cursor": cursor,
            },
        )
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_simple(self):
        """
        Fetch all references
        """
        self.invoke_success()


class GetAssetInformationTestSuite(ApiTestSuite):
    operation = "GetAssetInformation"

    def invoke_success(self) -> AssetInformation:
        request = Request(path=f"/asset-information")
        return invoke_and_decode(self.client, request, r_asset_information, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_fetch(self):
        """
        Fetch Asset Information
        """
        self.invoke_success()


class GetThumbnailTestSuite(ApiTestSuite):
    operation = "GetThumbnail"

    def invoke_success(self) -> bytes:
        request = Request(path=f"/asset-information/thumbnail")
        return invoke(self.client, request).content

    def test_fetch(self):
        """
        Fetch thumbnail
        """
        self.invoke_success()

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")
