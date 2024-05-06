from typing import Dict, List

def _group(elements: list) -> dict:
    assert isinstance(elements, list)
    grouped: Dict[str, List[any]] = {}
    for item in elements:
        assert isinstance(item, dict)
        key = item.get('idShort')
        assert isinstance(key, str)
        try:
            grouped[key].append(item)
        except KeyError:
            grouped[key] = [item]
    return grouped

def group(data: any) -> any:
    if isinstance(data, list):
        data = [group(i) for i in data]
    elif isinstance(data, dict):
        data: dict = {key: group(value) for key, value in data.items()}
        if data.get('modelType') == 'SubmodelElementCollection':
            elements = data.get('value')
            data['value'] = _group(elements)
        elif data.get('modelType') == 'Submodel':
            elements = data.get('submodelElements')
            data['submodelElements'] = _group(elements)
    return data

def _un_group(elements: dict) -> list:
    if not isinstance(elements, dict):
        return elements
    un_grouped: List[str, dict] = []
    for item in elements.values():
        if isinstance(item, list):
            un_grouped.extend(item)
        else:
            un_grouped.append(item)
    return un_grouped

def un_group(data: any) -> any:
    if isinstance(data, list):
        data = [un_group(i) for i in data]
        for idx, value in enumerate(data):
            data[idx] = un_group(value)
    elif isinstance(data, dict):
        data = {key: un_group(value) for key, value in data.items()}
        if data.get('modelType') == 'SubmodelElementCollection':
            elements = data.get('value')
            data['value'] = _un_group(elements)
        elif data.get('modelType') == 'Submodel':
            elements = data.get('submodelElements')
            data['submodelElements'] = _un_group(elements)
    return data
