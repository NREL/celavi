import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.shortest_paths.weighted import bidirectional_dijkstra
from scipy.spatial import ckdtree


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
        self._btree = ckdtree.cKDTree(np.array(list(zip(self.node_map.x, self.node_map.y))))

        self.edges = edges

        self.memory = memory

        self.algorithm = algorithm

        self.routes = {}
        self.Graph = nx.Graph()

        if self.memory is not None:
            self.get_route = self.memory.cache(self.get_route, ignore=['self'])

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