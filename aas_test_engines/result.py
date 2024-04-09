from typing import List
from enum import Enum
import os

script_dir = os.path.dirname(os.path.realpath(__file__))


class Level(Enum):
    INFO = 0
    WARNING = 1
    ERROR = 2

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


class AasTestResult:

    def __init__(self, message: str, path_fragment: str = '', level=Level.INFO):
        self.message = message
        self.path_fragment = path_fragment
        self.level = level
        self.sub_results: List[AasTestResult] = []

    def append(self, result: "AasTestResult"):
        self.sub_results.append(result)
        self.level = self.level | result.level

    def ok(self) -> bool:
        return self.level == Level.INFO

    def dump(self, indent=0, path=''):
        """Outputs the result to console"""
        ENDC = '\033[0m'
        print("   " * indent + self.level.color() + self.message + ENDC)
        for sub_result in self.sub_results:
            sub_result.dump(indent + 1, path + "/" + self.path_fragment)

    def _to_html(self) -> str:
        cls = {
            Level.INFO: 'info',
            Level.WARNING: 'warning',
            Level.ERROR: 'error'
        }[self.level]
        s = "<div>\n"
        if self.sub_results:
            s += f'<div class="{cls}">{self.message}<span class="caret"/></div>\n'
            s += '<div class="sub-results">\n'
            for sub_result in self.sub_results:
                s += sub_result._to_html()
            s += "</div>\n"
        else:
            s += f'<div class="{cls}">{self.message}</div>\n'
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

    def to_json(self):
        return {
            'm': self.message,
            'f': self.path_fragment,
            'l': self.level.value,
            's': [i.to_json() for i in self.sub_results]
        }

    @classmethod
    def from_json(self, data: dict) -> "AasTestResult":
        v = AasTestResult(
            data['m'], data['f'], Level(data['l'])
        )
        for i in data['s']:
            v.append(AasTestResult.from_json(i))
        return v
