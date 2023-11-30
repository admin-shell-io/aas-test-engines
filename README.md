# Test Engines for the Asset Administration Shell

[![Tests](https://github.com/admin-shell-io/aas-test-engines/actions/workflows/check.yml/badge.svg)](https://github.com/admin-shell-io/aas-test-engines/actions/workflows/check.yml)

The Asset Administration Shell (AAS) is a standard for Digital Twins.
More information can be found [here](https://industrialdigitaltwin.org/content-hub/downloads).

The tools in this repository offer measures to validate compliance of AAS implementations against the AAS standard.

## Installation

You can install the AAS Test Engines via pip:

```sh
python -m pip install aas_test_engines
```

## Check AAS Type 1 (File)

### Check AASX:
```python
from aas_test_engines import file
from xml.etree import ElementTree

with open('aas.aasx') as f:
    result = file.check_aasx_file(f)
# result.ok() == True

result.dump()
```

### Check JSON:

```python
from aas_test_engines import file

# Check file
with open('aas.json') as f:
    result = file.check_json_file(f)
# result.ok() == True

# Or check data directly
aas = {
    'assetAdministrationShells': [],
    'submodels': [],
    'conceptDescriptions': []
}
result = file.check_json_data(aas)
# result.ok() == True

result.dump()
```

### Check XML:
```python
from aas_test_engines import file
from xml.etree import ElementTree

# Check file
with open('aas.xml') as f:
    result = file.check_xml_file(f)
# result.ok() == True

# Or check data directly
data = ElementTree.fromstring(
    '<environment xmlns="https://admin-shell.io/aas/3/0" />')
result = file.check_xml_data(aas)
# result.ok() == True

result.dump()
```

### Checking older versions

By default, the `file.check...` methods check compliance to version 3.0 of the standard.
You may want to check against older versions by passing a string containing the version to these methods.

You can query the list of supported versions as follows:

```python
from aas_test_engines import file

print(file.supported_versions())
print(file.latest_version())
```

## Check AAS Type 2 (HTTP API)

### Check a running server instance

```python
from aas_test_engines import api

tests = api.generate_tests()

# Check an instance
api.execute_tests(tests, "http://localhost")

# Check another instance
api.execute_tests(tests, "http://localhost:3000")
```

### Checking older versions and specific test suites

By default, the `api.generate_tests` method generate test cases for version 3.0 of the standard and all associated test suites.
You may want to check against older versions by passing a string containing the version to these methods.
You can also provide a list of test suites to check against:

```python
from aas_test_engines import api

tests = api.generate_tests('1.0RC03', ['repository'])
api.execute_tests(tests, "http://localhost")
```

You can query the list of supported versions and their associated test suites as follows:

```python
from aas_test_engines import api

print(api.supported_versions())
print(api.latest_version())
```
For version 1.0RC03 the following test suites are available:

| API Name                                       | Test Suite Read                     | Test Suite Read and Write      |
| ---------------------------------------------- | ----------------------------------- | ------------------------------ |
| Asset Administration Shell API                 | aas_read                            | aas                            |
| Submodel API                                   | submodel_read                       | submodel                       |
| AASX File Server API                           | aasx_read                           | aasx                           |
| Asset Administration Shell Registry API        | aas_registry_read                   | aas_registry                   |
| Submodel Registry API                          | submodel_registry_read              | submodel_registry              |
| Asset Administration Shell Repository API      | aas_repository_read                 | aas_repository                 |
| Submodel Repository API                        | submodel_repository_read            | submodel_repository            |
| Concept Description Repository API             | concept_description_repository_read | concept_description_repository |
| Asset Administration Shell Basic Discovery API | aas_discovery_read                  | aas_discvoery                  |
| Serialization API                              | serialization                       | -                              |
| Description API                                | description                         | -                              |

## Command line interface

You may want to invoke the test tools using the simplified command line interface:

```sh
# Check file
python -m aas_test_engines file test.aasx

# Check server
python -m aas_test_engines api https://localhost --suite registry
```
