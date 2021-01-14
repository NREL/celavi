import networkx as nx
import pandas as pd
import pdb

# @todo resolve relative import with no known parent package error
from .unique_identifier import UniqueIdentifier

def read_excel_sheet(filename:str, sheetname:str):
    return pd.read_excel(filename, sheet_name=sheetname)

def get_node_names(unique_id, subgraph_steps: list):
    """
    Generates a list of unique node names for a single facility subgraph.

    Parameters
    ----------
    unique_id: int
        Unique facility identifier.

    subgraph_steps: list of strings
        List of processing steps at this facility

    Returns
    -------
    list of strings
        List of unique node IDs created from processing step and facility ID
    """
    return ["{}{}".format(i, str(unique_id)) for i in subgraph_steps]

# @todo automate creation of sub-graphs
def build_subgraph(edge_list: list, step_list: list,
                   steps_costs: dict, facilityID: int):
    """
    Constructs a networkx directed graph object representation of one facility
    or supply chain location

    :param edge_list: list of strings
        List of connections between processing steps
    :param steps_costs: dictionary
        Dictionary where the keys (strings) are the processing steps at this
        facility and the values (floats) are the processing costs (USD/metric
        ton) of each step
    :param facilityID:

    :return: DiGraph object
        Directed graph populated with unique node names, processing steps,
         processing costs, and unique facility ID attributes
    """
    # Create empty directed graph object
    facility = nx.DiGraph()

    # Use the facility ID and list of processing steps in this facility to
    # create a list of unique node names
    # Unique meaning over the entire supply chain (graph of subgraphs)
    _node_list = get_node_names(facilityID, step_list)

    # Populate the directed graph with nodes and attributes
    facility.add_nodes_from(_node_list,
                            steps=step_list,
                            cost=steps_costs,
                            facilityID=facilityID)

    # Populate the directed graph with edges
    # Edges within facilities don't have transportation costs or distances
    # associated with them.
    facility.add_edges_from(edge_list, cost=0.0, distance=0.0)

    return facility

# the locations dataset will be the largest; try to read that one in line by
# line. All other datasets will be relatively small, so storing and
# manipulating the entire dataset within the Python environment shouldn't
# slow execution down noticeably
mockdata="C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/input-data-mockup.xlsx"
steps_df = read_excel_sheet(mockdata, sheetname='processes')
costs_df = read_excel_sheet(mockdata, sheetname='costs')
interconnect_df = read_excel_sheet(mockdata, sheetname='interconnections')
loc_df = read_excel_sheet(mockdata, sheetname='locations')

facility_list = []

for index, row in loc_df.iterrows():

    # Determine facility type
    _fac_type = row['facility_type']

    # Generate unique facility ID
    # @todo replace index with UniqueIdentifier once import error is resolved
    _facID = index

    # Get the list of processing steps (-> nodes) and edges for this facility
    _steps = steps_df['steps'].loc[steps_df.facility_type == _fac_type]

    # Use unique facility ID to create unique-to-this-facility node names
    _nodes = get_node_names(_facID, _steps)

    # Get the edges within this facility
    # @todo how to create edges based on the uniqueified node names?
    _edges = steps_df['intra_edges'].loc[steps_df.facility_type == _fac_type]

    # Get the corresponding cost methods
    _cost_methods = costs_df['cost_method'].loc[costs_df.facility_type == _fac_type]

    # Build the subgraph representation and add it to the list of facility
    # subgraphs
    facility_list.append(build_subgraph(_edges, _nodes, _cost_methods, _facID))


# Transportation distances can be pre-calculated and stored as a table, by
# facility ID

## Create a subgraph from a list of edges

# Given a list of string pairs, get a list of unique values
# This is the list of processing steps in the facility
power_plant_steps_costs = {'in use': 0, 'rotor teardown': 1000.0, 'coarse grinding': 15.0, 'segmenting': 11.0}
power_plant_edges = [('in use', 'rotor teardown'), ('rotor teardown', 'coarse grinding'), ('rotor teardown', 'segmenting')]
power_plant_facility_id = 1
power_plant_steps = power_plant_steps_costs.keys()
power_plant_nodes = get_node_names(power_plant_facility_id, power_plant_steps_costs.keys())

# From the processing steps, append the facility ID to create unique node names
power_plant_nodes = get_node_names(power_plant_facility_id, power_plant_steps)


# @todo connect to regionalizations: every sub-graph needs a location and a
#  distance to every connected (every other?) sub-graph

# @todo dynamically update node costs based on cost-over-time and learning-by-
#  doing models

