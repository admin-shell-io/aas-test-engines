# Test Engines for the Asset Administration Shell

[![Tests](https://github.com/admin-shell-io/aas-test-engines/actions/workflows/check.yml/badge.svg)](https://github.com/admin-shell-io/aas-test-engines/actions/workflows/check.yml)

The Asset Administration Shell (AAS) is a standard for Digital Twins.
More information can be found [here](https://industrialdigitaltwin.org/content-hub/downloads).

The tools in this repository offer measures to validate compliance of AAS implementations against the AAS standard.

## Installation

You can install the AAS Test Engines via pip:

```sh
python -m pip install --upgrade aas_test_engines
```

## Command Line Interface

You may want to invoke the test tools using the simplified command line interface:

```sh
# Check file
aas_test_engines check_file test.aasx
aas_test_engines check_file test.json --format json

# Check file including submodel template
aas_test_engines check_file test.aasx --submodel_template ContactInformation

# Check server
aas_test_engines check_server https://localhost https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002

# Generate test data
aas_test_engines generate_files output_dir

# Alternative output formats
aas_test_engines check_file test.aasx --output html > output.html
aas_test_engines check_file test.aasx --output json > output.json
```

## Supported Versions and Suites

By default, the Test Engines test against the latest version 3.0 (file and api).
For v3.0 api testing, the following suites are defined:

 - `Asset Administration Shell API`
 - `Submodel API`
 - `Serialization API`
 - `AASX File Server API`
 - `Asset Administration Shell Registry API`
 - `Submodel Registry API`
 - `Asset Administration Shell Repository API`
 - `Submodel Repository API`
 - `Concept Description Repository API`
 - `Asset Administration Shell Basic Discovery API`
 - `Description API`
 - `Asset Administration Shell Service Specification`
 - `Submodel Service Specification`
 - `AASX File Server Service Specification`
 - `Asset Administration Shell Registry Service Specification`
 - `Submodel Registry Service Specification`
 - `Discovery Service Specification`
 - `Asset Administration Shell Repository Service Specification`
 - `Submodel Repository Service Specification`
 - `ConceptDescription Repository Service Specification`
 - `https://admin-shell.io/aas/API/3/0/AssetAdministrationShellServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/AssetAdministrationShellServiceSpecification/SSP-002`
 - `https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-002`
 - `https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-003`
 - `https://admin-shell.io/aas/API/3/0/AasxFileServerServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-002`
 - `https://admin-shell.io/aas/API/3/0/SubmodelRegistryServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/SubmodelRegistryServiceSpecification/SSP-002`
 - `https://admin-shell.io/aas/API/3/0/DiscoveryServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002`
 - `https://admin-shell.io/aas/API/3/0/SubmodelRepositoryServiceSpecification/SSP-001`
 - `https://admin-shell.io/aas/API/3/0/SubmodelRepositoryServiceSpecification/SSP-002`
 - `https://admin-shell.io/aas/API/3/0/SubmodelRepositoryServiceSpecification/SSP-003`
 - `https://admin-shell.io/aas/API/3/0/SubmodelRepositoryServiceSpecification/SSP-004`
 - `https://admin-shell.io/aas/API/3/0/ConceptDescriptionRepositoryServiceSpecification/SSP-001`
 
## Python Module Interface

### Check AAS Type 1 (File)

Check AASX:

```python
from aas_test_engines import file

with open('aas.aasx', 'rb') as f:
    result = file.check_aasx_file(f)
# result.ok() == True

result.dump()
# try result.to_html() to get an interactive representation
```

Check JSON:

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

Check XML:

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

Checking for submodel templates:

```python
from aas_test_engines import file
with open('aas.xml') as f:
    result = file.check_xml_file(f, submodel_templates=set(['ContactInformation']))
# result.ok() == True

```

Checking older versions:

```python
from aas_test_engines import file

print(file.supported_versions())
print(file.latest_version())
with open('aas.aasx', 'rb') as f:
    result = file.check_aasx_file(f, version="3.0")
# result.ok() == True

result.dump()
```

### Check AAS Type 2 (HTTP API)

Check a running server instance:

```python
from aas_test_engines import api

result = api.execute_tests("http://localhost", "https://localhost https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002")
result.dump()
```

Checking older versions:

```python
from aas_test_engines import api
print(api.supported_versions())
print(api.latest_version())

result = api.execute_tests("http://localhost", 'Asset Administration Shell API', version="3.0")
result.dump()
```

### Generating test data for software testing

If you develop an AAS application like an AAS editor you may want to use test data to verify correctness of your application.
The test engines allow to generate a set of AAS files which are compliant with the standard and you can therefore use to assess your application as follows:

```python
from aas_test_engines import file

for is_valid, sample in file.generate():
    print(sample) # or whatever you want to do with it
```
