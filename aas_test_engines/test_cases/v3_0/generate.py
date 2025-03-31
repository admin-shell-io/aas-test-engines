from typing import List, Dict
from aas_test_engines.reflect import (
    FunctionType,
    NumberType,
    StringType,
    StringFormattedValueType,
    EnumType,
    BoolType,
    ClassType,
)
from aas_test_engines.result import start, write
from .interfaces.shared import AssetId
import base64


class DummyEnumValue:
    """
    Behaves like a enum value but is none :)
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


_INVALID_BASE64URL = "invalid-base64url====="
try:
    base64.urlsafe_b64decode(_INVALID_BASE64URL)
    assert False, f"{_INVALID_BASE64URL} must not be base64-url decodable"
except ValueError:
    pass


def generate_invalid_values(arg: FunctionType.Argument) -> List[any]:
    if isinstance(arg.type, NumberType):
        if arg.name == "limit":
            return [-1]
    if isinstance(arg.type, StringType):
        return []
    if isinstance(arg.type, StringFormattedValueType):
        if arg.type.cls.base64:
            return [_INVALID_BASE64URL]
        else:
            return []
    if isinstance(arg.type, EnumType):
        length = max(len(i.value) for i in arg.type.cls) + 1
        return [DummyEnumValue("#" * length)]
    if isinstance(arg.type, BoolType):
        return ["invalid-bool"]
    if isinstance(arg.type, ClassType):
        if arg.type.cls is AssetId:
            return [_INVALID_BASE64URL]
        return []
    raise NotImplementedError(
        f"There is no generation implemented for:\n" + f"arg.type: {arg.type}\n" + f"arg.name: {arg.name}"
    )


def generate_calls(func: FunctionType, scope: str, valid_arguments: Dict[str, any]):
    for arg in func.args:
        for invalid_value in generate_invalid_values(arg):
            with start(f"Set {arg.name} = '{invalid_value}'"):
                args = {**valid_arguments, arg.name: invalid_value}
                try:
                    func.func(**args)
                except TypeError as e:
                    raise NotImplementedError(
                        f"Caught the following exception:\n"
                        + f"{e}\n"
                        + f"Have you set valid_arguments during setup() ?\n"
                        f"Scope: {scope}"
                    )
