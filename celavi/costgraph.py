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
        fac_edges_file: str,
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
        fac_edges_file : str
            Path to file listing intra-facility edges by facility type.
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
        self.fac_edges = pd.read_csv(fac_edges_file)
        self.transpo_edges = pd.read_csv(transpo_edges_file)

        # these data sets are processed line by line
        self.loc_file = locations_file
        self.routes_file = routes_file

        # also read in the locations as a dataframe for reference in
        # find_nearest
        self.loc_df = pd.read_csv(locations_file)

        self.sc_end = sc_end + sc_out_circ
        self.sc_begin = sc_begin + sc_in_circ
        
        if len(circular_components) == 1:
            self.circular_components = circular_components[0]
        else:
            self.circular_components = circular_components

        self.path_dict = path_dict

        self.year = year

        self.path_dict["component mass"] = component_initial_mass
        self.path_dict["year"] = self.year
        self.path_dict["vkmt"] = None

        self.verbose = verbose

        self.pathway_crit_history_filename = pathway_crit_history_filename
        self.run = run
        # create empty List to store the pathway cost output data
        self.pathway_crit_history = list()

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

    def find_nearest(self, source: str, crit: str):
        """
        Method that finds the nearest nodes to source and returns that node name,
        the path length to the nearest node, and the path to the nearest node as
        a list of nodes.

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
            print("Finding shortest paths from", source)

        # Calculate the length of paths from fromnode to all other nodes
        lengths = nx.single_source_bellman_ford_path_length(
            self.supply_chain, source, weight=crit
        )

        short_paths = nx.single_source_bellman_ford_path(self.supply_chain, source)

        # We are only interested in a particular type(s) of node
        targets = list(
            search_nodes(self.supply_chain, {"in": [("step",), self.sc_end]})
        )

        subdict = {k: v for k, v in lengths.items() if k in targets}

        # return the smallest of all lengths to get to typeofnode
        if subdict:
            # dict of shortest paths to all targets
            nearest = min(subdict, key=subdict.get)
            timeout = nx.get_node_attributes(self.supply_chain, "timeout")
            timeout_list = [
                value for key, value in timeout.items() if key in short_paths[nearest]
            ]
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
            _out = self.list_of_tuples(
                short_paths[nearest], timeout_list, dist_list, route_id_list
            )

            # create dictionary for this preferred pathway cost and decision
            # criterion and append to the pathway_crit_history
            _fac_id = self.supply_chain.nodes[source]["facility_id"]
            _loc_line = self.loc_df[self.loc_df.facility_id == _fac_id]
            _bol_crit = nx.shortest_path_length(
                self.supply_chain,
                source="manufacturing_"
                + str(self.find_upstream_neighbor(node_id=_fac_id, crit="cost")),
                target=str(source),
                weight=crit,
                method="bellman-ford",
            )

            for i in self.sc_end:
                _dest = [key for key, value in subdict.items() if i in key]
                _crit = [value for key, value in subdict.items() if i in key]
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
                            "bol_pathway_criterion": _bol_crit,
                        }
                    )

            return nearest, subdict[nearest], _out
        else:
            # not found, no path from source to typeofnode
            return None, None, None

    def get_edges(self, facility_df: pd.DataFrame, u_edge="step", v_edge="next_step"):
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
            print("Getting edges for ", facility_df["facility_type"].values[0])

        _type = facility_df["facility_type"].values[0]

        _out = (
            self.fac_edges[[u_edge, v_edge]]
            .loc[self.fac_edges.facility_type == _type]
            .dropna()
            .to_records(index=False)
            .tolist()
        )

        return _out

    def get_nodes(self, facility_df: pd.DataFrame):
        """
        Generates a data structure that defines all nodes and node attributes
        for a single facility.

        Parameters
        ----------
        facility_df : pd.DataFrame
            DataFrame containing unique facility IDs, processing steps, and
            the name of the method (if any) used to calculate processing costs

            Columns:
                - facility_id : int
                - step : str
                - connects : str
                - step_cost_method : str

        Returns
        -------
        List[(str, Dict)]
            Data structure used to define a networkx DiGraph. Attributes
            (dictionary keys) are: processing step, cost method, facility
            ID, and region identifiers.
        """
        if self.verbose > 1:
            print(
                "Getting nodes for facility ", str(facility_df["facility_id"].values[0])
            )

        _id = facility_df["facility_id"].values[0]

        # list of nodes (processing steps) within a facility
        _node_names = (
            self.step_costs["step"].loc[self.step_costs.facility_id == _id].tolist()
        )

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.step_costs[
            ["step", "step_cost_method", "facility_id", "connects"]
        ].loc[self.step_costs.facility_id == _id]

        _step_cost["timeout"] = 1

        # create list of dictionaries from data frame with processing steps,
        # cost calculation method, and facility-specific region identifiers
        _attr_data = _step_cost.merge(
            facility_df, how="outer", on="facility_id"
        ).to_dict(orient="records")

        # reformat data into a list of tuples as (str, dict)
        _nodes = self.list_of_tuples(self.get_node_names(_id, _node_names), _attr_data)

        return _nodes

    def build_facility_graph(self, facility_df: pd.DataFrame):
        """
        Creates networkx DiGraph object containing nodes, intra-facility edges,
        and all relevant attributes for a single facility.

        Parameters
        ----------
        facility_df : pd.DataFrame
            DataFrame with a single row that defines a supply chain facility.

            Columns:
                - facility_id : int
                - facility_type : str
                - lat : float
                - long : float
                - region_id_1 : str
                - region_id_2 : str
                - region_id_3 : str
                - region_id_4 : str

        Returns
        -------
        networkx.DiGraph
            Directed graph representation of one supply chain facility.
        """
        if self.verbose > 1:
            print(
                "Building facility graph for ",
                str(facility_df["facility_id"].values[0]),
            )

        # Create empty directed graph object
        _facility = nx.DiGraph()

        _id = str(facility_df["facility_id"].values[0])

        # Generates list of (str, dict) tuples for node definition
        _facility_nodes = self.get_nodes(facility_df)

        # Populate the directed graph with node names and attribute
        # dictionaries
        _facility.add_nodes_from(_facility_nodes)

        # Populate the directed graph with edges
        # Edges within facilities don't have transportation costs or distances
        # associated with them.
        _edges = self.get_edges(facility_df)
        _unique_edges = [tuple(map(lambda w: w + "_" + _id, x)) for x in _edges]

        _methods = [
            {
                "cost_method": [
                    getattr(
                        self.cost_methods, _facility.nodes[edge[0]]["step_cost_method"]
                    )
                ],
                "cost": 0.0,
                "dist": 0.0,
                "route_id": None,
            }
            for edge in _unique_edges
        ]

        _facility.add_edges_from(
            self.list_of_tuples(
                [node[0] for node in _unique_edges],
                [node[1] for node in _unique_edges],
                _methods,
            )
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
        """
        if self.verbose > 0:
            print(
                "Adding nodes and edges at        %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )

        # add all facilities and intra-facility edges to supply chain
        with open(self.loc_file, "r") as _loc_file:

            _reader = pd.read_csv(_loc_file, chunksize=1)

            for _line in _reader:

                # Build the subgraph representation and add it to the list of
                # facility subgraphs
                _fac_graph = self.build_facility_graph(facility_df=_line)

                # add onto the supply supply chain graph
                self.supply_chain.add_nodes_from(_fac_graph.nodes(data=True))
                self.supply_chain.add_edges_from(_fac_graph.edges(data=True))

        if self.verbose > 0:
            print(
                "Nodes and edges added at         %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )
            print(
                "Adding transport cost methods at %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )

        # add all inter-facility edges, with costs but without distances
        # this is a relatively short loop
        for index, row in self.transpo_edges.iterrows():
            if self.verbose > 1:
                print(
                    "Adding transport cost methods to edges between ",
                    row["u_step"],
                    " and ",
                    row["v_step"],
                )

            _u = row["u_step"]
            _v = row["v_step"]
            _transpo_cost = row["transpo_cost_method"]

            # get two lists of nodes to connect based on df row
            _u_nodes = list(search_nodes(self.supply_chain, {"==": [("step",), _u]}))
            _v_nodes = list(search_nodes(self.supply_chain, {"==": [("step",), _v]}))

            # convert the two node lists to a list of tuples with all possible
            # combinations of _u_nodes and _v_nodes
            _edge_list = self.all_element_combos(_u_nodes, _v_nodes)

            if not any(
                [self.supply_chain.nodes[_v]["step"] in self.sc_end for _v in _v_nodes]
            ):
                _methods = [
                    {
                        "cost_method": [
                            getattr(
                                self.cost_methods,
                                self.supply_chain.nodes[edge[0]]["step_cost_method"],
                            ),
                            getattr(self.cost_methods, _transpo_cost),
                        ],
                        "cost": 0.0,
                        "dist": -1.0,
                        "route_id": None,
                    }
                    for edge in _edge_list
                ]
            else:
                _methods = [
                    {
                        "cost_method": [
                            getattr(
                                self.cost_methods,
                                self.supply_chain.nodes[edge[0]]["step_cost_method"],
                            ),
                            getattr(self.cost_methods, _transpo_cost),
                            getattr(
                                self.cost_methods,
                                self.supply_chain.nodes[edge[1]]["step_cost_method"],
                            ),
                        ],
                        "cost": 0.0,
                        "dist": -1.0,
                        "route_id": None,
                    }
                    for edge in _edge_list
                ]

            # add these edges to the supply chain
            self.supply_chain.add_edges_from(
                self.list_of_tuples(
                    [edge[0] for edge in _edge_list],
                    [edge[1] for edge in _edge_list],
                    _methods,
                )
            )
        if self.verbose > 0:
            print(
                "Transport cost methods added at  %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )
        # read in and process routes line by line
        with open(self.routes_file, "r") as _route_file:
            if self.verbose > 0:
                print(
                    "Adding route distances at        %d s"
                    % np.round(time() - self.start_time, 0),
                    flush=True,
                )

            # Only read in columns relevant to CostGraph building
            _reader = pd.read_csv(
                _route_file,
                usecols=[
                    "source_facility_id",
                    "source_facility_type",
                    "destination_facility_id",
                    "destination_facility_type",
                    "total_vkmt",
                    "route_id",
                ],
                chunksize=1,
            )
            _prev_line = None

            for _line in _reader:
                if np.array_equal(_line, _prev_line):
                    continue

                _prev_line = _line

                # find the source nodes for this route
                _u = list(
                    search_nodes(
                        self.supply_chain,
                        {
                            "and": [
                                {
                                    "==": [
                                        ("facility_id",),
                                        _line["source_facility_id"].values[0],
                                    ]
                                },
                                {"in": [("connects",), ["out", "bid"]]},
                            ]
                        },
                    )
                )

                # loop thru all edges that connect to the source nodes
                for u_node, v_node, data in self.supply_chain.edges(_u, data=True):
                    # if the destination node facility ID matches the
                    # destination facility ID in the routing dataset row,
                    # apply the distance from the routing dataset to this edge
                    if (
                        self.supply_chain.nodes[v_node]["facility_id"]
                        == _line["destination_facility_id"].values[0]
                    ):
                        if self.verbose > 1:
                            print(
                                "Adding ",
                                str(_line["total_vkmt"].values[0]),
                                " km between ",
                                u_node,
                                " and ",
                                v_node,
                            )
                        data["dist"] = _line["total_vkmt"].values[0]
                        data["route_id"] = _line["route_id"].values[0]

        # After all of the route distances have been added, any edges that
        # have a distance of -1 km are deleted from the network.
        _all_edges = self.supply_chain.edges.data()
        _remove_edges = []
        for u, v, data in _all_edges:
            if data["dist"] == -1.0:
                if self.verbose > 1:
                    print(f"Removing edge between {u} and {v}")
                _remove_edges.append((u, v))
        self.supply_chain.remove_edges_from(_remove_edges)
        if self.verbose > 0:
            print(
                "Route distances added at         %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )
            print(
                "Calculating edge costs at        %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )

        for edge in self.supply_chain.edges():
            if self.verbose > 1:
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
            print(
                "Supply chain graph is built at   %d s"
                % np.round(time() - self.start_time, 0),
                flush=True,
            )

    def choose_paths(self, source: str = None, crit: str = "cost"):
        """
        Calculate total pathway costs (sum of all node and edge costs) over
        all possible pathways between source and target nodes. Other "costs"
        such as distance or environmental impacts may be used as well with
        modifications to the crit argument of the find_nearest call.

        Parameters
        ----------
        source : str
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
        if source is None:
            raise ValueError(f"CostGraph.choose_paths: source node cannot be None")
        else:
            if source not in self.supply_chain.nodes():
                raise ValueError(f"CostGraph.choose_paths: {source} not in CostGraph")
            else:
                _paths = []
                _chosen_path = self.find_nearest(source=source, crit=crit)
                _paths.append(
                    {
                        "source": source,
                        "target": _chosen_path[0],
                        "path": _chosen_path[2],
                        "cost": _chosen_path[1],
                    }
                )

                return _paths

    def find_upstream_neighbor(
        self, node_id: int, connect_to: str = "manufacturing", crit: str = "dist"
    ):
        """
        Given a node in the network, find the "nearest" upstream neighbor to
        that node that is of the type specified by connect_to. "Nearest" is
        determined according to the crit parameter.

        Parameters
        ----------
        node_id : int
            facility_id of a node in the supply chain network. No default.
        connect_to : str
            facility_type of the upstream node.
        crit : str
            Criteron used to decide which manufacturing node is "nearest".
            Defaults to distance.

        Returns
        -------
        _nearest_facility_id : int
            Integer identifying the "closest" upstream node of type connect_to
            that connects to the node with the provided node_id. Returns None
            if node_id does not exist in the network or if the node_id does not
            connect to any nodes of the connect_to type.
        """

        # Check that the node_id exists in the supply chain.
        # If it doesn't, print a message and return None
        if (
            not node_id
            in nx.get_node_attributes(self.supply_chain, name="facility_id").values()
        ):
            print("Facility %d does not exist in CostGraph" % node_id, flush=True)
            return None
        else:
            # If node_id does exist in the supply chain, pull out the node name
            _node = [
                x
                for x, y in self.supply_chain.nodes(data=True)
                if y["facility_id"] == node_id and y["connects"] == "bid"
            ][0]

        # Get a list of all nodes with an outgoing edge that connects to this
        # node_id, with the specified facility type
        _upstream_nodes = [
            n for n in self.supply_chain.predecessors(_node) if n.find(connect_to) != -1
        ]

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
            _upstream_dists = [
                self.supply_chain.edges[_up_n, _node][crit] for _up_n in _upstream_nodes
            ]
            _nearest_upstream_node = _upstream_nodes[
                _upstream_dists.index(min(_upstream_dists))
            ]
            _nearest_facility_id = _nearest_upstream_node.split("_")[1]

        else:
            # If there is only one option, pull that node's facility_id directly
            _nearest_facility_id = _upstream_nodes[0].split("_")[1]

        # Return the "closest" node's facility_id as an integer
        return int(_nearest_facility_id)

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

        if self.verbose > 0:
            print(
                "Updating costs for %d at         %d s"
                % (path_dict["year"], np.round(time() - self.start_time, 0)),
                flush=True,
            )

        for edge in self.supply_chain.edges():
            _edge_dict = path_dict.copy()
            _edge_dict["vkmt"] = self.supply_chain.edges[edge]["dist"]
            self.supply_chain.edges[edge]["cost"] = sum(
                [f(_edge_dict) for f in self.supply_chain.edges[edge]["cost_method"]]
            )

        if self.verbose > 0:
            print(
                "Costs updated for  %d at         %d s"
                % (path_dict["year"], np.round(time() - self.start_time, 0)),
                flush=True,
            )

    def save_costgraph_outputs(self):
        """
        Performs postprocessing on CostGraph outputs being saved to file and
        saves to user-specified filenames and directories
        """
        _out = pd.DataFrame(
            self.pathway_crit_history
            ).explode(
                column=['destination_facility_id','eol_pathway_criterion']
                ).drop_duplicates(
                    ignore_index=True
                    )
        _out["run"] = self.run
        with open(self.pathway_crit_history_filename, "a") as f:
            _out.to_csv(
                f, mode="a", header=f.tell() == 0, index=False, lineterminator="\n"
            )
