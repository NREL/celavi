import pandas as pd
import networkx as nx

edges_df = pd.read_csv("graph_specification/edges.csv")
nodes_df = pd.read_csv("graph_specification/nodes.csv")

edges_df.dropna(inplace=True, how="all")
nodes_df.dropna(inplace=True, how="all")

nodes = []
for _, row in nodes_df.iterrows():
    node_id = int(row["node_id"])
    name = row["name"]
    nodes.append((node_id, {"name": name}))

graph = nx.DiGraph()
graph.add_nodes_from(nodes)

print(graph.number_of_nodes())
