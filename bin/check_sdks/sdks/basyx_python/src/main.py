#! /usr/bin/env python3

import os
from basyx.aas.adapter.json import json_deserialization, json_serialization

test_data_dir = '/test_data'
out_dir = '/out'
for file in os.listdir(test_data_dir):
    with open(os.path.join(test_data_dir, file)) as f:
        try:
            data = json_deserialization.read_aas_json_file(f, failsafe=False)
        except (ValueError, KeyError, TypeError) as e:
            data = None
    if data:
        with open(os.path.join(out_dir, file), "w") as f:
            json_serialization.write_aas_json_file(f, data)
