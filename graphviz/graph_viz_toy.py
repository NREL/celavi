import pygraphviz as pgv

G = pgv.AGraph(strict=False, directed=True)

G.add_edge("use 1", "teardown 1", label=0)
G.add_edge("teardown 1", "segmenting 1", label=0)
G.add_edge("segmenting 1", "coarse grinding 1", label=11)
G.add_edge("coarse grinding 1", "cement processing 1", label=0.08)
G.add_edge("cement processing 1", "use 1", label=0.08)

G.add_edge("use 2", "teardown 2", label=0)
G.add_edge("teardown 2", "segmenting 2", label=0)
G.add_edge("segmenting 2", "coarse grinding 2", label=11)
G.add_edge("coarse grinding 2", "cement processing 2", label=0.08)
G.add_edge("cement processing 2", "use 2", label=0.08)

G.add_edge("coarse grinding 1", "fine grinding", label=0.08)
G.add_edge("coarse grinding 2", "fine grinding", label=0.08)
G.add_edge("fine grinding", "other sectors", label=0)

G.add_edge("fine grinding", "landfill 3", label=0.08)

G.write("toy.dot")
# Render with "dot -Tpng file.dot -o out.png"
