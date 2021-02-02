import networkx as nx
import pandas as pd
import numpy as np
import warnings

# the locations dataset will be the largest; try to read that one in line by
# line. All other datasets will be relatively small, so storing and
# manipulating the entire dataset within the Python environment shouldn't
# slow execution down noticeably
mockdata = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/input-data-mockup.xlsx"
steps_df = pd.read_excel(mockdata, sheet_name='edges')
costs_df = pd.read_excel(mockdata, sheet_name='costs')
interconnect_df = pd.read_excel(mockdata, sheet_name='interconnections')
loc_df = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/loc-mock.csv"
dist_file = "C:/Users/rhanes/Box Sync/Circular Economy LDRD/data/routes-mock.csv"

# @note cost, next state, relocation destination for the component

class CostGraph:
    """
        Contains methods for reading in graph data, creating network of
        facilities in a supply chain, and finding preferred pathways for
        implementation.
    """

    def __init__(self,
                 input_name : str,
                 locations_file : str,
                 routes_file : str,
                 timestep : int = 0,):
        """
        Reads in small datasets to DataFrames and stores the path to the large
        locations dataset for later use.

        Parameters
        ----------
        input_name
            File name or other identifier where input datasets are stored
        locations_file
            path to dataset of facility locations
        routes_file
            path to dataset of routes between facilities
        timestep
            DES model timestep at which cost graph is instantiated
        """
        # @todo update file IO method to match actual input data format
        self.steps_df=pd.read_excel(input_name, sheet_name='edges')
        self.costs_df=pd.read_excel(input_name, sheet_name='costs')
        self.interconnect_df=pd.read_excel(input_name, sheet_name='interconnections')

        # these data sets are processed line by line
        self.loc_df=locations_file
        self.routes_df=routes_file

        self.timestep = timestep

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

        _out = self.steps_df[[u_edge, v_edge]].loc[self.steps_df.facility_type == _type].dropna().to_records(index=False).tolist()

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
                ['facility_id', 'step', 'connects', 'cost_method']

        Returns
        -------
            List of (str, dict) tuples used to define a networkx DiGraph
            Attributes are: processing step, cost method, facility ID, and
            region identifiers

        """

        _id = facility_df['facility_id'].values[0]

        # list of nodes (processing steps) within a facility
        _node_names = self.costs_df['step'].loc[self.costs_df.facility_id == _id].tolist()

        # data frame matching facility processing steps with methods for cost
        # calculation over time
        _step_cost = self.costs_df[['step','cost_method','facility_id','connects']].loc[self.costs_df.facility_id == _id]

        # create list of dictionaries from data frame with processing steps,
        # cost calculation method, and facility-specific region identifiers
        _attr_data = _step_cost.merge(facility_df,how='outer',on='facility_id').to_dict(orient='records')

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

                # Build the subgraph representation and add it to the list of facility
                # subgraphs
                _fac_graph = self.build_facility_graph(facility_df = _line)

                # add onto the supply supply chain graph
                self.supply_chain.add_nodes_from(_fac_graph.nodes(data=True))
                self.supply_chain.add_edges_from(_fac_graph.edges(data=True))

        # add all inter-facility edges, with costs but without distances
        # this is a relatively short loop
        for index, row in interconnect_df.iterrows():
            _u = row['u_step']
            _v = row['v_step']
            _edge_cost = row['cost_method']

            # get two lists of nodes to connect based on df row
            _u_nodes = self.node_filter(self.supply_chain, 'step', _u)
            _v_nodes = self.node_filter(self.supply_chain, 'step', _v)
            _dict = {'cost':_edge_cost,
                     'dist': 0,
                     'u_id': None,
                     'v_id': None}

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
                # get all nodes that this route connects

                # find the source nodes for this route
                _u = self.node_filter(self.supply_chain,
                                      'facility_id',_line['source_facility_id'].values[0],
                                      'connects','out')

                # loop thru all edges that connect to the source nodes
                for u_node, v_node, data in self.supply_chain.edges(_u, data=True):
                    # if the destination node facility ID matches the
                    # destination facility ID in the routing dataset row,
                    # apply the distance from the routing dataset to this edge
                    if self.supply_chain.nodes[v_node]['facility_id'] == \
                            _line['destination_facility_id'].values[0]:
                        data['dist'] = _line['total_vmt'].values[0]


    def enumerate_paths(self):
        """
        # @todo update docstring
        Returns
        -------

        """
        # Calculate total pathway costs (sum of all node and edge costs) over all
        # possible pathways

        # @note simple paths have no repeated nodes; this might not work for a cyclic
        #  graph
        # The target parameter can be replaced by a list

        path_edge_list = list([])

        # Get list of nodes and edges by pathway
        for path in map(nx.utils.pairwise,
                        nx.all_simple_paths(self.supply_chain, source='in use',
                                            target='landfill')):
            path_edge_list.append(list(path))

        path_node_list = list(nx.all_simple_paths(self.supply_chain, source='in use', target='landfill'))

        # dictionary defining all possible pathways by nodes and edges
        # nodes = calculate total processing costs
        # edges = calculate total transportation costs and distances
        paths_dict = {'nodes': path_node_list, 'edges': path_edge_list}

        for edges in paths_dict['edges']:
            for u, v in edges:
                print(u, v, self.supply_chain.get_edge_data(u, v))

        for nodes, edges in zip(path_node_list, path_edge_list):
            costs = [self.supply_chain.get_edge_data(u, v)['cost'] for u, v in edges]
            distances = [self.supply_chain.get_edge_data(u, v)['distance'] for u, v in
                         edges]
            graph_path = ",".join(nodes)
            print(
                f"Path: {graph_path}. Total cost={sum(costs)}, total distance={sum(distances)}")

    def update_paths(self):
        pass
        # @todo dynamically update node costs based on cost-over-time and learning-by-
        #  doing models

        # The edges between sub-graphs will have different transportation costs depending
        # on WHAT's being moved: blade segments or ground/shredded blade material.
        # @note Is there a way to also track component-material "status" or general
        #  characteristics as it traverses the graph? Maybe connecting this graph to
        #  the state machine

    def landfill_fee_year(self, timestep):
        """
        UNITS: USD/tonne
        """
        _year = self.timesteps_to_years(timestep)
        _fee = 3.0E-29 * np.exp(0.0344 * _year)
        return _fee


    def blade_removal_year(self, timestep):
        """
        UNITS: USD/blade
        returns the cost of removing ONE blade from a standing wind turbine, prior
        to on-site size reduction or coarse grinding
        :param timestep:
        :return: blade removal cost
        """
        _year = self.timesteps_to_years(timestep)
        _cost = 42.6066109 * _year ** 2 - 170135.7518957 * _year +\
                169851728.663209
        return _cost


    def segment_transpo_cost(self, timestep):
        """
        UNITS: USD/blade-km
        :return:  cost of transporting large blade segments following
         onsite size reduction
        """
        _year = self.timesteps_to_years(timestep)
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
            warnings.warn('Year out of range for segment transport; setting cost = 17.40')
            _cost = 17.40

        return _cost


    def learning_by_doing(self, timestep, mass_tonnes):
        """
        This function so far only gets called if component.kind=='blade'
        returns the total pathway cost for a single blade
        :key
        """

        # rename the cost parameter dictionary for more compact equation writing
        pars = self.cost_params
        lbdc = self.learning_by_doing_costs
        print('Updating pathway costs for timestep ', timestep, '\n')
        # needed for capacity expansion
        # blade_rec_count_ts = self.recycle_to_raw_component_inventory.component_materials['blade']

        # Calculate the pathway cost per tonne of stuff sent through the
        # pathway and that is how we will make our decision.

        # calculate tipping fee
        # UNITS: USD/metric tonne
        landfill_tipping_fee = self.landfill_fee_year(timestep)

        # blade removal cost is the same regardless of pathway
        # UNITS: USD/blade / tonnes/blade [=] USD/tonnes
        blade_removal_cost = self.blade_removal_year(timestep) / mass_tonnes

        # segment transportation cost is also the same regardless of pathway
        # UNITS: USD/blade / tonnes/blade [=] USD/tonnes
        segment_transpo_cost = self.segment_transpo_cost(timestep) / mass_tonnes

        # divide out the loss factors that are applied to the inventory
        # entire blades are processed through raw material recycling, but only 70% is kept in the supply chain
        # similar for coarse grinding
        # cost models should be based on mass *processed*, not mass output
        cumulative_finegrind_mass = self.recycle_to_raw_material_inventory.component_materials['blade'] / pars['fine_grind_yield']
        cumulative_coarsegrind_mass = self.recycle_to_clinker_material_inventory.component_materials['blade'] / pars['coarse_grind_yield']

        # calculate cost reduction factors from learning-by-doing model
        # these factors are unitless
        # add 1.0 to avoid mathematical errors when the cumulative numbers are both zero
        # @note the 1.0 could be replaced with cumulative production at the start of the model,
        # if the EOL technologies have been previously commercialized
        coarse_grind_learning = (cumulative_coarsegrind_mass + cumulative_finegrind_mass + 1.0) ** -pars['recycling_learning_rate']
        fine_grind_learning = (cumulative_finegrind_mass + 1.0) ** -pars['recycling_learning_rate']

        # calculate grinding costs (USD/tonne) accounting for learning
        fine_grind_process = pars['fine_grinding'] * fine_grind_learning
        coarse_grind_process = pars['coarse_grinding_facility'] * coarse_grind_learning

        if pars['coarse_grinding_loc'] == 'onsite':
            # pathway cost in USD/tonne
            recycle_to_rawmat_pathway = np.sum([blade_removal_cost, # blade removal
                                                # coarse grinding onsite
                                                coarse_grind_process,
                                                # lost shred from turbine to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['turbine']['landfill'],
                                                # lost shred (from coarse grinding) landfill tipping fee
                                                (1 - pars['coarse_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # shred transpo from turbine to recycling facility
                                                pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['turbine']['recycling facility'],
                                                # fine grinding
                                                pars['coarse_grind_yield'] *
                                                    fine_grind_process,
                                                # lost shred from recycling facility to landfill
                                                pars['coarse_grind_yield'] *
                                                    (1 - pars['fine_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # lost shred (from fine grinding) landfill tipping fee
                                                pars['coarse_grind_yield'] *
                                                    (1 - pars['fine_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # raw material from recycling facility to next use facility
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['next use facility'],
                                                # revenue from raw material
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['rec_rawmat_revenue']])

            # total transportation in tonnes-km
            recycle_to_rawmat_transpo = mass_tonnes * \
                                        np.sum([ # lost shred from turbine to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['distances']['turbine']['landfill'],
                                                # shred transpo from turbine to recycling facility
                                                pars['coarse_grind_yield'] *
                                                    pars['distances']['turbine']['recycling facility'],
                                                # lost shred from recycling facility to landfill
                                                pars['coarse_grind_yield'] *
                                                    (1 - pars['fine_grind_yield']) *
                                                    pars['distances']['turbine']['recycling facility'],
                                                # (raw mat) shred from recycling facility to next use facility
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['next use facility']])

            # pathway cost in USD/tonne
            recycle_to_clink_pathway = np.sum([ # blade removal
                                                blade_removal_cost,
                                                # coarse grinding onsite
                                                coarse_grind_process,
                                                # lost shred from turbine to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['turbine']['landfill'],
                                                # lost shred landfill tipping fee
                                                (1 - pars['coarse_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # shred transpo from turbine to cement plant
                                                pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['turbine']['cement plant'],
                                                # revenue from sale of clinker replacement
                                                pars['coarse_grind_yield'] *
                                                    pars['rec_clink_revenue'],
                                                # clinker (50% of shred) transpo from cement plant to turbine
                                                0.5 *
                                                    pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['cement plant']['cement plant']])

            # total transportation in tonnes-km
            recycle_to_clink_transpo = mass_tonnes * \
                                        np.sum([ # lost shred from turbine to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['distances']['turbine']['landfill'],
                                                # shred transpo from turbine to cement plant
                                                pars['coarse_grind_yield'] *
                                                    pars['distances']['turbine']['cement plant'],
                                                # clinker (50% of shred) transpo from cement plant to turbine
                                                0.5 *
                                                    pars['coarse_grind_yield'] *
                                                    pars['distances']['cement plant']['turbine']])

            # pathway cost in USD/tonne
            landfill_pathway = np.sum([ # blade removal
                                        blade_removal_cost,
                                        # coarse grinding onsite
                                        coarse_grind_process,
                                        # shred transpo from turbine to landfill
                                        pars['shred_transpo_cost'] *
                                            pars['distances']['turbine']['landfill'],
                                        # landfill tipping fee
                                        landfill_tipping_fee])

            # total transportation in tonnes-km
            landfill_transpo = mass_tonnes * \
                               pars['distances']['turbine']['landfill']

        elif pars['coarse_grinding_loc'] == 'facility':
            # total pathway cost, USD/tonne
            recycle_to_rawmat_pathway = np.sum([# blade removal
                                                blade_removal_cost,
                                                # segmenting
                                                pars['onsite_segmenting_cost'],
                                                # segment transpo from turbine to recycling facility
                                                segment_transpo_cost,
                                                # coarse grinding
                                                coarse_grind_process,
                                                # fine grinding with loss factor
                                                pars['coarse_grind_yield'] *
                                                    fine_grind_process,
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # waste shred tipping fee
                                                (1 - pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # raw mat from recycling facility to next use facility
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['next use facility'],
                                                # revenue from raw mat sales
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['rec_rawmat_revenue']])

            # total pathway transpo, tonne-km
            recycle_to_rawmat_transpo = mass_tonnes *\
                                        np.sum([# segments from turbine to recycling facility
                                                pars['distances']['turbine']['recycling facility'],
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield']) *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # raw mat shred from recycling facility to next use facility
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['distances']['recycling facility']['next use facility']])

            # total pathway cost, USD/tonne
            recycle_to_clink_pathway = np.sum([ # blade removal
                                                blade_removal_cost,
                                                # segmenting
                                                pars['onsite_segmenting_cost'],
                                                # segment transpo from turbine to recycling facility
                                                segment_transpo_cost *
                                                    pars['distances']['turbine']['recycling facility'],
                                                # coarse grinding
                                                coarse_grind_process,
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # waste shred landfill tipping fee
                                                (1 - pars['coarse_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # shred from recycling facility to cement plant
                                                pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['cement plant'],
                                                # revenue from sale of clinker substitute
                                                pars['coarse_grind_yield'] *
                                                    pars['rec_clink_revenue'],
                                                # clinker (50% of shred) from cement plant to turbines
                                                0.5 *
                                                    pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['cement plant']['turbine']])

            # total pathway transpo, tonne-km
            recycle_to_clink_transpo = mass_tonnes *\
                                       np.sum([ # segments from turbine to recycling facility
                                                pars['distances']['turbine']['recycling facility'],
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # shred from recycling facility to cement plant
                                                pars['coarse_grind_yield'] *
                                                    pars['distances']['recycling facility']['cement plant'],
                                                # clinker (50% of shred) from cement plant to turbines
                                                0.5 *
                                                    pars['coarse_grind_yield'] *
                                                    pars['distances']['cement plant']['turbine']])

            # total pathway cost, USD/tonne
            landfill_pathway = np.sum([ # blade removal
                                        blade_removal_cost,
                                        # segmenting
                                        pars['onsite_segmenting_cost'],
                                        # segment transpo from turbine to landfill
                                        segment_transpo_cost * pars['distances']['turbine']['landfill']])

            # total pathway transportation, tonnes-km
            landfill_transpo = mass_tonnes * \
                               pars['distances']['turbine']['landfill']
        else:
            warnings.warn('Assuming coarse grinding happens at facility')
            # total pathway cost, USD/tonne
            recycle_to_rawmat_pathway = np.sum([# blade removal
                                                blade_removal_cost,
                                                # segmenting
                                                pars['onsite_segmenting_cost'],
                                                # segment transpo from turbine to recycling facility
                                                segment_transpo_cost,
                                                # coarse grinding
                                                coarse_grind_process,
                                                # fine grinding with loss factor
                                                pars['coarse_grind_yield'] *
                                                    fine_grind_process,
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # waste shred tipping fee
                                                (1 - pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # raw mat from recycling facility to next use facility
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['next use facility'],
                                                # revenue from raw mat sales
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['rec_rawmat_revenue']])

            # total pathway transpo, tonne-km
            recycle_to_rawmat_transpo = mass_tonnes *\
                                        np.sum([# segments from turbine to recycling facility
                                                pars['distances']['turbine']['recycling facility'],
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield']) *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # raw mat shred from recycling facility to next use facility
                                                pars['coarse_grind_yield'] *
                                                    pars['fine_grind_yield'] *
                                                    pars['distances']['recycling facility']['next use facility']])

            # total pathway cost, USD/tonne
            recycle_to_clink_pathway = np.sum([ # blade removal
                                                blade_removal_cost,
                                                # segmenting
                                                pars['onsite_segmenting_cost'],
                                                # segment transpo from turbine to recycling facility
                                                segment_transpo_cost *
                                                    pars['distances']['turbine']['recycling facility'],
                                                # coarse grinding
                                                coarse_grind_process,
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # waste shred landfill tipping fee
                                                (1 - pars['coarse_grind_yield']) *
                                                    landfill_tipping_fee,
                                                # shred from recycling facility to cement plant
                                                pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['recycling facility']['cement plant'],
                                                # revenue from sale of clinker substitute
                                                pars['coarse_grind_yield'] *
                                                    pars['rec_clink_revenue'],
                                                # clinker (50% of shred) from cement plant to turbines
                                                0.5 *
                                                    pars['coarse_grind_yield'] *
                                                    pars['shred_transpo_cost'] *
                                                    pars['distances']['cement plant']['turbine']])

            # total pathway transpo, tonne-km
            recycle_to_clink_transpo = mass_tonnes *\
                                       np.sum([ # segments from turbine to recycling facility
                                                pars['distances']['turbine']['recycling facility'],
                                                # waste shred from recycling facility to landfill
                                                (1 - pars['coarse_grind_yield']) *
                                                    pars['distances']['recycling facility']['landfill'],
                                                # shred from recycling facility to cement plant
                                                pars['coarse_grind_yield'] *
                                                    pars['distances']['recycling facility']['cement plant'],
                                                # clinker (50% of shred) from cement plant to turbines
                                                0.5 *
                                                    pars['coarse_grind_yield'] *
                                                    pars['distances']['cement plant']['turbine']])

            # total pathway cost, USD/tonne
            landfill_pathway = np.sum([ # blade removal
                                        blade_removal_cost,
                                        # segmenting
                                        pars['onsite_segmenting_cost'],
                                        # segment transpo from turbine to landfill
                                        segment_transpo_cost * pars['distances']['turbine']['landfill'],
                                        # landfill tipping fee
                                        landfill_tipping_fee])

            # total pathway transportation, tonnes-km
            landfill_transpo = mass_tonnes * \
                               pars['distances']['turbine']['landfill']

        # append the three pathway costs to the end of the cost-history dict,
        # but only if at least one of the values has changed
        if len(self.cost_history['year'])==0:

            self.cost_history['year'].append(self.timesteps_to_years(timestep))
            self.cost_history['landfilling cost'].append(landfill_pathway)
            self.cost_history['recycling to clinker cost'].append(recycle_to_clink_pathway)
            self.cost_history['recycling to raw material cost'].append(recycle_to_rawmat_pathway)
            self.cost_history['blade removal cost, per tonne'].append(blade_removal_cost)
            self.cost_history['blade removal cost, per blade'].append(mass_tonnes * blade_removal_cost)
            self.cost_history['blade mass, tonne'].append(mass_tonnes)
            self.cost_history['coarse grinding cost'].append(coarse_grind_process)
            self.cost_history['fine grinding cost'].append(fine_grind_process)
            self.cost_history['segment transpo cost'].append(segment_transpo_cost)
            self.cost_history['landfill tipping fee'].append(landfill_tipping_fee)

        elif (self.cost_history['landfilling cost'][-1] != landfill_pathway) or\
                (self.cost_history['recycling to clinker cost'][-1] != recycle_to_clink_pathway) or\
                (self.cost_history['recycling to raw material cost'][-1] != recycle_to_clink_pathway):

            self.cost_history['year'].append(self.timesteps_to_years(timestep))
            self.cost_history['landfilling cost'].append(landfill_pathway)
            self.cost_history['recycling to clinker cost'].append(recycle_to_clink_pathway)
            self.cost_history['recycling to raw material cost'].append(recycle_to_rawmat_pathway)
            self.cost_history['blade removal cost, per tonne'].append(blade_removal_cost)
            self.cost_history['blade removal cost, per blade'].append(mass_tonnes * blade_removal_cost)
            self.cost_history['blade mass, tonne'].append(mass_tonnes)
            self.cost_history['coarse grinding cost'].append(coarse_grind_process)
            self.cost_history['fine grinding cost'].append(fine_grind_process)
            self.cost_history['segment transpo cost'].append(segment_transpo_cost)
            self.cost_history['landfill tipping fee'].append(landfill_tipping_fee)

        # append the three transportation requirements to the end of the transpo-eol
        # dict
        self.transpo_eol['year'].append(self.timesteps_to_years(timestep))

        # save the transportation value for the lowest-cost pathway
        if min(recycle_to_rawmat_pathway, recycle_to_clink_pathway, landfill_pathway)==recycle_to_rawmat_pathway:
            self.transpo_eol['total eol transportation'].append(recycle_to_rawmat_transpo)
        elif min(recycle_to_rawmat_pathway, recycle_to_clink_pathway, landfill_pathway)==recycle_to_clink_pathway:
            self.transpo_eol['total eol transportation'].append(recycle_to_clink_transpo)
        else:
            self.transpo_eol['total eol transportation'].append(landfill_transpo)

        # Update learning by doing costs
        lbdc["recycle_to_rawmat_pathway"] = recycle_to_rawmat_pathway
        lbdc["recycle_to_clink_pathway"] = recycle_to_clink_pathway
        lbdc["landfilling"] = landfill_pathway

        return recycle_to_rawmat_pathway, recycle_to_clink_pathway, landfill_pathway