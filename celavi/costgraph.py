from typing import List, Union
import networkx as nx
import pandas as pd
import numpy as np
from itertools import product
from time import time
from networkx_query import search_nodes

from celavi.costmethods import CostMethods


class CostGraph:
    """
    Reads in supply chain data, creates a network of processing steps and facilities
    in a circular supply chain, identifies preferred end-of-life pathways through the
    supply chain, calculates supply chain characteristics such as pathway cost.
    """

    def __init__(
        self,
        step_costs_file: str,
        transpo_edges_file: str,
        locations_file: str,
        routes_file: str,
        pathway_crit_history_filename: str,
        circular_components: list,
        component_initial_mass: float,
        path_dict: dict,
        sc_begin : List[str] = ["manufacturing"],
        sc_end : List[str]=["landfilling"],
        sc_in_circ : List[str]=[],
        sc_out_circ : List[str]=[],
        year: float = 2000.0,
        start_year: float = 2000.0,
        verbose: int = 0,
        save_copy=False,
        save_name="netw.csv",
        run=0,
        random_state=np.random.default_rng(13),
    ):
        """
        Reads in small datasets to DataFrames and stores the path to the large
        locations dataset for later use.

        Parameters
        ----------
        step_costs_file : str
            Path to file listing processing steps and cost calculation methods
            by facility type.
        transpo_edges_file : str
            Path to file listing inter-facility edges and transportation cost
            calculation methods.
        locations_file : str
            Path to dataset of facility locations.
        routes_file : str
            Path to dataset of routes between facilities.
        pathway_crit_history_filename : str
            Path to file where the history of whatever criterion is used to
            decide between circularity pathways is saved.
        circular_components : list
            Names of components for which this CostGraph is built.
        component_initial_mass : float
            Average mass of a single technology component at the beginning of
            the model run. Units: metric tons (tonnes).
        path_dict : Dict
            Dictionary of case-study-specific parameters to be passed into
            the cost methods. Can be of any structure as defined in the
            scenario config file.
        sc_begin : List[str]
            List of processing step(s) where supply chain paths begin.
        sc_end : List[str]
            List of processing step(s) where supply chain paths terminate.
        sc_in_circ : List[str]
            Facility type(s) that process material for re-circulation within the supply chain.
        sc_out_circ: List[str]
            Facility type(s) that process material for re-circulation outside the supply chain
        year : float
            Simulation year provided by the DES at CostGraph instantiation.
        start_year : float
            Year at beginning of the model run.
        verbose : int
            Integer specifying how much info CostGraph should provide as it
            works.
            0 = No information other than return values
            1 = Info on when key methods start and stop
            >1 = Detailed info on facilities, nodes, and edges
        save_copy : bool
            Whether or not to save the initial Cost Graph network structure
            as a CSV file (edge list).
        save_name : str
            CSV file name where the initial Cost Graph network structure is
            saved (edge list).
        run : int
            Model run number for evaluating uncertainty within a scenario
        random_state : np.random.default_rng
            Instantiated random number generator for uncertainty analysis.
        """
        self.cost_methods = CostMethods(start_year = start_year, seed=random_state, run=run)

        self.start_time = time()
        self.step_costs = pd.read_csv(step_costs_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)

        # these data sets are processed line by line
        self.loc_file = locations_file

        # This file now contains edge definitions, node metadata, and route distances
        self.routes_file = pd.read_csv(routes_file)

        # also read in the locations as a dataframe for reference in
        # find_nearest
        self.loc_df = pd.read_csv(locations_file)

        self.sc_end = sc_end + sc_out_circ + sc_in_circ
        self.sc_begin = sc_begin
        
        if len(circular_components) == 1:
            self.circular_components = circular_components[0]
        else:
            self.circular_components = circular_components

        self.path_dict = path_dict

        self.year = year

        # Create a dictionary to store the cost adjustment factor by year
        # Using this factor prevents negative path weights, which break most shortest path algorithms
        # By storing the cost adjustment, we can post process costs back to their non-adjusted
        # values in each year
        self.cost_adjustment_factor = {}

        self.path_dict["component mass"] = component_initial_mass
        self.path_dict["year"] = self.year
        self.path_dict["vkmt"] = None

        self.verbose = verbose

        self.pathway_crit_history_filename = pathway_crit_history_filename
        self.run = run
        # create empty List to store the pathway cost output data
        self.pathway_crit_history = list()

        # Create network structure and metadata df for network building
        # @NOTE the drop_duplicates on step_costs will need to be removed
        # for studies with facility-specific cost methods
        self.network_data = self.routes_file.merge(
            self.step_costs[['step','step_cost_method']].drop_duplicates(),
            left_on = 'u_step',
            right_on = 'step',
            how = 'left'
            ).merge(
                self.transpo_edges,
                on=['u_step','v_step'],
                how='left'
            )

        # Any edges without a defined transportation cost method are assigned
        # the zero method
        # This is intended solely for colocated nodes ie within the same
        # facility
        self.network_data.loc[
            self.network_data.transpo_cost_method.isna(),
            'transpo_cost_method'] = 'zero_method'
        
        # create empty instance variable for supply chain DiGraph
        self.supply_chain = nx.DiGraph()

        # build the initial supply chain graph
        self.build_supplychain_graph()

        if save_copy:
            nx.write_edgelist(self.supply_chain, save_name, delimiter=",")

    @staticmethod
    def get_node_names(facilityID: List[Union[int, str]], subgraph_steps: list):
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

    def all_element_combos(self, list1: list, list2: list):
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
        A list of 2-tuples
        """
        if self.verbose > 1:
            print("Getting node combinations")

        _out = []
        _out = product(list1, list2)

        return list(_out)

    def list_of_tuples(
        self, list1: list, list2: list, list3: list = None, list4: list = None
    ):
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
        list4
            list of any data type

        Returns
        -------
        A list of n-tuples where n can be 2, 3, or 4
        """

        if list3 is not None and list4 is None:
            _len = len(list1)
            if any(len(lst) != _len for lst in [list1, list2, list3]):
                raise NotImplementedError
            else:
                return list(map(lambda x, y, z: (x, y, z), list1, list2, list3))
        elif list3 is not None and list4 is not None:
            _len = len(list1)
            if any(len(lst) != _len for lst in [list1, list2, list3, list4]):
                raise NotImplementedError
            else:
                return list(
                    map(lambda w, x, y, z: (w, x, y, z), list1, list2, list3, list4)
                )
        else:
            if len(list1) != len(list2):
                raise NotImplementedError
            else:
                return list(map(lambda x, y: (x, y), list1, list2))

    def find_nearest(self, source_node: str, crit: str):
        """
        Method that finds the nearest nodes to source and returns that node name,
        the path length to the nearest node, and the path to the nearest node as
        a list of nodes.

        Original code source:
        https://stackoverflow.com/questions/50723854/networkx-finding-the-shortest-path-to-one-of-multiple-nodes-in-graph

        Parameters
        ----------
        source_node
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
            print(f"Finding shortest paths from {source_node} to {self.sc_end}")

        # Pull out a list of all nodes in the supply chain that are terminal
        # The linear supply chain terminates there, OR one loop of a circular pathway
        # terminates there
        targets = [tnode for tnode in self.supply_chain.nodes 
                    if any([scr in tnode for scr in self.sc_end])]

        # Loop thru terminal nodes
        # Use the loop rather than list comprehension b/c if a terminal node isn't reachable from the source
        # node, the list comprehension will throw an error
        short_paths = {}
        lengths = {}
        for tnode in targets:
            try:
                # Find the shortest path (list of nodes) to terminal node
                short_paths[tnode] = nx.astar_path(self.supply_chain, source = source_node, target = tnode, weight = crit)
                # Find the shortest path length to terminal node
                lengths[tnode] = nx.astar_path_length(self.supply_chain, source = source_node, target = tnode, weight = crit)
            except nx.NetworkXNoPath:
                if self.verbose > 1: print(f'CostGraph.find_nearest: No path from {source_node} to {tnode}')
                continue
        
        # return the smallest of all lengths to get to typeofnode
        if len(lengths) > 0:
            # For detailed debugging, save a file of all paths found and their lengths
            pd.DataFrame([short_paths, lengths]).to_csv(f'{source_node}-{int(self.year)}-paths.csv', index=False)

            # Print a summary of the paths found
            if self.verbose > 1:
                print(f'CostGraph.find_nearest: {len(lengths)} paths from {source_node} to {targets} cost '
                        f'${np.round(min(lengths),2)} - ${np.round(max(lengths),2)}',
                        flush = True)

            # dict of shortest paths to all targets
            nearest = min(lengths, key=lengths.get)
            timeout_list = [self.supply_chain.nodes[node]['timeout'] for node in short_paths[nearest]]

            dist_list = [
                self.supply_chain.edges[short_paths[nearest][d : d + 2]]["dist"]
                for d in range(len(short_paths[nearest]) - 1)
            ]
            dist_list.insert(0, 0.0)
            route_id_list = [
                self.supply_chain.edges[short_paths[nearest][d : d + 2]]["route_id"]
                for d in range(len(short_paths[nearest]) - 1)
            ]
            route_id_list.insert(0, None)
            
            _out = self.list_of_tuples(short_paths[nearest], timeout_list, dist_list, route_id_list)

            # create dictionary for this preferred pathway cost and decision
            # criterion and append to the pathway_crit_history
            _fac_id = self.supply_chain.nodes[source_node]["facility_id"]
            _loc_line = self.loc_df[self.loc_df.facility_id == _fac_id]
            #_bol_crit = nx.shortest_path_length(
            #    self.supply_chain,
            #    source=self.find_upstream_neighbor(node_id=_fac_id, crit="cost"),
            #    target=source_node,
            #    weight=crit,
            #    method="bellman-ford",
            #)

            for i in self.sc_end:
                _dest = [key for key, value in lengths.items() if i in key]
                _crit = [value for key, value in lengths.items() if i in key]
                if len(_crit) > 0:
                    self.pathway_crit_history.append(
                        {
                            "year": self.year,
                            "source_facility_id": _fac_id,
                            "destination_facility_id": _dest,
                            "region_id_1": _loc_line.region_id_1.values[0],
                            "region_id_2": _loc_line.region_id_2.values[0],
                            "region_id_3": _loc_line.region_id_3.values[0],
                            "region_id_4": _loc_line.region_id_4.values[0],
                            "eol_pathway_type": i,
                            "eol_pathway_criterion": _crit,
                            #"bol_pathway_criterion": _bol_crit,
                        }
                    )

            return nearest, lengths[nearest], _out
        else:
            # not found, no path from source to typeofnode
            print(f'CostGraph.find_nearest: No paths from {source_node} to any of {self.sc_end} nodes')
            return None, None, None


    def find_nearest_factype(
        self,
        source_node: str,
        target_factype: str,
        crit: str
        ):
        """
        Method that finds the nearest nodes of type target_factype to source_node and
        returns that node name, the path length to the nearest node, and the 
        path to the nearest node as a list of nodes.

        See docstring for find_nearest for original code source

        Parameters
        ----------
        source_node : str
            Name of node where this path begins.
        
        target_factype : str
            Facility type of target nodes where this path should terminate.

        crit : str
            Criteria to calculate path "length". May be cost or dict.

        Returns
        -------
        [0] name of node of type target_factype "closest" to source_node
        [1] "length" of path between source_node and the closest target_factype node
        [2] list of nodes defining the path between source_node and the closest target_factype node
        """
        if self.verbose > 1:
            print(f"Finding path from {source_node} to nearest {target_factype}")

        # We are only interested in a particular type(s) of node
        targets = [tnode for tnode in self.supply_chain.nodes if target_factype in tnode]
        
        short_paths = {}
        lengths = {}
        for tnode in targets:
            try:
                # Find the shortest path (list of nodes) to target factype nodes
                short_paths[tnode] = nx.astar_path(self.supply_chain, source = source_node, target = tnode, weight = crit)
                # Find the shortest path length from source_node to target factype nodes
                lengths[tnode] = nx.astar_path_length(self.supply_chain, source = source_node, target = tnode, weight = crit)
            except nx.NetworkXNoPath:
                if self.verbose > 1: print(f'CostGraph.find_nearest_factype: No path from {source_node} to {tnode}')

        # return the smallest of all lengths to get to typeofnode
        if lengths:
            # dict of shortest paths to all targets
            nearest = min(lengths, key=lengths.get)
            timeout_list = [1.0 for node in short_paths[nearest]]
            dist_list = [
                self.supply_chain.edges[short_paths[nearest][d : d + 2]]["dist"]
                for d in range(len(short_paths[nearest]) - 1)
            ]
            dist_list.insert(0, 0.0)
            route_id_list = [
                self.supply_chain.edges[short_paths[nearest][d : d + 2]]["route_id"]
                for d in range(len(short_paths[nearest]) - 1)
            ]
            route_id_list.insert(0, None)
            _routes = [r for r in route_id_list if r is not None]

            # create dictionary for this preferred pathway cost and decision
            # criterion and append to the pathway_crit_history
            _fac_id = self.supply_chain.nodes[source_node]["facility_id"]
            _loc_line = self.loc_df[self.loc_df.facility_id == _fac_id]
            #_bol_crit = nx.shortest_path_length(
            #    self.supply_chain,
            #    source=self.find_upstream_neighbor(node_id=_fac_id, crit="cost"),
            #    target=source_node,
            #    weight=crit,
            #    method="bellman-ford",
            #)

            for i in self.sc_end:
                _dest = [key for key, value in lengths.items() if i in key]
                _crit = [value for key, value in lengths.items() if i in key]
                if len(_crit) > 0:
                    self.pathway_crit_history.append(
                        {
                            "year": self.year,
                            "source_facility_id": _fac_id,
                            "destination_facility_id": _dest,
                            "region_id_1": _loc_line.region_id_1.values[0],
                            "region_id_2": _loc_line.region_id_2.values[0],
                            "region_id_3": _loc_line.region_id_3.values[0],
                            "region_id_4": _loc_line.region_id_4.values[0],
                            "eol_pathway_type": i,
                            "eol_pathway_criterion": _crit,
                            #"bol_pathway_criterion": _bol_crit,
                        }
                    )

            return nearest, lengths[nearest], _routes
        else:
            print(f'CostGraph.find_nearest_factype: No path from {source_node} to {target_factype} facility type')
            # not found, no path from source to typeofnode
            return None, None, None


    def build_supplychain_graph(self):
        """
        Reads in the locations data set line by line. Each line becomes a
        DiGraph representing a single facility. Facility DiGraphs are
        added onto a supply chain DiGraph and connected with inter-facility
        edges. Edges within facilities have no cost or distance. Edges
        between facilities have costs defined in the interconnections
        dataset and distances defined in the routes dataset.
        """
        _netime = time()
        if self.verbose > 0:
            print(f'CostGraph: Adding nodes and edges',flush=True)

        # add all facilities and intra-facility edges to supply chain
        # The format the networkx DiGraph needs is a list of three-tuples
        # The first two elements per tuple define the u (source) and v 
        # (destination) nodes
        # The last element is a dictionary of edge attributes
        all_edge_list = [ (
            u_node,
            v_node,
            {'dist': dist, # the getattr method below pulls the actual function from costmethods.py
            'cost_method': [getattr(self.cost_methods, str(node_cost)), getattr(self.cost_methods, str(transpo_cost))],
            'cost': -1.0,
            'route_id': routeid}
            )
            for u_node, v_node, dist,
                node_cost, transpo_cost,
                routeid 
            in zip(self.network_data.u_node_id, self.network_data.v_node_id, self.network_data.vkmt,
            self.network_data.step_cost_method, self.network_data.transpo_cost_method,
            self.network_data.route_id)
        ]

        self.supply_chain.add_edges_from(all_edge_list)
        
        # Each node needs a facility_id attribute assigned
        # This is so pathfinding logic, which operates off facility_id, will work
        # the facility_id is the numeric code prepended by one letter, and it's already
        # a part of the node_id
        _node_attr_dict = {}
        for node_id, facility_id in zip(self.network_data.u_node_id, self.network_data.u_facility_id):
            if node_id not in _node_attr_dict.keys(): _node_attr_dict[node_id] = facility_id
        for node_id, facility_id in zip(self.network_data.v_node_id, self.network_data.v_facility_id):
            if node_id not in _node_attr_dict.keys(): _node_attr_dict[node_id] = facility_id

        nx.set_node_attributes(
            self.supply_chain,
            values = _node_attr_dict,
            name = 'facility_id'
        )

        # Add timespan to nodes. Facilities with "in use" in the name get either 20 or 30 year lifespans
        # @NOTE Eventually this should draw from facility information and component-level lifespans
        # in the YAML files. This logic is a quick fix specific to the glass case study.
        _node_timeout_dict = {}
        for node_id in self.network_data.u_node_id:
            if node_id not in _node_timeout_dict.keys(): 
                if 'pv in use' in node_id:
                    _timeout = 20.0
                elif 'window in use' in node_id:
                    _timeout = 30.0
                else:
                    _timeout = 1.0
                
                _node_timeout_dict[node_id] = _timeout
        for node_id in self.network_data.v_node_id:
            if node_id not in _node_timeout_dict.keys(): 
                if 'pv in use' in node_id:
                    _timeout = 20.0
                elif 'window in use' in node_id:
                    _timeout = 30.0
                else:
                    _timeout = 1.0
                
                _node_timeout_dict[node_id] = _timeout
        
        nx.set_node_attributes(
            self.supply_chain,
            values = _node_timeout_dict,
            name = 'timeout'
        )
        
        if self.verbose > 0:
            print(f'CostGraph: Adding nodes and edges took {np.round((time() - _netime)/60, 2)} minutes',flush=True)

        if self.verbose > 0:
            print(f'CostGraph: Calculating edge costs', flush=True)

        _ctime = time()
        for edge in self.supply_chain.edges():
            if self.verbose > 2:
                print("Calculating edge costs for ", edge)

            _edge_dict = self.path_dict.copy()
            _edge_dict["vkmt"] = self.supply_chain.edges[edge]["dist"]

            # Year and component mass are defined when CostGraph is instantiated
            # and do not need to be updated during supply chain generation
            try:
                self.supply_chain.edges[edge]["cost"] = sum(
                    [f(_edge_dict) for f in self.supply_chain.edges[edge]["cost_method"]]
                )
            except TypeError:
                print(f'CostGraph: A cost method assigned to {edge} is returning None', flush=True)
                raise TypeError
        
        if self.verbose > 0:
            print(f'CostGraph: Calculating edge costs took {np.round((time() - _ctime)/60, 2)} minutes', flush=True)

        _cost_adjust = min([value for key, value in nx.get_edge_attributes(self.supply_chain, 'cost').items()])
        if _cost_adjust < 0.0:
            print(f'CostGraph: Adjusting all costs for {self.year} upwards by ${np.round(abs(_cost_adjust), 2)}', flush = True)
            self.cost_adjustment_factor[self.year] = abs(_cost_adjust) if _cost_adjust < 0.0 else 0.0
            for edge in self.supply_chain.edges():
                self.supply_chain.edges[edge]['cost'] = self.supply_chain.edges[edge]['cost'] + self.cost_adjustment_factor[self.year]

        if self.verbose > 0:
            print(f'CostGraph: Instantiation took {np.round((time() - self.start_time)/60, 2)} minutes', flush = True)


    def choose_paths(self, source_node: str = None, crit: str = "cost"):
        """
        Calculate total pathway costs (sum of all node and edge costs) over
        all possible pathways between source and target nodes. Other "costs"
        such as distance or environmental impacts may be used as well with
        modifications to the crit argument of the find_nearest call.

        Parameters
        ----------
        source_node : str
            Node name in the format "facilitytype_facilityid".
        crit : str
            Criterion on which "shortest" path is defined. Defaults to cost.

        Returns
        -------
        Dict
            Dictionary containing the source node, target node, path between
            source and target, and the pathway "cost" (criterion).
        """
        # Since all edges now contain both processing costs (for the u node)
        # as well as transport costs (including distances), all we need to do
        # is get the shortest path using the 'cost' attribute as the edge weight
        if source_node is None:
            raise ValueError(f"CostGraph.choose_paths: source node cannot be None")
        else:
            if source_node not in self.supply_chain.nodes():
                raise ValueError(f"CostGraph.choose_paths: {source_node} not in CostGraph")
            else:
                _paths = []
                _chosen_path = self.find_nearest(source_node=source_node, crit=crit)
                _paths.append(
                    {
                        "source": source_node,
                        "target": _chosen_path[0],
                        "path": _chosen_path[2],
                        "cost": _chosen_path[1],
                    }
                )

                return _paths

    def find_upstream_neighbor(
        self, node_id: int, crit: str = "dist"
    ):
        """
        Given a node in the network, find the "nearest" upstream neighbor to
        that node that is of the type specified by self.sc_begin. "Nearest" is
        determined according to the crit parameter.

        Parameters
        ----------
        node_id : int
            facility_id of a node in the supply chain network. No default.
        crit : str
            Criteron used to decide which manufacturing node is "nearest".
            Defaults to distance.

        Returns
        -------
        _nearest_facility_id : int
            Integer identifying the "closest" upstream node of type listed in
            self.sc_begin that is connected to (possibly via multiple steps)
            the node with the provided node_id. Returns None
            if node_id does not exist in the network or if the node_id does not
            connect to any nodes of types listed in self.sc_begin.
        """
        # Check that the node_id exists in the supply chain.
        # If it doesn't, print a message and return None
        if (
            not node_id
            in nx.get_node_attributes(self.supply_chain, name="facility_id").values()
        ):
            print(f"Facility {node_id} does not exist in CostGraph", flush=True)
            return None
        else:
            # If node_id does exist in the supply chain, pull out the node name
            _node = [
                x
                for x, y in self.supply_chain.nodes(data=True)
                if ('facility_id',node_id) in y.items()
            ][0]

        # Get a list of all nodes upstream of this node_id with a facility type
        # specified in self.sc_begin
        # The while loop performs this operation recursively in case the node we're looking
        # for is several steps upstream
        # Only the node we're looking for is stored in _upstream_nodes
        # Note: the "find" function does not look for exact matches, only the existence of
        # strings in self.sc_begin in the node name
        _upstream_nodes = []
        _predec = [_node]
        while len(_upstream_nodes) == 0:
            _predec = [n for ns in [list(self.supply_chain.predecessors(p)) for p in _predec] for n in ns]
            if len(_predec) == 0:
                print(f'CostGraph.find_upstream_neighbor: {_node} has no predecessors', flush = True)
            _upstream_nodes = [n for n in _predec if any([n.find(begin + '_') != -1 for begin in self.sc_begin])]
            # Since we do this recursively, we also need to double check that a path exists between 
             # the upstream nodes and _node. If not, remove those entries from _upstream_nodes
            for _u in _upstream_nodes:
                try:
                    _ = nx.astar_path(self.supply_chain, source = _node, target = _u)
                except nx.NetworkXNoPath:
                    _upstream_nodes.remove(_u)
        
        # Search the list for the "closest" node
        if len(_upstream_nodes) == 0:
            # If there are no upstream nodes of the correct type, print a
            # message and return None
            print(
                f"Facility {node_id} does not have any upstream neighbors of type {connect_to}",
                flush=True,
            )
            return None

        elif len(_upstream_nodes) > 1:
            # If there are multiple options, identify the nearest neighbor
            # according to the crit(eria) parameter
            _upstream_dists = [nx.astar_path_length(self.supply_chain, source = _up_n, target = _node, weight = 'dist') 
                                 for _up_n in _upstream_nodes]
            _nearest_upstream_node = _upstream_nodes[_upstream_dists.index(min(_upstream_dists))]
            _nearest_facility = _nearest_upstream_node

        else:
            # If there is only one option, pull that node's facility_id directly
            _nearest_facility = _upstream_nodes[0]

        # Return the "closest" node's name (facility type + facility_id)
        return _nearest_facility

    def find_downstream(
        self,
        node_name: str = None,
        facility_id: int = None,
        connect_to: str = "landfill",
        crit: str = "dist",
        get_dist: bool = False,
    ):
        """
        Given a node (node_name and/or facility_id) in the network, find the
        node's "nearest" downstream neighbor of type connect_to. "Nearest"
        is specified by the crit parameter.

        Parameters
        ----------
        node_name : str
            Full node name of the starting node.
        facility_id : int
            Unique facility ID for the starting node.
        connect_to : str
            Facility type to connect to.
        crit : str
            Criterion on which "shortest" pathway is determined.
        get_dist : bool
            If True, also return the transportation distance to the downstream
            node and the route_id along which material is transported.

        Returns
        -------
        int or (int, float, str)
            Facility ID of the closest (according to "crit") facility
            of type "connect_to" downstream of the node indicated by node_id.
            Optionally returns the distance to the downstream node and the
            route_id along which material is transported to the downstream 
            node.
        """

        # Check that the node_id exists in the supply chain.
        # If it doesn't, print a message and return None
        # if a facility_id was provided, use that to locate the node
        if facility_id is not None:
            if (
                not facility_id
                in nx.get_node_attributes(
                    self.supply_chain, name="facility_id"
                ).values()
            ):
                print(f"Facility {facility_id} does not exist in CostGraph", flush=True)
                return None
            else:
                # If facility_id does exist in the supply chain, pull out the
                # node name
                _node = [
                    x
                    for x, y in self.supply_chain.nodes(data=True)
                    if y["facility_id"] == facility_id
                ][0]
                # Get a list of all nodes with an outgoing edge that connects
                # to this facility_id, with the specified facility type
                _downst_nodes = [
                    n
                    for n in self.supply_chain.successors(_node)
                    if n.find(connect_to) != -1
                ]
                _upstream_dists = [
                    self.supply_chain.edges[_node, _lnd_n][crit]
                    for _lnd_n in _downst_nodes
                ]

                # Search the list for the "closest" node
                if len(_downst_nodes) == 0:
                    # If there are no upstream nodes of the correct type, print a
                    # message and return None
                    print(
                        f"Node {node_name} does not have any downstream neighbors of type {connect_to}",
                        flush=True,
                    )
                    return None
                elif len(_downst_nodes) > 1:
                    # If there are multiple options, identify the nearest neighbor
                    # according to the crit(eria) parameter

                    _nearest_downst_node = _downst_nodes[
                        _upstream_dists.index(min(_upstream_dists))
                    ]
                    _nearest_route_id = self.supply_chain.edges[
                        _node, _nearest_downst_node
                    ]["route_id"]

                    if not get_dist:
                        return _nearest_downst_node
                    else:
                        return (
                            _nearest_downst_node,
                            min(_upstream_dists),
                            _nearest_route_id,
                        )
                else:
                    # If there is only one option, pull that node's facility_id directly
                    _nearest_downst_node = _downst_nodes[0]
                    _upstream_dist = _upstream_dists[0]
                    _nearest_route_id = self.supply_chain.edges[
                        _node, _nearest_downst_node
                    ]["route_id"]
                    if not get_dist:
                        return _nearest_downst_node
                    else:
                        return _nearest_downst_node, _upstream_dist, _nearest_route_id

        elif node_name is not None:
            if not node_name in self.supply_chain.nodes:
                print(f"Node {node_name} does not exist in CostGraph", flush=True)
                return None
            else:
                # Get a list of all nodes with an outgoing edge that connects
                # to this facility_id, with the specified facility type
                _downst_nodes = [
                    n
                    for n in self.supply_chain.successors(node_name)
                    if n.find(connect_to) != -1
                ]
                _upstream_dists = [
                    self.supply_chain.edges[node_name, _lnd_n][crit]
                    for _lnd_n in _downst_nodes
                ]

                if len(_downst_nodes) > 1:
                    _nearest_downst_node = _downst_nodes[
                        _upstream_dists.index(min(_upstream_dists))
                    ]
                    _nearest_route_id = self.supply_chain.edges[
                        node_name, _nearest_downst_node
                    ]["route_id"]

                    if not get_dist:
                        return _nearest_downst_node
                    else:
                        return (
                            _nearest_downst_node,
                            min(_upstream_dists),
                            _nearest_route_id,
                        )
                elif len(_downst_nodes) == 1:
                    _nearest_downst_node = _downst_nodes[0]
                    _nearest_route_id = self.supply_chain.edges[
                        node_name, _nearest_downst_node
                    ]["route_id"]
                    if not get_dist:
                        return _nearest_downst_node
                    else:
                        return (
                            _nearest_downst_node,
                            _upstream_dists[0],
                            _nearest_route_id,
                        )
                else:
                    print(
                        f"Node {node_name} does not have any downstream neighbors of type {connect_to}",
                        flush=True,
                    )
                    return None
        else:
            print(f"No node identifier provided to find_downstream", flush=True)
            return None

    def update_costs(self, path_dict):
        """
        Re-calculates all edge costs based on arguments passed to cost methods.

        Parameters
        ----------
        path_dict : Dict
            Dictionary of variable structure containing cost parameters for
            calculating and updating processing costs for circularity pathway
            processes
        """
        # update the year for CostGraph
        self.year = path_dict["year"]

        for edge in self.supply_chain.edges():
            _edge_dict = path_dict.copy()
            _edge_dict["vkmt"] = self.supply_chain.edges[edge]["dist"]
            self.supply_chain.edges[edge]["cost"] = sum(
                [f(_edge_dict) for f in self.supply_chain.edges[edge]["cost_method"]]
            )
        
        _cost_adjust = min([value for key, value in nx.get_edge_attributes(self.supply_chain, 'cost').items()])
        if _cost_adjust < 0.0:
            print(f'CostGraph.update_costs: Adjusting all costs for {self.year} upwards by ${np.round(abs(_cost_adjust), 2)}',
            flush = True)
            self.cost_adjustment_factor[self.year] = abs(_cost_adjust) if _cost_adjust < 0.0 else 0.0

            for edge in self.supply_chain.edges():
                self.supply_chain.edges[edge]['cost'] = self.cost_adjustment_factor[self.year] + self.supply_chain.edges[edge]['cost']

        if self.verbose > 0 and self.year > 2001:
            print(f'CostGraph.update_costs: Costs updated for {self.year} after {np.round(time() - self.update_time, 1)} s',
                    flush=True)
        self.update_time = time()

    def save_costgraph_outputs(self):
        """
        Performs postprocessing on CostGraph outputs being saved to file and
        saves to user-specified filenames and directories
        """
        try:
            _out = pd.DataFrame(
                self.pathway_crit_history
                ).explode(
                    ['destination_facility_id','eol_pathway_criterion']
                    ).drop_duplicates(
                        ignore_index=True
                        )
            _out["run"] = self.run
            with open(self.pathway_crit_history_filename, "a") as f:
                _out.to_csv(
                    f, mode="a", header=f.tell() == 0, index=False, lineterminator="\n"
                )
        except KeyError:
            print(f"CostGraph.save_costgraph_outputs: pathway_crit_history is empty; no end of life flows were simulated")
