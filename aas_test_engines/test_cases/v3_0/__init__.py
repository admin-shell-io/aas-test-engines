from typing import Tuple, Optional
from aas_test_engines.result import AasTestResult

from .parse import parse_and_check_json, parse_and_check_xml
from .adapter import JsonAdapter, XmlAdapter, AdapterPath
from .model import Environment


def json_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    return parse_and_check_json(Environment, value)


def xml_to_env(value: any) -> Tuple[AasTestResult, Optional[Environment]]:
    return parse_and_check_xml(Environment, value)
