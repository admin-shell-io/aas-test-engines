from typing import Any, Type


class NoDefault:
    pass


def assert_type(value: Any, _type: Type, json_path: str):
    if not isinstance(value, _type):
        raise TypeError('Expected "{}", got "{}" at {}'.format(
            _type, type(value), json_path))
    return value


def safe_dict_lookup(data: dict, key: str, _type: Type, json_path: str, default=NoDefault):
    if key not in data:
        if default is not NoDefault:
            return default
        else:
            raise KeyError('Expected key "{}" at {}'.format(key, json_path))
    return assert_type(data[key], _type, json_path + '.' + key)
