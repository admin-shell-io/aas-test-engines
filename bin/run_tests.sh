#! /usr/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/.."

black aas_test_engines test --exclude fixtures --line-length 120 --check

./bin/check_readme.py

coverage run \
         --source=aas_test_engines \
         -m unittest

PYTHONPATH=. ./test/acceptance/file.py
# PYTHONPATH=. ./test/acceptance/generate.py
PYTHONPATH=. ./test/acceptance/server.py
