#! /usr/bin/env python3

from aas_test_engines import file
import aas_core3.jsonization as aas_jsonization
import aas_core3.verification as aas_verification
from fences.core.util import ConfusionMatrix
import json

print("Running generation acceptance tests")

mat_core_works_no_constraints = ConfusionMatrix()
mat_core_works_with_constraints = ConfusionMatrix()
mat_test_engines = ConfusionMatrix()

causes = {}

blacklist = [
    'Message broker must be a model reference to a referable.',
    'Max. interval is not applicable for input direction.',
    'Observed must be a model reference to a referable.',
    'Constraint AASc-3a-008: For a concept description using data specification template IEC 61360, the definition is mandatory and shall be defined at least in English. Exception: The concept description describes a value.',
    'Constraint AASd-119: If any qualifier kind value of a qualifiable qualifier is equal to template qualifier and the qualified element has kind then the qualified element shall be of kind template.',
    'Constraint AASd-129: If any qualifier kind value of a Submodel element qualifier (attribute qualifier inherited via Qualifiable) is equal to Template Qualifier then the submodel element shall be part of a submodel template, i.e. a Submodel with submodel kind (attribute kind inherited via Has-Kind) value is equal to Template.',
    'Derived-from must be a model reference to an asset administration shell.',
    'All submodels must be model references to a submodel.',
]

c = 0
for is_valid, sample in file.generate():

    # Core Works (no constraints)
    env = None
    try:
        env = aas_jsonization.environment_from_jsonable(sample)
        mat_core_works_no_constraints.add(is_valid, True)
    except aas_jsonization.DeserializationException as e:
        mat_core_works_no_constraints.add(is_valid, False)

    # Core Works (with constraints)
    if env is None:
        accepted = False
    else:
        accepted = True
        errors = aas_verification.verify(env)
        for error in errors:
            if is_valid:
                try:
                    causes[error.cause] += 1
                except KeyError:
                    causes[error.cause] = 1
            if error.cause not in blacklist:
                accepted = False
    mat_core_works_with_constraints.add(is_valid, accepted)

    # Test Engines
    # error = file.check_json_data(sample)
    # mat_test_engines.add(is_valid, error.ok())

    c += 1
    if c % 100 == 0:
        print("Core Works (NO constraints)")
        mat_core_works_no_constraints.print()
        print("Core Works")
        mat_core_works_with_constraints.print()
        # print("Test Engines")
        # mat_test_engines.print()
        print("#" * 10)
    if c >= 1000:
        break

print("Core Works (NO constraints)")
mat_core_works_no_constraints.print()
print("Core Works")
mat_core_works_with_constraints.print()
# mat_test_engines.print()

for cause in sorted(causes.keys(), key=lambda x: causes[x]):
    print(f"{causes[cause]}: {cause}")

if mat_core_works_with_constraints.valid_rejected:
    print("Valid instances have been rejected!")
    exit(1)

if mat_core_works_with_constraints.invalid_accepted:
    print("Invalid instances have been accepted!")
    # exit(1) # TODO: need to fix some issues in aas-core-python first

exit(0)
