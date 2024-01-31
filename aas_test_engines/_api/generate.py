from typing import Dict, List, Optional, Set, Tuple

from dataclasses import dataclass, field
import hashlib
import json
from urllib.parse import urlencode
import os
import base64

from . import runconf
from . import openapi


@dataclass
class RequestParams:
    path_params: Dict[str, str] = field(default_factory=dict)
    body: str = ''
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)

    class Discard:
        pass

    def to_request(self, path: str, method: str) -> runconf.Request:
        for key, value in self.path_params.items():
            path = path.replace('{' + key + '}', value)
        if self.query_params:
            path += "?" + urlencode(self.query_params)
        return runconf.Request(
            path=path,
            method=method,
            # TODO: content type should not be hardcoded
            headers={**self.headers, 'content-type': 'application/json'},
            body=self.body,
        )


class ParameterOptions:
    def __init__(self, values: List[str]) -> None:
        self.values = values

    def inject(self, request: RequestParams, value: str):
        raise NotImplemented()


class QueryParameterOption(ParameterOptions):
    def __init__(self, key: str, values: str) -> None:
        super().__init__(values)
        self.key = key

    def inject(self, request: RequestParams, value: str):
        request.query_params[self.key] = value


class PathParameterOption(ParameterOptions):
    def __init__(self, key: str, values: str) -> None:
        super().__init__(values)
        self.key = key

    def inject(self, request: RequestParams, value: str):
        request.path_params[self.key] = value


class JsonBodyParameterOption(ParameterOptions):
    def __init__(self, values: str) -> None:
        super().__init__(values)

    def inject(self, request: RequestParams, value: str):
        request.body = json.dumps(value)


def generate_link_id(source_op: openapi.Operation, param: str, target_op: openapi.Operation) -> str:
    id_ = source_op.operation_id + "_" + param + "_" + target_op.operation_id
    return hashlib.sha256(id_.encode()).hexdigest()


def generate_valid_samples(schema: Optional[dict]):
    if 'enum' in schema:
        return schema['enum']
    if '$ref' in schema:
        ref = schema['$ref']
        samples_dir = os.path.dirname(
            os.path.realpath(__file__)) + '/../data/api/samples/'
        # TODO: make this configurable
        path = {
            '#/components/schemas/AssetAdministrationShell': 'aas.json',
            '#/components/schemas/AssetInformation': 'asset_info.json',
            '#/components/schemas/Reference': 'model_reference.json',
            '#/components/schemas/Submodel': 'submodel.json',
            '#/components/schemas/SubmodelElement': 'submodel_element.json',
            '#/components/schemas/OperationRequest': 'operation_request.json',
            '#/components/schemas/AssetAdministrationShellDescriptor': 'shell_descriptor.json',
            '#/components/schemas/SubmodelDescriptor': 'submodel_descriptor.json',
            '#/components/schemas/ConceptDescription': 'empty.json',
            '#/components/schemas/Identifier': 'empty.json',
            '#/components/schemas/IdentifierKeyValuePair': 'empty.json',
            '#/components/schemas/SubmodelMetadata': 'empty.json',
            '#/components/schemas/SubmodelValue': 'empty.json',
            '#/components/schemas/SubmodelElementMetadata': 'empty.json',
            '#/components/schemas/SubmodelElementValue': 'empty.json',
            '#/components/schemas/OperationRequestValueOnly': 'empty.json',
            '#/components/schemas/GetSubmodelElementsMetadataResult': 'empty.json',
            '#/components/schemas/GetSubmodelElementsValueResult': 'empty.json',
            '#/components/schemas/SpecificAssetId': 'empty.json',
        }.get(ref)
        if path:
            # TODO: check if example matches the schema
            return [json.load(open(samples_dir + path, "rb"))]
        else:
            raise Exception("Failed to generate valid samples for " + schema['$ref'])
    type_ = schema.get('type', 'object')
    if type_ == 'array':
        return [generate_valid_samples(schema['items'])]
    elif type_ == 'boolean':
        return [True, False]
    elif type_ == 'string':
        return ["random_string"]
    else:
        # Note we could pick random values for types 'string' and 'integer', too.
        # However, these are in most cases ids, which should be captured from other requests.
        # One should use OpenApi links for this purpose.
        raise Exception("Unknown schema type {}".format(type_))


def generate_invalid_samples(schema: dict):
    # TODO: this could be more elaborated ;)
    return ["INVALID"]


def extract_variables(operation: openapi.Operation, response: openapi.Response):
    # TODO: it is not needed to extract ALL variables, but only the ones we actually need for other tests, later
    # Furthermore, a lot of variables will have the same value, so they should not be evaluated multiple times
    vars = {}
    for link in response.links:
        for param, expression in link.parameters.items():
            id_ = generate_link_id(operation, param, link.target_operation)
            vars[id_] = expression
    return vars


