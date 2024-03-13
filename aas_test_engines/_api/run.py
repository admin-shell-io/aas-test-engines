#! /usr/bin/env python3

from dataclasses import dataclass
from .runconf import RunConfig, TestCase, Response, MatchType
import json
from typing import Dict, Optional, Generator
from string import Template
from aas_test_engines.result import AasTestResult, Level

from .runtime_expression import RuntimeExpressionException

import requests
import base64

from aas_test_engines.exception import AasTestToolsException
from json_schema_tool import parse_schema
from json_schema_tool.schema import ParseConfig
from aas_test_engines.file import _map_error

from dataclasses import dataclass


@dataclass
class ExecConf:
    server: str = ''
    dry: bool = False
    verify: bool = True


def _check_server(exec_conf: ExecConf) -> AasTestResult:
    result = AasTestResult(f'Check {exec_conf.server}')
    try:
        requests.get(exec_conf.server, verify=exec_conf.verify)
        result.append(AasTestResult('OK', '', Level.INFO))
    except requests.exceptions.RequestException as e:
        result.append(AasTestResult('Failed to reach: {}'.format(e), '', Level.ERROR))
    return result


def _check_response(test_case: TestCase, actual: requests.models.Response, data: Optional[dict], config: RunConfig, result: AasTestResult):
    expected = test_case.response
    if actual.status_code == expected.code:
        result.append(AasTestResult(f'Got status code {expected.code}'))
    else:
        result.append(AasTestResult(f"invalid status code: expected {expected.code}, got {actual.status_code}", '', Level.ERROR))

    if expected.match == MatchType.JSON_SCHEMA:
        schema = json.loads(test_case.response.content)
        if schema is None:
            return
        schema['components'] = config.components
        schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
        validator = parse_schema(schema, ParseConfig(raise_on_unknown_format=False))
        error = validator.validate(data)
        _map_error(result, error)
    elif expected.match == MatchType.STATUS_CODE_ONLY:
        pass
    else:
        raise AasTestToolsException(f"Unknown match type {expected.match}")


class TemplateWithNumericIds(Template):
    idpattern = r'(?a:[a-z0-9]+?(_base64))'
    delimiter = '!'


def inject_variables(value: str, variables: Dict[str, str]) -> str:
    return TemplateWithNumericIds(value).substitute(variables)


def _run_test_case(test_case: TestCase, exec_conf: ExecConf, variables: Dict[str, str], config: RunConfig) -> AasTestResult:
    url = exec_conf.server + test_case.request.path
    method = test_case.request.method

    try:
        url = inject_variables(url, variables)
        data = inject_variables(test_case.request.body, variables)
    except KeyError as e:
        m = "Failed to substitute variable {}, considering test case as failed".format(e.args[0])
        return AasTestResult(m, '', Level.ERROR)

    result = AasTestResult("{} {}".format(test_case.request.method.upper(), url))

    if exec_conf.dry:
        for name in test_case.response.variables.keys():
            variables[name] = 'dummy_value'
        result.append(AasTestResult('Skipped', '', Level.WARNING))
        return result
    else:
        response = requests.request(
            method=method,
            url=url,
            data=data,
            headers=test_case.request.headers,
            verify=exec_conf.verify,
        )
        try:
            data = response.json()
        except:
            data = None

        _check_response(test_case, response, data, config, result)
        for name, expression in test_case.response.variables.items():
            try:
                # TODO: str() will fail for non primitive types
                value = str(expression.lookup(url, method, response.status_code, data))
                variables[name] = value
                # TODO: we actually do not need ALL variables as encoded b64, later
                variables[name+'_base64'] = base64.urlsafe_b64encode(value.encode()).decode().replace('=', '')
            except RuntimeExpressionException:
                m = f"Failed to fetch variable {name}, subsequent test cases might fail"
                result.append(AasTestResult(m, '', Level.WARNING))

        # print("--- Additional info:")
        # print(response.content)
        # print("---")
    return result


def run(config: RunConfig, exec_conf: ExecConf) -> Generator[AasTestResult, None, None]:
    if not exec_conf.dry:
        result = _check_server(exec_conf)
        yield result
        if not result.ok():
            return
    variables: Dict[str, str] = {}
    for test_case in config.test_cases:
        yield _run_test_case(test_case, exec_conf, variables, config)
