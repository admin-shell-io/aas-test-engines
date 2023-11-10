from dataclasses import dataclass
import json
from typing import Dict, List, Any
from .runtime_expression import RuntimeExpression

from .parse_util import assert_type, safe_dict_lookup
from enum import Enum

VERSION = '0.1'


@dataclass
class Request:
    path: str
    method: str
    headers: Dict[str, str]
    body: str

    def to_dict(self) -> dict:
        return {
            'path': self.path,
            'method': self.method,
            'headers': self.headers,
            'body': self.body,
        }

    @classmethod
    def from_dict(cls: "Request", data: Any, json_path: str) -> "Request":
        return cls(
            path=safe_dict_lookup(data, 'path', str, json_path),
            method=safe_dict_lookup(data, 'method', str, json_path),
            headers=safe_dict_lookup(data, 'headers', dict, json_path),
            body=safe_dict_lookup(data, 'body', str, json_path),
        )


class MatchType(Enum):
    JSON_SCHEMA = 'json_schema'
    EQUALITY = 'equality'
    STATUS_CODE_ONLY = 'only_code'


@dataclass
class Response:
    code: int
    content: str
    match: MatchType
    variables: Dict[str, RuntimeExpression]

    def to_dict(self):
        return {
            'code': self.code,
            'content': self.content,
            'match': self.match.value,
            'variables': {k: v.to_string() for k, v in self.variables.items()}
        }

    @classmethod
    def from_dict(cls: "Response", data: Any, json_path: str) -> "Response":
        return cls(
            code=safe_dict_lookup(data, 'code', int, json_path),
            content=safe_dict_lookup(data, 'content', str, json_path),
            match=MatchType(safe_dict_lookup(data, 'match', str, json_path)),
            variables={k: RuntimeExpression.from_string(v) for k, v in safe_dict_lookup(
                data, 'variables', dict, json_path).items()},
        )


@dataclass
class TestCase:
    request: Request
    response: Response

    def to_dict(self):
        return {
            'request': self.request.to_dict(),
            'response': self.response.to_dict(),
        }

    @classmethod
    def from_dict(cls: "TestCase", data: Any, json_path: str) -> "TestCase":
        assert_type(data, dict, json_path)
        return cls(
            request=Request.from_dict(safe_dict_lookup(
                data, 'request', dict, json_path), json_path + '.' + 'request'),
            response=Response.from_dict(safe_dict_lookup(
                data, 'response', dict, json_path), json_path + '.' + 'response'),
        )


@dataclass
class RunConfig:
    test_cases: List[TestCase]
    components: dict

    def to_dict(self):
        return {
            'version': VERSION,
            'test_cases': [i.to_dict() for i in self.test_cases],
            'components': self.components,
        }

    @classmethod
    def from_dict(cls: "RunConfig", data) -> "RunConfig":
        assert_type(data, dict, '')
        version = safe_dict_lookup(data, 'version', str, '')
        if version != VERSION:
            raise Exception(
                "Incompatible format: got {}, expected {}".format(version, VERSION))
        return cls(
            test_cases=[TestCase.from_dict(tc, 'test_cases.' + str(i))
                        for i, tc in enumerate(safe_dict_lookup(data, 'test_cases', list, ''))],
            components=safe_dict_lookup(data, 'components', dict, ''),
        )
