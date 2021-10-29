import networkx as nx
import pandas as pd
import numpy as np
from itertools import product
from time import time
from networkx_query import search_nodes

from celavi.costmethods import CostMethods

class CostGraph:
    """
        Contains methods for reading in graph data, creating network of
        facilities in a supply chain, and finding preferred pathways for
        implementation.
    """

    def __init__(self,
                 step_costs_file : str,
                 fac_edges_file : str,
                 transpo_edges_file : str,
                 locations_file : str,
                 routes_file : str,
                 pathway_cost_history_filename: str,
                 sc_begin : str = 'manufacturing',
                 sc_end = ('landfilling', 'cement co-processing', 'next use'),
                 year : float = 2000.0,
                 max_dist : float = 300.0,
                 verbose : int = 0,
                 save_copy = False,
                 save_name = 'netw.csv',
                 **kwargs):
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

        Keyword Arguments
        -----------------
        blade_mass : float
            Average mass of a single turbine blade at the beginning of the
            model run. Units: metric tons (tonnes)

        finegrind_cumul_initial : float
            Cumulative production of fine grinding at the beginning of the
            model run.
            Units: metric tons (tonnes)

        coarsegrind_cumul_initial : float
            Cumulative production of coarse grinding at the beginning of the
            model run. NOTE: This value may be greater than
            cumul_finegrind_initial.
            Units: metric tons (tonnes)

        finegrind_initial_cost : float
            Cost in USD/metric ton of fine grinding at the beginning of the
            model run.

        coarsegrind_initial_cost : float
            Cost in USD/metric ton of coarse grinding at the beginning of the
            model run.

        finegrind_revenue : float
            Revenue in USD/metric ton from sales of finely ground blade
            material.

        finegrind_learnrate : float
            Industrial learning-by-doing rate for fine grinding. Unitless.

        coarsegrind_learnrate : float
            Industrial learning-by-doing rate for coarse grinding. Unitless.

        finegrind_material_loss : float
            Fraction of total blade material lost during fine grinding.
            Unitless. This is the amount of finely ground blade material that
            must be landfilled.
        """
        self.start_time = time()
        self.step_costs=pd.read_csv(step_costs_file)
        self.fac_edges=pd.read_csv(fac_edges_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)

        # these data sets are processed line by line
        self.loc_file=locations_file
        self.routes_file=routes_file

        # also read in the locations as a dataframe for reference in
        # find_nearest
        self.loc_df = pd.read_csv(locations_file)

        self.sc_end=sc_end
        self.sc_begin=sc_begin

        self.year=year

        self.blade_mass=kwargs['blade_mass']

        # The cumulative production numbers must not be zero to prevent
        # mathematical errors in the learning-by-doing equation.
        # Here, if the cumulative production value provided at instantiation is
        # zero, it is replaced with 1; otherwise, the provided value is used.
        if kwargs['finegrind_cumul_initial']==0:
            self.finegrind_cumul_initial=1.0
        else:
            self.finegrind_cumul_initial=kwargs['finegrind_cumul_initial']
        if kwargs['coarsegrind_cumul_initial']==0:
            self.coarsegrind_cumul_initial=1.0
        else:
            self.coarsegrind_cumul_initial=kwargs['coarsegrind_cumul_initial']

        self.finegrind_initial_cost = kwargs['finegrind_initial_cost']
        self.coarsegrind_initial_cost = kwargs['coarsegrind_initial_cost']

        self.finegrind_revenue = kwargs['finegrind_revenue']

        self.finegrind_learnrate = kwargs['finegrind_learnrate']
        self.coarsegrind_learnrate = kwargs['finegrind_learnrate']

        self.finegrind_material_loss = kwargs['finegrind_material_loss']

        self.max_dist = max_dist

        self.verbose = verbose

        self.pathway_cost_history_filename = pathway_cost_history_filename

        # create empty List to store the pathway cost output data
        self.pathway_cost_history = list()

        # create empty instance variable for supply chain DiGraph
        self.supply_chain = nx.DiGraph()

        # build the initial supply chain graph
        self.build_supplychain_graph()

        if save_copy:
            nx.write_edgelist(self.supply_chain, save_name, delimiter=',')


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
                       list2 : list,
                       list3 : list = None):
        """
        Converts two or three lists into a list of two- or three-tuples where
        each tuple contains the corresponding elements from each list:
        [(list1[0], list2[0]), (list1[1], list2[1]), ...] or
        [(list1[0], list2[0], list3[0]), (list1[1], list2[1], list3[1]), ...]

        Two or three lists may be specified. All three lists must be the same
        length.

        Parameters
        ----------
        list1
            list of any data type
        list2
            list of any data type
        list3
            list of any data type (optional)

        Returns
        -------
            list of 2-tuples
        """

        if list3 is not None:
            _len = len(list1)
            if any(len(lst) != _len for lst in [list1, list2, list3]):
                raise NotImplementedError
            else:
                return list(map(lambda x, y, z: (x, y, z), list1, list2, list3))
        else:
            if len(list1) != len(list2):
                raise NotImplementedError
            else:
                return list(map(lambda x, y: (x, y), list1, list2))


    def find_nearest(self,
                     source : str,
                     crit : str):
        """
        Method that finds the nearest nodes to source and returns that node name,
        the path length to the nearest node, and the path to the nearest node.

        Original code source:
        https://stackoverflow.com/questions/50723854/networkx-finding-the-shortest-path-to-one-of-multiple-nodes-in-graph

        Parameters
        ----------
        source
            Name of node where this path begins.
        crit
            Criteria to calculate path "length". May be cost or dict.

        Returns
        -------
        [0] name of node "closest" to source
        [1] "length" of path between source and the closest node
        [2] list of nodes defining the path between source and the closest node
        """
        if self.verbose > 1:
            print('Finding shortest paths from', source)

        # Calculate the length of paths from fromnode to all other nodes
        lengths = nx.single_source_bellman_ford_path_length(self.supply_chain,
                                                        source,
                                                        weight=crit)

        short_paths = nx.single_source_bellman_ford_path(self.supply_chain,
                                                     source)

        # We are only interested in a particular type(s) of node
        targets = list(search_nodes(self.supply_chain,
                                    {"in": [("step",), self.sc_end]}))

        subdict = {k: v for k, v in lengths.items() if k in targets}

        # return the smallest of all lengths to get to typeofnode
        if subdict:
            # dict of shortest paths to all targets
            nearest = min(subdict, key=subdict.get)
            timeout = nx.get_node_attributes(self.supply_chain, 'timeout')
            timeout_list = [value for key, value in timeout.items()
                            if key in short_paths[nearest]]
            dist_list = [self.supply_chain.edges[short_paths[nearest][d:d+2]]['dist']
                         for d in range(len(short_paths[nearest])-1)]
            dist_list.insert(0, 0.0)
            _out = self.list_of_tuples(short_paths[nearest],
                                       timeout_list,
                                       dist_list)

            # create dictionary for this preferred pathway cost and decision
            # criterion and append to the pathway_cost_history
            for i in self.sc_end:
                self.pathway_cost_history.append(
                    {
                        'year' : self.year,
                        'facility_id' : self.supply_chain.nodes[source]['facility_id'],
                        'region_id_1' : self.loc_df[
                            self.loc_df.facility_id == self.supply_chain.nodes[source]['facility_id']
                        ].region_id_1.values[0],
                        'region_id_2' : self.loc_df[
                            self.loc_df.facility_id == self.supply_chain.nodes[source]['facility_id']
                        ].region_id_2.values[0],
                        'region_id_3' : self.loc_df[
                            self.loc_df.facility_id == self.supply_chain.nodes[source]['facility_id']
                        ].region_id_3.values[0],
                        'region_id_4' : self.loc_df[
                            self.loc_df.facility_id == self.supply_chain.nodes[source]['facility_id']
                        ].region_id_4.values[0],
                        'eol_pathway_type' : i,
                        'eol_pathway_dist' : min(
                            [value for key,value in subdict.items()
                             if i in key]
                        ),
                        'bol_pathway_dist' :
                            nx.shortest_path_length(
                                self.supply_chain,
                                source='manufacturing_' + str(
                                    self.find_upstream_neighbor(
                                        node_id=int(str(source).split('_')[1]
                                                    ),
                                        crit='cost'
                                    )
                                ),
                                target=str(source),
                                weight='cost',
                                method='bellman-ford'
                            )
                    }
                )

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

        _out = self.fac_edges[
            [u_edge,v_edge]
        ].loc[
            self.fac_edges.facility_type == _type
        ].dropna().to_records(index=False).tolist()

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
        _node_names = self.step_costs['step'].loc[
            self.step_costs.facility_id == _id
        ].tolist()

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.step_costs[['step',
                                      'step_cost_method',
                                      'facility_id',
                                      'connects']].loc[
            self.step_costs.facility_id == _id
        ]

        _step_cost['timeout'] = 1

        # create list of dictionaries from data frame with processing steps,
        # cost calculation method, and facility-specific region identifiers
        _attr_data = _step_cost.merge(
            facility_df,
            how='outer',
            on='facility_id'
        ).to_dict(orient='records')

        # reformat data into a list of tuples as (str, dict)
        _nodes = self.list_of_tuples(self.get_node_names(_id, _node_names),
                                     _attr_data)

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

        _id = str(facility_df['facility_id'].values[0])

        # Generates list of (str, dict) tuples for node definition
        _facility_nodes = self.get_nodes(facility_df)

        # Populate the directed graph with node names and attribute
        # dictionaries
        _facility.add_nodes_from(_facility_nodes)

        # Populate the directed graph with edges
        # Edges within facilities don't have transportation costs or distances
        # associated with them.
        _edges = self.get_edges(facility_df)
        _unique_edges = [tuple(map(lambda w: w+'_'+_id, x)) for x in _edges]

        _methods = [
            {'cost_method':
                [
                    getattr(CostMethods,
                            _facility.nodes[edge[0]]['step_cost_method']
                            )
                ],
                'cost': 0.0,
                'dist': 0.0}
            for edge in _unique_edges
        ]

        _facility.add_edges_from(
            self.list_of_tuples([node[0] for node in _unique_edges],
                                [node[1] for node in _unique_edges],
                                _methods)
        )

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
            print('Adding nodes and edges at        %d s' % np.round(
                time() - self.start_time, 0), flush=True)

        # add all facilities and intra-facility edges to supply chain
        with open(self.loc_file, 'r') as _loc_file:

            _reader = pd.read_csv(_loc_file, chunksize=1)

            for _line in _reader:

                # Build the subgraph representation and add it to the list of
                # facility subgraphs
                _fac_graph = self.build_facility_graph(facility_df = _line)

                # add onto the supply supply chain graph
                self.supply_chain.add_nodes_from(_fac_graph.nodes(data=True))
                self.supply_chain.add_edges_from(_fac_graph.edges(data=True))

        if self.verbose > 0:
            print('Nodes and edges added at         %d s' % np.round(
                time() - self.start_time, 0), flush=True)
            print('Adding transport cost methods at %d s' % np.round(
                time() - self.start_time, 0), flush=True)

        # add all inter-facility edges, with costs but without distances
        # this is a relatively short loop
        for index, row in self.transpo_edges.iterrows():
            if self.verbose > 1:
                print('Adding transport cost methods to edges between ',
                      row['u_step'],
                      ' and ',
                      row['v_step'])

            _u = row['u_step']
            _v = row['v_step']
            _transpo_cost = row['transpo_cost_method']

            # get two lists of nodes to connect based on df row
            _u_nodes = list(search_nodes(self.supply_chain,
                                         {"==": [("step",), _u]}))
            _v_nodes = list(search_nodes(self.supply_chain,
                                         {"==": [("step",), _v]}))

            # convert the two node lists to a list of tuples with all possible
            # combinations of _u_nodes and _v_nodes
            _edge_list = self.all_element_combos(_u_nodes, _v_nodes)

            if not any([self.supply_chain.nodes[_v]['step']
                        in self.sc_end for _v in _v_nodes]):
                _methods = [
                    {'cost_method': [
                        getattr(CostMethods,
                                self.supply_chain.nodes[edge[0]]['step_cost_method']),
                        getattr(CostMethods,
                                _transpo_cost)
                    ],
                        'cost': 0.0,
                        'dist': -1.0}
                    for edge in _edge_list
                ]
            else:
                _methods = [
                    {'cost_method': [
                        getattr(CostMethods,
                                self.supply_chain.nodes[edge[0]]['step_cost_method']),
                        getattr(CostMethods,
                                _transpo_cost),
                        getattr(CostMethods,
                                self.supply_chain.nodes[edge[1]]['step_cost_method'])
                    ],
                        'cost': 0.0,
                        'dist': -1.0}
                    for edge in _edge_list
                ]

            # add these edges to the supply chain
            self.supply_chain.add_edges_from(
                self.list_of_tuples([edge[0] for edge in _edge_list],
                                    [edge[1] for edge in _edge_list],
                                    _methods)
            )
        if self.verbose > 0:
            print('Transport cost methods added at  %d s' % np.round(
                time() - self.start_time, 0), flush=True)

        # read in and process routes line by line
        with open(self.routes_file, 'r') as _route_file:
            if self.verbose > 0:
                print('Adding route distances at        %d s' % np.round(
                    time() - self.start_time, 0), flush=True)

            # Only read in columns relevant to CostGraph building
            _reader = pd.read_csv(_route_file,
                                  usecols=['source_facility_id',
                                           'source_facility_type',
                                           'destination_facility_id',
                                           'destination_facility_type',
                                           'total_vmt'],
                                  chunksize=1)
            _prev_line = None

            for _line in _reader:
                if np.array_equal(_line, _prev_line):
                    continue

                _prev_line = _line

                # find the source nodes for this route
                _u = list(
                    search_nodes(
                        self.supply_chain,
                        {'and': [{"==": [("facility_id",),
                                         _line['source_facility_id'].values[0]]},
                                 {"in": [("connects",),
                                         ["out","bid"]]}]}))

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
                        # Additional factor converts miles to km
                        data['dist'] = 1.60934 * _line['total_vmt'].values[0]

        if self.verbose > 0:
            print('Route distances added at         %d s' % np.round(
                time() - self.start_time, 0), flush=True)
            print('Calculating edge costs at        %d s' % np.round(
                time() - self.start_time, 0), flush=True)

        for edge in self.supply_chain.edges():
            if self.verbose > 1:
                print('Calculating edge costs for ', edge)

            self.supply_chain.edges[edge]['cost'] = sum(
                [f(vkmt=self.supply_chain.edges[edge]['dist'],
                   year=self.year,
                   blade_mass=self.blade_mass,
                   finegrind_cumul_initial=self.finegrind_cumul_initial,
                   coarsegrind_cumul_initial=self.coarsegrind_cumul_initial,
                   finegrind_initial_cost=self.finegrind_initial_cost,
                   coarsegrind_initial_cost=self.coarsegrind_initial_cost,
                   finegrind_revenue=self.finegrind_revenue,
                   finegrind_learnrate=self.finegrind_learnrate,
                   coarsegrind_learnrate=self.coarsegrind_learnrate,
                   finegrind_material_loss=self.finegrind_material_loss)
                 for f in self.supply_chain.edges[edge]['cost_method']]
            )

        if self.verbose > 0:
            print('Supply chain graph is built at   %d s' % np.round(
                time() - self.start_time, 0), flush=True)


    def choose_paths(self,
                     source : str = None,
                     crit : str = 'cost'):
        """
        Calculate total pathway costs (sum of all node and edge costs) over
        all possible pathways between source and target nodes. Other "costs"
        such as distance or environmental impacts may be used as well with
        modifications to the crit argument of the find_nearest call.

        @todo verify that this method works for a cyclic graph

        Parameters
        ----------
        source
            Node name in the format "facility_type_facilityid".
        crit
            Criterion on which "shortest" path is defined. Defaults to cost.

        Returns
        -------
        Dictionary containing the source, node, target node, path between
        source and target, and the pathway "cost".
        """
        # Since all edges now contain both processing costs (for the u node)
        # as well as transport costs (including distances), all we need to do
        # is get the shortest path using the 'cost' attribute as the edge weight
        if source is None:
            raise ValueError(f"CostGraph.choose_paths: source node cannot be None")
        else:
            if source not in self.supply_chain.nodes():
                raise ValueError(f"CostGraph.choose_paths: {source} not in CostGraph")
            else:
                _paths = []
                _chosen_path = self.find_nearest(source=source, crit=crit)
                _paths.append({'source': source,
                               'target': _chosen_path[0],
                               'path': _chosen_path[2],
                               'cost': _chosen_path[1]})

                return _paths


    def find_upstream_neighbor(self,
                               node_id : int,
                               connect_to : str = 'manufacturing',
                               crit : str = 'dist'):
        """
        Given a node in the network, find the "nearest" upstream neighbor to
        that node that is of the type specified by connect_to. "Nearest" is
        determined according to the crit parameter.

        Parameters
        ----------
        node_id
            facility_id of a node in the supply chain network. No default.
        connect_to
            facility_type of the upstream node.
        crit
            Criteron used to decide which manufacturing node is "nearest".
            Defaults to distance.

        Returns
        -------
        _nearest_facility_id
            Integer identifying the "closest" upstream node of type connect_to
            that connects to the node with the provided node_id. Returns None
            if node_id does not exist in the network or if the node_id does not
            connect to any nodes of the connect_to type.

        """

        # Check that the node_id exists in the supply chain.
        # If it doesn't, print a message and return None
        if not node_id in nx.get_node_attributes(self.supply_chain,
                                                 name='facility_id').values():
            print('Facility %d does not exist in CostGraph' % node_id,
                  flush=True)
            return None
        else:
            # If node_id does exist in the supply chain, pull out the node name
            _node = [x for x,y in self.supply_chain.nodes(data=True)
                     if y['facility_id'] == node_id
                     and y['connects'] == 'bid'][0]

        # Get a list of all nodes with an outgoing edge that connects to this
        # node_id, with the specified facility type
        _upstream_nodes = [n for n in self.supply_chain.predecessors(_node)
                           if n.find(connect_to) != -1]
        
        # Search the list for the "closest" node
        if len(_upstream_nodes) == 0:
            # If there are no upstream nodes of the correct type, print a
            # message and return None
            print(f'Facility {node_id} does not have any upstream neighbors of type {connect_to}',
                  flush=True)
            return None

        elif len(_upstream_nodes) > 1:
            # If there are multiple options, identify the nearest neighbor
            # according to the crit(eria) parameter
            _upstream_dists = [self.supply_chain.edges[_up_n, _node][crit]
                               for _up_n in _upstream_nodes]
            _nearest_upstream_node = _upstream_nodes[_upstream_dists.index(
                min(_upstream_dists)
            )]
            _nearest_facility_id = _nearest_upstream_node.split('_')[1]

        else:
            # If there is only one option, pull that node's facility_id directly
            _nearest_facility_id = _upstream_nodes[0].split('_')[1]

        # Return the "closest" node's facility_id as an integer
        return int(_nearest_facility_id)


    def find_downstream(self,
                        node_name : str = None,
                        facility_id : int = None,
                        connect_to : str = 'landfill',
                        crit : str = 'dist'):
        """

        Parameters
        ----------
        node_name
        facility_id
        node_id
        connect_to
        crit

        Returns
        -------
            Facility ID of the closest (according to "crit") facility
             of type "connect_to" downstream of the node indicated by node_id.

        """
        # Check that the node_id exists in the supply chain.
        # If it doesn't, print a message and return None
        # if a facility_id was provided, use that to locate the node
        if facility_id is not None:
            if not facility_id in nx.get_node_attributes(self.supply_chain,
                                                     name='facility_id').values():
                print(f'Facility {facility_id} does not exist in CostGraph',
                      flush=True)
                return None
            else:
                # If facility_id does exist in the supply chain, pull out the
                # node name
                _node = [x for x, y in self.supply_chain.nodes(data=True)
                         if y['facility_id'] == facility_id][0]
                # Get a list of all nodes with an outgoing edge that connects
                # to this facility_id, with the specified facility type
                _downst_nodes = [n for n in self.supply_chain.successors(_node)
                                 if n.find(connect_to) != -1]
        elif node_name is not None:
            if not node_name in self.supply_chain.nodes:
                print(f'Node {node_name} does not exist in CostGraph',
                      flush=True)
                return None
            else:
                # Get a list of all nodes with an outgoing edge that connects
                # to this facility_id, with the specified facility type
                _downst_nodes = [n for n in
                                 self.supply_chain.successors(node_name)
                                 if n.find(connect_to) != -1]
        else:
            print(f'No node identifier provided to find_downstream',
                  flush=True)
            return None

        # Search the list for the "closest" node
        if len(_downst_nodes) == 0:
            # If there are no upstream nodes of the correct type, print a
            # message and return None
            print(f'Node {node_name} does not have any downstream neighbors of type {connect_to}',
                  flush=True)
            return None

        elif len(_downst_nodes) > 1:
            # If there are multiple options, identify the nearest neighbor
            # according to the crit(eria) parameter

            _upstream_dists = [self.supply_chain.edges[_node, _lnd_n][crit]
                               for _lnd_n in _downst_nodes]
            _nearest_downst_node = _downst_nodes[_upstream_dists.index(
                min(_upstream_dists)
            )]
            _nearest_facility_id = _nearest_downst_node.split('_')[1]

        else:
            # If there is only one option, pull that node's facility_id directly
            _nearest_downst_node = _downst_nodes[0]

        return _nearest_downst_node


    def update_costs(self, **kwargs):
        """
        Re-calculates all edge costs based on arguments passed to cost methods.

        Keyword Arguments
        -----------------
        year : float
            Model year provided by DES.

        blade_mass : float
            Average turbine blade mass provided by DES.

        finegrind_cumul : float
            Cumulative mass of blades that have been finely ground,
            provided by DES.

        coarsegrind_cumul : float
            Cumulative mass of blades that have been coarsely ground,
            provided by DES.

        Returns
        -------
        None
        """
        # update the year for CostGraph
        self.year = kwargs['year']

        if self.verbose > 0:
            print('Updating costs for %d at         %d s' %
                  (kwargs['year'], np.round(time() - self.start_time, 0)),
                  flush=True)
        
        for edge in self.supply_chain.edges():
            self.supply_chain.edges[edge]['cost'] = sum(
                [f(vkmt=self.supply_chain.edges[edge]['dist'],
                   year=kwargs['year'],
                   blade_mass=kwargs['blade_mass'],
                   finegrind_cumul=kwargs['finegrind_cumul'],
                   coarsegrind_cumul=kwargs['coarsegrind_cumul'],
                   finegrind_cumul_initial=self.finegrind_cumul_initial,
                   coarsegrind_cumul_initial=self.coarsegrind_cumul_initial,
                   finegrind_initial_cost=self.finegrind_initial_cost,
                   finegrind_revenue=self.finegrind_revenue,
                   coarsegrind_initial_cost=self.coarsegrind_initial_cost,
                   finegrind_learnrate=self.finegrind_learnrate,
                   coarsegrind_learnrate=self.coarsegrind_learnrate,
                   finegrind_material_loss=self.finegrind_material_loss)
                 for f in self.supply_chain.edges[edge]['cost_method']]
            )

        if self.verbose > 0:
            print('Costs updated for  %d at         %d s' %
                 (kwargs['year'], np.round(time() - self.start_time, 0)),
                 flush=True)


    def save_costgraph_outputs(self):
        """
        Performs postprocessing on CostGraph outputs being saved to file and
        saves to user-specified filenames and directories

        Parameters
        ----------

        Returns
        -------
        None
        """

        pd.DataFrame(
            self.pathway_cost_history
        ).drop_duplicates(
            ignore_index=True
        ).to_csv(self.pathway_cost_history_filename,index=False)
