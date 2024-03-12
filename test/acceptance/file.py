#! /usr/bin/env python3

import os
from aas_test_engines import file

script_dir = os.path.dirname(os.path.realpath(__file__))

def is_blacklisted(path):
    blacklist = [
        'UnexpectedAdditionalProperty',
        'Double/lowest.',
        'Double/max.',
        'Float/largest_normal.',
        'ConstraintViolation/Reference/',
        'ConstraintViolation/reference',
        'ConstraintViolation/SubmodelElementList',
        'ConstraintViolation/submodelElementList',
        'basicEventElement/messageTopic.xml',
        'TypeViolation/langStringNameType/text.xml',
        'TypeViolation/blob/value.xml',
        'TypeViolation/langStringShortNameTypeIec61360/text.xml',
        'TypeViolation/assetInformation/assetType.xml',
        'TypeViolation/assetInformation/globalAssetId.xml',
        'TypeViolation/submodelElementList/orderRelevant.xml',
        'TypeViolation/conceptDescription/administration.xml',
        'TypeViolation/conceptDescription/id.xml',
        'TypeViolation/administrativeInformation/templateId.xml',
        'TypeViolation/specificAssetId/value.xml',
        'TypeViolation/specificAssetId/name.xml',
        'TypeViolation/langStringPreferredNameTypeIec61360/text.xml',
        'TypeViolation/langStringTextType/text.xml',
        'TypeViolation/submodel/administration.xml',
        'TypeViolation/submodel/id.xml',
        'TypeViolation/dataSpecificationIec61360/symbol.xml',
        'TypeViolation/dataSpecificationIec61360/value.xml',
        'TypeViolation/dataSpecificationIec61360/sourceOfDefinition.xml',
        'TypeViolation/dataSpecificationIec61360/valueFormat.xml',
        'TypeViolation/dataSpecificationIec61360/unit.xml',
        'TypeViolation/langStringDefinitionTypeIec61360/text.xml',
        'TypeViolation/assetAdministrationShell/administration.xml',
        'TypeViolation/assetAdministrationShell/id.xml',
        'TypeViolation/key/value.xml',
        'TypeViolation/valueReferencePair/value.xml',
        'TypeViolation/levelType/min.xml',
        'TypeViolation/levelType/max.xml',
        'TypeViolation/levelType/typ.xml',
        'TypeViolation/levelType/nom.xml',
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
    for root, dirs, files in os.walk(os.path.join(script_dir, f'../fixtures/aas-core3.0-testgen/test_data/{dirname}/ContainedInEnvironment'), topdown=False):
        for name in files:
            path_in = os.path.join(root, name)
            if is_blacklisted(path_in):
                skipped += 1
                continue
            with open(path_in) as f:
                errors = check(f)
            if errors.ok():
                if 'Expected' in path_in:
                    valid_accepted += 1
                else:
                    invalid_accepted += 1
            else:
                if 'Expected' in path_in:
                    valid_rejected += 1
                else:
                    invalid_rejected += 1
    print("valid, accepted",     valid_accepted)
    print("invalid, rejected",   invalid_rejected)
    print("valid, rejected",     valid_rejected)
    print("invalid, accepted",   invalid_accepted)
    print("skipped",             skipped)
    if valid_rejected or invalid_accepted:
        raise RuntimeError("Acceptance test failed")


if __name__ == '__main__':
    print("Running file acceptance tests")
    run('Json', file.check_json_file)
    run('Xml', file.check_xml_file)
