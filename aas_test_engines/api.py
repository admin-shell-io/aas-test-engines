from typing import Dict, Set, Generator
from .exception import AasTestToolsException
from .result import AasTestResult

from ._api import openapi
from ._api import generate
from ._api import runconf
from ._api import run

import os
from yaml import safe_load


class AasSpec:

    def __init__(self, api: openapi.OpenApi, tags: Set[str]) -> None:
        self.api = api
        self.tags = tags


def _find_specs() -> Dict[str, AasSpec]:
    result = {}
    script_dir = os.path.dirname(os.path.realpath(__file__))
    data_dir = os.path.join(script_dir, 'data', 'api')
    for i in os.listdir(data_dir):
        path = os.path.join(data_dir, i)
        if not i.endswith('.yml'):
            continue
        spec = safe_load(open(path, "rb"))
        api = openapi.OpenApi.from_dict(spec)
        suites = set()
        for path in api.paths:
            for operation in path.operations:
                suites.update(operation.tags)
        result[i[:-4]] = AasSpec(api, suites)
    return result


_specs = _find_specs()

_DEFAULT_VERSION = '3.0'


def _get_spec(version: str) -> AasSpec:
    try:
        return _specs[version]
    except KeyError:
        raise AasTestToolsException(
            f"Unknown version {version}, must be one of {supported_versions()}")


def generate_tests(version: str = _DEFAULT_VERSION, suites: Set[str] = None) -> runconf.RunConfig:
    spec = _get_spec(version)
    if suites is None:
        suites = spec.tags
    if not spec.tags.issuperset(suites):
        raise AasTestToolsException(f"Unknown suites {suites}, must be in {spec.tags}")
    conf = generate.generate(spec.api, suites)
    return conf


def execute_tests(conf: runconf.RunConfig, server: str, dry: bool = False) -> Generator[AasTestResult, None, None]:
    yield from run.run(conf, server, dry)


def supported_versions():
    return {ver: spec.tags for ver, spec in _specs.items()}


def latest_version():
    return _DEFAULT_VERSION
