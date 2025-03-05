from typing import Optional
from .shared import (
    ApiTestSuite,
    invoke_and_decode,
    _assert,
    ErrorResult,
    r_error_result,
)
from aas_test_engines.http import Request
from aas_test_engines.result import Level
from .aas_repo import get_all_shells, Base64String
from aas_test_engines.test_cases.v3_0.model import r_environment, Environment


class GenerateSerializationSuite(ApiTestSuite):
    operation = "GenerateSerializationByIds"

    def setup(self):
        shells = get_all_shells(self.client, limit=1)
        self.valid_id = Base64String(shells.result[0].id.raw_value)
        self.valid_submod_id = Base64String(shells.result[0].submodels[0].keys[0].value.raw_value)

    def _invoke(self, aas_id, submodel_id, include_cds, reflection, status):
        request = Request(
            "/serialization",
            query_parameters={
                "aasIds": aas_id,
                "submodelIds": submodel_id,
                "includeConceptDescriptions": include_cds,
            },
        )
        return invoke_and_decode(self.client, request, reflection, status)

    def invoke_success(
        self,
        aas_id: Optional[Base64String] = None,
        submodel_id: Optional[Base64String] = None,
        include_concept_descriptions: Optional[bool] = None,
    ) -> Environment:
        return self._invoke(aas_id, submodel_id, include_concept_descriptions, r_environment, {200})

    def invoke_error(
        self,
        aas_id: Optional[Base64String] = None,
        submodel_id: Optional[Base64String] = None,
        include_concept_descriptions: Optional[bool] = None,
    ) -> ErrorResult:
        return self._invoke(
            aas_id,
            submodel_id,
            include_concept_descriptions,
            r_error_result,
            range(400, 500),
        )

    def test_simple(self):
        """
        Invoke without parameters
        """
        self.invoke_success()

    def test_filter_by_aasids(self):
        """
        Filter by aas ids
        """
        self.invoke_success(aas_id=self.valid_id)

    def test_filter_by_submodel_ids(self):
        """
        Filter by submodel ids
        """
        self.invoke_success(submodel_id=self.valid_submod_id)

    def test_include_concept_descriptions(self):
        """
        Invoke with includeConceptDescriptions
        """
        result = self.invoke_success(include_concept_descriptions=True)
        _assert(
            result.concept_descriptions is not None,
            "contains conceptDescriptions",
            Level.WARNING,
        )
