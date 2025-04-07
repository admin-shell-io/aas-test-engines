# Test Engines for the Asset Administration Shell

[![Tests](https://github.com/admin-shell-io/aas-test-engines/actions/workflows/check.yml/badge.svg)](https://github.com/admin-shell-io/aas-test-engines/actions/workflows/check.yml)

The Asset Administration Shell (AAS) is a standard for Digital Twins.
More information can be found [here](https://industrialdigitaltwin.org/content-hub/downloads).

The tools in this repository offer measures to validate compliance of AAS implementations against the AAS standard.

## Installation

You can install the AAS Test Engines via pip:

<!-- no-check -->
```sh
python -m pip install --upgrade aas_test_engines
```

If you want to try the latest development version, you might want to install from git directly:

<!-- no-check -->
```sh
python -m pip install --upgrade pip install git+https://github.com/admin-shell-io/aas-test-engines.git
```



## Command Line Interface

You may want to invoke the test tools using the command line interface:

<!-- no-check -->
```sh
# Check file
aas_test_engines check_file test.aasx
aas_test_engines check_file test.json --format json

# Check server
aas_test_engines check_server https://localhost https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002

# Generate test data
aas_test_engines generate_files output_dir

# Alternative output formats (work for all commands)
aas_test_engines check_file test.aasx --output html > output.html
aas_test_engines check_file test.aasx --output json > output.json
```

Note that the Test Engines return zero in case of compliance and non-zero otherwise so that you can integrate them into ci.

For more detailed instructions on how to test your AAS Software, see [Test Setups](#test-setups).
If you want to include the Test Engines into your software, see [Python Module Interface](#python-interface).

## Supported Versions, Suites and Templates

By default, the Test Engines test against the latest version 3.0, precisely: metamodel => 3.0.1 and API => 3.0.3.
In case of Files, the IDTA specifies submodel templates.
For a full list, please visit [AAS Submodel Templates](https://industrialdigitaltwin.org/content-hub/teilmodelle).
The following templates are supported:
| Name | Semantic ID | Support in test-engine |
| :--- | :---        |  :---                  |
| Contact Information | https://admin-shell.io/zvei/nameplate/1/0/ContactInformations | ✅ |
| Digital Nameplate for Industrial Equipment | https://admin-shell.io/zvei/nameplate/2/0/Nameplate | ✅ |

For a detailed list of what is checked (and what is not), see [here](doc/file.md).

In case of API, the IDTA specifications define service specifications and profiles. Below tables describes the supported API profiles by the current test-engine. For more information about these profiles, please visit [IDTA Specifications for API](https://industrialdigitaltwin.org/wp-content/uploads/2024/10/IDTA-01002-3-0-3_SpecificationAssetAdministrationShell_Part2_API.pdf).

| Name | Profile Identifier | Description | Support in test-engine |
| :--- | :---               | :---        | :---                   |
| AAS Repository Read Profile | https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002 | Only read operations for the AAS Repository Service | ✅ |
| AAS Read Profile | https://admin-shell.io/aas/API/3/0/AssetAdministrationShellServiceSpecification/SSP-002 | Only read operations for the AAS Service | ✅ |
| Submodel Repository Read Profile | https://admin-shell.io/aas/API/3/0/SubmodelRepositoryServiceSpecification/SSP-002 | Only read operations for the Submodel Repository Service | ✅ |
| Submodel Read Profile | https://admin-shell.io/aas/API/3/0/SubmodelServiceSpecification/SSP-002 | Only read operations for the Submodel Repository Service | ✅ |
| AAS Registry Read Profile | https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRegistryServiceSpecification/SSP-002 | Only read operations for AAS Registry Service | (✔️) |

For a detailed list of what is checked (and what is not), see [here](doc/api.md).

## Test Setups
<a name="test-setups"></a>

### Check File for Compliance
Given a file in either AASX package format or XML/JSON "raw" format, you can use the Test Engines to check compliance of these files.
Assuming your file is named `my_aas.aasx`, you can invoke the Test Engines using the command line:
<!-- no-check -->
```sh
aas_test_engines check_file my_aas.aasx
```
This will first check, if your aasx package is correct (in terms of relationships etc.).
Then it checks if all contained AAS are compliant to the meta-model and all constraints hold as defined by Part 1 and Part 3a of the specification.
Finally, the Test Engines will iterate over all submodels in your AAS and check if these are compliant to the corresponding submodel templates.

In case you want to check other formats, use the `--format` parameter:
<!-- no-check -->
```sh
aas_test_engines check_file my_aas.json --format json
aas_test_engines check_file my_aas.xml --format xml
```

### Check Server for compliance
To test compliance of an AAS server to the HTTP/REST API, the Test Engines send a series of requests.
Your server should then answer according to the behavior as defined by Part 2 of the specification.
The Test Engines check the conformance of the responses.
For each operation (aka endpoint) we execute a set of negative tests.
These set parameters to invalid values like negative integers for the `limit` parameter.
Afterwards we execute a set of positive tests which set all parameters to valid values and check the response accordingly.

Before starting the actual testing procedure, you need to populate some test data at your server which is stored at `bin/check_servers/test_data`.
Then you start the testing by running passing the url of your server and a profile name:
<!-- no-check -->
```sh
aas_test_engines check_server http://my-server.com/api/v3.0 https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002
```

This starts the testing procedure which may take some seconds.
You may prefer the HTML output for better readability by running:

<!-- no-check -->
```sh
aas_test_engines check_server http://my-server.com/api/v3.0 https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002 --output html > result.html
```

### Handling Authorization
In case your server applies some authorization mechanism for security, you need to pass credentials to the Test Engines.
You can use the `--header` option to do so by providing credentials within header fields:

<!-- no-check -->
```sh
aas_test_engines check_server http://my-server.com/api/v3.0 https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002 --header 'Authorization: Basic YWxhZGRpbjpvcGVuc2VzYW1l'
```

If you need a more sophisticated authorization mechanism, you should use the Python module interface and provide your own `aas_test_engines.http.HttpClient` class.

## Python Module Interface
<a name="python-interface"></a>

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
result = file.check_xml_data(data)
# result.ok() == True

result.dump()
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
from aas_test_engines import api, config, http

client = http.HttpClient(
    host="http://localhost",
)
conf = config.CheckApiConfig(
    suite="https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002",
)

result, mat = api.execute_tests(client, conf)
result.dump()
```

To check older versions pass `version` to the `ApiConfig`:

```python
from aas_test_engines import api, config
print(api.supported_versions())
print(api.latest_version())

conf = config.CheckApiConfig(
    suite="https://admin-shell.io/aas/API/3/0/AssetAdministrationShellRepositoryServiceSpecification/SSP-002",
    version='3.0'
)
```

### Generating test data for software testing

If you develop an AAS application like an AAS editor you may want to use test data to verify correctness of your application.
The test engines allow to generate a set of AAS files which are compliant with the standard and you can therefore use to assess your application as follows:

<!-- no-check -->
```python
from aas_test_engines import file

for is_valid, sample in file.generate():
    print(sample) # or whatever you want to do with it
```