def generate_positive_tests(test_cases: List[runconf.TestCase], path: str, operation: openapi.Operation, response: openapi.Response) -> List[RequestParams]:

    options: List[ParameterOptions] = []

    for i in operation.parameters:
        if not i.required:
            # TODO: should be generated, too
            options.append(PathParameterOption(
                key=i.name,
                values=[RequestParams.Discard]
            ))
            continue
        if i.source_link:
            id_ = generate_link_id(i.source_link.source_operation, i.name, operation)
            base64url_encoded = i.schema.get('format') == 'byte'
            if base64url_encoded:
                values = ['!{' + id_ + '_base64}']
            else:
                values = ['!{' + id_ + '}']
            # TODO: if base64_urlencoded, add negative test which does not encode
        else:
            # TODO: escape strings of the form !{*}, to avoid clash with variables above
            values = generate_valid_samples(i.schema)
        if i.position == openapi.ParameterPosition.PATH:
            options.append(PathParameterOption(
                key=i.name,
                values=values,
            ))
        elif i.position == openapi.ParameterPosition.QUERY:
            options.append(QueryParameterOption(
                key=i.name,
                values=values,
            ))
        else:
            raise Exception(
                "Parameter position {} not implemented".format(i.position))

    if operation.request_body and operation.request_body.schema:
        options.append(JsonBodyParameterOption(
            generate_valid_samples(operation.request_body.schema)
        ))

    variables = extract_variables(operation, response)

    all_params: List[RequestParams] = []

    if options:
        num_test_cases = max([len(i.values) for i in options])
        for i in range(num_test_cases):
            params = RequestParams()
            for option in options:
                value = option.values[i % len(option.values)]
                if value != RequestParams.Discard:
                    option.inject(params, value)

            req = params.to_request(path, operation.method)
            if response.schema is not None:
                res = runconf.Response(
                    code=response.code,
                    content=json.dumps(response.schema),
                    match=runconf.MatchType.JSON_SCHEMA,
                    variables=variables
                )
            else:
                res = runconf.Response(
                    code=response.code,
                    content='',
                    match=runconf.MatchType.STATUS_CODE_ONLY,
                    variables=variables
                )
            test_cases.append(runconf.TestCase(req, res))
            all_params.append(params)
    else:
        params = RequestParams()
        req = params.to_request(path, operation.method)
        res = runconf.Response(
            code=response.code,
            content=json.dumps(response.schema),
            match=runconf.MatchType.JSON_SCHEMA,
            variables=variables,
        )
        test_cases.append(runconf.TestCase(req, res))
        all_params.append(params)

    # We need these for negative test case generation
    return all_params


def generate_negative_tests(test_cases: List[runconf.TestCase],  positive_params: List[RequestParams], path: str, operation: openapi.Operation, response: openapi.Response) -> runconf.TestCase:

    if not positive_params:
        raise Exception("Need positive params as basis for negative tests")

    options: List[ParameterOptions] = []
    for i in operation.parameters:
        values = generate_invalid_samples(i.schema)
        if i.required:
            values += [RequestParams.Discard]
        if i.position == openapi.ParameterPosition.PATH:
            options.append(PathParameterOption(
                key=i.name,
                values=values,
            ))
        elif i.position == openapi.ParameterPosition.QUERY:
            options.append(QueryParameterOption(
                key=i.name,
                values=values,
            ))
        else:
            raise Exception(
                "Parameter position {} not implemented".format(i.position))

    if operation.request_body:
        options.append(JsonBodyParameterOption(
            generate_invalid_samples(operation.request_body.schema)
        ))

    positive_params_idx = 0
    for option in options:
        for value in option.values:
            params = positive_params[positive_params_idx]
            if value != RequestParams.Discard:
                option.inject(params, value)
            positive_params_idx = (
                positive_params_idx + 1) % len(positive_params)
            req = params.to_request(path, operation.method)
            res = runconf.Response(
                code=response.code,
                content=json.dumps(response.schema),
                match=runconf.MatchType.JSON_SCHEMA,
                variables={},
            )
            test_cases.append(runconf.TestCase(req, res))


def generate_tests(test_cases: List[runconf.TestCase], path: str, operation: openapi.Operation) -> runconf.TestCase:
    # print("Generating tests for {} {}".format(operation.method, path))
    positive_response = None
    negative_response = None
    for response in operation.responses:
        if response.code >= 200 and response.code < 300:
            if positive_response:
                # print("Ignoring multiple positives for " + path)
                continue
            positive_response = response
        elif response.code >= 400 and response.code < 500:
            if negative_response:
                # print("Ignoring multiple negatives for " + path)
                continue
            negative_response = response
    if not positive_response:
        raise Exception("Must have a positive response")
    positive_params = generate_positive_tests(
        test_cases, path, operation, positive_response)
    if not negative_response:
        # print("No negative response given for {} {}, guessing one".format(operation.method, path))
        negative_response = openapi.Response(
            code=400,
            schema={},
            links=[]
        )
    generate_negative_tests(test_cases, positive_params,
                            path, operation, negative_response)


def has_all_params(operation: openapi.Operation, already_tested: Set[str]) -> bool:
    for param in operation.parameters:
        if param.source_link:
            if param.source_link.source_operation.operation_id not in already_tested:
                return False
    return True


def get_next(api: openapi.OpenApi, already_tested: Set[str], tag_filter: Set[str]) -> Tuple[openapi.Path, openapi.Operation]:

    def find(delete_only: bool):
        it = reversed(api.paths) if delete_only else api.paths
        for path in it:
            for operation in path.operations:
                if (operation.method == 'delete') != delete_only:
                    continue
                if not (operation.tags & tag_filter):
                    continue
                if operation.operation_id in already_tested:
                    continue
                if has_all_params(operation, already_tested):
                    return path, operation

    result = find(False)
    if result:
        return result
    result = find(True)
    if result:
        return result
    raise Exception("No more operations whose parameters are available. Maybe you have a cyclic dependency within your links?")


def generate(api: openapi.OpenApi, tag_filter=Set[str]):
    test_cases: List[runconf.TestCase] = []
    num_ops = 0
    for path in api.paths:
        for op in path.operations:
            if op.tags & tag_filter:
                num_ops += 1
    already_tested: Set[str] = set()
    while len(already_tested) != num_ops:
        next_path, next_operation = get_next(api, already_tested, tag_filter)
        already_tested.add(next_operation.operation_id)
        generate_tests(test_cases, next_path.path, next_operation)
    return runconf.RunConfig(
        components=api.components,
        test_cases=test_cases,
    )
