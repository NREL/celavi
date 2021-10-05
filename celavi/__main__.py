import argparse
import os
import pickle
import time
from scipy.stats import weibull_min
import numpy as np
import pandas as pd
from celavi.routing import Router
from celavi.costgraph import CostGraph
from celavi.compute_locations import ComputeLocations
from celavi.data_filtering import filter_locations, filter_routes
import yaml

parser = argparse.ArgumentParser(description='Execute CELAVI model')
parser.add_argument('--data', help='Path to the input and output data folder.')
parser.add_argument('--config', help='Name of config file in data folder.')
args = parser.parse_args()

# YAML filename
config_yaml_filename = os.path.join(args.data, args.config)
try:
    with open(config_yaml_filename, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
        flags = config.get('flags', {})
        scenario_params = config.get('scenario_parameters', {})
        data_dirs = config.get('data_directories', {})
        inputs = config.get('input_filenames', {})
        outputs = config.get('output_filenames', {})
        cg_params = config.get('costgraph_parameters', {})
        des_params = config.get('discrete_event_parameters', {})
except IOError as err:
    print(f'Could not open {config_yaml_filename} for configuration. Exiting with status code 1.')
    exit(1)


# if compute_locations is enabled (True), compute locations from raw input
# files (e.g., LMOP, US Wind Turbine Database)
compute_locations = flags.get('compute_locations', False)  # default to False
# if run_routes is enabled (True), compute routing distances between all
# input locations
run_routes = flags.get('run_routes', False)
# if use_computed_routes is enabled, read in a pre-assembled routes file
# instead of generating a new one
use_computed_routes = flags.get('use_computed_routes', True)
# create cost graph fresh or use an imported version
initialize_costgraph = flags.get('initialize_costgraph', False)
enable_data_filtering = flags.get('enable_data_filtering', False)
# save the newly initialized costgraph as a pickle file
pickle_costgraph = flags.get('pickle_costgraph', True)
generate_step_costs = flags.get('generate_step_costs', True)
use_fixed_lifetime = flags.get('use_fixed_lifetime', True)


# SUB FOLDERS
subfolder_dict = {
    'preprocessing_output_folder':
        os.path.join(args.data,
                     data_dirs.get('preprocessing_output')),
    'lci_folder':
        os.path.join(args.data,
                     data_dirs.get('lci')),
    'outputs_folder':
        os.path.join(args.data,
                     data_dirs.get('outputs')),
    'routing_output_folder':
        os.path.join(args.data,
                     data_dirs.get('routing_output'))
}

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

# file where the turbine data will be saved after generating from raw inputs
turbine_data_filename = os.path.join(args.data,
                                     data_dirs.get('inputs'),
                                     inputs.get('turbine_data'))

standard_scenarios_filename = os.path.join(args.data,
                                           data_dirs.get('raw_locations'),
                                           inputs.get('standard_scenario'))

step_costs_default_filename = os.path.join(args.data,
                                           data_dirs.get('lookup_tables'),
                                           inputs.get('lookup_step_costs'))

# Get pickle and CSV filenames for initialized CostGraph object
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
from celavi.diagnostic_viz import DiagnosticVizAndDataFrame


# Note that the step_cost file must be updated (or programmatically generated)
# to include all facility ids. Otherwise, cost graph can't run with the full
# computed data set.
if compute_locations:
    loc = ComputeLocations(
        wind_turbine_locations=wind_turbine_locations_filename,
        landfill_locations=landfill_locations_filename,
        other_facility_locations=other_facility_locations_filename,
        transportation_graph=transportation_graph_filename,
        node_locations=node_locations_filename,
        lookup_facility_type=lookup_facility_type_filename,
        turbine_data_filename=turbine_data_filename,
        standard_scenarios_filename=standard_scenarios_filename)

    loc.join_facilities(locations_output_file=locations_computed_filename)

# if the step_costs file is being generated, then all facilities of the same
# type will have the same cost models.
if generate_step_costs:
    pd.read_csv(
        step_costs_default_filename
    ).merge(
        pd.read_csv(locations_computed_filename)[
            ['facility_id', 'facility_type']
        ],
        on='facility_type',
        how='outer'
    ).to_csv(
        step_costs_filename,
        index=False
    )

if use_computed_routes:
    routes = routes_computed_filename
else:
    routes = routes_custom_filename

time0 = time.time()

# Data filtering for states
states_to_filter = scenario_params.get('states_to_filter', [])
if enable_data_filtering:
    if len(states_to_filter) == 0:
        print('Cannot filter data; no state list provided', flush=True)
    else:
        print(f'Filtering locations: {states_to_filter}',
              flush=True)
        filter_locations(locations_computed_filename,
                         turbine_data_filename,
                         states_to_filter)
    # if the data is being filtered and a new routes file is NOT being
    # generated, then the existing routes file must also be filtered
    if not run_routes:
        print(f'Filtering routes: {states_to_filter}',
              flush=True)
        filter_routes(locations_computed_filename,
                      routes)

print('State filtering completed in %d s' % np.round(time.time() - time0, 1),
        flush=True)

time0 = time.time()

if run_routes:
    routes_computed = Router.get_all_routes(
        locations_file=locations_computed_filename,
        route_pair_file=route_pair_filename,
        transportation_graph=transportation_graph_filename,
        node_locations=node_locations_filename,
        routing_output_folder=subfolder_dict['routing_output_folder'],
        preprocessing_output_folder=subfolder_dict['preprocessing_output_folder'])

avgblade = pd.read_csv(avg_blade_masses_filename)

print('Run routes completed in %d s' % np.round(time.time() - time0, 1),
        flush=True)


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
    print('CostGraph completed at %d s' % np.round(time.time() - time0, 1),
          flush=True)

    if pickle_costgraph:
        # Save the CostGraph object using pickle
        pickle.dump(netw, open(costgraph_pickle_filename, 'wb'))
        print('Cost graph pickled and saved',flush = True)

else:
    # Read in a previously generated CostGraph object
    print(f'Reading in CostGraph object at {np.round(time.time() - time0, 1)}',
          flush=True)

    netw = pickle.load(open(costgraph_pickle_filename, 'rb'))

    print(f'CostGraph object read in at {np.round(time.time() - time0, 1)}',
          flush=True)

print('CostGraph exists\n\n\n')

# calculate des timesteps such that the model runs through the end of the
# end year rather than stopping at the beginning of the end year
des_timesteps = int(scenario_params.get('timesteps_per_year') * (
        scenario_params.get('end_year') - scenario_params.get('start_year')
) + scenario_params.get('timesteps_per_year'))

# Create the DES context and tie it to the CostGraph
context = Context(
    locations_filename=locations_computed_filename,
    step_costs_filename=step_costs_filename,
    avg_blade_masses_filename=avg_blade_masses_filename,
    possible_items=des_params.get('component_list'),
    cost_graph=netw,
    cost_graph_update_interval_timesteps=cg_params.get('cg_update_timesteps'),
    min_year = scenario_params.get('start_year'),
    max_timesteps = des_timesteps,
    timesteps_per_year = scenario_params.get('timesteps_per_year')
)

# Create the turbine dataframe that will be used to populate
# the context with components. Repeat the creation of blades
# 3 times for each turbine.

print(f'Creating components at {np.round(time.time() - time0, 1)} s',
      flush=True)

turbine_data = pd.read_csv(turbine_data_filename)

components = []
for _, row in turbine_data.iterrows():
    year = row['year']
    in_use_facility_id = int(row['facility_id'])
    manuf_facility_id = netw.find_upstream_neighbor(int(row['facility_id']))
    n_turbine = int(row['n_turbine'])

    for _ in range(n_turbine):
        for _ in range(3):
            components.append({
                'year': year,
                'kind': 'blade',
                'manuf_facility_id': manuf_facility_id,
                'in_use_facility_id': in_use_facility_id
            })

print(f'Components created at {np.round(time.time() - time0, 1)} s',
      flush=True)

components = pd.DataFrame(components)

# Create the lifespan functions for the components.
np.random.seed(des_params.get('seed', 13))
timesteps_per_year = scenario_params.get('timesteps_per_year')
lifespan_fns = {
    "nacelle": lambda: des_params.get(
        'component_fixed_lifetimes'
    )['nacelle'] * timesteps_per_year,
    "foundation": lambda: des_params.get(
        'component_fixed_lifetimes'
    )['foundation'] * timesteps_per_year,
    "tower": lambda: des_params.get(
        'component_fixed_lifetimes'
    )['tower'] * timesteps_per_year,
}

if use_fixed_lifetime:
    lifespan_fns['blade'] = lambda: des_params.get(
        'component_fixed_lifetimes'
    )['blade'] * timesteps_per_year
else:
    lifespan_fns['blade'] = lambda: weibull_min.rvs(
        des_params.get('blade_weibull_K'),
        loc=des_params.get('min_lifespan'),
        scale=des_params.get('blade_weibull_L') - des_params.get('min_lifespan'),
        size=1
    )[0]

print('Components created at %d s\n\n\n' % np.round(time.time() - time0),
      flush=True)

# Populate the context with components.
context.populate(components, lifespan_fns)

print(f'Context created  at {np.round(time.time() - time0)} s\n\n\n',
      flush=True)

print(f'Run starting for DES at {np.round(time.time() - time0)} s\n\n\n',
      flush=True)

# Run the context
count_facility_inventories = context.run()

print(f'FINISHED RUN at {np.round(time.time() - time0)} s',
      flush=True)

# Plot the cumulative count levels of the inventories
diagnostic_viz = DiagnosticVizAndDataFrame(context, subfolder_dict['outputs_folder'])
diagnostic_viz.generate_blade_count_plots()
cumulative_histories = diagnostic_viz.gather_cumulative_histories()
cumulative_histories_filename = os.path.join(subfolder_dict['outputs_folder'], 'blade_counts.csv')
cumulative_histories.to_csv(cumulative_histories_filename, index_label='id')
