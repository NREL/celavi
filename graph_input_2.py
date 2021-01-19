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
            ["turbines", "segmenting", 0],
            ["segmenting", "coarse_grinding", 0],
            ["coarse_grinding", "concrete_production", 0],
            ["concrete_production", "turbines", 0]
        ],
        "outbound_edges": [
            ["segmenting", "landfill_0", 99]
        ]
    },

    "landfill": {
        "nodes": {
            "landfill": {}
        },
        "entry_node": "landfill"
    }
}

facility_types = [
    "landfill",
    "wind_plant",
    "wind_plant"
]

subgraphs = []

for facility_type in facility_types:
    subgraph = nx.DiGraph(outbound_edges=[], node_type_to_id={})
    if facility_type not in facility_configurations:
        raise KeyError(f"{facility_type} is not valid")
    configuration = facility_configurations[facility_type]
    facility_node_ids = {}
    for node, node_data in configuration["nodes"].items():
        node_id = f"{node}_{id_counter[node]}"
        subgraph.add_node(node_id)
        facility_node_ids[node] = node_id
        id_counter[node] += 1
    if "internal_edges" in configuration:
        for u_node, v_node, weight in configuration["internal_edges"]:
            u_node_id = facility_node_ids[u_node]
            v_node_id = facility_node_ids[v_node]
            subgraph.add_edge(u_node_id, v_node_id, weight=weight)
    if "outbound_edges" in configuration:
        outbound_edges = []
        for u_node, v_node_id, weight in configuration["outbound_edges"]:
            u_node_id = facility_node_ids[u_node]
            outbound_edges.append([u_node_id, v_node_id, weight])
        subgraph.graph["outbound_edges"].extend(outbound_edges)
    subgraphs.append(subgraph)

total_graph = nx.DiGraph()

# First pass: Establish the subgraphs as islands
for subgraph in subgraphs:
    total_graph.add_nodes_from(subgraph.nodes)
    total_graph.add_edges_from(subgraph.edges)

# Second pass: establish the connections among islands
for subgraph in subgraphs:
    outbound_edges = subgraph.graph["outbound_edges"]
    for u_node_id, v_node_id, weight in outbound_edges:
        total_graph.add_edge(u_node_id, v_node_id, weight=weight)

plt.subplot(111)
# nx.draw_kamada_kawai(total_graph, with_labels=True, font_weight="bold")
nx.draw(total_graph, with_labels=True)
plt.show()
