from typing import Any, Optional, List, Dict, Set
from dataclasses import dataclass
from enum import Enum
from .parse_util import assert_type, safe_dict_lookup
from .runtime_expression import RuntimeExpression

from .resolver import Resolver
import warnings

@dataclass
class Info:
    title: str

    @classmethod
    def from_dict(cls, data: Any, json_path: str) -> "Info":
        return cls(
            title=safe_dict_lookup(data, 'title', str, json_path)
        )


class ParameterPosition(Enum):
    QUERY = "query"
    HEADER = "header"
    PATH = "path"
    COOKIE = "cookie"


class ParameterStyle(Enum):
    FORM = "form"
    SIMPLE = "simple"


@dataclass
class Parameter:
    name: str
    position: ParameterPosition
    required: bool
    style: ParameterStyle
    explode: bool
    schema: dict
    source_link: Optional["BackwardLink"] = None

    @classmethod
    def from_dict(cls: "Parameter", data: Any, json_path: str, resolver: Resolver) -> "Parameter":
        if '$ref' in data:
            ref = safe_dict_lookup(data, '$ref', str, json_path)
            data = resolver.lookup(ref)
        return cls(
            name=safe_dict_lookup(data, 'name', str, json_path),
            position=ParameterPosition(
                safe_dict_lookup(data, 'in', str, json_path)),
            required=safe_dict_lookup(data, "required", bool, json_path, True),
            style=ParameterStyle(safe_dict_lookup(
                data, 'style', str, json_path, ParameterStyle.SIMPLE.value)),
            explode=safe_dict_lookup(data, 'explode', bool, json_path, False),
            schema=safe_dict_lookup(data, 'schema', dict, json_path),
        )


@dataclass
class RequestBody:
    description: str
    schema: Optional[Dict]
    required: bool

    @classmethod
    def from_dict(cls: "RequestBody", data: Any, json_path: str) -> "RequestBody":
        assert_type(data, dict, json_path)
        content = safe_dict_lookup(data, 'content', dict, json_path)
        json_content_type = 'application/json'
        if len(content.keys()) != 1:
            warnings.warn(f"Ignoring some content types at {json_path}")
        if json_content_type not in content.keys():
            warnings.warn(f"Support for non-json request bodies not implemented, at {json_path}")
            json_content = {}
        else:
            json_content = safe_dict_lookup(content, json_content_type, dict, json_path)
        return cls(
            description=safe_dict_lookup(data, 'description', str, json_path),
            required=safe_dict_lookup(data, 'required', bool, json_path, True),
            schema=safe_dict_lookup(
                json_content, 'schema', dict, json_path, None)
        )


@dataclass
class Link:
    name: str
    target_operation: "Operation"
    parameters: Dict[str, RuntimeExpression]

    @classmethod
    def from_dict(cls: "Link", name: str, data: Any, json_path: str):
        assert_type(data, dict, json_path)
        return cls(
            name=name,
            target_operation=safe_dict_lookup(
                data, 'operationId', str, json_path),
            parameters={k: RuntimeExpression.from_string(v) for k, v in safe_dict_lookup(
                data, "parameters", dict, json_path).items()},
        )


@dataclass
class BackwardLink:
    source_operation: "Operation"
    source_response: "Response"
    param_query: str


@dataclass
class Response:
    code: int
    schema: Optional[Dict]
    links: List[Link]

    @classmethod
    def from_dict(cls: "Response", code: str, data: Any, json_path) -> "Response":
        content = safe_dict_lookup(data, 'content', dict, json_path, None)
        schema = None
        if content is not None:
            json_content_type = 'application/json'
            if len(content.keys()) != 1:
                warnings.warn(f"Ignoring some content types at {json_path}")
            if json_content_type not in content.keys():
                warnings.warn(f"Support for non-json request bodies not implemented, at {json_path}")
                json_content = {}
            else:
                json_content = safe_dict_lookup(content, json_content_type, dict, json_path)
            schema = safe_dict_lookup(
                json_content, 'schema', dict, json_path, None)

        links = safe_dict_lookup(data, 'links', dict, json_path, None)
        if links:
            links = [Link.from_dict(k, v, json_path + '.' + k)
                     for k, v in links.items()]
        else:
            links = []

        return cls(
            code= 400 if code == 'default' else int(code),
            schema=schema,
            links=links,
        )


