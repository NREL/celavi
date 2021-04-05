import networkx as nx
import pandas as pd
import numpy as np
import warnings
from itertools import product

from networkx_query import search_nodes

class CostGraph:
    """
        Contains methods for reading in graph data, creating network of
        facilities in a supply chain, and finding preferred pathways for
        implementation.
    """

    def __init__(self,
                 step_costs_file : str = '../celavi-data/inputs/step_costs.csv',
                 fac_edges_file : str = '../celavi-data/inputs/fac_edges.csv',
                 transpo_edges_file : str = '../celavi-data/inputs/transpo_edges.csv',
                 locations_file : str = '../celavi-data/inputs/locations.csv',
                 routes_file : str = '../celavi-data/preprocessing/routes.csv',
                 sc_begin : str = 'in use',
                 sc_end = ['landfilling', 'cement co-processing'],
                 year : float = 2000.0,
                 max_dist : float = 300.0,
                 verbose : int = 0):
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
        sc_begin
            processing step(s) where supply chain paths begin. String or list
            of strings.
        sc_end
            processing step(s) where supply chain paths terminate. String or
            list of strings.
        year
            DES model year at which cost graph is instantiated.
        max_dist
            Maximum allowable transportation distance for a single supply chain
            pathway.
        verbose
            Integer specifying how much info CostGraph should provide as it
            works.
            0 = No information other than return values
            1 = Info on when key methods start and stop
            >1 = Detailed info on facilities, nodes, and edges
        """

        self.step_costs=pd.read_csv(step_costs_file)
        self.fac_edges=pd.read_csv(fac_edges_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)

        # these data sets are processed line by line
        self.loc_df=locations_file
        self.routes_df=routes_file

        self.sc_end=sc_end
        self.sc_begin=sc_begin

        self.year=year

        # @todo get current blade mass from DES model
        self.blade_mass=1000.0

        self.max_dist = max_dist

        self.verbose = verbose

        # create empty instance variable for supply chain DiGraph
        self.supply_chain = nx.DiGraph()

        self.build_supplychain_graph()


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
        return ["{}_{}".format(i, str(facilityID)) for i in subgraph_steps]


    def all_element_combos(self,
                           list1 : list,
                           list2 : list):
        """
        Converts two lists into a list of tuples where each tuple contains
        one element from each list:
        [(list1[0], list2[0]), (list1[0], list2[1]), ...]
        Exactly two lists of any length must be specified.

        Parameters
        ----------
        list1
            list of any data type
        list2
            list of any data type

        Returns
        -------
            list of 2-tuples
        """
        if self.verbose > 1:
            print('Getting node combinations')

        _out = []
        _out = product(list1, list2)

        return list(_out)


    def list_of_tuples(self,
                       list1 : list,
                       list2 : list):
        """
        Converts two lists into a list of tuples where each tuple contains
        one element from each list:
        [(list1[0], list2[0]), (list1[1], list2[1]), ...]
        Exactly two lists of any length must be specified.

        Parameters
        ----------
        list1
            list of any data type
        list2
            list of any data type

        Returns
        -------
            list of 2-tuples
        """
        if self.verbose > 1:
            print('Getting list of tuples')

        if len(list1) != len(list2):
            raise NotImplementedError
        else:
            return list(map(lambda x, y: (x, y), list1, list2))


    @staticmethod
    def zero_method(**kwargs):
        """

        Returns
        -------
        float
            Use this method for any processing step or transportation edge with
            no associated cost
        """
        return 0.0



    def find_nearest(self,
                     source : str,
                     crit : str):
        """
        # original code source:
        # https://stackoverflow.com/questions/50723854/networkx-finding-the-shortest-path-to-one-of-multiple-nodes-in-graph

        Parameters
        ----------
        source
            Name of node where this path begins.
        crit
            Criteria to calcualte path "length". May be cost or dict.

        Returns
        -------
        [0] name of node "closest" to source
        [1] "length" of path between source and the closest node
        [2] list of nodes defining the path between source and the closest node
        """
        if self.verbose > 1:
            print('Finding shortest paths from', source)

        # Calculate the length of paths from fromnode to all other nodes
        lengths = nx.single_source_dijkstra_path_length(self.supply_chain,
                                                        source,
                                                        weight=crit)

        short_paths = nx.single_source_dijkstra_path(self.supply_chain,
                                                     source)

        # We are only interested in a particular type(s) of node
        targets = list(search_nodes(self.supply_chain,
                                    {"in": [("step",), self.sc_end]}))

        subdict = {k: v for k, v in lengths.items() if k in targets}

        # return the smallest of all lengths to get to typeofnode
        if subdict:
            # dict of shortest paths to all targets
            nearest = min(subdict, key=subdict.get)
            # shortest "distance" to any of the targets
            a_dictionary = {1: "a", 2: "b", 3: "c"}
            timeout = nx.get_node_attributes(self.supply_chain, 'timeout')
            timeout_list = [value for key, value in timeout.items() if key in short_paths[nearest]]

            _out = self.list_of_tuples(short_paths[nearest], timeout_list)

            return nearest, subdict[nearest], _out
        else:
            # not found, no path from source to typeofnode
            return None, None, None


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
        if self.verbose > 1:
            print('Getting edges for ',
                  facility_df['facility_type'].values[0])

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
        if self.verbose > 1:
            print('Getting nodes for facility ',
                  str(facility_df['facility_id'].values[0]))

        _id = facility_df['facility_id'].values[0]

        # list of nodes (processing steps) within a facility
        _node_names = self.step_costs['step'].loc[self.step_costs.facility_id == _id].tolist()

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.step_costs[['step',
                                      'step_cost_method',
                                      'facility_id',
                                      'connects']].loc[self.step_costs.facility_id == _id]
        # @todo update dummy value for timeout with info from DES
        _step_cost['timeout'] = 1

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
        if self.verbose > 1:
            print('Building facility graph for ',
                  str(facility_df['facility_id'].values[0]))

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
                                 cost_method=[],
                                 cost=0.0,
                                 dist=0.0)

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
        if self.verbose > 0:
            print('-------Building supply chain graph-------')

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

        if self.verbose > 0:
            print('Adding cost methods to supply chain graph')

        # add all inter-facility edges, with costs but without distances
        # this is a relatively short loop
        for index, row in self.transpo_edges.iterrows():
            if self.verbose > 1:
                print('Adding cost methods to edges between ',
                      row['u_step'],
                      ' and ',
                      row['v_step'])

            _u = row['u_step']
            _v = row['v_step']
            _edge_cost = row['transpo_cost_method']

            # get two lists of nodes to connect based on df row
            _u_nodes = list(search_nodes(self.supply_chain,
                                         {"==": [("step",), _u]}))
            _v_nodes = list(search_nodes(self.supply_chain,
                                         {"==": [("step",), _v]}))

            # convert the two node lists to a list of tuples with all possible
            # combinations of _u_nodes and _v_nodes
            _edge_list = self.all_element_combos(_u_nodes, _v_nodes)

            # add these edges to the supply chain
            self.supply_chain.add_edges_from(_edge_list,
                                             cost_method=[getattr(CostGraph,
                                                                  _edge_cost)],
                                             cost=0.0,
                                             dist=np.nan)


        # read in and process routes line by line
        with open(self.routes_df, 'r') as _route_file:
            if self.verbose > 0:
                print('Adding distances to supply chain graph')

            _reader = pd.read_csv(_route_file, chunksize=1)

            for _line in _reader:

                # find the source nodes for this route
                _u = list(search_nodes(self.supply_chain,
                                       {'and': [{"==": [("facility_id",), _line['source_facility_id'].values[0]]},
                                                {"==": [("connects",), "out"]}]}))

                # loop thru all edges that connect to the source nodes
                for u_node, v_node, data in self.supply_chain.edges(_u, data=True):
                    # if the destination node facility ID matches the
                    # destination facility ID in the routing dataset row,
                    # apply the distance from the routing dataset to this edge
                    if self.supply_chain.nodes[v_node]['facility_id'] == \
                            _line['destination_facility_id'].values[0]:
                        if self.verbose > 1:
                            print('Adding ',
                                  str(_line['total_vmt'].values[0]),
                                  ' km between ',
                                  u_node,
                                  ' and ',
                                  v_node)
                        data['dist'] = _line['total_vmt'].values[0]

        if self.verbose > 1:
            print('Calculating node and edge costs')

        # @todo edges starting from 'in use' nodes have rotor teardown costs
        # assigned to them in addition to the zero method
        for edge in self.supply_chain.edges():

            _method = getattr(CostGraph, self.supply_chain.nodes[edge[0]]['step_cost_method'])

            if _method not in self.supply_chain[edge[0]][edge[1]]['cost_method']:
                self.supply_chain[edge[0]][edge[1]]['cost_method'].append(_method)

            # if the node terminates at a landfill,
            if self.supply_chain.nodes[edge[1]]['step'] in self.sc_end:
                _addl_method = getattr(CostGraph,
                                           self.supply_chain.nodes[edge[1]]['step_cost_method'])
                # also add in the landfill cost method
                if _addl_method not in self.supply_chain[edge[0]][edge[1]]['cost_method']:
                    self.supply_chain[edge[0]][edge[1]]['cost_method'].append(_addl_method)

            self.supply_chain.edges[edge]['cost'] = sum([f(vkmt=self.supply_chain.edges[edge]['dist'],
                                                           year=self.year,
                                                           blade_mass=self.blade_mass,
                                                           cumul_finegrind=1000.0,
                                                           cumul_coarsegrind=1000.0) for f in self.supply_chain.edges[edge]['cost_method']])

        if self.verbose > 0:
            print('-------Supply chain graph is built-------')


    def choose_paths(self):
        """
        Calculate total pathway costs (sum of all node and edge costs) over
        all possible pathways.
        @note simple paths have no repeated nodes; this might not work for a
         cyclic graph
        @note The target parameter can be replaced by a list
        # @todo update docstring

        # @note cost, next state, relocation destination for the component
        # @todo: based on current_step where component is currently, pull the
        # next step from the preferred pathway

        Parameters
        ----------

        Returns
        -------

        """
        # Since all edges now contain both processing costs (for the u node)
        # as well as transport costs (including distances), all we need to do
        # is get the shortest path using the 'cost' attribute as the edge weight
        if self.verbose > 1:
            print('Choosing shortest paths')

        _sources = list(search_nodes(self.supply_chain,
                                     {"in": [("step",), self.sc_begin]}))

        _paths = []
        # Find the lowest-cost path from EACH source node to ANY target node
        for _node in _sources:
            _chosen_path = self.find_nearest(source=_node, crit='cost')
            _paths.append({'source': _node,
                           'target': _chosen_path[0],
                           'path': _chosen_path[2],
                           'cost': _chosen_path[1]})

        return _paths


    def update_costs(self, **kwargs):
        """

        Parameters
        ----------

        Returns
        -------
        None
        """
        # @todo dynamically update node costs based on cost-over-time and
        # learning-by-doing models

        for edge in self.supply_chain.edges():
            self.supply_chain.edges[edge]['cost'] = sum([f(vkmt=self.supply_chain.edges[edge]['dist'],
                                                           year=kwargs['year'],
                                                           blade_mass=kwargs['blade_mass'],
                                                           cumul_finegrind=kwargs['cumul_finegrind'],
                                                           cumul_coarsegrind=kwargs['cumul_coarsegrind']) for f in self.supply_chain.edges[edge]['cost_method']])

    @staticmethod
    def landfilling(**kwargs):
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
            Landfill tipping fee in USD/metric ton
        """
        _year = kwargs['year']
        _fee = 3.0E-29 * np.exp(0.0344 * _year)
        return _fee


    @staticmethod
    def rotor_teardown(**kwargs):
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
        _year = kwargs['year']
        _cost = 42.6066109 * _year ** 2 - 170135.7518957 * _year +\
                169851728.663209
        return _cost


    @staticmethod
    def segmenting(**kwargs):
        """

        Returns
        -------
            Cost (USD/metric ton) of cutting a turbine blade into 30-m segments.
        """
        return 27.56


    @staticmethod
    def coarse_grinding_onsite(**kwargs):
        """
        # @todo update with relevant FacilityInventories from DES

        Parameters
        ----------

        Returns
        -------
            Cost of coarse grinding one metric ton of blade material onsite at
            the wind power plant.
        """
        cumulative_coarsegrind_mass = kwargs['cumul_coarsegrind']

        if cumulative_coarsegrind_mass is None:
            cumulative_coarsegrind_mass = 1000

        coarse_grinding_onsite_initial = 90.0

        coarse_grind_learning = (cumulative_coarsegrind_mass + 1.0) ** -0.05

        return coarse_grinding_onsite_initial * coarse_grind_learning


    @staticmethod
    def coarse_grinding(**kwargs):
        """
        # @todo update with correct FacilityInventory values from Context

        Parameters
        ----------

        Returns
        -------
            Cost of coarse grinding one metric ton of segmented blade material
            in a mechanical recycling facility.
        """
        cumulative_coarsegrind_mass = kwargs['cumul_coarsegrind']

        if cumulative_coarsegrind_mass is None:
            cumulative_coarsegrind_mass = 1000

        coarse_grinding_initial = 80.0

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        # add 1.0 to avoid mathematical errors when the cumulative numbers are both zero
        coarse_grind_learning = (cumulative_coarsegrind_mass + 1.0) ** -0.05

        return coarse_grinding_initial * coarse_grind_learning


    @staticmethod
    def fine_grinding(**kwargs):
        """
        # @todo update with relevant FacilityInventory values from Context

        Parameters
        ----------

        Returns
        -------
            Cost of grinding one metric ton of coarse-ground blade material at
            a mechanical recycling facility.
        """
        cumulative_finegrind_mass = kwargs['cumul_finegrind']

        if cumulative_finegrind_mass is None:
            cumulative_finegrind_mass = 1000

        fine_grinding_initial = 100.0

        fine_grind_learning = (cumulative_finegrind_mass + 1.0) ** -0.05

        return fine_grinding_initial * fine_grind_learning


    @staticmethod
    def coprocessing(**kwargs):
        """

        Returns
        -------
            Revenue (USD/metric ton) from selling 1 metric ton of ground blade
             to cement co-processing plant
        """
        return -10.37


    @staticmethod
    def segment_transpo(**kwargs):
        """
        Calculate segment transportation cost in USD/metric ton

        Returns
        -------
            Cost of transporting one segmented blade one kilometer. Units:
            USD/blade
        """
        _vkmt = kwargs['vkmt']
        _mass = kwargs['blade_mass']
        _year = kwargs['year']

        if np.isnan(_vkmt) or np.isnan(_mass):
            return 0.0
        else:
            if _year < 2001.0 or 2002.0 <= _year < 2003.0:
                _cost = 4.35
            elif 2001.0 <= _year < 2002.0 or 2003.0 <= _year < 2019.0:
                _cost = 8.70
            elif 2019.0 <= _year < 2031.0:
                _cost = 13.05
            elif 2031.0 <= _year < 2044.0:
                _cost = 17.40
            elif 2044.0 <= _year <= 2050.0:
                _cost = 21.75
            else:
                warnings.warn(
                    'Year out of range for segment transport; setting cost = 17.40')
                _cost = 17.40

            return _cost * _vkmt / _mass


    @staticmethod
    def shred_transpo(**kwargs):
        """
        Parameters
        -------
        vkmt
            Distance traveled in kilometers

        Returns
        -------
            Cost of transporting 1 metric ton of shredded blade material by
            one kilometer. Units: USD/metric ton.
        """
        _vkmt = kwargs['vkmt']
        if np.isnan(_vkmt):
            return 0.0
        else:
            return 0.08 * _vkmt
