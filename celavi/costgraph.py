import networkx as nx
import pandas as pd
import numpy as np
import warnings
import pdb


class CostGraph:
    """
        Contains methods for reading in graph data, creating network of
        facilities in a supply chain, and finding preferred pathways for
        implementation.
    """

    def __init__(self,
                 step_costs_file : str = 'step_costs.csv',
                 fac_edges_file : str = 'fac_edges.csv',
                 transpo_edges_file : str = 'transpo_edges.csv',
                 locations_file : str = 'locations.csv',
                 routes_file : str = 'routes.csv',
                 target_step : str = 'landfilling',
                 timestep : int = 0,
                 max_dist : float = 300.0):
        """
        Reads in small datasets to DataFrames and stores the path to the large
        locations dataset for later use.

        Parameters
        ----------
        step_costs_file
            file listing processing steps and cost calculation methods by
            facility type
        fac_edges_file
            file listing intra-facility edges by facility type
        transpo_edges_file
            file listing inter-facility edges and transpo cost calculation
            methods
        locations_file
            path to dataset of facility locations
        routes_file
            path to dataset of routes between facilities
        target_step
            processing step(s) where supply chain paths terminate. String or
            list of strings.
        timestep
            DES model timestep at which cost graph is instantiated
        max_dist
            Maximum allowable transportation distance for a single supply chain
            pathway.
        """
        # @todo update file IO method to match actual input data format
        self.step_costs=pd.read_csv(step_costs_file)
        self.fac_edges=pd.read_csv(fac_edges_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)

        # these data sets are processed line by line
        self.loc_df=locations_file
        self.routes_df=routes_file

        self.target=target_step

        self.timestep = timestep

        self.max_dist = max_dist

        # ideally we could use this to execute all the cost methods and store
        # the output here. Then update the values in this structure only as
        # needed.
        self.step_cost_dict

        # create empty instance variable for supply chain DiGraph
        self.supply_chain = nx.DiGraph()


    @staticmethod
    def get_node_names(facilityID : [int, str],
                       subgraph_steps: list):
        """
        Generates a list of unique node names from a list of processing steps
        and a unique facility ID

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

    @staticmethod
    def node_filter(graph : nx.DiGraph,
                    attr_key_1 : str,
                    get_val_1,
                    attr_key_2 : str = None,
                    get_val_2 = None):
        """
        Finds node names in graph that have 'attr_key': get_val in
             their attribute dictionary

        Parameters
        ----------
        graph
            a networkx DiGraph containing at least one node with a node
            attribute dictionary
        attr_key_1
            key in the attribute dictionary on which to filter nodes in graph
        get_val_1
            value of attribute key on which to filter nodes in graph
        attr_key_2

        get_val_2

        Returns
        -------
            list of names of nodes (str) in graph
        """
        if attr_key_2 is not None:
            _out = [x for x, y in graph.nodes(data=True)
                    if (y[attr_key_1] == get_val_1) and
                    (y[attr_key_2] == get_val_2)]
        else:
            _out = [x for x, y in graph.nodes(data=True)
                    if y[attr_key_1] == get_val_1]

        return _out

    @staticmethod
    def list_of_tuples(list1 : list,
                       list2 : list,
                       list3 : list = None):
        """
        Converts two lists into a list of tuples where each tuple contains
        one element from each list:
        [(list1[0], list2[0], list3[0]), (list1[1], list2[1], list3[0]), ...]
        At least two lists must be specified. A maximum of three lists can be
        specified.

        Parameters
        ----------
        list1
            list of any data type
        list2
            list of any data type
        list3
            list of any data type

        Returns
        -------
            list of 2- or 3-tuples
        """
        if list3 is not None:
            return list(map(lambda x, y, z: (x, y, z), list1, list2, list3))
        else:
            return list(map(lambda x, y: (x, y), list1, list2))

    @staticmethod
    def zero_method():
        """

        Returns
        -------
        float
            Use this method for any processing step or transportation edge with
            no associated cost
        """
        return 0.0


    def get_edges(self,
                  facility_df : pd.DataFrame,
                  u_edge='step',
                  v_edge='next_step'):
        """
        Converts two columns of node names into a list of string tuples
        for intra-facility edge definition with networkx

        Parameters
        ----------
        facility_df
            DataFrame listing processing steps (u_edge) and the next
            processing step (v_edge) by facility type
        u_edge
            unique processing steps within a facility type
        v_edge
            steps to which the processing steps in u_edge connect

        Returns
        -------
            list of string tuples that define edges within a facility type
        """
        _type = facility_df['facility_type'].values[0]

        _out = self.fac_edges[[u_edge,v_edge]].loc[self.fac_edges.facility_type == _type].dropna().to_records(index=False).tolist()

        return _out


    def get_nodes(self,
                  facility_df : pd.DataFrame):
        """
        Generates a data structure that defines all nodes and node attributes
        for a single facility.

        Parameters
        ----------
        facility_df : pd.DataFrame
            DataFrame containing unique facility IDs, processing steps, and
            the name of the method (if any) used to calculate processing costs
            Column names in facility_df must be:
                ['facility_id', 'step', 'connects', 'step_cost_method']

        Returns
        -------
            List of (str, dict) tuples used to define a networkx DiGraph
            Attributes are: processing step, cost method, facility ID, and
            region identifiers

        """

        _id = facility_df['facility_id'].values[0]

        # list of nodes (processing steps) within a facility
        _node_names = self.step_costs['step'].loc[self.step_costs.facility_id == _id].tolist()

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.step_costs[['step',
                                      'step_cost_method',
                                      'facility_id',
                                      'connects']].loc[self.step_costs.facility_id == _id]

        # create list of dictionaries from data frame with processing steps,
        # cost calculation method, and facility-specific region identifiers
        _attr_data = _step_cost.merge(facility_df,
                                      how='outer',
                                      on='facility_id').to_dict(orient='records')

        # reformat data into a list of tuples as (str, dict)
        _nodes = self.list_of_tuples(_node_names, _attr_data)

        return _nodes


    def build_facility_graph(self,
                             facility_df : pd.DataFrame):
        """
        Creates networkx DiGraph object containing nodes, intra-facility edges,
        and all relevant attributes for a single facility.

        Parameters
        ----------
        facility_df
            DataFrame with a single row that defines a supply chain facility.
            facility_df must contain the columns:
            ['facility_id', 'facility_type', 'lat', 'long', 'region_id_1',
            'region_id_2', 'region_id_3', 'region_id_4']

        Returns
        -------
            networkx DiGraph
        """
        # Create empty directed graph object
        _facility = nx.DiGraph()

        # Generates list of (str, dict) tuples for node definition
        _facility_nodes = self.get_nodes(facility_df)

        # Populate the directed graph with node names and attribute
        # dictionaries
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

        # Construct a dict of {'old node name': 'new node name'}
        _labels = {}
        for i in np.arange(0, len(_node_names_unique)):
            _labels.update({_node_names[i]: _node_names_unique[i]})

        # Relabel nodes to unique names (step + facility ID)
        nx.relabel_nodes(_facility, _labels, copy=False)

        return _facility


    def build_supplychain_graph(self):
        """
        Reads in the locations data set line by line. Each line becomes a
        DiGraph representing a single facility. Facility DiGraphs are
        added onto a supply chain DiGraph and connected with inter-facility
        edges. Edges within facilities have no cost or distance. Edges
        between facilities have costs defined in the interconnections
        dataset and distances defined in the routes dataset.
        
        Returns
        -------
        None
        """

        # add all facilities and intra-facility edges to supply chain
        with open(self.loc_df, 'r') as _loc_file:

            _reader = pd.read_csv(_loc_file, chunksize=1)

            for _line in _reader:

                # Build the subgraph representation and add it to the list of
                # facility subgraphs
                _fac_graph = self.build_facility_graph(facility_df = _line)

                # add onto the supply supply chain graph
                self.supply_chain.add_nodes_from(_fac_graph.nodes(data=True))
                self.supply_chain.add_edges_from(_fac_graph.edges(data=True))

        # add all inter-facility edges, with costs but without distances
        # this is a relatively short loop
        for index, row in self.transpo_edges.iterrows():
            _u = row['u_step']
            _v = row['v_step']
            _edge_cost = row['transpo_cost_method']

            # get two lists of nodes to connect based on df row
            _u_nodes = self.node_filter(self.supply_chain, 'step', _u)
            _v_nodes = self.node_filter(self.supply_chain, 'step', _v)
            # convert the two lists to a list of tuples
            _edge_list = self.list_of_tuples(_u_nodes, _v_nodes)

            # @todo use the dist=NaN as a condition to exclude paths with this
            # edge from pathways being considered
            self.supply_chain.add_edges_from(_edge_list,
                                             cost=_edge_cost,
                                             dist=np.nan)

        # read in and process routes line by line
        with open(self.routes_df, 'r') as _route_file:

            _reader = pd.read_csv(_route_file, chunksize=1)

            for _line in _reader:
                # find the source nodes for this route
                _u = self.node_filter(self.supply_chain,
                                      'facility_id',
                                      _line['source_facility_id'].values[0],
                                      'connects','out')

                # loop thru all edges that connect to the source nodes
                for u_node, v_node, data in self.supply_chain.edges(_u,
                                                                    data=True):
                    # if the destination node facility ID matches the
                    # destination facility ID in the routing dataset row,
                    # apply the distance from the routing dataset to this edge
                    if self.supply_chain.nodes[v_node]['facility_id'] == \
                            _line['destination_facility_id'].values[0]:
                        data['dist'] = _line['total_vmt'].values[0]

        return self.supply_chain


    def enumerate_paths(self, source_node):
        """
        Calculate total pathway costs (sum of all node and edge costs) over
        all possible pathways.
        @note simple paths have no repeated nodes; this might not work for a
         cyclic graph
        @note The target parameter can be replaced by a list
        # @todo update docstring

        Parameters
        ----------
        source_node
            Source node name in the format 'facilitytypefacilityID'

        Returns
        -------

        """

        # create empty list of dicts to store pathways and characteristics
        _paths = list()

        _targets = self.node_filter(self.supply_chain,
                                    attr_key_1='step',
                                    get_val_1=self.target)

        # Enumerate and store pathways by source node
        for path in map(nx.utils.pairwise,
                        nx.all_simple_paths(self.supply_chain,
                                            source=source_node,
                                            target=_targets)):

            # get list of edges in this path
            _edges = list(path)

            # get list of nodes in this path by looking at the v node in
            # every edge
            _nodes = list(list(zip(*_edges))[1])
            # add source node to the list
            _nodes.insert(0, source_node)
            pdb.set_trace()
            # generate unique path id based on source and target nodes
            # @todo this isn't actually unique, how to uniqueify?
            _path_id = _nodes[0] + '_' + _nodes[-1]

            # sum transpo costs along edges to get pathway transpo cost
            _path_transpo_cost = 0.0

            # sum processing cost for all nodes in path to get pathway
            # processing cost
            # get dict of node name: cost method
            # we don't need to call every cost method every time - can we
            # instead evaluate all cost methods up-front and store those
            # values in self for accessibility? Then update as needed?
            _cost_dict = nx.get_node_attributes(nx.subgraph(self.supply_chain,
                                                            _nodes),
                                                'step_cost_method')
            # evaluate each cost method and calculate sum
            _path_processing_cost = 0.0

            # sum edge distances along edges to get total transportation dist
            _path_dist = 0.0


            # add this path and its characteristics to the list of path dicts
            _paths.append({'source' : source_node,
                           'path_id': _path_id,
                           'edges': _edges,
                           'nodes': _nodes,
                           'path_cost': _path_transpo_cost + _path_processing_cost,
                           'path_dist': _path_dist,
                           'path_gwp': 0.0})

            pdb.set_trace()

        path_node_list = list(nx.all_simple_paths(self.supply_chain,
                                                  source=source_node,
                                                  target=_targets))

        # for nodes, edges in zip(path_node_list, path_edge_list):
        #     costs = [self.supply_chain.get_edge_data(u, v)['cost']
        #              for u, v in edges]
        #     distances = [self.supply_chain.get_edge_data(u, v)['distance']
        #                  for u, v in edges]
        #     graph_path = ",".join(nodes)
        #     print(
        #         f"Path: {graph_path}. Total cost={sum(costs)},"
        #         f" total distance={sum(distances)}")


    def update_paths(self):
        pass
        # @todo dynamically update node costs based on cost-over-time and
        # learning-by-doing models

        # @note Is there a way to also track component-material "status" or
        # general characteristics as it traverses the graph? Maybe connecting
        # this graph to the state machine


    def rank_paths(self):
        """

        Returns
        -------

        """
        pass


    def choose_next_step(self, current_step=None):
        """

        Parameters
        ----------
        current_step

        Returns
        -------

        """
        # @note cost, next state, relocation destination for the component
        # @todo: based on current_step where component is currently, pull the
        # next step from the preferred pathway

    @staticmethod
    def landfilling(year):
        """
        Tipping fee model based on tipping fees in the South-Central region
        of the U.S. which includes TX.

        Parameters
        ----------
        year
            Model year obtained from DES model (timestep converted to year)
        Returns
        -------
        _fee
            Landfill tipping fee in USD/tonne
        """

        _fee = 3.0E-29 * np.exp(0.0344 * year)
        return _fee

    @staticmethod
    def rotor_teardown(year):
        """
        Cost of removing one blade from the turbine, calculated as one-third
        the rotor teardown cost.

        Parameters
        ----------
        year
            Model year obtained from DES model (timestep converted to year)
        Returns
        -------
        _cost
            Cost in USD per blade (note units!) of removing a blade from an
            in-use turbine. Equivalent to 1/3 the rotor teardown cost.
        """

        _cost = 42.6066109 * year ** 2 - 170135.7518957 * year +\
                169851728.663209
        return _cost


    @staticmethod
    def segmenting():
        """

        Returns
        -------
            Cost of cutting a turbine blade into 30-m segments.
        """
        return 27.56

    @staticmethod
    def coarse_grinding_onsite():
        """

        Parameters
        ----------

        Returns
        -------
            Cost of coarse grinding one metric ton of blade material onsite at
            the wind power plant.
        """
        raise NotImplementedError

        coarse_grinding_onsite_initial = 90.0

        cumulative_coarsegrind_mass = Context.recycle_to_clinker_material_inventory.component_materials['blade']

        coarse_grind_learning = (cumulative_coarsegrind_mass + cumulative_finegrind_mass + 1.0) ** -0.05

        coarse_grind_process = coarse_grinding_onsite_initial * coarse_grind_learning

        return coarse_grind_process

    @staticmethod
    def coarse_grinding():
        """

        Parameters
        ----------

        Returns
        -------
            Cost of coarse grinding one metric ton of segmented blade material
            in a mechanical recycling facility.
        """
        raise NotImplementedError

        coarse_grinding_initial = 80.0

        # divide out the loss factors that are applied to the inventory
        # entire blades are processed through raw material recycling, but only 70% is kept in the supply chain
        # similar for coarse grinding
        # cost models should be based on mass *processed*, not mass output
        cumulative_coarsegrind_mass = self.recycle_to_clinker_material_inventory.component_materials['blade']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        # add 1.0 to avoid mathematical errors when the cumulative numbers are both zero
        coarse_grind_learning = (cumulative_coarsegrind_mass + cumulative_finegrind_mass + 1.0) ** -0.05

        coarse_grind_process = coarse_grinding_initial * coarse_grind_learning

        return coarse_grind_process

    @staticmethod
    def fine_grinding():
        """

        Parameters
        ----------

        Returns
        -------
            Cost of grinding one metric ton of coarse-ground blade material at
            a mechanical recycling facility.
        """
        raise NotImplementedError

        fine_grinding_initial = 100.0

        cumulative_finegrind_mass = Context.recycle_to_raw_material_inventory.component_materials['blade'] / 0.7

        fine_grind_learning = (cumulative_finegrind_mass + 1.0) ** -0.05

        fine_grind_process = fine_grinding_initial * fine_grind_learning

        return fine_grind_process


    @staticmethod
    def coprocessing():
        """

        Returns
        -------
            Revenue from selling 1 metric ton of ground blade to cement
            co-processing plant
        """
        return -10.37


    @staticmethod
    def segment_transpo(year):
        """

        Parameters
        ----------
        year
            Model year from the DES model.

        Returns
        -------
            Cost of transporting one segmented blade one kilometer. Units:
            USD/blade-km
        """

        if year < 2001.0 or 2002.0 <= year < 2003.0:
            _cost = 4.35
        elif 2001.0 <= year < 2002.0 or 2003.0 <= year < 2019.0:
            _cost = 8.70
        elif 2019.0 <= year < 2031.0:
            _cost = 13.05
        elif 2031.0 <= year < 2044.0:
            _cost = 17.40
        elif 2044.0 <= year <= 2050.0:
            _cost = 21.75
        else:
            warnings.warn('Year out of range for segment transport; setting cost = 17.40')
            _cost = 17.40

        return _cost


    @staticmethod
    def shred_transpo():
        """

        Returns
        -------
            Cost of transporting 1 metric ton of shredded blade material by
            one kilometer. Units: USD/tonne-km.
        """
        return 0.08

## Debug code
netw = CostGraph()
netw.build_supplychain_graph()
netw.enumerate_paths('in use0')
