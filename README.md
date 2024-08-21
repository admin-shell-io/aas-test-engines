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

## Command line interface

You may want to invoke the test tools using the simplified command line interface:

```sh
# Check file
python -m aas_test_engines check_file test.aasx
python -m aas_test_engines check_file test.json --format json

# Check file including submodel template
python -m aas_test_engines check_file test.aasx --submodel_template ContactInformation

# Check server
python -m aas_test_engines check_server https://localhost --suite 'Asset Administration Shell API'

# Generate test data
python -m aas_test_engines generate_files output_dir

# Alternative output formats
python -m aas_test_engines check_file test.aasx --output html > output.html
python -m aas_test_engines check_file test.aasx --output json > output.json
```

## Check AAS Type 1 (File)

### Check AASX:
```python
from aas_test_engines import file
from xml.etree import ElementTree

with open('aas.aasx', 'rb') as f:
    result = file.check_aasx_file(f)
# result.ok() == True

result.dump()
# try result.to_html() to get an interactive representation
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

### Checking for submodel templates
By passing a set of submodel template names you can check a file for compliance to these:

```python
from aas_test_engines import file
with open('aas.xml') as f:
    result = file.check_xml_file(f, submodel_templates=set(['ContactInformation']))
# result.ok() == True

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

conf = api.ExecConf(
    server="http://localhost",
)
result = api.execute_tests(conf=conf)
result.dump()
```

### Checking older versions and specific test suites

By default, the `api.generate_tests` method generate test cases for version 3.0 of the standard and all associated test suites.
You may want to check against older versions by passing a string containing the version to these methods.
You can also provide a list of test suites to check against:

```python
from aas_test_engines import api

conf = api.ExecConf(
    server="http://localhost",
)
result = api.execute_tests(version="3.0", suite='Asset Administration Shell API', conf=conf)
result.dump()
```

For the naming of test suites we follow the names given by the specification. These are:
* **APIs:** Asset Administration Shell API, Submodel API, ...
* **Service Specifications:** Asset Administration Shell Service Specification, Submodel Service Specification, ...
* **Profiles:**  AssetAdministrationShellServiceSpecification/SSP-001, ...

You can query the list of supported versions and their associated test suites as follows:

```python
from aas_test_engines import api

print(api.supported_versions())
print(api.latest_version())
```

## Generating test data for software testing

If you develop an AAS application like an AAS editor you may want to use test data to verify correctness of your application.
The test engines allow to generate a set of AAS files which are compliant with the standard and you can therefore use to assess your application as follows:

```python
from aas_test_engines import file

for is_valid, sample in file.generate():
    print(sample) # or whatever you want to do with it
```
