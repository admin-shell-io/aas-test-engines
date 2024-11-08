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

By default, the Test Engines test against the latest version 3.0, precisely: metamodel => 3.0.1 and API => 3.0.3.
In case of API, the IDTA specifications define service specifications and profiles. Below tables describes the supported API profiles by the current test-engine. For more information about these profiles, please visit [IDTA Specifications for API](https://industrialdigitaltwin.org/wp-content/uploads/2024/10/IDTA-01002-3-0-3_SpecificationAssetAdministrationShell_Part2_API.pdf).

Full support: ✅
Partial support: ✔️

| Name | Profile Identifier | Description | Support in test-engine |
| :--- | :---               | :---        | :---                   |
| AAS Repository Read Profile | https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002 | Only read operations for the AAS Repository Service | ✅ |
| Submodel Repository Read Profile | https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-002 | Only read operations for the Submodel Repository Service | ✅ |
| AAS Registry Read Profile | https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-002 | Only reads operations for AAS Registry Service | ✔️ |

 
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
