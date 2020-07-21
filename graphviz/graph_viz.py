import pygraphviz as pgv

G = pgv.AGraph(strict=False, directed=True)

G.add_edge("use", "use", label="reusing")
G.add_edge("use", "landfill", label="landfilling")
G.add_edge("use", "recycle", label="recycling")
G.add_edge("use", "remanufacture", label="remanufacturing")
G.add_edge("recycle", "remanufacture", label="remanufacturing")
G.add_edge("remanufacture", "use", label="using")

G.write("file.dot")
# Render with "dot -Tpng file.dot -o out.png"
