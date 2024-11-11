#! /usr/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/.."

./bin/check_readme.py

coverage run \
         --source=aas_test_engines \
         -m unittest

PYTHONPATH=. ./test/acceptance/file.py
PYTHONPATH=. ./test/acceptance/generate.py
