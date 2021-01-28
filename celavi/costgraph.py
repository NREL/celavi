import networkx as nx
from csv import reader
import pandas as pd
import numpy as np

# the locations dataset will be the largest; try to read that one in line by
# line. All other datasets will be relatively small, so storing and
# manipulating the entire dataset within the Python environment shouldn't
# slow execution down noticeably
mockdata = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/input-data-mockup.xlsx"
steps_df = pd.read_excel(mockdata, sheet_name='steps')
costs_df = pd.read_excel(mockdata, sheet_name='costs')
interconnect_df = pd.read_excel(mockdata, sheet_name='interconnections')
loc_df = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/loc-mock.csv"

# @todo investigate csv module DictReader object for defining node attributes



# @todo move cost methods here

# @note cost, next state, relocation destination for the component

class CostGraph():
    """

    """

    def __init__(self, input_name):
        """

        Parameters
        ----------
        input_name

        """
        # @todo get input_name to read in the small datasets
        self.steps_df=None
        self.costs_df=None
        self.interconnect_df=None

        # for the dataset containing all facilities, save the filename to
        # self and process it line by line in a method
        self.loc_df=None

        # create empty instance variable for supply chain DiGraph
        self.supply_chain = nx.DiGraph()


    @staticmethod
    def read_excel_sheet(filename:str, sheetname:str):
        """

        Parameters
        ----------
        filename
        sheetname

        Returns
        -------

        """
        # @todo remove or replace with input datatype-appropriate method
        return pd.read_excel(filename, sheet_name=sheetname)

    def get_edge_list(self,
                      facilityType : str,
                      u_edge='steps',
                      v_edge='intra_edges'):
        """
        # @todo reformat and update docstring
        converts two columns of node names (u and v) into a list of string tuples
        for edge definition with networkx

        :param df: DataFrame
            data frame of edges by facility type
        :param facilityType: string
            facility type for which edges are being extracted
        :param u_edge: string
            column in df with edge origin node names
        :param v_edge: string
            column in df with edge destination node names
        :return: list of string tuples
        """
        _out = self.steps_df[[u_edge, v_edge]].loc[self.steps_df.facility_type == facilityType].dropna().to_records(index=False).tolist()
        return _out


    def get_step_list(self,
                      facilityType : str,
                      u='steps'):
        """
        # @todo reformat and update docstring
        converts a DataFrame column containing processing steps into a list of
        strings for DiGraph creation

        :param df: DataFrame
            data frame with processing steps by facility type
        :param facilityType: str
            facility type
        :param u: str
            name of data frame column with processing steps
        :return: list of strings
            used to add nodes to a networkx DiGraph
        """
        return self.steps_df[u].loc[self.steps_df.facility_type == facilityType].unique().tolist()

    @staticmethod
    def get_node_names(facilityID : [int, str],
                       subgraph_steps: list):
        """
        Generates a list of unique node names for a single facility subgraph.

        Parameters
        ----------
        facilityID: [int, str]
            Unique facility identifier.

        subgraph_steps: list of strings
            List of processing steps at this facility

        Returns
        -------
        list of strings
            List of unique node IDs created from processing step and facility ID
        """
        return ["{}{}".format(i, str(facilityID)) for i in subgraph_steps]

    # @todo THOUGHT: method to assemble dict of node attributes including
    #  processing step, method for cost calculations, unique facility ID,
    #  region identifiers, ...

    def get_cost_methods(self,
                         facilityID : [int, str],
                         steps_col='steps',
                         cost_method_col='cost_method'):
        """
        # @todo update docstring
        Parameters
        ----------
        facilityID
        steps_col
        cost_method_col

        Returns
        -------

        """
        return self.costs_df[[steps_col, cost_method_col]].loc[self.costs_df.facility_id == facilityID]


    def build_facility_graph(self,
                             facilityID: [int, str],
                             facilityType: str):
        """
        # @todo update docstring format and content
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
        :param facilityID: [int, str]
            Unique facility identifier
        :param facilityType: str
        :return: DiGraph object
            Directed graph populated with unique node names, processing steps,
             processing costs, and unique facility ID attributes
        """
        # Create empty directed graph object
        _facility = nx.DiGraph()

        # Get the list of processing steps for this facility
        _steps = self.get_step_list(facilityType)

        # Get the edges within this facility
        _edges = self.get_edge_list(facilityType)

        # Get the corresponding cost methods
        _cost_methods = self.get_cost_methods(facilityID)

        # Populate the directed graph with node names and facilityIDs (same for
        # all nodes in this graph)
        # @todo vectorize to remove loop
        for i in np.arange(0, len(_steps)):
            _facility.add_node(
                _steps[i], #node name, to be uniquified
                step=_steps[i], #processing step at this node
                cost=None, # @todo add in cost method information
                facilityID=facilityID # unique facility ID
            )

        # Populate the directed graph with edges
        # Edges within facilities don't have transportation costs or distances
        # associated with them.
        _facility.add_edges_from(_edges,
                                cost=0,
                                distance=0)

        # Use the facility ID and list of processing steps in this facility to
        # create a list of unique node names
        # Unique meaning over the entire supply chain (graph of subgraphs)
        _node_list = self.get_node_names(facilityID, _steps)

        _labels = {}
        for i in np.arange(0, len(_node_list)):
            _labels.update({_steps[i]: _node_list[i]})

        # Relabel nodes to unique names (step + facility ID)
        nx.relabel_nodes(_facility, _labels, copy=False)

        return _facility


    def build_supplychain_graph(self):
        """
        # @todo update docstring
        """

        with open(self.loc_df, 'r') as _loc_file:
            _loc_csv = reader(_loc_file)

            for _line in _loc_csv:

                # Get unique facility ID
                _facID = _line[0]

                # Get facility type
                _factype = _line[1]

                # Get region identifiers
                # @todo implement region identifiers in node attributes

                # Build the subgraph representation and add it to the list of facility
                # subgraphs
                _fac_graph = self.build_facility_graph(
                    facilityID = _facID,
                    facilityType = _factype,
                )

                # add onto the supply supply chain graph
                self.supply_chain.add_nodes_from(_fac_graph)
                self.supply_chain.add_edges_from(_fac_graph.edges)

            # @todo connect to regionalizations: every sub-graph needs a location and a
            #  distance to every connected (every other?) sub-graph


    def enumerate_paths(self):
        # Calculate total pathway costs (sum of all node and edge costs) over all
        # possible pathways

        # @note simple paths have no repeated nodes; this might not work for a cyclic
        #  graph
        # The target parameter can be replaced by a list

        # @note the generator from all_simple_paths can only be used once per definition
        path_edge_list = list([])

        # Get list of nodes and edges by pathway
        for path in map(nx.utils.pairwise,
                        nx.all_simple_paths(self.supply_chain, source='in use',
                                            target='landfill')):
            path_edge_list.append(list(path))

        path_node_list = list(
            nx.all_simple_paths(self.supply_chain, source='in use', target='landfill'))

        # dictionary defining all possible pathways by nodes and edges
        # nodes = calculate total processing costs
        # edges = calculate total transportation costs and distances
        paths_dict = {'nodes': path_node_list, 'edges': path_edge_list}

        for edges in paths_dict['edges']:
            for u, v in edges:
                print(u, v, self.supply_chain.get_edge_data(u, v))

        for nodes, edges in zip(path_node_list, path_edge_list):
            costs = [self.supply_chain.get_edge_data(u, v)['cost'] for u, v in edges]
            distances = [self.supply_chain.get_edge_data(u, v)['distance'] for u, v in
                         edges]
            graph_path = ",".join(nodes)
            print(
                f"Path: {graph_path}. Total cost={sum(costs)}, total distance={sum(distances)}")

    def update_paths(self):
        pass
        # @todo dynamically update node costs based on cost-over-time and learning-by-
        #  doing models

        # The edges between sub-graphs will have different transportation costs depending
        # on WHAT's being moved: blade segments or ground/shredded blade material.
        # @note Is there a way to also track component-material "status" or general
        #  characteristics as it traverses the graph? Maybe connecting this graph to
        #  the state machine