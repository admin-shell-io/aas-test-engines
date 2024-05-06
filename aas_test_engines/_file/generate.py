from fences.json_schema.normalize import normalize
from fences.json_schema.parse import default_config
from fences.json_schema.parse import parse
from fences.core.node import Node as FlowGraph

def generate_graph(schema) -> FlowGraph:
    schema_norm = normalize(schema, False)
    config = default_config()
    config.normalize = False
    graph = parse(schema_norm, config)
    return graph
