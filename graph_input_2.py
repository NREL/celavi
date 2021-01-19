import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms import shortest_path
from collections import Counter

id_counter = Counter()

facility_configurations = {
    "wind_plant": {
        "nodes": {
            # Nodes cannot be repeated!
            "turbines": {},
            "segmenting": {},
            "coarse_grinding": {},
            "concrete_production": {}
        },
        "internal_edges": [
            ["turbines", "segmenting"],
            ["segmenting", "coarse_grinding"],
            ["coarse_grinding", "concrete_production"]
        ]
    }
}

facility_types = [
    "wind_plant",
    "wind_plant",
    "wind_plant",
]

subgraphs = []

for facility_type in facility_types:
    subgraph = nx.DiGraph()
    if facility_type not in facility_configurations:
        raise KeyError(f"{facility_type} is not valid")
    configuration = facility_configurations[facility_type]
    facility_node_ids = {}
    for node in configuration["nodes"]:
        node_id = f"{node}_{id_counter[node]}"
        subgraph.add_node(node_id)
        facility_node_ids[node] = node_id
        id_counter[node] += 1
    for u_node, v_node in configuration["internal_edges"]:
        u_node_id = facility_node_ids[u_node]
        v_node_id = facility_node_ids[v_node]
        subgraph.add_edge(u_node_id, v_node_id)
    subgraphs.append(subgraph)

total_graph = nx.DiGraph()

for subgraph in subgraphs:
    total_graph.add_nodes_from(subgraph.nodes)
    total_graph.add_edges_from(subgraph.edges)

print(total_graph.edges)
