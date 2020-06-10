import pygraphviz as pgv

G = pgv.AGraph(strict=False, directed=True)

G.add_edge("use", "use", label="reusing")
G.add_edge("use", "landfill", label="landfilling")
G.add_edge("use", "recycler", label="recycling")
G.add_edge("use", "remanufacturer", label="remanufacturing")
G.add_edge("recycler", "remanufacturer", label="remanufacturing")
G.add_edge("remanufacturer", "use", label="using")

G.write("file.dot")
# Render with "dot -Tpng file.dot -o out.png"
