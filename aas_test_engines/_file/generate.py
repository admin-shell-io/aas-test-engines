from fences.json_schema.normalize import normalize
from fences.json_schema.parse import default_config
from fences.json_schema.parse import parse
from fences.core.node import Node as FlowGraph


def generate_graph(schema) -> FlowGraph:
    # TODO: remove these after fixing fences.core.exception.InternalException: Decision without valid leaf detected
    del schema['$defs']['AssetInformation']['allOf'][1]['properties']['specificAssetIds']['items']['allOf'][0]
    del schema['$defs']['Entity']['allOf'][1]
    schema_norm = normalize(schema, False)
    config = default_config()
    config.normalize = False
    graph = parse(schema_norm, config)
    return graph
