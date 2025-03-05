from typing import Tuple, Optional
from aas_test_engines.result import AasTestResult

from .parse import parse_and_check_json, parse_and_check_xml
from .model import Environment, r_environment
from .submodel_templates import parse_submodel_templates


def json_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    result, env = parse_and_check_json(r_environment, value)
    if result.ok():
        parse_submodel_templates(result, env)
    return result, env


def xml_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    result, env = parse_and_check_xml(r_environment, value)
    if result.ok():
        parse_submodel_templates(result, env)
    return result, env
