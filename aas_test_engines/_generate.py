from fences.json_schema.normalize import normalize, NormalizationConfig
from fences.json_schema.parse import default_config, parse, KeyReference
from fences.json_schema.config import FormatSamples
from fences.core.node import Node as FlowGraph, NoOpDecision, Leaf

default_samples = {
    'xs:decimal': FormatSamples(
        valid=["10.4"]
    ),
    "xs:integer": FormatSamples(
        valid=["12"]
    ),
    "xs:float": FormatSamples(
        valid=["12"]
    ),
    "xs:double": FormatSamples(
        valid=["12"]
    ),
    "xs:time": FormatSamples(
        valid=["14:23:00"],
    ),
    "xs:date": FormatSamples(
        valid=["2000-01-01+12:05"]
    ),
    "xs:dateTime": FormatSamples(
        valid=["2000-01-01T14:23:00.66372+14:00"]
    ),
    "xs:dateTimeUTC": FormatSamples(
        valid=["2000-01-01T14:23:00Z"]
    ),
    "xs:gYearMonth": FormatSamples(
        valid=["2000-01+03:00"]
    ),
    "xs:gMonthDay": FormatSamples(
        valid=["--01-01"]
    ),
    "xs:gYear": FormatSamples(
        valid=["2000"]
    ),
    "xs:gMonth": FormatSamples(
        valid=["--04"]
    ),
    "xs:gDay": FormatSamples(
        valid=["---10"],
    ),
    "xs:duration": FormatSamples(
        valid=["-P1Y2M3DT1H"],
    ),
    "xs:byte": FormatSamples(
        valid=["12"]
    ),
    "xs:short": FormatSamples(
        valid=["12"]
    ),
    "xs:int": FormatSamples(
        valid=["12"]
    ),
    "xs:negativeInteger": FormatSamples(
        valid=["-12"]
    ),
    "xs:long": FormatSamples(
        valid=["12"]
    ),
    "xs:nonNegativeInteger": FormatSamples(
        valid=["12"]
    ),
    "xs:nonPositiveInteger": FormatSamples(
        valid=["-12"]
    ),
    "xs:positiveInteger": FormatSamples(
        valid=["12"]
    ),
    "xs:unsignedByte": FormatSamples(
        valid=["12"]
    ),
    "xs:unsignedInt": FormatSamples(
        valid=["12"]
    ),
    "xs:unsignedShort": FormatSamples(
        valid=["12"]
    ),
    "xs:unsignedLong": FormatSamples(
        valid=["12"]
    ),
    "xs:base64Binary": FormatSamples(
        valid=["AA=="]
    ),
    "xs:anyURI": FormatSamples(
        valid=["http://example.com"]
    ),
    "bcpLangString": FormatSamples(
        valid=["de"]
    ),
    'version': FormatSamples(
        valid=['567'],
    ),
    'contentType': FormatSamples(
        valid=["application/json"],
    ),
    'path': FormatSamples(
        valid=["file://example.com/myfile"],
    ),
}

