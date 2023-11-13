#! /usr/bin/env python3

from dataclasses import dataclass
from .runconf import RunConfig, TestCase, Response, MatchType
import json
from typing import Dict, Optional, Generator
from string import Template
from aas_test_engines.result import AasTestResult, Level

from .runtime_expression import RuntimeExpressionException

import requests
import jsonschema
import base64

from aas_test_engines.exception import AasTestToolsException


def _check_server(server: str) -> AasTestResult:
    result = AasTestResult(f'Check {server}')
    try:
        requests.get(server)
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
        schema['components'] = config.components
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            result.append(AasTestResult(f"Invalid response: {e.args[0]}", '', Level.ERROR))
    elif expected.match == MatchType.STATUS_CODE_ONLY:
        pass
    else:
        raise AasTestToolsException(f"Unknown match type {expected.match}")


class TemplateWithNumericIds(Template):
    idpattern = r'(?a:[a-z0-9]+?(_base64))'
    delimiter = '!'


def inject_variables(value: str, variables: Dict[str, str]) -> str:
    return TemplateWithNumericIds(value).substitute(variables)


def _run_test_case(test_case: TestCase, server: str, dry: bool, variables: Dict[str, str], config: RunConfig) -> AasTestResult:
    url = server + test_case.request.path
    method = test_case.request.method

    try:
        url = inject_variables(url, variables)
        data = inject_variables(test_case.request.body, variables)
    except KeyError as e:
        m = "Failed to substitute variable {}, considering test case as failed".format(e.args[0])
        return AasTestResult(m, '', Level.ERROR)

    result = AasTestResult("{} {}".format(test_case.request.method.upper(), url))

    if dry:
        for name in test_case.response.variables.keys():
            variables[name] = 'dummy_value'
        result.append(AasTestResult('Skipped', '', Level.WARNING))
        return result
    else:
        response = requests.request(
            method=method,
            url=url,
            data=data,
            headers=test_case.request.headers
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

def run(config: RunConfig, server: str, dry: bool = False) -> Generator[AasTestResult, None, None]:
    if not dry:
        result = _check_server(server)
        yield result
        if not result.ok():
            return
    variables: Dict[str, str] = {}
    for test_case in config.test_cases:
        yield _run_test_case(test_case, server, dry, variables, config)
