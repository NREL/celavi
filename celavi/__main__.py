import argparse
import os
import sys
import pickle
import time
from math import ceil
import matplotlib.pyplot as plt
from scipy.stats import weibull_min
import numpy as np
import pandas as pd
from celavi.routing import Router
from celavi.costgraph import CostGraph
from celavi.compute_locations import ComputeLocations
from celavi.data_filtering import data_filter

# if compute_locations is enabled (True), compute locations from raw input files (e.g., LMOP, US Wind Turbine Database)
compute_locations = False
# if run_routes is enabled (True), compute routing distances between all input locations
run_routes = False
# if use_computed_routes is enabled, read in a pre-assembled routes file instead
# of generating a new one
use_computed_routes = True
# create cost graph fresh or use an imported version
initialize_costgraph = True
# save the newly initialized costgraph as a pickle file
pickle_costgraph = True


parser = argparse.ArgumentParser(description='Execute CELAVI model')
parser.add_argument('--data', help='Path to the input and output data folder.')
parser.add_argument('-l','--list', nargs='+', help='Enter the states to filter')
args = parser.parse_args()

# SUB FOLDERS
subfolder_dict = {}
# input data folder for pre-processed route datas
subfolder_dict['preprocessing_output_folder'] = os.path.join(args.data, 'preprocessing/')
# input data folder for LCI
subfolder_dict['lci_folder'] = os.path.join(args.data, 'pylca_celavi_data')
# output folder for CELAVI results
subfolder_dict['outputs_folder'] = os.path.join(args.data, 'outputs')
# output folder for intermediate routing data
subfolder_dict['routing_output_folder'] = os.path.join(args.data, 'preprocessing', 'routing_intermediate_files/')

# check if directories exist, if not, create them
for folder in subfolder_dict.values():
    isdir = os.path.isdir(folder)
    if not isdir:
        os.makedirs(folder)

# FILE NAMES FOR INPUT DATA
# TODO: add check to ensure files exist
# general inputs
locations_computed_filename = os.path.join(args.data, 'inputs', 'locations_computed.csv')
step_costs_filename = os.path.join(args.data, 'inputs', 'step_costs.csv')
fac_edges_filename = os.path.join(args.data, 'inputs', 'fac_edges.csv')
transpo_edges_filename = os.path.join(args.data, 'inputs', 'transpo_edges.csv')
route_pair_filename = os.path.join(args.data, 'inputs', 'route_pairs.csv')
avg_blade_masses_filename = os.path.join(args.data, 'inputs', 'avgblademass.csv')
routes_custom_filename = os.path.join(args.data, 'preprocessing', 'routes.csv')
routes_computed_filename = os.path.join(args.data, 'preprocessing', 'routes_computed.csv')

# input file paths for precomputed US road network data
# transport graph (pre computed; don't change)
transportation_graph_filename = os.path.join(args.data, 'inputs',
                                             'precomputed_us_road_network',
                                             'transportation_graph.csv')

# node locations for transport graph (pre computed; don't change)
node_locations_filename = os.path.join(args.data, 'inputs',
                                       'precomputed_us_road_network',
                                       'node_locations.csv')

# file paths for raw data used to compute locations
wind_turbine_locations_filename = os.path.join(args.data, 'inputs',
                                               'raw_location_data',
                                               'uswtdb_v4_1_20210721.csv')
# LMOP data for landfill locations
landfill_locations_filename = os.path.join(args.data, 'inputs',
                                           'raw_location_data',
                                           'landfilllmopdata.csv')
# other facility locations (e.g., cement)
other_facility_locations_filename = os.path.join(args.data, 'inputs',
                                                 'raw_location_data',
                                                 'other_facility_locations_all_us.csv')

lookup_facility_type_filename = os.path.join(args.data, 'lookup_tables',
                                             'facility_type.csv')

turbine_data_filename = os.path.join(args.data, 'inputs', 'number_of_turbines.csv')

standard_scenarios_filename = os.path.join(args.data,
                                           'inputs',
                                           'raw_location_data',
                                           'StScen20A_MidCase_annual_state.csv')

data_filtering_choice = False
if args.list == ['US']:
   print('National Scale Run')
   data_filtering_choice = False
#Data filtering for states

if data_filtering_choice:
    print('Filtered Runs')
    states_to_filter = args.list
    print('filtering')
    print(states_to_filter)
    data_filter(locations_computed_filename, routes_computed_filename, turbine_data_filename, states_to_filter)




# Pickle file containing CostGraph object
costgraph_pickle_filename = os.path.join(args.data, 'inputs', 'netw.obj')
costgraph_csv_filename = os.path.join(args.data, 'inputs', 'netw.csv')

# Because the LCIA code has filenames hardcoded and cannot be reconfigured,
# change the working directory to the lci_folder to accommodate those read
# and write operations. Also, the Context must be imported down here after
# the working directory is changed because the LCIA will attempt to read
# files immediately.

os.chdir(subfolder_dict['lci_folder'])
from celavi.des import Context
from celavi.diagnostic_viz import DiagnosticViz


