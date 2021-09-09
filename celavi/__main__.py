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
import yaml
import pdb
parser = argparse.ArgumentParser(description='Execute CELAVI model')
parser.add_argument('--data', help='Path to the input and output data folder.')
args = parser.parse_args()

# YAML filename
config_yaml_filename = os.path.join(args.data, 'config.yaml')
try:
    with open(config_yaml_filename, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        flags = config.get('flags', {})
        data_filtering = config.get('data_filtering', {})
        scenario_params = config.get('scenario_parameters', {})
        data_dirs = config.get('data_directories', {})
        inputs = config.get('input_filenames', {})
        outputs = config.get('output_filenames', {})
        cg_params = config.get('costgraph_parameters', {})
except IOError as err:
    print(f'Could not open {config_yaml_filename} for configuration. Exiting with status code 1.')
    exit(1)


# if compute_locations is enabled (True), compute locations from raw input files (e.g., LMOP, US Wind Turbine Database)
compute_locations = flags.get('compute_locations', False)  # default to False
# if run_routes is enabled (True), compute routing distances between all input locations
run_routes = flags.get('compute_locations', False)
# if use_computed_routes is enabled, read in a pre-assembled routes file instead
# of generating a new one
use_computed_routes = flags.get('use_computes_routes', True)
# create cost graph fresh or use an imported version
initialize_costgraph = flags.get('initialize_costgraph', False)
# save the newly initialized costgraph as a pickle file
pickle_costgraph = flags.get('pickle_costgraph', True)


# SUB FOLDERS
subfolder_dict = {}
# input data folder for pre-processed route datas
subfolder_dict['preprocessing_output_folder'] = os.path.join(args.data,
                                                             data_dirs.get('preprocessing_output'))
# input data folder for LCI
subfolder_dict['lci_folder'] = os.path.join(args.data,
                                            data_dirs.get('lci'))
# output folder for CELAVI results
subfolder_dict['outputs_folder'] = os.path.join(args.data,
                                                data_dirs.get('outputs'))
# output folder for intermediate routing data
subfolder_dict['routing_output_folder'] = os.path.join(args.data,
                                                       data_dirs.get('routing_output'))

# check if directories exist, if not, create them
for folder in subfolder_dict.values():
    isdir = os.path.isdir(folder)
    if not isdir:
        os.makedirs(folder)

# FILE NAMES FOR INPUT DATA
# TODO: add check to ensure files exist
# general inputs
locations_computed_filename = os.path.join(args.data,
                                           data_dirs.get('inputs'),
                                           inputs.get('locs'))
step_costs_filename = os.path.join(args.data,
                                   data_dirs.get('inputs'),
                                   inputs.get('step_costs'))
fac_edges_filename = os.path.join(args.data,
                                   data_dirs.get('inputs'),
                                   inputs.get('fac_edges'))
transpo_edges_filename = os.path.join(args.data,
                                      data_dirs.get('inputs'),
                                      inputs.get('transpo_edges'))
route_pair_filename = os.path.join(args.data,
                                   data_dirs.get('inputs'),
                                   inputs.get('route_pairs'))
avg_blade_masses_filename = os.path.join(args.data,
                                         data_dirs.get('inputs'),
                                         inputs.get('avg_blade_masses'))
routes_custom_filename = os.path.join(args.data,
                                      data_dirs.get('inputs'),
                                      inputs.get('routes_custom'))
routes_computed_filename = os.path.join(args.data,
                                        data_dirs.get('preprocessing_output'),
                                        inputs.get('routes_computed'))

# input file paths for precomputed US road network data
# transport graph (pre computed; don't change)
transportation_graph_filename = os.path.join(args.data,
                                             data_dirs.get('us_roads'),
                                             inputs.get('transportation_graph'))

# node locations for transport graph (pre computed; don't change)
node_locations_filename = os.path.join(args.data,
                                       data_dirs.get('us_roads'),
                                       inputs.get('node_locs'))

# file paths for raw data used to compute locations
wind_turbine_locations_filename = os.path.join(args.data,
                                               data_dirs.get('raw_locations'),
                                               inputs.get('power_plant_locs'))
# LMOP data for landfill locations
landfill_locations_filename = os.path.join(args.data,
                                           data_dirs.get('raw_locations'),
                                           inputs.get('landfill_locs'))
# other facility locations (e.g., cement)
other_facility_locations_filename = os.path.join(args.data,
                                                 data_dirs.get('raw_locations'),
                                                 inputs.get('other_facility_locs'))

lookup_facility_type_filename = os.path.join(args.data,
                                             data_dirs.get('lookup_tables'),
                                             inputs.get('lookup_facility_type'))

turbine_data_filename = os.path.join(args.data,
                                     data_dirs.get('inputs'),
                                     inputs.get('turbine_data'))


#Data filtering for states
data_filtering_choice = data_filtering.get('enable_data_filtering', False)
if data_filtering_choice:
    states_to_filter = data_filtering_choice.get('states_to_filter', [])
    print('filtering')
    print(states_to_filter)
    data_filter(locations_computed_filename, routes_computed_filename, turbine_data_filename, states_to_filter)




# Pickle and CSV files for initialized CostGraph object
costgraph_pickle_filename = os.path.join(args.data,
                                         data_dirs.get('inputs'),
                                         outputs.get('costgraph_pickle'))
costgraph_csv_filename = os.path.join(args.data,
                                      data_dirs.get('outputs'),
                                      outputs.get('costgraph_csv'))

# Because the LCIA code has filenames hardcoded and cannot be reconfigured,
# change the working directory to the lci_folder to accommodate those read
# and write operations. Also, the Context must be imported down here after
# the working directory is changed because the LCIA will attempt to read
# files immediately.

os.chdir(subfolder_dict['lci_folder'])
from celavi.des import Context


# Note that the step_cost file must be updated (or programmatically generated)
# to include all facility ids. Otherwise, cost graph can't run with the full
# computed data set.
if compute_locations:
    loc = ComputeLocations(wind_turbine_locations=wind_turbine_locations_filename,
                           landfill_locations=landfill_locations_filename,
                           other_facility_locations=other_facility_locations_filename,
                           transportation_graph=transportation_graph_filename,
                           node_locations=node_locations_filename,
                           lookup_facility_type=lookup_facility_type_filename)
    loc.join_facilities(locations_output_file=locations_computed_filename)


if run_routes:
    routes_computed = Router.get_all_routes(locations_file=locations_computed_filename,
                                            route_pair_file=route_pair_filename,
                                            transportation_graph=transportation_graph_filename,
                                            node_locations=node_locations_filename,
                                            routing_output_folder=subfolder_dict['routing_output_folder'],
                                            preprocessing_output_folder=subfolder_dict['preprocessing_output_folder'])

if use_computed_routes:
    routes = routes_computed_filename
else:
    routes = routes_custom_filename

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
        routes_file=routes,
        sc_begin=cg_params.get('sc_begin'),
        sc_end=cg_params.get('sc_end'),
        year=scenario_params.get('start_year'),
        max_dist=scenario_params.get('max_dist'),
        verbose=cg_params.get('cg_verbose'),
        save_copy=cg_params.get('save_cg_csv'),
        save_name=costgraph_csv_filename,
        blade_mass=avgblade.loc[avgblade.year==scenario_params.get('start_year'),
                                'Glass Fiber:Blade'].values[0],
        finegrind_cumul_initial=cg_params.get('finegrind_cumul_initial'),
        coarsegrind_cumul_initial=cg_params.get('coarsegrind_cumul_initial'),
        finegrind_initial_cost=cg_params.get('finegrind_initial_cost'),
        finegrind_revenue=cg_params.get('finegrind_revenue'),
        coarsegrind_initial_cost=cg_params.get('coarsegrind_initial_cost'),
        finegrind_learnrate=cg_params.get('finegrind_learnrate'),
        coarsegrind_learnrate=cg_params.get('coarsegrind_learnrate'),
        finegrind_material_loss=cg_params.get('finegrind_material_loss'),
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
step_costs_data = pd.read_csv(step_costs_filename)
corrected_turbine_data = turbine_data.merge(step_costs_data, on = ['facility_id'], how = 'inner')
turbine_data = corrected_turbine_data[['facility_id','p_name','year','n_turbine']]
turbine_data.to_csv('corrected_turbine_data.csv', index = False)

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
count_facility_inventory_items = list(count_facility_inventories.items())
nrows = 5
ncols = ceil(len(count_facility_inventory_items) / nrows)
fig, axs = plt.subplots(nrows=nrows, ncols=ncols, figsize=(10, 10))
plt.tight_layout()
for i in range(len(count_facility_inventory_items)):
    subplot_col = i // nrows
    subplot_row = i % nrows
    ax = axs[subplot_row][subplot_col]
    facility_name, facility = count_facility_inventory_items[i]
    cum_hist_blade = facility.cumulative_history["blade"]
    ax.set_title(facility_name)
    ax.plot(range(len(cum_hist_blade)), cum_hist_blade)
    ax.set_ylabel("count")
plot_output_path = os.path.join(subfolder_dict['outputs_folder'], 'blade_counts.png')
plt.savefig(plot_output_path)

pickle.dump(count_facility_inventory_items, open('graph_context_count_facility.obj', 'wb'))


