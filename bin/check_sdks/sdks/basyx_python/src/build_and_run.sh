#! /bin/bash

set -e

pip install git+https://github.com/eclipse-basyx/basyx-python-sdk.git@v3.0

./main.py
