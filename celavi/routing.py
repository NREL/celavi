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


class Router:
    """
    Discover routing between nodes
    """

    def __init__(self,
                 edges,
                 node_map,
                 memory=None, algorithm=bidirectional_dijkstra,
                 ):
        """

        Parameters
        ----------
        edges: [DataFrame]
        node_map: [DataFrame]
        memory [joblib.Memory]
        algorithm: [function]

        Returns
        -------
        None
        """

        self.node_map = node_map
        self._btree = ckdtree.cKDTree(np.array(list(zip(self.node_map.long, self.node_map.lat))))

        self.edges = edges

        self.memory = memory

        self.algorithm = algorithm

        self.routes = {}
        self.Graph = nx.Graph()

        if self.memory is not None:
            self.get_route = self.memory.cache(self.get_route, ignore=['self'], verbose=0)

        print('loading routing graph', flush=True)
        _ = self.edges.apply(lambda x: self.Graph.add_edge(**x), axis=1)

    def get_route(self, start, end):

        """
        Find route from <start> to <end>, if exists.

        Parameters
        ----------
        start: [list] [long, lat]

        end: [list] [long, lat]

        Returns
        -------
        [DataFrame]
        """

        _start_point = np.array(start)
        _start_point_idx = self._btree.query(_start_point, k=1)[1]
        from_node = self.node_map.loc[_start_point_idx, 'node_id']

        _end_point = np.array(end)
        _end_point_idx = self._btree.query(_end_point, k=1)[1]
        to_node = self.node_map.loc[_end_point_idx, 'node_id']

        if not (from_node and to_node):
            raise ValueError('start or end node is undefined')

        _path = self.algorithm(self.Graph, from_node, to_node)[1]

        _route = pd.DataFrame(_path, columns=['start_node'], dtype=int)
        _route['end_node'] = _route['start_node'].shift(-1)
        _route = _route[:-1]
        _route['end_node'] = _route['end_node'].astype(int)

        _edges = _route.apply(lambda x: self.Graph.get_edge_data(u=x.start_node,
                                                                 v=x.end_node)['edge_id'], axis=1)

        _summary = self.edges.loc[self.edges.edge_id.isin(_edges.values.tolist()) &
                                  ~self.edges.countyfp.isna() &
                                  ~self.edges.statefp.isna()][['edge_id',
                                                               'statefp',
                                                               'countyfp',
                                                               'weight',
                                                               'fclass']].groupby(['statefp',
                                                                                   'countyfp',
                                                                                   'fclass'])\
            .sum().reset_index()

        _summary['region_transportation'] = _summary['statefp'] + _summary['countyfp']
        _summary['vkmt'] = _summary['weight'] / 1000.0  # converts from meters to kilometers for 'vkmt' summary information

        return _summary[['region_transportation', 'fclass', 'vkmt']]

    @staticmethod
    def get_all_routes(locations_file,
                       route_pair_file,
                       distance_filtering,
                       transportation_graph,
                       node_locations,
                       routes_output_file,
                       routing_output_folder):
        """
        Calculates distances traveled between all locations in the locations_file.
        Includes distance traveled through each transportation region (e.g., county FIPS) and road class.

        Parameters
        ----------
        locations_file
            Dataset of facility locations

        route_pair_file
            Dataset of allowable facility pairs to connect with routes

        distance_filtering
            Dataset of distance-based router filtering

        transportation_graph
            Transportation network data

        node_locations
            Node locations within transportation graph

        routes_output_file
            Path to file where complete routes dataset is saved.

        routing_output_folder
            Path to directory for routing outputs

        Returns
        -------
        DataFrame
        """
        backfill = True  # data backfill flag - True will replace nulls; user must input value for replacement

        # import transportation graph and node locations
        _transportation_graph = Data.TransportationGraph(fpath=transportation_graph, backfill=backfill)
        _node_locations = Data.TransportationNodeLocations(fpath=node_locations, backfill=backfill)

        # create temporary file directory
        _temp_dir = tempfile.mkdtemp()

        # initiate router
        router = Router(edges=_transportation_graph,
                        node_map=_node_locations,
                        memory=Memory(location=_temp_dir))

        # import locations data
        locations = pd.read_csv(locations_file)
        route_pairs = Data.RoutePairs(fpath=route_pair_file,backfill=backfill)
        # Get a list of destination facility types that must be in-state
        # from route_pairs
        _instate_dest = route_pairs[route_pairs['in_state_only'] == True].destination_facility_type.drop_duplicates().values

        # identify states in locations data and loop through states (useful for debugging; loop could be removed)
        # compute routes for all locations in each state and save results
        state_list = locations.region_id_2.unique()
        file_output_list = []
        for state in state_list:
            print(state, flush=True)
            file_output = routing_output_folder + 'route_list_output_{}.csv'.format(state)
            file_output_list.append(file_output)

            # select all source locations within this state
            _source_loc = locations[locations.region_id_2 == state]
            # select all destination locations in the complete data set
            _dest_loc = locations
            # rename columns before merging
            _source_loc = _source_loc[['facility_id', 'facility_type', 'region_id_2', 'lat', 'long']].add_prefix('source_')
            _dest_loc = _dest_loc[['facility_id', 'facility_type', 'region_id_2', 'lat', 'long']].add_prefix('destination_')
            _source_loc.insert(0, 'merge', 'True')
            _dest_loc.insert(0, 'merge', 'True')

            # merge source and destination pairs
            source_dest_pairs = _source_loc.merge(_dest_loc, on='merge')

            # Filter down to only the source/destination pairs allowed by route_pairs
            source_dest_allowable_pairs = route_pairs[['source_facility_type', 'destination_facility_type']].apply(tuple, axis=1)
            source_dest_complete_pairs = source_dest_pairs[['source_facility_type', 'destination_facility_type']].apply(tuple, axis=1)
            source_dest_select_route_types = source_dest_complete_pairs.isin(source_dest_allowable_pairs)
            selected_routes = source_dest_pairs[source_dest_select_route_types]
            all_route_list = selected_routes.merge(route_pairs, on=['source_facility_type', 'destination_facility_type'])

            # divide all_route_list into two sets of routes, one with connections
            # within this state and one with connections out of state
            instate_routes = all_route_list[all_route_list.destination_region_id_2 == state]
            outstate_routes = all_route_list[all_route_list.destination_region_id_2 != state]

            # Remove entries from the out-of-state route list where the
            # connections are required to be in-state
            _keep = outstate_routes.in_state_only == False
            route_list = instate_routes.append(outstate_routes[_keep])

            # if route_list is empty, generate empty data frame for export (e.g., create column for total_vkmt)
            # otherwise, loop through all locations in route_list and compute routing distances
            if route_list.empty:
                print('list is empty')
                route_list['vkmt'] = ''
                route_list = route_list.drop(['merge'], axis=1)
                route_list['total_vkmt'] = route_list.groupby(by=['source_facility_id', 'source_facility_type', 'source_lat',
                                                                 'source_long', 'destination_facility_id', 'destination_facility_type',
                                                                 'destination_lat', 'destination_long'])['vkmt'].transform('sum')
                route_list.to_csv(file_output)

            else:

                route_list.to_csv(routing_output_folder + 'route_list.csv')

                _routes = route_list[['source_long',
                                      'source_lat',
                                      'destination_long',
                                      'destination_lat']]

                _routes.to_csv(routing_output_folder + 'latlongs.csv')

                # if routing engine is specified, use it to get the route (fips and
                # vkmt) for each pair of input locations
                if router is not None:

                    # initialize holder for all routes
                    _vkmt_by_county_all_routes = pd.DataFrame()

                    # loop through all locations to compute routes
                    print('finding routes', flush=True)
                    for i in np.arange(_routes.shape[0]):

                        # print every 20 routes
                        if i % 20 == 0:
                            print(i, flush=True)

                        _vkmt_by_county = router.get_route(start=(_routes.source_long.iloc[i],
                                                                 _routes.source_lat.iloc[i]),
                                                          end=(_routes.destination_long.iloc[i],
                                                               _routes.destination_lat.iloc[i]))

                        # add identifier columns for later merging with route_list
                        _vkmt_by_county['source_long'] = _routes.source_long.iloc[i]
                        _vkmt_by_county['source_lat'] = _routes.source_lat.iloc[i]
                        _vkmt_by_county['destination_long'] = _routes.destination_long.iloc[i]
                        _vkmt_by_county['destination_lat'] = _routes.destination_lat.iloc[i]

                        # either create the data frame to store all routes,
                        # or append the current route
                        if _vkmt_by_county_all_routes.empty:
                            _vkmt_by_county_all_routes = _vkmt_by_county

                        else:
                            _vkmt_by_county_all_routes = \
                                _vkmt_by_county_all_routes.append(_vkmt_by_county,
                                                                 ignore_index=True,
                                                                 sort=True)

                    # after the loop through all routes is complete, merge the data
                    # frame containing all routes with route_list
                    route_list = route_list.merge(_vkmt_by_county_all_routes,
                                                  how='left',
                                                  on=['source_long',
                                                      'source_lat',
                                                      'destination_long',
                                                      'destination_lat'])


                route_list = route_list.drop(['merge'], axis=1)
                # compute total_vkmt
                route_list['total_vkmt'] = route_list.groupby(by=['source_facility_id', 'source_facility_type', 'source_lat',
                                                                 'source_long', 'destination_facility_id', 'destination_facility_type',
                                                                 'destination_lat', 'destination_long'])['vkmt'].transform('sum')

                # if the routes should be filtered based on distance,
                if distance_filtering:
                    # remove rows where total_vkmt > max distance
                    route_list = route_list[route_list.total_vkmt <= route_list.vkmt_max]

                # remove columns used in distance filtering
                route_list.drop(
                    labels=['in_state_only', 'vkmt_max'],
                    axis=1,
                    inplace=True
                )

                route_list.to_csv(file_output)

        # append all data from independent state loops into one master routing data frame
        data_complete = pd.DataFrame()
        for file in file_output_list:
            data = pd.read_csv(file)
            data_complete = data_complete.append(data)



        data_complete.to_csv(routes_output_file,
                             index=False)

