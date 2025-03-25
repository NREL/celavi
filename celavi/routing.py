#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 08:03:13 2021

routing.py uses Dijkstra’s algorithm to compute distances between vertices on a network

Developed using code from Feedstock Production Emissions to Air Model (FPEAM) Copyright (c) 2018
Alliance for Sustainable Energy, LLC; Noah Fisher.
Builds on functionality in the FPEAM's Router.py and Data.py.
Unmodified FPEAM code is available at https://github.com/NREL/fpeam.

@author: aeberle
"""

import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.shortest_paths.weighted import bidirectional_dijkstra
from scipy.spatial import ckdtree
from joblib import Memory
import tempfile
import celavi.data_manager as Data
import uuid
import time


class Router:
    """
    Calculate minimum-distance routes between supply chain facilities.
    """

    def __init__(
        self, edges, node_map, memory=None, algorithm=bidirectional_dijkstra,
    ):
        """

        Parameters
        ----------
        edges: [DataFrame]
            DataFrame of edges within the routing (transportation) network.
        node_map: [DataFrame]
            DataFrame of nodes within the routing (transportation) network.
        memory [joblib.Memory]
            Allows for caching.
        algorithm: [function]
            Method for finding minimum-distance route. Defaults to bidirectional_dijkstra.
        """

        self.node_map = node_map
        self._btree = ckdtree.cKDTree(
            np.array(list(zip(self.node_map.long, self.node_map.lat)))
        )

        self.edges = edges

        self.memory = memory

        self.algorithm = algorithm

        self.routes = {}
        self.Graph = nx.Graph()

        if self.memory is not None:
            self.get_route = self.memory.cache(
                self.get_route, ignore=["self"], verbose=0
            )

        print("loading routing graph", flush=True)
        _ = self.edges.apply(lambda x: self.Graph.add_edge(**x), axis=1)

    def get_route(self, start, end):

        """
        Find route from <start> to <end>, if exists.

        Parameters
        ----------
        start: [list] [long, lat]
            Starting point of route: a node in node_map.

        end: [list] [long, lat]
            Ending point of route: a node in node_map.

        Returns
        -------
        [DataFrame]
            Length and characteristics of route from <start> to <end>.

            Columns:
                - region_transportation : str
                - fclass : int
                - vkmt : float
        """

        _start_point = np.array(start)
        _start_point_idx = self._btree.query(_start_point, k=1)[1]
        from_node = self.node_map.loc[_start_point_idx, "node_id"]

        _end_point = np.array(end)
        _end_point_idx = self._btree.query(_end_point, k=1)[1]
        to_node = self.node_map.loc[_end_point_idx, "node_id"]

        if not (from_node and to_node):
            raise ValueError("start or end node is undefined")

        _path = self.algorithm(self.Graph, from_node, to_node)[1]

        _route = pd.DataFrame(_path, columns=["start_node"], dtype=int)
        _route["end_node"] = _route["start_node"].shift(-1)
        _route = _route[:-1]
        _route["end_node"] = _route["end_node"].astype(int)

        _edges = _route.apply(
            lambda x: self.Graph.get_edge_data(u=x.start_node, v=x.end_node)["edge_id"],
            axis=1,
        )

        _summary = (
            self.edges.loc[
                self.edges.edge_id.isin(_edges.values.tolist())
                & ~self.edges.countyfp.isna()
                & ~self.edges.statefp.isna()
            ][["edge_id", "statefp", "countyfp", "weight", "fclass"]]
            .groupby(["statefp", "countyfp", "fclass"])
            .sum()
            .reset_index()
        )

        _summary["region_transportation"] = _summary["statefp"] + _summary["countyfp"]
        _summary["vkmt"] = (
            _summary["weight"] / 1000.0
        )  # converts from meters to kilometers for 'vkmt' summary information

        return _summary[["region_transportation", "fclass", "vkmt"]]

    @staticmethod
    def get_all_routes(
        network_edges,
        transportation_graph,
        node_locations,
        routes_output_file,
        county_routes_file,
        routing_output_folder,
    ):
        """
        Calculate distances traveled between all connected supply chain facilities.

        Includes distance traveled through each transportation region (e.g., county FIPS) and road class.

        This method has no return value. Routes are saved to CSV file.

        Parameters
        ----------
        network_edges : str
            File of network structure defining source (u) and destination (v) locations
            along with node and facility level metadata

        transportation_graph : str
            File of transportation network data.

        node_locations : str
            File of node locations within transportation graph.

        routes_output_file : str
            Path to file where complete network + routes dataset is saved.
        
        county_routes_file : str
            Path to file where routes with vkmt by county is saved.

        routing_output_folder : str
            Path to directory for intermediate routing outputs.
        """
        backfill = True  # data backfill flag - True will replace nulls; user must input value for replacement

        # import transportation graph and node locations
        _transportation_graph = Data.TransportationGraph(
            fpath=transportation_graph, backfill=backfill
        )
        _node_locations = Data.TransportationNodeLocations(
            fpath=node_locations, backfill=backfill
        )

        # create temporary file directory
        _temp_dir = tempfile.mkdtemp()

        # initiate router
        router = Router(
            edges=_transportation_graph,
            node_map=_node_locations,
            memory=Memory(location=_temp_dir),
        )

        network = pd.read_csv(network_edges)

        # Get a table of which processing steps require downstream
        # landfill facilities, for use in postprocessing routes
        _landfill_edges = network.loc[
            [vkmtmax > 0 and instate 
            for vkmtmax, instate in zip(network.vkmt_max, network.in_state)],
            ['u_step','v_step']
            ].drop_duplicates().reset_index()
        
        _network_dist = []

        vkmt_by_county_list = []

        if router is None:
            print('No router found', flush = True)
            
        else:
            print(f'Router.get_all_routes: Finding {len(network)} routes', flush = True)
            _rtime = time.time()
            for idx, edge in network.iterrows():                
                # Do not find routes between co-located nodes
                if edge.u_facility_id == edge.v_facility_id:
                    _network_dist = _network_dist + [{'index': idx, 'vkmt': 0.0, 'route_id': 'colocated'}]
                # Do not find routes between co-located facilities
                elif edge.u_lat == edge.v_lat and edge.u_long == edge.v_long:
                    _network_dist = _network_dist + [{'index': idx, 'vkmt': 0.0, 'route_id': 'colocated'}]
                else:
                    _vkmt_by_county = router.get_route(
                        start=(
                            edge.u_long,
                            edge.u_lat,
                        ),
                        end=(
                            edge.v_long,
                            edge.v_lat,
                        ),
                    )
                    # If the route distance is greater than a max distance, do not save
                    # the route information. Instead, record the index to drop it from
                    # the network routes file
                    if _vkmt_by_county.vkmt.sum() > edge.vkmt_max:
                        _network_dist = _network_dist + [{'index': idx, 'vkmt': _vkmt_by_county.vkmt.sum(), 'route_id': 'vkmt_max'}]
                    # If the route returned has a total distance of under 1 kilometer, assume
                    # those facilities are colocated
                    # This accounts for facilities that are essentially colocated but don't
                    # have numerically identical lat/long values
                    elif _vkmt_by_county.vkmt.sum() < 1.0:
                        _network_dist = _network_dist + [{'index': idx, 'vkmt': 0.0, 'route_id': 'colocated'}]
                    else:
                        # Assign a route id and node information to the county-level distance data
                        _vkmt_by_county['route_id'] = uuid.uuid4().hex
                        _vkmt_by_county['u_node_id'] = edge.u_node_id
                        _vkmt_by_county['v_node_id'] = edge.v_node_id
                        # Save the total distance into the network dataframe
                        _network_dist = _network_dist + [{'index': idx, 'vkmt': _vkmt_by_county.vkmt.sum(), 'route_id': _vkmt_by_county.route_id.unique()[0]}]
                        # Attach the county-level data to a list for later saving
                        vkmt_by_county_list = vkmt_by_county_list + [_vkmt_by_county]
                
                # Print a status message every 100 routes
                if idx % 100 == 0: print(f'Router.get_all_routes: {idx} routes found after {np.round((time.time() - _rtime)/60, 1)} minutes', flush = True)
            
            network_all_routes = network.merge(
                pd.DataFrame(_network_dist),
                left_index = True,
                right_on = 'index',
                how = 'left'
            )

            # Save the raw routes file including edges that violate the vkmt_max
            network_all_routes.to_csv('network-routes-all.csv', index=False)

            # Remove edges from the network if any have distances greater than the max allowed
            if any(network_all_routes.route_id == 'vkmt_max'):
                network_routes = network_all_routes.drop(network_all_routes.loc[network_all_routes.route_id == 'vkmt_max',:].index)

                # Check through the dataset of nodes that require connections to a landfill
                # If the vkmt_max restriction has removed all edges from these nodes to landfills,
                # locate the nearest landfill and re-add that edge to the network regardless 
                # of the vkmt_max
                _add_edges = pd.DataFrame()
                for _, edge in _landfill_edges.iterrows():
                    _nodes_need_landfills = list(
                        set(
                            network_all_routes.loc[network_all_routes.u_step == edge['u_step'],'u_node_id'].drop_duplicates()
                        ).difference(
                            network_routes.loc[[(u == edge['u_step']) and (v == edge['v_step']) for u, v in zip(network_routes.u_step, network_routes.v_step)],'u_node_id'].drop_duplicates()
                            )
                        )
                    if len(_nodes_need_landfills) > 0:
                        _closest_landfills = network_all_routes.loc[
                            (network_all_routes.u_node_id.isin(_nodes_need_landfills)) & (network_all_routes.v_step == edge.v_step),:
                            ].groupby('u_node_id').agg({'vkmt':'min'}).reset_index()
                        if len(_closest_landfills) == 0:
                            # If the nodes have no available downstream facilities, print a warning
                            # The location data may need to be revised in this case
                            print(f'Router.get_all_routes: Nodes {_nodes_need_landfills} have no available {edge.v_step} nodes')
                        else:
                            _add_edges = pd.concat(
                                [_add_edges,
                                network_all_routes.loc[
                                    (network_all_routes.u_node_id.isin(_nodes_need_landfills)) & (network_all_routes.v_step == edge.v_step) & (network_all_routes.vkmt.isin(_closest_landfills.vkmt)), :]
                                    ]
                                )
                        
            
            # Add in the landfill connections
            network_routes = pd.concat([network_routes, _add_edges]).reset_index()

            # Save the network routes file for use in Cost Graph
            network_routes.to_csv(routes_output_file, index=False)

            # Calculate total distance over fclass and save the county level di
            vkmt_by_county_all = pd.concat(
                vkmt_by_county_list
                ).groupby(
                    ['u_node_id','v_node_id','route_id','region_transportation']
                    ).sum('vkmt').reset_index()
            
            vkmt_by_county_all.drop(columns='fclass', inplace = True)

            vkmt_by_county_all.to_csv(county_routes_file, index=False)
