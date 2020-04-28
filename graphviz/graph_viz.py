import pygraphviz as pgv

G = pgv.AGraph(strict=False,directed=True)

G.add_edge("wind plant", "wind plant")
G.add_edge("wind plant", "landfill")
G.add_edge("wind plant", "recycler")
G.add_edge("wind plant", "remanufacturer")
G.add_edge("recycler", "remanufacturer")
G.add_edge("remanufacturer", "wind plant")

G.write("file.dot")
