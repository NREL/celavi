import networkx as nx
from csv import DictReader
import pandas as pd
import numpy as np

# the locations dataset will be the largest; try to read that one in line by
# line. All other datasets will be relatively small, so storing and
# manipulating the entire dataset within the Python environment shouldn't
# slow execution down noticeably
mockdata = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/input-data-mockup.xlsx"
steps_df = pd.read_excel(mockdata, sheet_name='edges')
costs_df = pd.read_excel(mockdata, sheet_name='costs')
interconnect_df = pd.read_excel(mockdata, sheet_name='interconnections')
loc_df = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/loc-mock.csv"

# @todo move cost methods here

# @note cost, next state, relocation destination for the component

class CostGraph:
    """

    """

    def __init__(self, input_name : str, locations_file : str):
        """

        Parameters
        ----------
        input_name
            File name or other identifier where input datasets are stored
        """
        # @todo get input_name to read in the small datasets
        self.steps_df=pd.read_excel(input_name, sheet_name='edges')
        self.costs_df=pd.read_excel(input_name, sheet_name='costs')
        self.interconnect_df=pd.read_excel(input_name, sheet_name='interconnections')

        # for the dataset containing all facilities, save the filename to
        # self and process it line by line in a method
        self.loc_df=locations_file

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

    def get_edges(self,
                  facility_df : pd.DataFrame,
                  u_edge='steps',
                  v_edge='intra_edges'):
        """
        # @todo reformat and update docstring

        converts two columns of node names (u and v) into a list of string tuples
        for edge definition with networkx

        :param facility_df : dict

        :param u_edge: string
            column in df with edge origin node names
        :param v_edge: string
            column in df with edge destination node names
        :return: list of string tuples
        """
        _type = facility_df['facility_type'].values[0]

        _out = self.steps_df[[u_edge, v_edge]].loc[self.steps_df.facility_type == _type].dropna().to_records(index=False).tolist()

        return _out


    def get_nodes(self,
                  facility_df : pd.DataFrame,
                  step_col='step',
                  cost_method_col='cost_method',
                  facility_id_col='facility_id'):
        """
        # @todo update docstring

        Parameters
        ----------
        facility_df
        step_col
        cost_method_col
        facility_id_col

        Returns
        -------
            List of (str, dict) tuples used to define a networkx DiGraph
            Attributes are: processing step, cost method, facility ID, and
            region identifiers

        """

        _id = facility_df['facility_id'].values[0]

        # list of nodes (processing steps) within a facility
        _node_names = self.costs_df[step_col].loc[self.costs_df.facility_id == _id].tolist()

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.costs_df[[step_col,cost_method_col,facility_id_col]].loc[self.costs_df.facility_id == _id]

        # create dictionary from data frame with processing steps, cost
        # calculation method, and facility-specific region identifiers
        _attr_data = _step_cost.merge(facility_df, how='outer',on=facility_id_col).to_dict(orient='records')

        # reformat data into a list of tuples as (str, dict)
        _nodes = list(map(lambda x,y: (x,y), _node_names, _attr_data))

        return _nodes


    def build_facility_graph(self,
                             facility_df : pd.DataFrame):
        """
        # @todo update docstring
        Parameters
        ----------
        facility_df

        Returns
        -------

        """
        # Create empty directed graph object
        _facility = nx.DiGraph()

        _facility_nodes = self.get_nodes(facility_df)

        # Populate the directed graph with node names and facilityIDs
        _facility.add_nodes_from(_facility_nodes)

        # Populate the directed graph with edges
        # Edges within facilities don't have transportation costs or distances
        # associated with them.
        _facility.add_edges_from(self.get_edges(facility_df),
                                 cost=0,
                                 dist=0)

        # Use the facility ID and list of processing steps in this facility to
        # create a list of unique node names
        # Unique meaning over the entire supply chain (graph of subgraphs)
        _node_names = list(_facility.nodes)
        _id = facility_df['facility_id'].values[0]
        _node_names_unique = self.get_node_names(_id,_node_names)

        _labels = {}
        for i in np.arange(0, len(_node_names_unique)):
            _labels.update({_node_names[i]: _node_names_unique[i]})

        # Relabel nodes to unique names (step + facility ID)
        nx.relabel_nodes(_facility, _labels, copy=False)

        return _facility


    def build_supplychain_graph(self):
        """
        # @todo update docstring
        """

        # add all facilities and intra-facility edges
        with open(self.loc_df, 'r') as _loc_file:

            _reader = pd.read_csv(_loc_file, chunksize=1)

            for _line in _reader:

                # Build the subgraph representation and add it to the list of facility
                # subgraphs
                _fac_graph = self.build_facility_graph(facility_df = _line)

                # add onto the supply supply chain graph
                self.supply_chain.add_nodes_from(_fac_graph.nodes(data=True))

                self.supply_chain.add_edges_from(_fac_graph.edges(data=True))

        return self.supply_chain
        # add all inter-facility edges




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
