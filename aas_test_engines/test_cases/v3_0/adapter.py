from typing import Dict, List, Optional
from xml.etree.ElementTree import Element


class AdapterPath:
    def __init__(self):
        self.elements = []

    def __add__(self, other):
        result = AdapterPath()
        result.elements = self.elements + [other]
        return result

    def __str__(self):
        return "/" + "/".join([str(i) for i in self.elements])


class AdapterException(Exception):
    pass


class Adapter:

    path: AdapterPath

    def as_object(self) -> Dict[str, "Adapter"]:
        raise NotImplementedError()

    def as_list(self, allow_empty: bool) -> List["Adapter"]:
        raise NotImplementedError()

    def as_string(self) -> str:
        raise NotImplementedError()

    def as_bool(self) -> bool:
        raise NotImplementedError()

    def get_model_type(self) -> str:
        raise NotImplementedError()


class JsonAdapter(Adapter):

    def __init__(self, value: any, path: AdapterPath):
        self.value = value
        self.path = path

    def as_object(self) -> Dict[str, Adapter]:
        if not isinstance(self.value, dict):
            raise AdapterException(f"Cannot convert {self.value} to object")
        return {k: JsonAdapter(v, self.path + k) for k, v in self.value.items() if k != "modelType"}

    def as_list(self, allow_empty: bool) -> List["Adapter"]:
        if not isinstance(self.value, list):
            raise AdapterException(f"Cannot convert {self.value} to list")
        if len(self.value) == 0 and not allow_empty:
            raise AdapterException(f"Empty array not allowed")
        return [JsonAdapter(val, self.path + idx) for idx, val in enumerate(self.value)]

    def as_string(self):
        if not isinstance(self.value, str):
            raise AdapterException(f"Cannot convert {self.value} to string")
        return self.value

    def as_bool(self):
        if not isinstance(self.value, bool):
            raise AdapterException(f"Cannot convert {self.value} to bool")
        return self.value

    def get_model_type(self) -> str:
        if not isinstance(self.value, dict):
            raise AdapterException(f"Expected an object, got {self.value}")
        try:
            return self.value["modelType"]
        except KeyError:
            raise AdapterException(f"Missing 'modelType'")

    def __str__(self):
        return str(self.value)


_expected_namespace = "{https://admin-shell.io/aas/3/0}"


def _get_single_child(el: Element) -> Element:
    if len(el) != 1:
        raise AdapterException("DataSpecificationContent must have exactly one child")
    return el[0]


def _assert_no_children(el: Element):
    if next(iter(el), None):
        raise AdapterException("No child elements allowed")


def _assert_no_text(el: Element):
    if el.text is None:
        return
    if el.text.strip():
        raise AdapterException("No inline text allowed")


def _get_model_type(el: Element, expected_namespace: str):
    model_type = el.tag[len(expected_namespace) :]
    model_type = model_type[0].upper() + model_type[1:]
    return model_type


class XmlAdapter:

    def __init__(self, value: Element, path: AdapterPath):
        self.value = value
        self.path = path

    def as_object(self) -> Dict[str, "Adapter"]:
        if not self.value.tag.startswith(_expected_namespace):
            raise AdapterException(f"invalid namespace, got '{self.value.tag}'")
        _assert_no_text(self.value)

        # Special handling for data specification content
        if self.value.tag.endswith("dataSpecificationContent"):
            data = _get_single_child(self.value)
        else:
            data = self.value

        result = {}
        for child in data:
            if not child.tag.startswith(_expected_namespace):
                raise AdapterException(f"invalid namespace, got {child.tag}")
            tag = child.tag[len(_expected_namespace) :]
            if self.get_model_type() == "OperationVariable" and tag == "value":
                result[tag] = XmlAdapter(_get_single_child(child), self.path + tag)
            else:
                result[tag] = XmlAdapter(child, self.path + tag)
        return result

    def as_list(self, allow_empty: bool) -> List["Adapter"]:
        result = []
        for idx, child in enumerate(self.value):
            result.append(XmlAdapter(child, self.path + idx))
        if not result and not allow_empty:
            raise AdapterException("Empty list not allowed")
        return result

    def as_string(self) -> str:
        _assert_no_children(self.value)
        return self.value.text or ""

    def as_bool(self) -> bool:
        _assert_no_children(self.value)
        return self.value.text == "true"

    def get_model_type(self) -> str:
        # Special handling for data specification content
        if self.value.tag.endswith("dataSpecificationContent"):
            data = _get_single_child(self.value)
        else:
            data = self.value
        return _get_model_type(data, _expected_namespace)
