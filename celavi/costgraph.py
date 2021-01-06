import networkx as nx

# @note a facility ID for all nodes, s.t. nodes within the same sub-graph
# (location) are marked as being co-located at the same facility.
# Then at the Supply Chain graph level, edges between nodes with the same
# facility ID incur no transportation costs or distances.
# This could help automate edge creation.

# Transportation distances can be pre-calculated and stored as a table, by
# facility location.

# Create lists of processes/steps within each facility location
# Each facility needs a list of nodes (one node = one step) and a corresponding
# list of costs incurred at each node (processing costs)
power_plant_nodes = ['in use', 'rotor teardown', 'coarse grinding', 'segmenting']
power_plant_node_costs = [0.0, 1000.0, 15.0, 11.0]
power_plant_facility_id = 1

rec_facility_nodes = ['facility coarse grinding', 'facility fine grinding']
rec_facility_node_costs = [120.0, 220.0]
rec_facility_id = 2

cement_plant_nodes = ['cement co-processing']
cement_plant_node_costs = [-11.0]
cement_plant_facility_id = 3

landfill_nodes = ['landfill']
landfill_node_costs = [54.0]
landfill_facility_id = 4

# This list of lists contains all options for processes, organized by location
node_list = [power_plant_nodes, rec_facility_nodes,
             cement_plant_nodes, landfill_nodes]


# a sub-graph for processes/steps located at the power plant
# Processes: turbines in use, coarse grinding, blade segmenting
# Edges within sub-graphs will always have cost = 0.0 (no transportation costs)
# and distance = 0.0 (co-located steps have no transportation between them)
plant = nx.DiGraph()
plant.add_nodes_from(power_plant_nodes, cost=power_plant_node_costs,
                     facilityID=power_plant_facility_id)
plant.add_edges_from([('in use', 'rotor teardown')], cost=0.0, distance=0.0)
plant.add_edges_from([('rotor teardown', 'coarse grinding')], cost=0.0, distance=0.0)
plant.add_edges_from([('rotor teardown', 'segmenting')], cost=0.0, distance=0.0)

# a sub-graph for processes/steps located at the recycling facility
recycle = nx.DiGraph()
recycle.add_nodes_from(rec_facility_nodes, cost=rec_facility_node_costs,
                       facilityID=rec_facility_id)
recycle.add_edges_from([('facility coarse grinding', 'facility fine grinding')], cost=0.0, distance=0.0)

# a sub-graph for processes/steps located at the landfill
landfill = nx.DiGraph()
landfill.add_nodes_from(landfill_nodes, cost=landfill_node_costs,
                        facilityID=landfill_facility_id)

# the Supply Chain graph contains all sub-graphs
# Each sub-graph represents one facility location and all processes/steps that
# occur there.
# Additional edges representing transportation between facility locations
# are added at the Supply Chain graph level
supply_chain = nx.DiGraph()
supply_chain.add_nodes_from(plant)
supply_chain.add_nodes_from(recycle)
supply_chain.add_nodes_from(landfill)
supply_chain.add_edges_from(plant.edges)
supply_chain.add_edges_from(recycle.edges)
supply_chain.add_edges_from(landfill.edges)

# onsite coarse grinding to facility fine grinding
supply_chain.add_edges_from([('coarse grinding', 'facility fine grinding')], cost=0.08, distance=54.0)

# onsite coarse grinding to landfill
supply_chain.add_edges_from([('coarse grinding', 'landfill')], cost=0.08, distance=42.0)

# onsite segmenting to landfill
supply_chain.add_edges_from([('segmenting', 'landfill')], cost=12.0, distance=42.0)

# fine grinding to landfill - MANDATORY if this node is used
supply_chain.add_edges_from([('facility fine grinding', 'landfill')], cost=0.08, distance=2.0)

# The edges between sub-graphs will have different transportation costs depending
# on WHAT's being moved: blade segments or ground/shredded blade material.
# @note Is there a way to also track component-material "status" or general
# characteristics as it traverses the graph? Maybe connecting this graph to
# the state machine
