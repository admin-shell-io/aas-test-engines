#! /usr/bin/bash

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

cd "$SCRIPT_DIR/.."

coverage run \
         --source=aas_test_engines \
         -m unittest

PYTHONPATH=. ./test/acceptance/file.py
