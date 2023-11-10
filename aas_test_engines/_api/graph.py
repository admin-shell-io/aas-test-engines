import pydot
import openapi


def to_graph(api: openapi.OpenApi):

    graph = pydot.Dot("link_dependencies", graph_type="digraph")

    for path in api.paths:
        for operation in path.operations:
            graph.add_node(pydot.Node(
                operation.operation_id,
                label=operation.operation_id + "\n" + operation.method.upper() + " " +
                path.path,
                shape="rect",
            ))
            for param in operation.parameters:
                if param.source_link:
                    graph.add_edge(pydot.Edge(
                        param.source_link.source_operation.operation_id,
                        operation.operation_id,
                        color="blue",
                        label=param.name,
                    ))

    return graph
