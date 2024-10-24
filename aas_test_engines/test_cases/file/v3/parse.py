from .adapter import Adapter, AdapterException

from dataclasses import dataclass, fields, field, is_dataclass
from typing import List, Dict, Optional, Tuple, Union, ForwardRef, Pattern, Callable
from aas_test_engines.result import AasTestResult, Level
from enum import Enum
import re


class CheckConstraintException(Exception):
    pass


INVALID = object()


def to_lower_camel_case(snake_str):
    camel_string = "".join(x.capitalize() for x in snake_str.lower().split("_"))
    return snake_str[0].lower() + camel_string[1:]


def unwrap_optional(cls) -> Tuple[bool, type]:
    try:
        origin = cls.__origin__
    except AttributeError:
        return True, cls
    if origin is not Union:
        return True, cls
    # We only support Optional aka. Union[x, NoneType]
    assert len(cls.__args__) == 2 and cls.__args__[1] is type(None)
    return False, cls.__args__[0]


def abstract(cls):
    # Prefix with cls to apply only to base class
    setattr(cls, f'_{cls}_abstract', True)
    return cls


def isabstract(cls):
    return hasattr(cls, f'_{cls}_abstract')


def requires_model_type(cls):
    setattr(cls, f'_requires_model_type', True)
    return cls


def has_requires_model_type(cls):
    return hasattr(cls, f'_requires_model_type')


def collect_subclasses(cls, result: Dict[str, type]):
    if not isabstract(cls):
        result[cls.__name__] = cls
    for i in cls.__subclasses__():
        collect_subclasses(i, result)


class StringFormattedValue:
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[Pattern] = None

    def __init__(self, raw_value: str):
        self.raw_value = raw_value
        if self.min_length is not None:
            if len(raw_value) < self.min_length:
                raise ValueError("String is too short")
        if self.max_length is not None:
            if len(raw_value) > self.max_length:
                raise ValueError("String is too long")

        # Constraint AASd-130: An attribute with data type "string" shall be restricted to the characters as defined in
        # XML Schema 1.0, i.e. the string shall consist of these characters only: ^[\x09\x0A\x0D\x20-\uD7FF\uE000-
        # \uFFFD\u00010000-\u0010FFFF]*$.
        if re.fullmatch(r"[\x09\x0a\x0d\x20-\ud7ff\ue000-\ufffd\U00010000-\U0010ffff]*", raw_value) is None:
            raise ValueError("String is not XML serializable")

        if self.pattern:
            if re.fullmatch(self.pattern, raw_value) is None:
                raise ValueError("String does not match pattern")

    def __eq__(self, other: "StringFormattedValue") -> bool:
        return self.raw_value == other.raw_value

    def __str__(self) -> str:
        return f"*{self.raw_value}"


def parse_string_formatted_value(cls, value: Adapter, result: AasTestResult) -> StringFormattedValue:
    try:
        return cls(value.as_string())
    except (AdapterException, ValueError) as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
    return None


def parse_list(item_cls, value: Adapter, result: AasTestResult) -> list:
    try:
        items = value.as_list()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
        return INVALID
    return [parse(item_cls, i, result) for i in items]


def parse_bool(value: Adapter, result: AasTestResult) -> bool:
    try:
        return value.as_bool()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
        return INVALID


def parse_string(value: Adapter, result: AasTestResult) -> str:
    try:
        return value.as_string()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
        return INVALID


def parse_enum(cls, value: Adapter, result: AasTestResult):
    try:
        str_val = value.as_string()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
        return INVALID
    try:
        return cls(str_val)
    except ValueError as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
    return INVALID


def parse_abstract_object(cls, adapter: Adapter, result: AasTestResult):
    try:
        discriminator = adapter.get_model_type()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {adapter.path}", level=Level.ERROR))
        return INVALID
    subclasses = {}
    collect_subclasses(cls, subclasses)
    try:
        cls = subclasses[discriminator]
    except KeyError:
        result.append(AasTestResult(f"Invalid model type {discriminator} @ {adapter.path}", level=Level.ERROR))
        return INVALID
    return parse_concrete_object(cls, adapter, result)


def parse_concrete_object(cls, adapter: Adapter, result: AasTestResult):
    try:
        obj = adapter.as_object()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {adapter.path}", level=Level.ERROR))
        return INVALID
    if has_requires_model_type(cls):
        try:
            discriminator = adapter.get_model_type()
            if discriminator != cls.__name__:
                result.append(AasTestResult(f"Wrong model type @ {adapter.path}", level=Level.ERROR))
        except AdapterException as e:
            result.append(AasTestResult(f"Model typ missing @ {adapter.path}", level=Level.ERROR))

    args = {}
    for field in fields(cls):
        field_name = to_lower_camel_case(field.name)
        required, field_type = unwrap_optional(field.type)
        try:
            obj_value = obj[field_name]
        except KeyError:
            if required:
                result.append(AasTestResult(f"Missing attribute {field_name}", level=Level.ERROR))
            args[field.name] = None
            continue
        args[field.name] = parse(field_type, obj_value, result)
    return cls(**args)


def parse(cls, obj_value: Adapter, result: AasTestResult):
    # Unwrap a forward reference
    if isinstance(cls, ForwardRef):
        # TODO: this is a hack to get our only ForwardRef["Reference"] into scope
        from .model import Reference
        try:
            cls = cls._evaluate(globals(), locals(), frozenset())
        except TypeError:
            # Python < 3.9
            cls = cls._evaluate(globals(), locals())

    origin = getattr(cls, '__origin__', None)
    if origin:
        if origin is list:
            item_type = cls.__args__[0]
            return parse_list(item_type, obj_value, result)
    else:
        if is_dataclass(cls):
            if isabstract(cls):
                return parse_abstract_object(cls, obj_value, result)
            else:
                return parse_concrete_object(cls, obj_value, result)
        elif cls is bool:
            return parse_bool(obj_value, result)
        elif cls is str:
            return parse_string(obj_value, result)
        elif isinstance(cls, Enum.__class__):
            return parse_enum(cls, obj_value, result)
        elif isinstance(cls, StringFormattedValue.__class__):
            return parse_string_formatted_value(cls, obj_value, result)
    print(origin)
    print(getattr(cls, '__args__', None))
    print(obj_value)
    print(cls)
    raise NotImplementedError()


def check_constraints(obj, result: AasTestResult):
    if not is_dataclass(obj):
        return
    fns = [getattr(obj, i) for i in dir(obj) if i.startswith('check_')]
    for fn in fns:
        try:
            fn()
        except CheckConstraintException as e:
            result.append(AasTestResult(f"{e}", level=Level.ERROR))
    for field in fields(obj):
        value = getattr(obj, field.name)
        if isinstance(value, list):
            for i in value:
                check_constraints(i, result)
        else:
            check_constraints(value, result)
