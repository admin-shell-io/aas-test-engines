from typing import Dict, List, Tuple
import base64


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


def b64urlsafe(value: str) -> str:
    return base64.urlsafe_b64encode(value.encode()).decode()


def normpath(path: str) -> str:
    """
    Normalizes a given path.
    E.g. normpath('///a/../b/)') == '/b'
    This implementation is platform independent and behaves like os.normpath on a unix system.
    See https://docs.python.org/3/library/os.path.html#os.path.normpath for more details.
    """
    path = path.strip()
    if len(path) == 0:
        return ''
    result = []
    for token in path.split("/"):
        if token.strip() == '' or token == '.':
            continue
        if token == '..':
            if result:
                result.pop()
        else:
            result.append(token)
    if path.startswith('/'):
        return "/" + "/".join(result)
    else:
        return "/".join(result)


def splitpath(path: str) -> Tuple[str, str]:
    """
    Splits a path into a pair (head, tail)
    This implementation is platform independent and behaves like os.path.split on a unix system.
    See https://docs.python.org/3/library/os.path.html#os.path.split for more details.
    """
    prefix, _, suffix = path.rpartition('/')
    return prefix, suffix
