import networkx as nx
import pandas as pd
import numpy as np

def read_excel_sheet(filename:str, sheetname:str):
    return pd.read_excel(filename, sheet_name=sheetname)

def get_edge_list(df : pd.DataFrame,
                  fac_type : str,
                  u_edge='steps',
                  v_edge='intra_edges'):
    """
    converts two columns of node names (u and v) into a list of string tuples
    for edge definition with networkx

    :param df: DataFrame
        data frame of edges by facility type
    :param fac_type: string
        facility type for which edges are being extracted
    :param u_edge: string
        column in df with edge origin node names
    :param v_edge: string
        column in df with edge destination node names
    :return: list of string tuples
    """
    _out = df[[u_edge, v_edge]].loc[df.facility_type == fac_type].dropna().to_records(index=False).tolist()
    return _out

def get_step_list(df : pd.DataFrame,
                  fac_type : str,
                  u='steps'):
    """
    converts a DataFrame column containing processing steps into a list of
    strings for DiGraph creation

    :param df: DataFrame
        data frame with processing steps by facility type
    :param fac_type: str
        facility type
    :param u: str
        name of data frame column with processing steps
    :return: list of strings
        used to add nodes to a networkx DiGraph
    """
    return df[u].loc[df.facility_type == fac_type].unique().tolist()

def get_node_names(unique_id : int,
                   subgraph_steps: list):
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

def get_cost_methods(df : pd.DataFrame,
                     unique_id : int):
    """

    :param df:
    :param unique_id:
    :return:
    """

def build_subgraph(edge_list: list,
                   step_list: list,
                   steps_costs: dict,
                   facilityID: int):
    """
    Constructs a networkx directed graph object representation of one facility
    or supply chain location

    :param edge_list: list of strings
        List of connections between processing steps
    :param step_list: list of strings
        List of processing steps within this facility
    :param steps_costs: dictionary
        Dictionary where the keys (strings) are the processing steps at this
        facility and the values (floats) are the processing costs (USD/metric
        ton) of each step
    :param facilityID: int
        Unique facility identifier
    :return: DiGraph object
        Directed graph populated with unique node names, processing steps,
         processing costs, and unique facility ID attributes
    """
    # Create empty directed graph object
    facility = nx.DiGraph()

    # Populate the directed graph with node names and facilityIDs (same for
    # all nodes in this graph)
    # @todo vectorize to remove loop
    for i in np.arange(0, len(step_list)):
        facility.add_node(
            step_list[i],
            step=step_list[i],
            cost=None, # @todo add in steps_costs information
            facilityID=facilityID
        )

    # Populate the directed graph with edges
    # Edges within facilities don't have transportation costs or distances
    # associated with them.
    facility.add_edges_from(edge_list,
                            cost=0,
                            distance=0)

    # Use the facility ID and list of processing steps in this facility to
    # create a list of unique node names
    # Unique meaning over the entire supply chain (graph of subgraphs)
    _node_list = get_node_names(facilityID, step_list)

    _labels = {}
    for i in np.arange(0, len(_node_list)):
        _labels.update({step_list[i]: _node_list[i]})

    # Relabel nodes to unique names (step + facility ID)
    nx.relabel_nodes(facility, _labels, copy=False)

    return facility


# the locations dataset will be the largest; try to read that one in line by
# line. All other datasets will be relatively small, so storing and
# manipulating the entire dataset within the Python environment shouldn't
# slow execution down noticeably
mockdata="C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/input-data-mockup.xlsx"
steps_df = read_excel_sheet(mockdata, sheetname='steps')
costs_df = read_excel_sheet(mockdata, sheetname='costs')
interconnect_df = read_excel_sheet(mockdata, sheetname='interconnections')
loc_df = read_excel_sheet(mockdata, sheetname='locations')

# initialize supply chain directed graph
supply_chain = nx.DiGraph()

for index, row in loc_df.iterrows():

    # Get facility type
    _fac_type = row['facility_type']

    # Get unique facility ID
    _facID = row['facility_id']

    # Get the list of processing steps for this facility
    _steps = get_step_list(steps_df, _fac_type)

    # Get the edges within this facility
    _edges = get_edge_list(steps_df, _fac_type)

    # Get the corresponding cost methods
    _cost_methods = costs_df[['steps', 'cost_method']].loc[costs_df.facility_id == _facID]

    # Build the subgraph representation and add it to the list of facility
    # subgraphs
    _fac_graph = build_subgraph(
        edge_list=_edges,
        step_list=_steps,
        steps_costs=_cost_methods,
        facilityID=_facID
    )

    # add onto the supply supply chain graph
    supply_chain.add_nodes_from(_fac_graph)
    supply_chain.add_edges_from(_fac_graph.edges)



# Transportation distances can be pre-calculated and stored as a table, by
# facility ID

# @todo connect to regionalizations: every sub-graph needs a location and a
#  distance to every connected (every other?) sub-graph

# @todo dynamically update node costs based on cost-over-time and learning-by-
#  doing models

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
