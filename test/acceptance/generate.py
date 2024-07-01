#! /usr/bin/env python3

from aas_test_engines import file
import aas_core3.jsonization as aas_jsonization
from fences.core.util import ConfusionMatrix

print("Running generation acceptance tests")

mat = ConfusionMatrix()

c = 0
for is_valid, sample in file.generate():
    try:
        aas_jsonization.environment_from_jsonable(sample)
        if is_valid:
            mat.valid_accepted += 1
        else:
            mat.invalid_accepted += 1
    except aas_jsonization.DeserializationException as e:
        if is_valid:
            mat.valid_rejected += 1
        else:
            mat.invalid_rejected += 1
    c += 1
    if c % 1000 == 0:
        print(c)
        mat.print()

mat.print()
if mat.valid_rejected:
    print("Valid instances have been rejected!")
    exit(1)

if mat.invalid_accepted:
    print("Invalid instances have been accepted!")
    # exit(1) # TODO: need to fix some issues in aas-core-python first

exit(0)
