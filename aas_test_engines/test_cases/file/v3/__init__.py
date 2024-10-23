from typing import Tuple, Optional
from aas_test_engines.result import AasTestResult

from .parse import parse_concrete_object, check_constraints
from .adapter import JsonAdapter, AdapterPath
from .model import Environment


def json_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    result_root = AasTestResult("Check")
    result_meta_model = AasTestResult("Check meta model")
    env: Environment = parse_concrete_object(Environment, JsonAdapter(value, AdapterPath()), result_meta_model)
    result_root.append(result_meta_model)
    if result_meta_model.ok():
        result_constraints = AasTestResult("Check constraints")
        check_constraints(env, result_constraints)
        result_root.append(result_constraints)
    return result_root, env
