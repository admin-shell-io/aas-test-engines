from .adapter import Adapter, AdapterException
from aas_test_engines.reflect import (
    TypeBase,
    ListType,
    ClassType,
    StringFormattedValueType,
    EnumType,
    StringType,
    BoolType,
    AnyType,
)

from dataclasses import dataclass, fields, field, is_dataclass
from typing import List, Dict, Optional, Tuple, Union, ForwardRef, Pattern, Callable
from aas_test_engines.result import AasTestResult, Level
from enum import Enum
import re
from .adapter import AdapterPath, JsonAdapter, XmlAdapter
from aas_test_engines.reflect import StringFormattedValue


class CheckConstraintException(Exception):
    pass


INVALID = object()


def to_lower_camel_case(snake_str):
    camel_string = "".join(x.capitalize() for x in snake_str.lower().split("_"))
    return snake_str[0].lower() + camel_string[1:]


def requires_model_type(cls):
    setattr(cls, f"_requires_model_type", True)
    return cls


def has_requires_model_type(cls):
    return hasattr(cls, f"_requires_model_type")


def parse_string_formatted_value(
    cls: StringFormattedValueType, value: Adapter, result: AasTestResult
) -> StringFormattedValue:
    try:
        return cls.construct(value.as_string())
    except (AdapterException, ValueError) as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
    return INVALID


def parse_list(item_cls: ListType, value: Adapter, result: AasTestResult, allow_empty: bool) -> list:
    try:
        items = value.as_list(allow_empty)
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
        return INVALID
    return [parse(item_cls.item_type, i, result) for i in items]


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


def parse_enum(cls: EnumType, value: Adapter, result: AasTestResult):
    try:
        str_val = value.as_string()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
        return INVALID
    try:
        return cls.construct(str_val)
    except ValueError as e:
        result.append(AasTestResult(f"{e} @ {value.path}", level=Level.ERROR))
    return INVALID


def parse_abstract_object(cls: ClassType, adapter: Adapter, result: AasTestResult):
    try:
        discriminator = adapter.get_model_type()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {adapter.path}", level=Level.ERROR))
        return INVALID
    subclass = None
    for subclass in cls.subclasses:
        if subclass.cls.__name__ == discriminator:
            return parse_concrete_object(subclass, adapter, result)
    result.append(
        AasTestResult(
            f"Invalid model type {discriminator} @ {adapter.path}",
            level=Level.ERROR,
        )
    )
    return INVALID


def parse_concrete_object(cls: ClassType, adapter: Adapter, result: AasTestResult):
    try:
        obj = adapter.as_object()
    except AdapterException as e:
        result.append(AasTestResult(f"{e} @ {adapter.path}", level=Level.ERROR))
        return INVALID
    if has_requires_model_type(cls.cls):
        try:
            discriminator = adapter.get_model_type()
            if discriminator != cls.cls.__name__:
                result.append(AasTestResult(f"Wrong model type @ {adapter.path}", level=Level.ERROR))
        except AdapterException as e:
            result.append(AasTestResult(f"Model typ missing @ {adapter.path}", level=Level.ERROR))

    args = {}
    all_fields = set()
    for field in cls.attrs:
        field_name = field.force_name or to_lower_camel_case(field.name)
        all_fields.add(field_name)
        try:
            obj_value = obj[field_name]
        except KeyError:
            if field.required:
                result.append(
                    AasTestResult(
                        f"Missing attribute {field_name} @ {adapter.path}",
                        level=Level.ERROR,
                    )
                )
                args[field.name] = INVALID
            else:
                args[field.name] = None
            continue
        args[field.name] = parse(field.type, obj_value, result)

    # Check unknown additional attributes
    for key in obj.keys():
        if key not in all_fields:
            result.append(
                AasTestResult(
                    f"Unknown additional attribute {key} @ {adapter.path}",
                    level=Level.ERROR,
                )
            )

    return cls.construct(args)


def parse(cls: TypeBase, obj_value: Adapter, result: AasTestResult):
    if isinstance(cls, ListType):
        return parse_list(cls, obj_value, result, cls.allow_empty)
    elif isinstance(cls, ClassType):
        if cls.is_abstract():
            return parse_abstract_object(cls, obj_value, result)
        else:
            obj = parse_concrete_object(cls, obj_value, result)
            post_parse = getattr(obj, "post_parse", None)
            if post_parse and result.ok():
                post_parse()
            return obj
    elif isinstance(cls, BoolType):
        return parse_bool(obj_value, result)
    elif isinstance(cls, StringType):
        return parse_string(obj_value, result)
    elif isinstance(cls, AnyType):
        return obj_value
    elif isinstance(cls, EnumType):
        return parse_enum(cls, obj_value, result)
    elif isinstance(cls, StringFormattedValueType):
        return parse_string_formatted_value(cls, obj_value, result)
    raise NotImplementedError(
        f"There is no parsing implemented for:\n"
        f"  args:      {getattr(cls, '__args__', None)}\n"
        f"  obj_value: {obj_value}\n"
        f"  cls:       {cls}\n"
    )


def check_constraints(obj, result: AasTestResult, path: AdapterPath = AdapterPath()):
    if not is_dataclass(obj):
        return
    fns = [getattr(obj, i) for i in dir(obj) if i.startswith("check_")]
    for fn in fns:
        try:
            fn()
        except CheckConstraintException as e:
            result.append(AasTestResult(f"{e} @ {path}", level=Level.ERROR))
    for field in fields(obj):
        value = getattr(obj, field.name)
        if isinstance(value, list):
            for idx, i in enumerate(value):
                check_constraints(i, result, path + field.name + idx)
        else:
            check_constraints(value, result, path + field.name)


def _parse_and_check(cls, adapter: Adapter) -> Tuple[object, AasTestResult]:
    result_root = AasTestResult("Check")
    result_meta_model = AasTestResult("Check meta model")
    env = parse(cls, adapter, result_meta_model)
    result_root.append(result_meta_model)
    if result_root.ok():
        result_constraints = AasTestResult("Check constraints")
        check_constraints(env, result_constraints)
        result_root.append(result_constraints)
    else:
        result_root.append(AasTestResult("Skipped checking of constraints", Level.WARNING))
    return result_root, env


def parse_and_check_json(t: TypeBase, value: any) -> Tuple[AasTestResult, object]:
    return _parse_and_check(t, JsonAdapter(value, AdapterPath()))


def parse_and_check_xml(t: TypeBase, value: any) -> Tuple[AasTestResult, object]:
    return _parse_and_check(t, XmlAdapter(value, AdapterPath()))
