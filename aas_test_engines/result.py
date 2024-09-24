from typing import List, TypeVar, Generator
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
            return '\033[92m'
        if self.value == 1:
            return '\033[93m'
        if self.value == 2:
            return '\033[91m'
        return '\033[94m'


# https://stackoverflow.com/questions/34073370
class ValueKeepingGenerator(object):
    def __init__(self, generator):
        self.generator = generator
        self.return_value = None

    def __iter__(self):
        self.return_value = yield from self.generator

class ResultException(Exception):
    pass

class _NoResultException(Exception):
    pass

class AasTestResult:

    def __init__(self, message: str, path_fragment: str = '', level=Level.INFO):
        self.message = message
        self.path_fragment = path_fragment
        self.level = level
        self.sub_results: List[AasTestResult] = []

    def append(self, result: "AasTestResult"):
        self.sub_results.append(result)
        self.level = self.level | result.level

    def append_from(self, it: Generator["AasTestResult", any, T], is_root: bool = False) -> T:
        val_it = ValueKeepingGenerator(it)
        try:
            for result in val_it:
                self.append(result)
        except ResultException as e:
            self.append(AasTestResult(str(e), level=Level.ERROR))
            if not is_root:
                raise _NoResultException()
        except _NoResultException as e:
            if not is_root:
                raise e
        return val_it.return_value

    def ok(self) -> bool:
        return self.level == Level.INFO or self.level == Level.WARNING

    def dump(self):
        """Outputs the result to console"""
        for line in self.to_lines():
            print(line)

    def to_lines(self, indent=0, path=''):
        ENDC = '\033[0m'
        yield "   " * indent + self.level.color() + self.message + ENDC
        for sub_result in self.sub_results:
            yield from sub_result.to_lines(indent + 1, path + "/" + self.path_fragment)

    def _to_html(self) -> str:
        cls = {
            Level.INFO: 'info',
            Level.WARNING: 'warning',
            Level.ERROR: 'error',
            Level.CRITICAL: 'critical',
        }[self.level]
        s = "<div>\n"
        msg = html.escape(self.message)
        if self.sub_results:
            c = "" if self.ok() else "caret-down"
            s += f'<div class="{cls}">{msg}<span class="caret {c}"/></div>\n'
            c = "" if self.ok() else "visible"
            s += f'<div class="sub-results {c}">\n'
            for sub_result in self.sub_results:
                s += sub_result._to_html()
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
        with open(os.path.join(script_dir, 'data', 'template.html'), 'r') as f:
            content = f.read()
        return content.replace("<!-- CONTENT -->", self._to_html())

    def to_dict(self):
        return {
            'm': self.message,
            'f': self.path_fragment,
            'l': self.level.value,
            's': [i.to_dict() for i in self.sub_results]
        }

    @classmethod
    def from_json(self, data: dict) -> "AasTestResult":
        v = AasTestResult(
            data['m'], data['f'], Level(data['l'])
        )
        for i in data['s']:
            v.append(AasTestResult.from_json(i))
        return v
