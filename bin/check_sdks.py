#! /usr/bin/env python3

import os
from aas_test_engines import file
import json
import subprocess
from fences.core.util import ConfusionMatrix

script_dir = os.path.dirname(os.path.realpath(__file__))
root_dir = os.path.realpath(os.path.join(script_dir, "check_sdks"))

test_data_dir = os.path.join(root_dir, "test_data")
valid_samples_dir = os.path.join(test_data_dir, "valid")
invalid_samples_dir = os.path.join(test_data_dir, "invalid")


def is_non_empty(directory: str) -> bool:
    return os.path.exists(directory) and os.listdir(directory)


print("--- Generate Test Data ---")
num_valid = 0
num_invalid = 0

if is_non_empty(test_data_dir):
    print(f"{test_data_dir} already exists, skipping sample generation")
    for f in os.listdir(test_data_dir):
        if f.startswith('i'):
            num_invalid += 1
        else:
            num_valid += 1
else:
    print(f"Writing samples to {test_data_dir}...")
    os.mkdir(test_data_dir)

    for is_valid, sample in file.generate():
        if is_valid:
            with open(os.path.join(test_data_dir, f"v{num_valid}.json"), "w") as f:
                json.dump(sample, f, indent=4)
            num_valid += 1
        else:
            with open(os.path.join(test_data_dir, f"i{num_invalid}.json"), "w") as f:
                json.dump(sample, f, indent=4)
            num_invalid += 1

        if (num_valid + num_invalid) % 100 == 0:
            print(f"#Valid:   {num_valid}")
            print(f"#Invalid: {num_invalid}")

    print("Done.")

print(f"#Valid:   {num_valid}")
print(f"#Invalid: {num_invalid}")
print()

sdks = [
    'aas_core_csharp',
    'basyx_python',
]

print("--- Execute SDKs ---")
for sdk in sdks:
    print(f"Executing {sdk}...")
    sdk_dir = os.path.join(root_dir, "sdks", sdk)
    out_dir = os.path.join(root_dir, "out", sdk)

    if is_non_empty(out_dir):
        print(f"{out_dir} already exists, reusing last results")
    else:
        compose_file = os.path.join(sdk_dir, "docker-compose.yml")
        print(f"compose={compose_file}")
        subprocess.check_call([
            "docker", "compose",
            "-f", compose_file,
            "run",
            "--remove-orphans",
            "app"
        ], cwd=sdk_dir)
print()

print("--- Analyse Results ---")
for sdk in sdks:
    mat = ConfusionMatrix()
    out_dir = os.path.join(root_dir, "out", sdk)
    for file in os.listdir(out_dir):
        if file.startswith('i'):
            mat.invalid_accepted += 1
        else:
            mat.valid_accepted += 1
    mat.valid_rejected = num_valid - mat.valid_accepted
    mat.invalid_rejected = num_invalid - mat.invalid_accepted
    mat.print()