def post_process(entry: dict, result: FlowGraph) -> FlowGraph:
    try:
        check = entry['check']
    except KeyError:
        return result
    sub_root = NoOpDecision(all_transitions=True)
    sub_root.add_transition(result)
    check = entry['check']
    for ch in check:
        if ch == 'Constraint_AASd-124':
            class FixConstraint124(Leaf):
                def apply(self, data: KeyReference) -> any:
                    try:
                        keys = data.get()['keys']
                    except (KeyError, TypeError):
                        return data
                    if not isinstance(keys, list):
                        return data
                    keys.append({
                        'type': 'GlobalReference',
                        'value': 'xyz'
                    })
                    return data
            sub_root.add_transition(FixConstraint124(is_valid=True))
        elif ch == 'Constraint_AASd-125':
            class FixConstraint125(Leaf):
                def apply(self, data: KeyReference) -> any:
                    try:
                        keys: list = data.get()['keys']
                    except (KeyError, TypeError):
                        return data
                    if isinstance(keys, list):
                        for key in keys[1:]:
                            if isinstance(key, dict):
                                key['type'] = 'Range'
                    return data
            sub_root.add_transition(FixConstraint125(is_valid=True))
        elif ch == 'Constraint_AASd-107':
            class FixConstraint107(Leaf):
                def apply(self, data: KeyReference) -> any:
                    l: list = data.get()
                    try:
                        l['semanticIdListElement'] = l['value'][0]['semanticId']
                    except (KeyError, TypeError):
                        pass
                    return data
            sub_root.add_transition(FixConstraint107(is_valid=True))
        elif ch == 'Constraint_AASd-108':
            class FixConstraint108(Leaf):
                def apply(self, data: KeyReference) -> any:
                    l: list = data.get()
                    try:
                        l['typeValueListElement'] = l['value'][0]['modelType']
                    except (KeyError, TypeError):
                        pass
                    return data
            sub_root.add_transition(FixConstraint108(is_valid=True))
        elif ch == 'Constraint_AASd-109':
            class FixConstraint109(Leaf):
                def apply(self, data: KeyReference) -> any:
                    l: list = data.get()
                    try:
                        if l['typeValueListElement'] in ['Property', 'Range']:
                            l['valueTypeListElement'] = l['value'][0]['valueType']
                    except (KeyError, TypeError):
                        pass
                    return data
            sub_root.add_transition(FixConstraint109(is_valid=True))
        elif ch == 'Constraint_AASd-119':
            class FixConstraint119(Leaf):
                def apply(self, data: KeyReference) -> any:
                    d: dict = data.get()
                    try:
                        if any(i.get('kind') == 'TemplateQualifier' for i in d['qualifiers']):
                            d['kind'] = 'Template'
                    except (KeyError, TypeError, AttributeError):
                        pass
                    return data
            sub_root.add_transition(FixConstraint119(is_valid=True))
        elif ch == 'Constraint_AASd-129':
            class FixConstraint129(Leaf):
                def apply(self, data: KeyReference) -> any:
                    d: dict = data.get()
                    try:
                        submodel_elements = d.get('submodelElements', [])
                        for element in submodel_elements:
                            if any(i.get('kind') == 'TemplateQualifier' for i in element['qualifiers']):
                                d['kind'] = 'Template'
                                break
                    except (KeyError, TypeError, AttributeError):
                        pass
                    return data
            sub_root.add_transition(FixConstraint129(is_valid=True))
        elif ch == 'Constraint_AASd-134':
            class FixConstraint134(Leaf):
                def apply(self, data: KeyReference) -> any:
                    d: dict = data.get()
                    try:
                        for idx, var in enumerate(d['inputVariables']):
                            var['value']['idShort'] = f"i{idx}"
                    except (KeyError, TypeError):
                        pass
                    try:
                        for idx, var in enumerate(d['outputVariables']):
                            var['value']['idShort'] = f"o{idx}"
                    except (KeyError, TypeError):
                        pass
                    try:
                        for idx, var in enumerate(d['inoutputVariables']):
                            var['value']['idShort'] = f"io{idx}"
                    except (KeyError, TypeError):
                        pass
                    return data
            sub_root.add_transition(FixConstraint134(is_valid=True))
        elif ch == 'Constraint_AASc-3a-002':
            class FixConstraint008(Leaf):
                def apply(self, data: KeyReference) -> any:
                    d: dict = data.get()
                    try:
                        d['preferredName'] = [{
                            'language': 'en',
                            'text': 'xyz',
                        }]
                    except (KeyError, TypeError, AttributeError) as e:
                        pass
                    return data
            sub_root.add_transition(FixConstraint008(is_valid=True))
        elif ch == 'Constraint_AASc-3a-008':
            class FixConstraint008(Leaf):
                def apply(self, data: KeyReference) -> any:
                    d: dict = data.get()
                    try:
                        if 'value' not in d:
                            d['definition'] = [{
                                'language': 'en',
                                'text': 'xyz',
                            }]
                    except (KeyError, TypeError, AttributeError) as e:
                        pass
                    return data
            sub_root.add_transition(FixConstraint008(is_valid=True))
    return sub_root


def generate_graph(schema) -> FlowGraph:
    norm_config = NormalizationConfig(
        full_merge=False,
        additional_mergers={
            'check': lambda x, y: x + y
        },
        detect_duplicate_subschemas=True,
    )
    schema_norm = normalize(schema, norm_config)
    config = default_config()
    config.normalize = False
    config.format_samples = default_samples
    config.post_processor = post_process
    graph = parse(schema_norm, config)
    return graph
