#! /usr/bin/env python3

from dataclasses import dataclass
from .runconf import RunConfig, TestCase, Response, MatchType
import json
from typing import Dict, Optional
from string import Template

from .runtime_expression import RuntimeExpressionException

import requests
import jsonschema
import base64

def _check_server(server: str):
    try:
        requests.get(server)
        return True
    except requests.exceptions.RequestException as e:
        print('Failed to reach "{}": {}'.format(server, e))
        return False


def _check_response(test_case: TestCase, actual: requests.models.Response, data: Optional[dict], config: RunConfig) -> bool:
    expected = test_case.response
    if actual.status_code != expected.code:
        print("  invalid status code: expected {}, got {}".format(
            expected.code, actual.status_code))
        return False

    if expected.match == MatchType.JSON_SCHEMA:
        schema = json.loads(test_case.response.content)
        schema['components'] = config.components
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.exceptions.ValidationError as e:
            print("  response does not match json schema:")
            print("  {}".format(e.args[0]))
            return False
    elif expected.match == MatchType.STATUS_CODE_ONLY:
        pass
    else:
        print("Unknown match type {}".format(expected.match))
        return False

    return True


class TemplateWithNumericIds(Template):
    idpattern = r'(?a:[a-z0-9]+?(_base64))'


def inject_variables(value: str, variables: Dict[str, str]) -> str:
    return TemplateWithNumericIds(value).substitute(variables)


@dataclass
class TestResult:
    passed: bool


def _run_test_case(test_case: TestCase, server: str, dry: bool, variables: Dict[str, str], config: RunConfig) -> TestResult:
    url = server + test_case.request.path
    try:
        url = inject_variables(url, variables)
        data = inject_variables(test_case.request.body, variables)
    except KeyError as e:
        print("Failed to substitute variable {}, considering test cases as failed".format(
            e.args[0]))
        return TestResult(passed=False)
    method = test_case.request.method
    print("{} {}".format(test_case.request.method.upper(), url))
    if dry:
        for name in test_case.response.variables.keys():
            variables[name] = 'dummy_value'
        print(" --> Skipped")
        return TestResult(passed=True)
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
        ok = _check_response(test_case, response, data, config)
        for name, expression in test_case.response.variables.items():
            try:
                # TODO: str() will fail for non primitive types
                value = str(expression.lookup(url, method, response.status_code, data))
                variables[name] = value
                # TODO: we actually do not need ALL variables as encoded b64, later
                variables[name+'_base64'] = base64.urlsafe_b64encode(value.encode()).decode().replace('=', '')

            except RuntimeExpressionException:
                print("  Failed to fetch variable {}, subsequent test cases might fail".format(name))
        if ok:
            print("  -> Passed")
        else:
            print("  -> Failed")
            print("--- Additional info:")
            print(response.content)
            print("---")
        return TestResult(passed=ok)


def run(config: RunConfig, server: str, dry: bool = False) -> float:
    if not dry:
        _check_server(server)
    variables: Dict[str, str] = {}
    num_passed = 0
    for test_case in config.test_cases:
        result = _run_test_case(test_case, server, dry, variables, config)
        if result.passed:
            num_passed += 1
    return num_passed / len(config.test_cases)
