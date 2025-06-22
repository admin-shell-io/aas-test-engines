#! /usr/bin/env python3

import os
from aas_test_engines import file
import time

script_dir = os.path.dirname(os.path.realpath(__file__))


def is_blacklisted(path):
    blacklist = [
        "Double/lowest.",
        "Double/max.",
        "Float/largest_normal.",
        "lastUpdate/date_time_without_zone",
        "lastUpdate/date_time_with_offset",
    ]
    for i in blacklist:
        if i in path:
            return True
    return False


def run(dirname: str, check):
    print(f"Testing {dirname}, this might take a few minutes...")
    valid_accepted = 0
    valid_rejected = 0
    invalid_accepted = 0
    invalid_rejected = 0
    skipped = 0
    for root, dirs, files in os.walk(
        os.path.join(
            script_dir,
            f"../fixtures/aas-core3.0-testgen/test_data/{dirname}/ContainedInEnvironment",
        ),
        topdown=False,
    ):
        for name in files:
            path_in = os.path.join(root, name)
            if is_blacklisted(path_in):
                skipped += 1
                continue
            with open(path_in) as f:
                errors = check(f)
            if errors.ok():
                if "Expected" in path_in:
                    valid_accepted += 1
                else:
                    print(path_in)
                    invalid_accepted += 1
            else:
                if "Expected" in path_in:
                    valid_rejected += 1
                else:
                    invalid_rejected += 1
    print("valid, accepted", valid_accepted)
    print("invalid, rejected", invalid_rejected)
    print("valid, rejected", valid_rejected)
    print("invalid, accepted", invalid_accepted)
    print("skipped", skipped)
    if valid_rejected or invalid_accepted:
        raise RuntimeError("Acceptance test failed")


if __name__ == "__main__":
    print("Running file acceptance tests")
    start = time.time()
    run("Json", file.check_json_file)
    run("Xml", file.check_xml_file)
    print(f"Testing AASX...")
    aasx_file = os.path.join(script_dir, "..", "..", "bin/check_servers/test_data/TestDataWithThumbnail.aasx")
    file.check_aasx_file(aasx_file)
    stop = time.time()
    print(f"Elapsed time: {stop - start:.1f}s")
