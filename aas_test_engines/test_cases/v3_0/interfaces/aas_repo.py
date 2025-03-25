from typing import List, Optional
from dataclasses import dataclass, field
from aas_test_engines.reflect import reflect
from aas_test_engines.http import HttpClient, Request
from aas_test_engines.test_cases.v3_0.model import AssetAdministrationShell, Reference
from .shared import (
    PagedResult,
    invoke_and_decode,
    Base64String,
    AssetId,
    ApiTestSuite,
    PaginationTests,
    _assert,
    r_error_result,
    ErrorResult,
)


@dataclass
class GetAllShellsResponse(PagedResult):
    result: List[AssetAdministrationShell] = field(metadata={"allow_empty": True})


@dataclass
class GetAllShellsReferenceResponse(PagedResult):
    result: List[Reference] = field(metadata={"allow_empty": True})


r_get_all_shells_response, _ = reflect(GetAllShellsResponse, globals(), locals())
r_get_all_shells_reference_response, _ = reflect(GetAllShellsReferenceResponse, globals(), locals())
r_asset_administration_shell, _ = reflect(AssetAdministrationShell, globals(), locals())
r_reference, _ = reflect(Reference, globals(), locals())


def get_all_shells(
    client: HttpClient,
    limit: Optional[int] = None,
    cursor: Optional[str] = None,
    id_short: Optional[str] = None,
    asset_id: Optional[AssetId] = None,
) -> GetAllShellsResponse:
    request = Request(
        path="/shells",
        query_parameters={
            "cursor": cursor,
            "limit": limit,
            "idShort": id_short,
            "assetIds": asset_id,
        },
    )
    return invoke_and_decode(client, request, r_get_all_shells_response, {200})


class GetAllAasTestSuiteBase(ApiTestSuite):
    def setup(self):
        self.cursor: Optional[str] = None
        shells = get_all_shells(self.client, limit=1)
        self.valid_id_short = shells.result[0].id_short.raw_value
        global_asset_id = shells.result[0].asset_information.global_asset_id.raw_value
        if global_asset_id:
            self.asset_id = AssetId(name="globalAssetId", value=global_asset_id)
        else:
            specific_asset_id = shells.result[0].asset_information.specific_asset_ids[0]
            self.asset_id = AssetId(
                name=specific_asset_id.name.raw_value,
                value=specific_asset_id.value.raw_value,
            )
        self.cursor = shells.paging_metadata.cursor

    def test_no_parameters(self):
        """
        Invoke without parameters
        """
        self.invoke_success()

    def test_filter_by_non_existing_idshort(self):
        """
        Filter by non-existing idShort
        """
        result = self.invoke_success(id_short="does-not-exist")
        _assert(len(result.result) == 0, "Result is empty")

    def test_filter_by_asset_id(self):
        """
        Filter by assetId
        """
        result = self.invoke_success(asset_id=self.asset_id)
        _assert(len(result.result) != 0, "Returns non-empty list")


class GetAllAasTestSuite(GetAllAasTestSuiteBase, PaginationTests):
    operation = "GetAllAssetAdministrationShells"

    def invoke_success(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        id_short: Optional[str] = None,
        asset_id: Optional[AssetId] = None,
    ) -> GetAllShellsResponse:
        return get_all_shells(self.client, limit, cursor, id_short, asset_id)

    def invoke_error(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        id_short: Optional[str] = None,
        asset_id: Optional[AssetId] = None,
    ) -> ErrorResult:
        request = Request(
            path="/shells",
            query_parameters={
                "cursor": cursor,
                "limit": limit,
                "idShort": id_short,
                "assetIds": asset_id,
            },
        )
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_filter_by_idshort(self):
        """
        Filter by idShort
        """
        result = self.invoke_success(id_short=self.valid_id_short)
        _assert(len(result.result) > 0, "Returns entries")
        _assert(
            result.result[0].id_short.raw_value == self.valid_id_short,
            "Result has the requested idShort",
        )


class GetAllAasRefsTestSuite(GetAllAasTestSuiteBase, PaginationTests):
    operation = "GetAllAssetAdministrationShells-Reference"

    def _invoke(self, limit, cursor, id_short, asset_id, reflection, status):
        request = Request(
            path="/shells/$reference",
            query_parameters={
                "cursor": cursor,
                "limit": limit,
                "idShort": id_short,
                "assetIds": asset_id,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        id_short: Optional[str] = None,
        asset_id: Optional[AssetId] = None,
    ) -> GetAllShellsReferenceResponse:
        return self._invoke(
            limit,
            cursor,
            id_short,
            asset_id,
            r_get_all_shells_reference_response,
            {200},
        )

    def invoke_error(
        self,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
        id_short: Optional[str] = None,
        asset_id: Optional[AssetId] = None,
    ) -> ErrorResult:
        return self._invoke(limit, cursor, id_short, asset_id, r_error_result, range(400, 500))

    def test_filter_by_idshort(self):
        """
        Filter by idShort
        """
        result = self.invoke_success(id_short=self.valid_id_short)
        _assert(len(result.result) > 0, "Returns entries")


class GetAasByIdTestSuite(ApiTestSuite):
    operation = "GetAssetAdministrationShellById"

    def setup(self):
        shells = get_all_shells(self.client, limit=1)
        self.valid_id = shells.result[0].id.raw_value

    def invoke_success(self, aas_id: Base64String) -> AssetAdministrationShell:
        request = Request(path=f"/shells/{aas_id}")
        return invoke_and_decode(self.client, request, r_asset_administration_shell, {200})

    def invoke_error(self, aas_id: Base64String) -> ErrorResult:
        request = Request(path=f"/shells/{aas_id}")
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_get(self):
        """
        Fetch AAS
        """
        result = self.invoke_success(Base64String(self.valid_id))
        _assert(result.id.raw_value == self.valid_id, "Returns the requested aas")


class GetAasByIdReferenceTestSuite(ApiTestSuite):
    operation = "GetAssetAdministrationShellById-Reference"

    def setup(self):
        shells = get_all_shells(self.client, limit=1)
        self.valid_id = shells.result[0].id.raw_value

    def invoke_success(self, aas_id: Base64String) -> Reference:
        request = Request(path=f"/shells/{aas_id}/$reference")
        return invoke_and_decode(self.client, request, r_reference, {200})

    def invoke_error(self, aas_id: Base64String) -> ErrorResult:
        request = Request(path=f"/shells/{aas_id}/$reference")
        return invoke_and_decode(self.client, request, r_error_result, range(400, 500))

    def test_get(self):
        """
        Fetch AAS Reference
        """
        result = self.invoke_success(Base64String(self.valid_id))
        _assert(result.keys[0].value.raw_value == self.valid_id, "Returns the requested aas")
