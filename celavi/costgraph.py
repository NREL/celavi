import networkx as nx
from csv import reader
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
loc_df = pd.read_excel(mockdata, sheet_name='locations')

# @todo move cost methods here

# @note cost, next state, relocation destination for the component

class CostGraph:
    """

    """

    def __init__(self, input_name):
        """

        Parameters
        ----------
        input_name
            File name or other identifier where input datasets are stored
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
                  facilityType : str,
                  u_edge='steps',
                  v_edge='intra_edges'):
        """
        # @todo reformat and update docstring
        converts two columns of node names (u and v) into a list of string tuples
        for edge definition with networkx

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


    def get_nodes(self,
                  facilityID: [int, str],
                  step_col='steps',
                  cost_method_col='cost_method',
                  facility_id_col='facility_id',
                  region_id1_col='region_id_1',
                  region_id2_col='region_id_2',
                  region_id3_col='region_id_3',
                  region_id4_col='region_id_4'):
        """
        # @todo update docstring

        Parameters
        ----------
        facilityID
        step_col
        cost_method_col
        facility_id_col
        region_id1_col
        region_id2_col
        region_id3_col
        region_id4_col

        Returns
        -------
            List of (str, dict) tuples used to define a networkx DiGraph
            Attributes are: processing step, cost method, facility ID, and
            region identifiers

        """
        # list of nodes (processing steps) within a facility
        _node_names = self.costs_df[step_col].loc[self.costs_df.facility_id == facilityID].tolist()

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.costs_df[[step_col,
                                    cost_method_col,
                                    facility_id_col]].loc[self.costs_df.facility_id == facilityID]

        # data frame of region identifiers that apply to all processing steps
        # within this facility
        _region_ids = self.loc_df[[facility_id_col,
                                   region_id1_col,
                                   region_id2_col,
                                   region_id3_col,
                                   region_id4_col]].loc[self.loc_df.facility_id == facilityID]

        # create dictionary from data frame with processing steps, cost
        # calculation method, and facility-specific region identifiers
        _attr_data = _step_cost.merge(_region_ids, how='outer',on=facility_id_col).to_dict(orient='records')

        # reformat data into a list of tuples as (str, dict)
        _nodes = tuple(zip(_node_names, _attr_data))

        return _nodes


    def build_facility_graph(self,
                             facilityID: [int, str],
                             facilityType: str):
        """
        # @todo update docstring format and content
        Constructs a networkx directed graph object representation of one facility
        or supply chain location

        :param facilityID: [int, str]
            Unique facility identifier
        :param facilityType: str
        :return: DiGraph object
            Directed graph populated with unique node names, processing steps,
             processing costs, and unique facility ID attributes
        """
        # Create empty directed graph object
        _facility = nx.DiGraph()

        # Populate the directed graph with node names and facilityIDs
        _facility.add_nodes_from(self.get_nodes(facilityID))

        # Populate the directed graph with edges
        # Edges within facilities don't have transportation costs or distances
        # associated with them.
        _facility.add_edges_from(self.get_edges(facilityType),
                                 cost=0,
                                 dist=0)

        # Use the facility ID and list of processing steps in this facility to
        # create a list of unique node names
        # Unique meaning over the entire supply chain (graph of subgraphs)
        _node_names = list(_facility.nodes)
        _node_names_unique = self.get_node_names(facilityID, _node_names)

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

        with open(self.loc_df, 'r') as _loc_file:
            _loc_csv = reader(_loc_file)

            for _line in _loc_csv:

                # Get unique facility ID
                _facID = _line[0]

                # Get facility type
                _factype = _line[1]

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