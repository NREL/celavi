import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from networkx.algorithms import shortest_path

edges_df = pd.read_csv("graph_specification/edges.csv")
nodes_df = pd.read_csv("graph_specification/nodes.csv")

edges_df.dropna(inplace=True, how="all")
nodes_df.dropna(inplace=True, how="all")

nodes = []
for _, row in nodes_df.iterrows():
    node_id = int(row["node_id"])
    name = row["name"]
    nodes.append((node_id, {"name": name}))

edges = []
for _, row in edges_df.iterrows():
    edge_id = int(row["edge_id"])
    weight = row["weight"]
    u_id = row["u_id"]
    v_id = row["v_id"]
    edges.append((u_id, v_id, {"edge_id": edge_id, "weight": weight}))

graph = nx.DiGraph()
graph.add_nodes_from(nodes)
graph.add_edges_from(edges)

path = shortest_path(graph, 1, 3)
print("Path:", list(path))
weight_sum = 0
for i in range(0, len(path) - 1):
    u = path[i]
    v = path[i + 1]
    edge_data = graph.get_edge_data(u, v)
    weight_sum += edge_data["weight"]
print("Total weight: ", weight_sum)

plt.subplot(111)
nx.draw_kamada_kawai(graph, with_labels=True, font_weight="bold")
plt.show()
