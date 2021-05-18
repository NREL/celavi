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
import data_manager as Data


class Router(object):
    """Discover routing between nodes"""

    def __init__(self,
                 edges,
                 node_map,
                 memory=None, algorithm=bidirectional_dijkstra,
                 ):
        """
        :param edges: [DataFrame]
        :param node_map: [DataFrame]
        :param memory [joblib.Memory]
        :param algorithm: [function]
        :return:
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

        print('loading routing graph')
        _ = self.edges.apply(lambda x: self.Graph.add_edge(**x), axis=1)

    def get_route(self, start, end):

        """
        Find route from <start> to <end>, if exists.
        :param start: [list] [long, lat]
        :param end: [list] [long, lat]
        :return: [DataFrame]
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
        _summary['vmt'] = _summary['weight'] / 1000.0 * 0.621371

        return _summary[['region_transportation', 'fclass', 'vmt']]


    def get_all_routes(locations_file : str = '../celavi-data/inputs/locations.csv'):
        """
        Calculates distances traveled between all locations in the locations_file.
        Includes distance traveled through each transportation region (e.g., county FIPS) and road class.

        :return:
        """
        backfill = True  # data backfill flag - True will replace nulls; user must input value for replacement

        # set input file paths for precomputed US road network data
        transportation_graph = '../celavi-data/inputs/precomputed_us_road_network/transportation_graph.csv'  # transport graph (pre computed; don't change)
        node_locations = '../celavi-data/inputs/precomputed_us_road_network/node_locations.csv'  # node locations for transport graph (pre computed; don't change)

        # set output folders for intermediate routing data
        routing_output_folder = '../celavi-data/preprocessing/routing_intermediate_files/'
        preprocessing_output_folder = '../celavi-data/preprocessing/'  # data in this folder will be inputs to CELAVI

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

        # identify states in locations data and loop through states (useful for debugging; loop could be removed)
        # compute routes for all locations in each state and save results
        state_list = locations.region_id_2.unique()
        file_output_list = []
        for state in state_list:
            print(state)
            file_output = routing_output_folder + 'route_list_output_{}.csv'.format(state)
            file_output_list.append(file_output)

            # select all source and destination locations (right now source locations = destination locations)
            # this setup allows us to find routs between all locations in the input locations file
            _source_loc = locations[locations.region_id_2 == state]
            _dest_loc = locations[locations.region_id_2 == state]
            _source_loc = _source_loc[['facility_id', 'facility_type', 'lat', 'long']].add_prefix('source_')
            _dest_loc = _dest_loc[['facility_id', 'facility_type', 'lat', 'long']].add_prefix('destination_')
            _source_loc.insert(0, 'merge', 'True')
            _dest_loc.insert(0, 'merge', 'True')
            route_list = _source_loc.merge(_dest_loc, on='merge')

            # if route_list is empty, generate empty data frame for export (e.g., create column for total_vmt)
            # otherwise, loop through all locations in route_list and compute routing distances
            if route_list.empty:
                print('list is empty')
                route_list['vmt'] = ''
                route_list = route_list.drop(['merge'], axis=1)
                route_list['total_vmt'] = route_list.groupby(by=['source_facility_id', 'source_facility_type', 'source_lat',
                                                                 'source_long', 'destination_facility_id', 'destination_facility_type',
                                                                 'destination_lat', 'destination_long'])['vmt'].transform('sum')
                route_list.to_csv(file_output)
            else:

                route_list.to_csv(routing_output_folder + 'route_list.csv')

                _routes = route_list[['source_long',
                                      'source_lat',
                                      'destination_long',
                                      'destination_lat']]  # .drop_duplicates()

                _routes.to_csv(routing_output_folder + 'routes.csv')

                # if routing engine is specified, use it to get the route (fips and
                # vmt) for each pair of input locations
                if router is not None:

                    # initialize holder for all routes
                    _vmt_by_county_all_routes = pd.DataFrame()

                    # loop through all locations to compute routes
                    print('finding routes')
                    for i in np.arange(_routes.shape[0]):

                        # print every 20 routes
                        if i % 20 == 0:
                            print(i)

                        _vmt_by_county = router.get_route(start=(_routes.source_long.iloc[i],
                                                                 _routes.source_lat.iloc[i]),
                                                          end=(_routes.destination_long.iloc[i],
                                                               _routes.destination_lat.iloc[i]))

                        # add identifier columns for later merging with route_list
                        _vmt_by_county['source_long'] = _routes.source_long.iloc[i]
                        _vmt_by_county['source_lat'] = _routes.source_lat.iloc[i]
                        _vmt_by_county['destination_long'] = _routes.destination_long.iloc[i]
                        _vmt_by_county['destination_lat'] = _routes.destination_lat.iloc[i]

                        # either create the data frame to store all routes,
                        # or append the current route
                        if _vmt_by_county_all_routes.empty:
                            _vmt_by_county_all_routes = _vmt_by_county

                        else:
                            _vmt_by_county_all_routes = \
                                _vmt_by_county_all_routes.append(_vmt_by_county,
                                                                 ignore_index=True,
                                                                 sort=True)

                    # after the loop through all routes is complete, merge the data
                    # frame containing all routes with route_list
                    route_list = route_list.merge(_vmt_by_county_all_routes,
                                                  how='left',
                                                  on=['source_long',
                                                      'source_lat',
                                                      'destination_long',
                                                      'destination_lat'])


                route_list = route_list.drop(['merge'], axis=1)
                # compute total_vmt
                route_list['total_vmt'] = route_list.groupby(by=['source_facility_id', 'source_facility_type', 'source_lat',
                                                                 'source_long', 'destination_facility_id', 'destination_facility_type',
                                                                 'destination_lat', 'destination_long'])['vmt'].transform('sum')

                route_list.to_csv(file_output)

        # append all data from independent state loops into one master routing data frame
        data_complete = pd.DataFrame()
        for file in file_output_list:
            data = pd.read_csv(file)
            data_complete = data_complete.append(data)

        data_complete.to_csv(preprocessing_output_folder + 'routes_computed.csv')

        return data_complete
