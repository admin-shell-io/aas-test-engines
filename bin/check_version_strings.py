#! /usr/bin/env python3

import subprocess
import os
import re

script_dir = os.path.dirname(os.path.realpath(__file__))


def get_current_tag():
    output = subprocess.check_output(['git', 'tag', '--points-at', 'HEAD'])
    return output.decode().strip()


def assert_line_in_file(expected_line: str, file: str):
    path = os.path.join(script_dir, '..', file)
    with open(path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line == expected_line + "\n":
            print(f"{file} is ok.")
            return
    raise RuntimeError(f"'{expected_line}' not found in {file}")


tag = get_current_tag()
if not tag:
    raise RuntimeError("Commit is not tagged")

print(f"Tag: '{tag}'")
if not re.fullmatch(r'v\d+\.\d+\.\d+', tag):
    raise RuntimeError(f"Tag has invalid format")

# Remove 'v'
tag = tag[1:]

assert_line_in_file(f'version = "{tag}"', 'pyproject.toml')
assert_line_in_file(f'    return "{tag}"', 'aas_test_engines/__init__.py')
