# Implements OpenApi runtime expressions
# See: https://github.com/OAI/OpenAPI-Specification/blob/main/versions/3.0.3.md#runtimeExpression

from typing import Any, List
import jsonpath_ng


class RuntimeExpressionException(Exception):
    pass


class RuntimeExpression:

    PREFIX = None
    CLASSES: List["RuntimeExpression".__class__] = []

    def to_string(self) -> str:
        return self.PREFIX

    @classmethod
    def from_string(cls: "RuntimeExpression", value: str) -> "RuntimeExpression":
        for expression_class in cls.CLASSES:
            if value.startswith(expression_class.PREFIX):
                return expression_class(value)
        raise RuntimeExpressionException(
            "Cannot parse '{}' as runtime expression".format(value))

    def __init__(self, value: str):
        if value != self.PREFIX:
            raise RuntimeExpressionException(
                "Expected {}, got {}".format(self.PREFIX, value))

    def lookup(self, url: str, method: str, status_code: int, response_body: dict) -> Any:
        raise NotImplemented()


class UrlRuntimeExpression(RuntimeExpression):

    PREFIX = "$url"

    def lookup(self, url: str, method: str, status_code: int, response_body: dict) -> Any:
        return url


RuntimeExpression.CLASSES.append(UrlRuntimeExpression)


class MethodRuntimeExpression(RuntimeExpression):

    PREFIX = "$method"

    def lookup(self, url: str, method: str, status_code: int, response_body: dict) -> Any:
        return method


RuntimeExpression.CLASSES.append(MethodRuntimeExpression)


class StatusCodeRuntimeExpression(RuntimeExpression):

    PREFIX = "$statusCode"

    def lookup(self, url: str, method: str, status_code: int, response_body: dict) -> Any:
        return status_code


RuntimeExpression.CLASSES.append(StatusCodeRuntimeExpression)


class RequestRuntimeExpression(RuntimeExpression):

    PREFIX = "$request."

    def __init__(self, value: str):
        raise NotImplemented()


RuntimeExpression.CLASSES.append(RequestRuntimeExpression)


class ResponseHeaderRuntimeExpression(RuntimeExpression):

    PREFIX = "$response.header."

    def __init__(self, value: str):
        raise NotImplemented()


RuntimeExpression.CLASSES.append(ResponseHeaderRuntimeExpression)


class ResponseQueryRuntimeExpression(RuntimeExpression):

    PREFIX = "$response.query."

    def __init__(self, value: str):
        raise NotImplemented()


RuntimeExpression.CLASSES.append(ResponseQueryRuntimeExpression)


class ResponsePathRuntimeExpression(RuntimeExpression):

    PREFIX = "$response.path."

    def __init__(self, value: str):
        raise NotImplemented()


RuntimeExpression.CLASSES.append(ResponsePathRuntimeExpression)


class ResponseBodyRuntimeExpression(RuntimeExpression):

    PREFIX = "$response.body"

    def __init__(self, value: str):
        if not value.startswith(self.PREFIX):
            raise RuntimeExpressionException(
                "Failed to parse '{}': expected prefix {}".format(value, self.PREFIX))
        json_path = value[len(self.PREFIX):]
        if json_path:
            if json_path.startswith("#"):
                json_path = json_path[1:]
            else:
                raise Exception(
                    "Failed to parse '{}': '{}' is not a local json path".format(value, json_path))
            try:
                self.json_path = jsonpath_ng.parse(json_path)
            except jsonpath_ng.exceptions.JSONPathError as e:
                raise RuntimeExpressionException(
                    "Failed to parse '{}': {}".format(json_path, e))
        else:
            self.json_path = None

    def lookup(self, url: str, method: str, status_code: int, response_body: dict) -> Any:
        if self.json_path:
            try:
                val = [i.value for i in self.json_path.find(response_body)]
            except KeyError as e:
                raise RuntimeExpressionException(
                    "Cannot find {}".format(self.json_path))
            if len(val) != 1:
                raise RuntimeExpressionException(
                    "Expected one value, got {}".format(val))
            return val[0]
        else:
            return response_body

    def to_string(self) -> str:
        if self.json_path:
            return self.PREFIX + "#" + str(self.json_path)
        else:
            return self.PREFIX


RuntimeExpression.CLASSES.append(ResponseBodyRuntimeExpression)
