from typing import List, Union
from dataclasses import dataclass
from aas_test_engines.reflect import reflect
from aas_test_engines.http import HttpClient, Request
from aas_test_engines.result import Level
from .shared import (
    ErrorResult,
    invoke_and_decode,
    r_error_result,
    ApiTestSuite,
    _assert,
)


@dataclass
class ServiceDescription:
    profiles: List[str]


r_service_spec, _ = reflect(ServiceDescription)


class GetDescriptionTestSuite(ApiTestSuite):
    operation = "GetDescription"

    def invoke_success(self) -> ServiceDescription:
        request = Request(path="/description")
        return invoke_and_decode(self.client, request, r_service_spec, {200})

    def invoke_error(self) -> ErrorResult:
        raise NotImplementedError("Cannot fail")

    def test_contains_suite(self):
        """
        Returned profiles must contain suite
        """
        specs = self.invoke_success()
        _assert(self.profile in specs.profiles, f"Contains {self.profile}", Level.WARNING)