# @todo identify input data structure
power_plant_steps = ['in use', 'rotor teardown', 'coarse grinding', 'segmenting']
power_plant_edges = [('in use', 'rotor teardown'), ('rotor teardown', 'coarse grinding'), ('rotor teardown', 'segmenting')]
power_plant_node_costs = [0.0, 1000.0, 15.0, 11.0]



rec_facility_steps = ['facility coarse grinding', 'facility fine grinding']
rec_facility_edges = [('facility coarse grinding', 'facility fine grinding')]
rec_facility_node_costs = [120.0, 220.0]
rec_facility_id = 2

cement_plant_steps = ['cement co-processing']
cement_plant_node_costs = [-11.0]
cement_plant_facility_id = 3

landfill_steps = ['landfill']
landfill_node_costs = [54.0]
landfill_facility_id = 4

# Create lists of processes/steps within each facility location
# Each facility needs a list of nodes (one node = one step) and a corresponding
# list of costs incurred at each node (processing costs)

power_plant_nodes = get_node_names(power_plant_facility_id, power_plant_steps)
rec_facility_nodes = get_node_names(rec_facility_id, rec_facility_steps)
cement_plant_nodes = get_node_names(cement_plant_facility_id, cement_plant_steps)
landfill_nodes = get_node_names(landfill_facility_id, landfill_steps)


plant = build_subgraph(power_plant_nodes, power_plant_edges,
                       power_plant_steps, power_plant_node_costs,
                       power_plant_facility_id)

# a sub-graph for processes/steps located at the recycling facility
recycle = nx.DiGraph()
recycle.add_nodes_from(rec_facility_nodes,
                       steps=rec_facility_steps,
                       cost=rec_facility_node_costs,
                       facilityID=rec_facility_id)
recycle.add_edges_from(rec_facility_edges, cost=0.0, distance=0.0)

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

# onsite segmenting to facility coarse grinding
supply_chain.add_edges_from([('segmenting', 'facility coarse grinding')], cost=12.0, distance=54.0)

# onsite coarse grinding to landfill
supply_chain.add_edges_from([('coarse grinding', 'landfill')], cost=0.08, distance=42.0)

# onsite segmenting to landfill
supply_chain.add_edges_from([('segmenting', 'landfill')], cost=12.0, distance=42.0)

# fine grinding to landfill - MANDATORY if this node is used
supply_chain.add_edges_from([('facility fine grinding', 'landfill')], cost=0.08, distance=2.0)

# These are here to force consistency of edge data, otherwise they do not have edge
# data

supply_chain.add_edges_from([('in use', 'rotor teardown')], cost=0.0, distance=0.0)
supply_chain.add_edges_from([('rotor teardown', 'segmenting')], cost=0.0, distance=0.0)
supply_chain.add_edges_from([('rotor teardown', 'coarse grinding')], cost=0.0, distance=0.0)
supply_chain.add_edges_from([('facility coarse grinding', 'facility fine grinding')], cost=0.0, distance=0.0)

# The edges between sub-graphs will have different transportation costs depending
# on WHAT's being moved: blade segments or ground/shredded blade material.
# @note Is there a way to also track component-material "status" or general
#  characteristics as it traverses the graph? Maybe connecting this graph to
#  the state machine

# Calculate total pathway costs (sum of all node and edge costs) over all
# possible pathways

# @note simple paths have no repeated nodes; this might not work for a cyclic
#  graph
# The target parameter can be replaced by a list

# @note the generator from all_simple_paths can only be used once per definition
path_edge_list = list([])

# Get list of nodes and edges by pathway
for path in map(nx.utils.pairwise, nx.all_simple_paths(supply_chain, source='in use', target='landfill')):
    path_edge_list.append(list(path))

path_node_list = list(nx.all_simple_paths(supply_chain, source='in use', target='landfill'))

# dictionary defining all possible pathways by nodes and edges
# nodes = calculate total processing costs
# edges = calculate total transportation costs and distances
paths_dict = {'nodes': path_node_list, 'edges': path_edge_list}

for edges in paths_dict['edges']:
    for u, v in edges:
        print(u, v, supply_chain.get_edge_data(u, v))

for nodes, edges in zip(path_node_list, path_edge_list):
    costs = [supply_chain.get_edge_data(u, v)['cost'] for u, v in edges]
    distances = [supply_chain.get_edge_data(u, v)['distance'] for u, v in edges]
    graph_path = ",".join(nodes)
    print(f"Path: {graph_path}. Total cost={sum(costs)}, total distance={sum(distances)}")
