from .model import (
    Submodel,
    SubmodelElement,
    Property,
    DataTypeDefXsd,
    MultiLanguageProperty,
    SubmodelElementCollection,
)
from .adapter import AdapterPath

from aas_test_engines.result import AasTestResult, Level
from typing import List, Dict, Tuple, Union
from collections import defaultdict
from dataclasses import is_dataclass, fields
from enum import Enum
import datetime

INVALID = object()
LangString = Dict[str, str]


def to_camel_case(s: str) -> str:
    return "".join(s.title().split("_"))


def _unwrap(cls) -> Tuple[int, int, type]:
    try:
        origin = cls.__origin__
    except AttributeError:
        # neither List nor Optional
        return 1, 1, cls
    # List[T]
    if origin is list:
        return 1, float("inf"), cls.__args__[0]
    # Dict[T] aka LangString
    if origin is dict:
        return 1, 1, LangString

    # We only support Optional aka. Union[x, NoneType]
    assert origin is Union, origin
    assert len(cls.__args__) == 2 and cls.__args__[1] is type(None)
    cls = cls.__args__[0]
    try:
        origin = cls.__origin__
    except AttributeError:
        # Optional[T]
        return 0, 1, cls
    # Optional[Dict[T]] aka Optional[LangString]
    if origin is dict:
        return 0, 1, LangString
    assert origin is list
    # Optional[List[T]]
    return 0, float("inf"), cls.__args__[0]


def _parse_string(root_result: AasTestResult, element: SubmodelElement, path: AdapterPath) -> str:
    if not isinstance(element, Property):
        root_result.append(
            AasTestResult(
                f"Cannot convert to string: must be a Property @ {path}",
                level=Level.ERROR,
            )
        )
        return
    if not element.value:
        root_result.append(AasTestResult(f"Cannot convert to string: no value @ {path}", level=Level.ERROR))
        return
    if element.value_type != DataTypeDefXsd.string:
        root_result.append(
            AasTestResult(
                f"Cannot convert '{element.value}' to string: valueType must be xs:string @ {path}",
                level=Level.ERROR,
            )
        )
        return
    return element.value.raw_value


def _parse_date(root_result: AasTestResult, element: SubmodelElement, path: AdapterPath) -> str:
    if not isinstance(element, Property):
        root_result.append(
            AasTestResult(
                f"Cannot convert to date: must be a Property @ {path}",
                level=Level.ERROR,
            )
        )
        return
    if not element.value:
        root_result.append(AasTestResult(f"Cannot convert to date: no value @ {path}", level=Level.ERROR))
        return
    if element.value_type != DataTypeDefXsd.date:
        root_result.append(
            AasTestResult(
                f"Cannot convert '{element.value}' to date: valueType must be xs:date @ {path}",
                level=Level.ERROR,
            )
        )
        return
    return datetime.date.fromisoformat(element.value.raw_value)


def _parse_lang_string(root_result: AasTestResult, element: SubmodelElement, path: AdapterPath) -> LangString:
    if not isinstance(element, MultiLanguageProperty):
        root_result.append(
            AasTestResult(
                f"Cannot convert to lang string: not a MultiLanguageProperty @ {path}",
                Level.ERROR,
            )
        )
        return
    if not element.value:
        root_result.append(AasTestResult(f"Cannot convert to lang string: no value @ {path}", Level.ERROR))
        return
    result: LangString = {}
    for i in element.value:
        result[i.language] = i.text
    return result


def _parse_element_collection(
    root_result: AasTestResult,
    cls,
    collection: SubmodelElementCollection,
    path: AdapterPath,
):
    if collection.value is None:
        root_result.append(AasTestResult(f"No elements @ {path}", level=Level.ERROR))
        return INVALID
    return _parse_elements(root_result, cls, collection.value, path)


def _parse_elements(root_result: AasTestResult, cls, elements: List[SubmodelElement], path: AdapterPath):
    elements_by_semantic_id: Dict[str, List[SubmodelElement]] = defaultdict(list)
    for collection in elements:
        if collection.semantic_id:
            key = collection.semantic_id.keys[0].value.raw_value
            elements_by_semantic_id[key].append(collection)
    args = {}
    all_semantic_ids = set()
    for field in fields(cls):
        try:
            semantic_id = field.metadata["semantic_id"]
        except KeyError:
            raise Exception(f"Internal error: field {field.name} is missing metadata 'semantic_id'")
        if semantic_id in all_semantic_ids:
            raise Exception(f"Internal error: duplicate metadata semantic_id {semantic_id}")

        all_semantic_ids.add(semantic_id)

        min_card, max_card, field_type = _unwrap(field.type)
        sub_elements = elements_by_semantic_id[semantic_id]
        name = to_camel_case(field.name)
        if len(sub_elements) > max_card:
            root_result.append(
                AasTestResult(
                    f"Field {name}: found {len(sub_elements)} elements with semanticId {semantic_id}, but at most {max_card} allowed",
                    level=Level.ERROR,
                )
            )
            field_val = INVALID
        elif len(sub_elements) < min_card:
            root_result.append(
                AasTestResult(
                    f"Field {name}: found {len(sub_elements)} elements with semanticId {semantic_id}, but at least {min_card} required",
                    level=Level.ERROR,
                )
            )
            field_val = INVALID
        else:
            if len(sub_elements) == 0:
                field_val = None
            elif max_card == 1:
                field_val = _parse(field_type, sub_elements[0], root_result, path + name)
            else:  # i.e. list
                field_val = [
                    _parse(field_type, el, root_result, path + name + idx) for idx, el in enumerate(sub_elements)
                ]
        args[field.name] = field_val
    return cls(**args)


def _parse_enum(root_result: AasTestResult, cls, elements: List[SubmodelElement], path: AdapterPath):
    value = _parse_string(root_result, elements, path)
    if not root_result.ok():
        return INVALID
    try:
        return cls(value)
    except ValueError as e:
        root_result.append(AasTestResult(f"{e} @ {path}", level=Level.ERROR))
        return INVALID


def _parse(cls, element: SubmodelElement, root_result, path: AdapterPath):
    origin = getattr(cls, "__origin__", None)
    if origin:
        if origin is dict:
            return _parse_lang_string(root_result, element, path)
    else:
        if is_dataclass(cls):
            return _parse_element_collection(root_result, cls, element, path)
        elif cls is str:
            return _parse_string(root_result, element, path)
        elif cls is datetime.date:
            return _parse_date(root_result, element, path)
        elif isinstance(cls, Enum.__class__):
            return _parse_enum(root_result, cls, element, path)
    raise NotImplementedError(
        f"There is no parsing implemented for:\n"
        f"  origin:    {origin}\n"
        f"  args:      {getattr(cls, '__args__', None)}\n"
        f"  cls:       {cls}\n"
    )


def parse_submodel(root_result: AasTestResult, cls, submodel: Submodel):
    return _parse_elements(root_result, cls, submodel.submodel_elements, AdapterPath())
