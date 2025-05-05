from typing import Tuple, Optional
from aas_test_engines.result import AasTestResult

from .parse import parse_and_check_json, parse_and_check_xml
from .model import Environment, symbol_table
from .submodel_templates import parse_submodel_templates


def json_to_obj(value: any, model_type: str) -> Tuple[AasTestResult, any]:
    reflection = symbol_table.lookup(model_type)
    result, env = parse_and_check_json(reflection, value)
    if result.ok():
        parse_submodel_templates(result, env)
    return result, env


def xml_to_obj(value: any, model_type: str) -> Tuple[AasTestResult, Optional[Environment]]:
    reflection = symbol_table.lookup(model_type)
    result, env = parse_and_check_xml(reflection, value)
    if result.ok():
        parse_submodel_templates(result, env)
    return result, env
