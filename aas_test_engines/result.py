from typing import List, TypeVar, Union
from enum import Enum
import os
import html

T = TypeVar("T")


script_dir = os.path.dirname(os.path.realpath(__file__))


class Level(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

    def __or__(self, other: "Level") -> "Level":
        return Level(max(self.value, other.value))

    def color(self) -> str:
        if self.value == 0:
            return "\033[92m"
        if self.value == 1:
            return "\033[93m"
        if self.value == 2:
            return "\033[91m"
        return "\033[94m"


class AasTestResult:

    def __init__(self, message: str, level=Level.INFO):
        assert isinstance(level, Level)
        self.message = message
        self.level = level
        self.sub_results: List[AasTestResult] = []

    def append(self, result: "AasTestResult"):
        self.sub_results.append(result)
        self.level = self.level | result.level

    def ok(self) -> bool:
        return self.level == Level.INFO or self.level == Level.WARNING

    def dump(self):
        """Outputs the result to console"""
        for line in self.to_lines():
            print(line)

    def to_lines(self, indent=0, path=""):
        ENDC = "\033[0m"
        yield "   " * indent + self.level.color() + self.message + ENDC
        for sub_result in self.sub_results:
            yield from sub_result.to_lines(indent + 1)

    def _to_html(self, level: int) -> str:
        cls = {
            Level.INFO: "info",
            Level.WARNING: "warning",
            Level.ERROR: "error",
            Level.CRITICAL: "critical",
        }[self.level]
        s = "<div>\n"
        msg = html.escape(self.message)
        if self.sub_results:
            c = "" if self.ok() else "caret-down"
            s += f'<div class="{cls}">{msg}<span class="caret level-{level} {c}"/></div>\n'
            c = "" if self.ok() else "visible"
            s += f'<div class="sub-results {c}">\n'
            for sub_result in self.sub_results:
                s += sub_result._to_html(level + 1)
            s += "</div>\n"
        else:
            s += f'<div class="{cls}">{msg}</div>\n'
        s += "</div>\n"
        return s

    def to_html(self) -> str:
        """Generates an interactive view of the result as HTML.
        You should write the result into a file:
            content = self.result.to_html()
            with open("result.html", "w") as file:
                file.write(content)
        Then open result.html in your browser.
        """
        with open(os.path.join(script_dir, "data", "template.html"), "r") as f:
            content = f.read()
        return content.replace("<!-- CONTENT -->", self._to_html(0))

    def to_dict(self):
        return {
            "m": self.message,
            "l": self.level.value,
            "s": [i.to_dict() for i in self.sub_results],
        }

    @classmethod
    def from_json(self, data: dict) -> "AasTestResult":
        v = AasTestResult(data["m"], Level(data["l"]))
        for i in data["s"]:
            v.append(AasTestResult.from_json(i))
        return v


managers: List["ContextManager"] = []


class ContextManager:

    def __init__(self, result: AasTestResult, catch_all_exceptions: bool):
        self.result = result
        self.catch_all_exceptions = catch_all_exceptions

    def __enter__(self) -> AasTestResult:
        managers.append(self)
        return self.result

    def __exit__(self, exc_type, exc_val, traceback):
        m = managers.pop()
        assert m is self
        if exc_val is None:
            if managers:
                managers[-1].result.append(self.result)
        elif isinstance(exc_val, ResultException):
            self.result.append(exc_val.result)
            if managers:
                managers[-1].result.append(self.result)
            return True
        elif self.catch_all_exceptions:
            self.result.append(AasTestResult(f"Internal error: {exc_val}", Level.CRITICAL))
            if managers:
                managers[-1].result.append(self.result)
            return True
        else:
            return False


class ResultException(Exception):
    def __init__(self, result) -> None:
        self.result = result


def _as_result(message: Union[str, AasTestResult], level: Level):
    if isinstance(message, AasTestResult):
        return message
    assert isinstance(message, str)
    return AasTestResult(message, level=level)


def write(message: Union[str, AasTestResult]):
    if not managers:
        raise RuntimeError("No open context")
    message = _as_result(message, Level.INFO)
    managers[-1].result.append(message)


def start(message: Union[str, AasTestResult], catch_all_exceptions: bool = False) -> ContextManager:
    result = _as_result(message, Level.INFO)
    return ContextManager(result, catch_all_exceptions)


def abort(message: Union[str, AasTestResult]):
    result = _as_result(message, Level.ERROR)
    raise ResultException(result)
