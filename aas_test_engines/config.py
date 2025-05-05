from typing import Optional
from dataclasses import dataclass
import fnmatch
import re
from .exception import InvalidFilterException


# Implement gtest-like test filter:
#    https://google.github.io/googletest/advanced.html#running-a-subset-of-the-tests
class TestCaseFilter:
    FILTER_SEP = "~"
    PATTERN_SEP = ":"

    def __init__(self, filter_pattern: str):
        tokens = filter_pattern.split(self.FILTER_SEP)
        if len(tokens) == 1:
            include_pattern = tokens[0]
            exclude_pattern = ""
        elif len(tokens) == 2:
            include_pattern = tokens[0]
            exclude_pattern = tokens[1]
        else:
            raise InvalidFilterException(f"Separator {self.FILTER_SEP} must only occur once")
        self.includes = [re.compile(fnmatch.translate(i)) for i in include_pattern.split(self.PATTERN_SEP) if i.strip()]
        self.excludes = [re.compile(fnmatch.translate(i)) for i in exclude_pattern.split(self.PATTERN_SEP) if i.strip()]

    def selects(self, test_case: str) -> bool:
        if self.includes and not any(i.match(test_case) for i in self.includes):
            return False
        if self.excludes and any(i.match(test_case) for i in self.excludes):
            return False
        return True


@dataclass
class CheckApiConfig:
    suite: str
    version: Optional[str] = None
    dry: bool = False
    filter: Optional[TestCaseFilter] = None
