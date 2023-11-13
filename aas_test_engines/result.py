from typing import List
from enum import Enum


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

    def __init__(self, message: str, path_fragment: str = '', level = Level.INFO):
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
        ENDC = '\033[0m'
        print("   " * indent + self.level.color() + self.message + ENDC)
        for sub_result in self.sub_results:
            sub_result.dump(indent + 1, path + "/" + self.path_fragment)

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