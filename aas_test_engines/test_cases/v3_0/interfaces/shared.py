from typing import List, Union, Optional, Dict, Set
from enum import Enum
from aas_test_engines.http import HttpClient, Request, Response
from aas_test_engines.reflect import (
    reflect,
    TypeBase,
    reflect_function,
    StringFormattedValue,
)
from aas_test_engines.test_cases.v3_0.parse import parse_and_check_json
from dataclasses import dataclass, field
from aas_test_engines.result import (
    write,
    start,
    abort,
    AasTestResult,
)
from aas_test_engines.result import Level as ResultLevel
import base64
import json
import requests
from fences.core.util import ConfusionMatrix

# Util

all_operations: Dict[str, callable] = {}


def _assert(predicate: bool, message, level: ResultLevel = ResultLevel.ERROR):
    if predicate:
        write(f"{message}: OK")
    else:
        abort(AasTestResult(f"{message}: Fail", level))


class Base64String(StringFormattedValue):
    base64 = True


def _shorten(content: bytes, max_len: int = 300) -> str:
    try:
        content = content.decode()
    except UnicodeDecodeError:
        return "<binary-data>"
    if len(content) > max_len:
        return content[:max_len] + "..."
    return content


def extract_json(response: Response) -> dict:
    try:
        data = response.json()
        if not isinstance(data, (dict, list)):
            abort(f"Expected JSON, got {type(data)}")
        return data
    except requests.exceptions.JSONDecodeError as e:
        abort(f"Cannot decode as JSON: {e}")


def invoke(client: HttpClient, request: Request) -> Response:
    url = "".join(client.prefixes) + request.make_url()
    write(f"Invoke {url}")
    response = client.send(request)
    write(f"Response: ({response.status_code}): {_shorten(response.content)}")
    return response


def invoke_and_decode(
    client: HttpClient,
    request: Request,
    return_type: TypeBase,
    expected_status: Set[int],
):
    request.headers["content-type"] = "application/json"
    response = invoke(client, request)
    if response.status_code >= 500:
        abort(
            AasTestResult(
                f"Got unexpected status code {response.status_code}",
                ResultLevel.CRITICAL,
            )
        )
    if response.status_code not in expected_status:
        abort(AasTestResult(f"Got unexpected status code {response.status_code}", ResultLevel.ERROR))
    data = extract_json(response)
    result, parsed = parse_and_check_json(return_type, data)
    if result.ok():
        write(result)
        return parsed
    else:
        abort(result)


# Common


class MessageType(Enum):
    Undefined = "Undefined"
    Info = "Info"
    Warning = "Warning"
    Error = "Error"
    Exception = "Exception"


@dataclass
class Message:
    code: Optional[str]  # 1 < len < 32
    correlation_id: Optional[str]  # 1 < len < 32
    message_type: Optional[MessageType]
    text: Optional[str]
    timestamp: Optional[str]


# TODO: should be Optional[List[Message]]
@dataclass
class ErrorResult:
    messages: Optional[List[any]] = field(metadata={"force_name": "Messages"})


r_error_result, _ = reflect(ErrorResult)


@dataclass
class PagingMetadata:
    cursor: Optional[str]


@dataclass
class PagedResult:
    paging_metadata: PagingMetadata = field(metadata={"force_name": "paging_metadata"})


@dataclass
class AssetId:
    name: str
    value: str

    def __str__(self):
        return base64.b64encode(json.dumps({"name": self.name, "value": self.value}).encode()).decode()


class ApiTestSuite:
    operation = "?"

    def __init__(self, client: HttpClient, profile: str):
        self.client = client
        self.profile = profile
        self.valid_arguments: Dict[str, any] = {}

    def setup(self):
        pass

    def invoke_success(self, *args, **kwargs) -> any:
        raise NotImplementedError(self)

    def invoke_error(self, *args, **kwargs) -> ErrorResult:
        raise NotImplementedError(self)


class PaginationTests(ApiTestSuite):
    cursor: Optional[str] = None

    def test_get_one(self):
        """
        Pagination: Fetch exactly one
        """
        result = self.invoke_success(limit=1, **self.valid_arguments)
        _assert(len(result.result) == 1, "Has exactly one result entry")

    def test_pagination(self):
        """
        Pagination: Fetch using cursor
        """
        if self.cursor is None:
            abort(
                AasTestResult(
                    "Cannot check pagination, there must be at least 2 entities",
                    level=ResultLevel.WARNING,
                )
            )
        result = self.invoke_success(limit=1, **self.valid_arguments)
        _assert(len(result.result) == 1, "Exactly one entry")


class Level(Enum):
    Core = "core"
    Deep = "deep"


class Extent(Enum):
    WithBlobValue = "withBlobValue"
    WithoutBlobValue = "withoutBlobValue"


def unpack_enum(e: Enum):
    if e is None:
        return None
    return e.value
