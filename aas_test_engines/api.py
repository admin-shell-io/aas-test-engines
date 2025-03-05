from typing import Dict, List, Tuple
from aas_test_engines.test_cases.v3_0.api import ExecConf
from aas_test_engines.test_cases.v3_0 import api as v3_0
from fences.core.util import ConfusionMatrix
from .result import AasTestResult
from .exception import AasTestToolsException

_DEFAULT_VERSION = "3.0"


def supported_versions() -> Dict[str, List[str]]:
    return {"3.0": v3_0.available_suites.keys()}


def latest_version():
    return _DEFAULT_VERSION


def execute_tests(conf: ExecConf, suite: str, version: str = _DEFAULT_VERSION) -> Tuple[AasTestResult, ConfusionMatrix]:
    if version != _DEFAULT_VERSION:
        raise AasTestToolsException(f"Unknown version {version}, must be one of {supported_versions()}")
    return v3_0.execute_tests(conf, suite)
