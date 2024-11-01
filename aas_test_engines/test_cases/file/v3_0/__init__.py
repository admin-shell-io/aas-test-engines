from typing import Tuple, Optional
from aas_test_engines.result import AasTestResult

from .parse import parse_concrete_object, check_constraints
from .adapter import JsonAdapter, XmlAdapter, AdapterPath
from .model import Environment

def _check_constraints(result_root: AasTestResult, env: Environment):
    if result_root.ok():
        result_constraints = AasTestResult("Check constraints")
        check_constraints(env, result_constraints)
        result_root.append(result_constraints)

def json_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    result_root = AasTestResult("Check")
    result_meta_model = AasTestResult("Check meta model")
    env: Environment = parse_concrete_object(Environment, JsonAdapter(value, AdapterPath()), result_meta_model)
    result_root.append(result_meta_model)
    _check_constraints(result_root, env)
    return result_root, env


def xml_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    result_root = AasTestResult("Check")
    result_meta_model = AasTestResult("Check meta model")
    env: Environment = parse_concrete_object(Environment, XmlAdapter(value, AdapterPath()), result_meta_model)
    result_root.append(result_meta_model)
    _check_constraints(result_root, env)
    return result_root, env