# Note that the step_cost file must be updated (or programmatically generated)
# to include all facility ids. Otherwise, cost graph can't run with the full
# computed data set.
if compute_locations:
    loc = ComputeLocations(wind_turbine_locations=wind_turbine_locations_filename,
                           landfill_locations=landfill_locations_filename,
                           other_facility_locations=other_facility_locations_filename,
                           transportation_graph=transportation_graph_filename,
                           node_locations=node_locations_filename,
                           lookup_facility_type=lookup_facility_type_filename,
                           turbine_data_filename=turbine_data_filename,
                           standard_scenarios_filename=standard_scenarios_filename)
    loc.join_facilities(locations_output_file=locations_computed_filename)


if run_routes:
    routes_computed = Router.get_all_routes(locations_file=locations_computed_filename,
                                            route_pair_file=route_pair_filename,
                                            transportation_graph=transportation_graph_filename,
                                            node_locations=node_locations_filename,
                                            routing_output_folder=subfolder_dict['routing_output_folder'],
                                            preprocessing_output_folder=subfolder_dict['preprocessing_output_folder'])

if use_computed_routes:
    args.routes = routes_computed_filename
else:
    args.routes = routes_custom_filename

avgblade = pd.read_csv(avg_blade_masses_filename)

time0 = time.time()

if initialize_costgraph:
    # Initialize the CostGraph using these parameter settings
    print('Cost Graph Starts at %d s' % np.round(time.time() - time0, 1),
          flush=True)
    netw = CostGraph(
        step_costs_file=step_costs_filename,
        fac_edges_file=fac_edges_filename,
        transpo_edges_file=transpo_edges_filename,
        locations_file=locations_computed_filename,
        routes_file=args.routes,
        sc_begin= 'manufacturing',
        sc_end=['landfilling', 'cement co-processing', 'blade next use'],
        year=2000.0,
        max_dist=300.0,
        verbose=1,
        save_copy=True,
        save_name=costgraph_csv_filename,
        blade_mass=avgblade.loc[avgblade.year==2000,
                                'Glass Fiber:Blade'].values[0],
        finegrind_cumul_initial=1.0,
        coarsegrind_cumul_initial=1.0,
        finegrind_initial_cost=165.38,
        finegrind_revenue=242.56,
        coarsegrind_initial_cost=121.28,
        finegrind_learnrate=-0.05,
        coarsegrind_learnrate=-0.05,
        finegrind_material_loss=0.3,
    )
    print('CostGraph initialized at %d s' % np.round(time.time() - time0, 1),
          flush=True)

    if pickle_costgraph:
        # Save the CostGraph object using pickle
        pickle.dump(netw, open(costgraph_pickle_filename, 'wb'))
        print('Cost graph pickled and saved',flush = True)

else:
    # Read in a previously generated CostGraph object
    print('Reading in CostGraph object at %d s' % np.round(time.time() - time0, 1),
          flush=True)

    netw = pickle.load(open(costgraph_pickle_filename, 'rb'))

    print('CostGraph object read in at %d s' % np.round(time.time() - time0, 1),
          flush=True)

print('CostGraph exists\n\n\n')

# Get the initial supply chain pathways to connect power plants to their
# nearest-neighbor manufacturing facilities
initial_paths = netw.choose_paths()

# Create the DES context and tie it to the CostGraph
context = Context(
    locations_filename=locations_computed_filename,
    step_costs_filename=step_costs_filename,
    possible_items=["nacelle", "blade", "tower", "foundation"],
    cost_graph=netw,
    cost_graph_update_interval_timesteps=12,
    avg_blade_masses_filename=avg_blade_masses_filename
)

# Create the turbine dataframe that will be used to populate
# the context with components. Repeat the creation of blades
# 3 times for each turbine.

print('Reading turbine file at %d s\n\n\n' % np.round(time.time() - time0, 1),
      flush=True)

turbine_data = pd.read_csv(turbine_data_filename)

components = []
for _, row in turbine_data.iterrows():
    year = row['year']
    facility_id = netw.find_upstream_neighbor(int(row['facility_id']))
    n_turbine = int(row['n_turbine'])

    for _ in range(n_turbine):
        for _ in range(3):
            components.append({
                'year': year,
                'kind': 'blade',
                'facility_id': facility_id
            })


print('Turbine file read at %d s\n\n\n' % np.round(time.time() - time0, 1),
      flush=True)

components = pd.DataFrame(components)

# Create the lifespan functions for the components.
np.random.seed(13)
timesteps_per_year = 12
min_lifespan = 120
L = 240
K = 2.2
lifespan_fns = {
    "nacelle": lambda: 30 * timesteps_per_year,
    "blade": lambda: 20 * timesteps_per_year,
    # "blade": lambda: weibull_min.rvs(K, loc=min_lifespan, scale=L-min_lifespan, size=1)[0],
    "foundation": lambda: 50 * timesteps_per_year,
    "tower": lambda: 50 * timesteps_per_year,
}

print('Components created at %d s\n\n\n' % np.round(time.time() - time0),
      flush=True)

# Populate the context with components.
context.populate(components, lifespan_fns)

print('Context created  at %d s\n\n\n' % np.round(time.time() - time0),
      flush=True)

print('Run starting for DES at %d s\n\n\n' % np.round(time.time() - time0),
      flush=True)

# Run the context
count_facility_inventories = context.run()

print('FINISHED RUN at %d s' % np.round(time.time() - time0),
      flush=True)

# Plot the cumulative count levels of the inventories
diagnostic_viz = DiagnosticViz(context, subfolder_dict['outputs_folder'])
diagnostic_viz.generate_blade_count_plots()
