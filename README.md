# Test Tools for the Asset Administration Shell

The Asset Administration Shell (AAS) is a standard for Digital Twins.
It can be found [here](https://industrialdigitaltwin.org/content-hub/downloads).

For a given implementation of the AAS standard, these test tools offer measures to ensure compliance.

## Check AAS Type 1 (File)

### Check AASX:
```python
from aas_test_tools import file
from xml.etree import ElementTree

with open('aas.aasx') as f:
    file.check_aasx_file(f)
```

### Check JSON:

```python
from aas_test_tools import file

# Check file
with open('aas.json') as f:
    file.check_json_file(f)

# Or check data directly
aas = {
    'assetAdministrationShells': [],
    'submodels': [],
    'conceptDescriptions': []
}
file.check_json_data(aas)
```

### Check XML:
```python
from aas_test_tools import file
from xml.etree import ElementTree

# Check file
with open('aas.xml') as f:
    file.check_xml_file(f)

# Or check data directly
data = ElementTree.fromstring(
    '<environment xmlns="https://admin-shell.io/aas/3/0" />')
file.check_xml_data(aas)
```

### Checking older versions

By default, the `file.check...` methods check compliance to version 3.0.0 of the standard.
You may want to check against older versions by passing a string containing the version to these methods.

You can query the list of supported versions as follows:

```python
from aas_test_tools import file

print(file.supported_versions)
```

## Check AAS Type 2 (HTTP API)