@dataclass
class Operation:
    operation_id: str
    summary: str
    method: str
    parameters: List[Parameter]
    request_body: Optional[RequestBody]
    responses: List[Response]
    tags: Set[str]

    @classmethod
    def from_dict(cls: "Operation", method: str, data: Any, json_path: str, resolver: Resolver) -> "Operation":
        assert_type(data, dict, json_path)
        request_body = safe_dict_lookup(
            data, 'requestBody', dict, json_path, None)
        return cls(
            operation_id=safe_dict_lookup(data, 'operationId', str, json_path),
            summary=safe_dict_lookup(data, 'summary', str, json_path, ''),
            method=method,
            parameters=[Parameter.from_dict(param, json_path + '.parameters.' + str(
                i), resolver) for i, param in enumerate(safe_dict_lookup(data, 'parameters', list, json_path, []))],
            request_body=RequestBody.from_dict(
                request_body, json_path + '.' + 'requestBody') if request_body is not None else None,
            responses=[Response.from_dict(k, v, json_path + '.' + k)
                       for k, v in safe_dict_lookup(data, 'responses', dict, json_path).items()],
            tags=set(safe_dict_lookup(data, 'tags', list, json_path))
        )

    def get_param_by_name(self, name: str) -> Parameter:
        for p in self.parameters:
            if p.name == name:
                return p
        raise Exception("Could not find parameter {} in operation {}".format(
            name, self.operation_id))


@dataclass
class Path:
    path: str
    operations: List[Operation]

    @classmethod
    def from_dict(cls: "Path", path_name: str, data: Any, json_path: str, resolver: Resolver) -> "Path":
        assert_type(data, dict, json_path)
        operations: List[Operation] = []
        for k, v in assert_type(data, dict, json_path).items():
            operations.append(Operation.from_dict(k, v, json_path + '.' + k, resolver))
        return cls(
            path=path_name,
            operations=operations
        )


@dataclass
class OpenApi:
    info: Info
    paths: List[Path]
    components: dict

    @classmethod
    def from_dict(cls: "OpenApi", data: Any) -> "OpenApi":
        assert_type(data, dict, '')
        resolver = Resolver(data)
        api = cls(
            info=Info.from_dict(safe_dict_lookup(
                data, 'info', dict, ''), 'info'),
            paths=[
                Path.from_dict(path_name, path_info, 'paths.' + path_name, resolver)
                for path_name, path_info in safe_dict_lookup(data, 'paths', dict, '').items()
                if not path_name.startswith('/packages')  # TODO: remove this
            ],
            components=safe_dict_lookup(data, 'components', dict, ''),
        )
        _resolve_links(api)
        return api


def _resolve_links(api: OpenApi):
    operations: Dict[str, Operation] = {}

    # first pass: collect all operations
    for path in api.paths:
        for operation in path.operations:
            if operation.operation_id in operations:
                raise Exception("Duplicate operation name {}".format(
                    operation.operation_id))
            operations[operation.operation_id] = operation

    # second pass: resolve links
    for path in api.paths:
        for operation in path.operations:
            for response in operation.responses:
                for link in response.links:
                    link.target_operation = operations[link.target_operation]
                    for param_name, param_query in link.parameters.items():
                        param = link.target_operation.get_param_by_name(
                            param_name)
                        if param.source_link:
                            raise Exception("Param already has a source link")
                        param.source_link = BackwardLink(
                            source_operation=operation,
                            source_response=response,
                            param_query=param_query,
                        )
