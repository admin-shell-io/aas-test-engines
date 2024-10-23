from typing import Dict, List

class AdapterPath:
    def __init__(self):
        self.elements = []

    def __add__(self, other):
        result = AdapterPath()
        result.elements = self.elements + [other]
        return result

    def __str__(self):
        return "/".join([str(i) for i in self.elements])


class AdapterException(Exception):
    pass


class Adapter:

    path: AdapterPath

    def as_object(self) -> Dict[str, "Adapter"]:
        raise NotImplementedError()

    def as_list(self) -> List["Adapter"]:
        raise NotImplementedError()

    def as_string(self) -> str:
        raise NotImplementedError()

    def as_bool(self) -> bool:
        raise NotImplementedError()

    def get_model_type(self) -> str:
        raise NotImplementedError()

    def path(self) -> AdapterPath:
        raise NotImplementedError()


class JsonAdapter(Adapter):

    def __init__(self, value: any, path: AdapterPath):
        self.value = value
        self.path = path

    def as_object(self) -> Dict[str, Adapter]:
        if not isinstance(self.value, dict):
            raise AdapterException(f"Cannot convert {self.value} to object")
        return {k: JsonAdapter(v, self.path + k) for k, v in self.value.items()}

    def as_list(self) -> List[Adapter]:
        if not isinstance(self.value, list):
            raise AdapterException(f"Cannot convert {self.value} to list")
        if len(self.value) == 0:
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
            return self.value['modelType']
        except KeyError:
            raise AdapterException(f"Missing 'modelType'")

    def __str__(self):
        return str(self.value)
