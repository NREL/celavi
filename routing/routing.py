#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 22 08:03:13 2021

Uses code from Feedstock Production Emissions to Air Model (FPEAM) Copyright (c) 2018
Alliance for Sustainable Energy, LLC; Noah Fisher.
Builds on functionality in the FPEAM's FPEAM.py, Router.py, Data.py, and IO.py.
Unmodified code is available at https://github.com/NREL/fpeam.

@author: aeberle
"""

import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.shortest_paths.weighted import bidirectional_dijkstra
from scipy.spatial import ckdtree
from joblib import Memory
import tempfile
import Data
import matplotlib.pyplot as plt


class Router(object):
    """Discover routing between nodes"""

    def __init__(self, edges, node_map, memory=None, algorithm=bidirectional_dijkstra):
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
        Find route from <from_fips> to <to_fips>, if exists.
        :param start: [list] [x, y]
        :param end: [list] [x, y]
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


transportation_graph = 'data/inputs/transportation_graph.csv'

# graph node locations
node_locations = 'data/inputs/node_locations.csv'

# data backfill flag
backfill = True

_transportation_graph = Data.TransportationGraph(fpath=transportation_graph, backfill=backfill)
_node_locations = Data.TransportationNodeLocations(fpath=node_locations, backfill=backfill)
_temp_dir = tempfile.mkdtemp()

router = Router(edges=_transportation_graph,
                node_map=_node_locations,
                memory=Memory(location=_temp_dir))

# nx.write_weighted_edgelist(router.Graph, 'data/outputs/transport_graph.csv')

# G = nx.petersen_graph()
# plt.subplot(121)
# nx.draw(router.Graph, with_labels=True, font_weight='bold')
# plt.subplot(122)
# nx.draw_shell(G, nlist=[range(5, 10), range(5)], with_labels=True, font_weight='bold')

# get routing information between each unique region_production and
# region_destination pair

generic_locations = 'data/inputs/locations short.csv'
locations = Data.Locations(fpath=generic_locations, backfill=backfill)

# separate source and destination locations from generic "locations" list
_source_loc = locations[locations['facility_type'] == 'wind_plant']
_dest_loc = locations[locations['facility_type'] != 'wind_plant']
_source_loc = _source_loc[['facility_id', 'facility_type', 'lat', 'long']].add_prefix('source_')
_dest_loc = _dest_loc[['facility_id', 'facility_type', 'lat', 'long']].add_prefix('destination_')
_source_loc.insert(0, 'merge', 'True')
_dest_loc.insert(0, 'merge', 'True')
route_list = _source_loc.merge(_dest_loc, on='merge')


# OR load source and destination locations directly
#source_locations = 'data/inputs/plant_locations.csv'
#destination_locations = 'data/inputs/destination_locations.csv'
#_source_loc = Data.StartLocations(fpath=source_locations, backfill=backfill)
#_dest_loc = Data.EndLocations(fpath=destination_locations, backfill=backfill)
# route_list = _source_loc.merge(_dest_loc, on='end_facility_type')
# route_list = route_list.rename(columns={"start_long": "source_long",
#                                         "start_lat": "source_lat",
#                                         "end_long": "destination_long",
#                                         "end_lat": "destination_lat"})

route_list.to_csv('data/outputs/route_list.csv')


_routes = route_list[['source_long',
                      'source_lat',
                      'destination_long',
                      'destination_lat']]  # .drop_duplicates()

_routes.to_csv('data/outputs/_routes.csv')

# if routing engine is specified, use it to get the route (fips and
# vmt) for each unique region_production and region_destination pair
if router is not None:

    # initialize holder for all routes
    _vmt_by_county_all_routes = pd.DataFrame()

    # loop through all routes
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
route_list['total_vmt'] = route_list.groupby(by=['source_facility_id', 'source_facility_type', 'source_lat',
                                                 'source_long', 'destination_facility_id', 'destination_facility_type',
                                                 'destination_lat', 'destination_long'])['vmt'].transform('sum')

route_list.to_csv('data/outputs/route_list_output.csv')
