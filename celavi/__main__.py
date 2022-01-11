"""
Circular Economy Lifecycle Analysis and VIsualization, CELAVI

This file performs data I/O, preprocessing, and calls modules to perform a
complete CELAVI model run and save results.

Authors: Rebecca Hanes, Alicia Key, Tapajyoti (TJ) Ghosh, Annika Eberle
"""

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
from celavi.pylca_celavi.des_interface import PylcaCelavi
from celavi.des import Context
from celavi.diagnostic_viz import DiagnosticViz
import yaml

parser = argparse.ArgumentParser(description='Execute CELAVI model')
parser.add_argument('--data', help='Path to the input and output data folder.')
parser.add_argument('--casestudy', help='Name of case study config file in data folder.')
parser.add_argument('--scenario', help='Name of scenario-specific config file in the data folder.')
args = parser.parse_args()

time0 = time.time()

# YAML filenames
case_yaml_filename = os.path.join(args.data, args.casestudy)
scen_yaml_filename = os.path.join(args.data, args.scenario)
try:
    with open(case_yaml_filename, 'r') as f:
        case = yaml.load(f, Loader=yaml.FullLoader)
        model_run = case.get('model_run', {})
        data_dirs = case.get('data_directories', {})
        inputs = case.get('input_files', {})
        generated = case.get('generated_files', {})
        outputs = case.get('output_files', {})
except IOError as err:
    print(f'Could not open {case_yaml_filename} for configuration. Exiting with status code 1.')
    exit(1)
try:
    with open(scen_yaml_filename, 'r') as f:
        scen = yaml.load(f, Loader=yaml.FullLoader)
        flags = scen.get('flags', {})
        scenario = scen.get('scenario', {})
        pathways = scen.get('circular_pathways', {})
        tech = scen.get('technology_components', {})
except IOError as err:
    print(f'Could not open {scen_yaml_filename} for configuration. Exiting with status code 1.')
    exit(1)

## Flags
# if compute_locations is enabled (True), compute locations from raw input
# files (e.g., LMOP, US Wind Turbine Database)
compute_locations = flags.get('compute_locations', False)  # default to False
# if run_routes is enabled (True), compute routing distances between all
# input location pairs
run_routes = flags.get('run_routes', False)
# if use_computed_routes is enabled, read in a pre-assembled routes file
# instead of generating a new one
use_computed_routes = flags.get('use_computed_routes', True)
# create cost graph fresh or use an imported version
initialize_costgraph = flags.get('initialize_costgraph', False)
# filter down locations dataset by state
location_filtering = flags.get('location_filtering', False)
# filter down routes by maximum allowable distance between facility types
distance_filtering = flags.get('distance_filtering', False)
# save the newly initialized costgraph as a pickle file
pickle_costgraph = flags.get('pickle_costgraph', True)
# automatically generate step_costs dataset, if costs do not vary by region
generate_step_costs = flags.get('generate_step_costs', True)
# use fixed (or random Weibull) lifetimes for technology components
use_fixed_lifetime = flags.get('use_fixed_lifetime', True)
# use previously generated LCIA results instead of re-calculating
use_lcia_shortcut = flags.get('use_lcia_shortcut', False)


## SUB FOLDERS
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

## FILE NAMES FOR INPUT DATA

# general inputs
locations_computed_filename = os.path.join(args.data,
                                           data_dirs.get('inputs'),
                                           generated.get('locs'))
fac_edges_filename = os.path.join(args.data,
                                  data_dirs.get('inputs'),
                                  inputs.get('fac_edges'))
transpo_edges_filename = os.path.join(args.data,
                                      data_dirs.get('inputs'),
                                      inputs.get('transpo_edges'))
route_pair_filename = os.path.join(args.data,
                                   data_dirs.get('inputs'),
                                   inputs.get('route_pairs'))
component_material_masses_filename = os.path.join(args.data,
                                         data_dirs.get('inputs'),
                                         inputs.get('component_material_mass'))
routes_custom_filename = os.path.join(args.data,
                                      data_dirs.get('inputs'),
                                      inputs.get('routes_custom'))
routes_computed_filename = os.path.join(args.data,
                                        data_dirs.get('preprocessing_output'),
                                        generated.get('routes_computed'))

# input file paths for precomputed US road network data
# transport graph (pre computed; don't change)
transportation_graph_filename = os.path.join(args.data,
                                             data_dirs.get('us_roads'),
                                             inputs.get('transportation_graph')
                                             )

# node locations for transport graph (pre computed; don't change)
node_locations_filename = os.path.join(args.data,
                                       data_dirs.get('us_roads'),
                                       inputs.get('node_locs'))

# file paths for raw data used to compute locations
power_plant_locations_filename = os.path.join(args.data,
                                               data_dirs.get('raw_locations'),
                                               inputs.get('power_plant_locs'))
# LMOP data for landfill locations
landfill_locations_filename = os.path.join(args.data,
                                           data_dirs.get('raw_locations'),
                                           inputs.get('landfill_locs'))
# other facility locations (e.g., cement)
other_facility_locations_filename = os.path.join(args.data,
                                                 data_dirs.get(
                                                     'raw_locations'),
                                                 inputs.get(
                                                     'other_facility_locs'))

lookup_facility_type_filename = os.path.join(args.data,
                                             data_dirs.get('lookup_tables'),
                                             inputs.get('lookup_facility_type')
                                             )

# file where the technology data will be saved after generating from raw inputs
technology_data_filename = os.path.join(args.data,
                                     data_dirs.get('inputs'),
                                     generated.get('technology_data'))

# dataset of capacity expansion projections
capacity_proj_filename = os.path.join(args.data,
                                      data_dirs.get('raw_locations'),
                                      scenario.get('capacity_proj_file'))

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

# LCI input filenames
lcia_des_filename = os.path.join(args.data,
                                 data_dirs.get('lci'),
                                 generated.get('lcia_to_des'))

lca_results_filename = os.path.join(args.data,
                                    data_dirs.get('outputs'),
                                    outputs.get('lca_results_filename'))

shortcutlca_filename = os.path.join(args.data,
                                    data_dirs.get('lci'),
                                    generated.get('shortcutlca_filename'))

intermediate_demand_filename = os.path.join(args.data,
                                            data_dirs.get('lci'),
                                            generated.get('intermediate_demand'))

static_lci_filename = os.path.join(args.data,
                                   data_dirs.get('lci'),
                                   inputs.get('static_lci_filename'))

uslci_filename = os.path.join(args.data,
                              data_dirs.get('lci'),
                              inputs.get('uslci_filename'))

lci_locations_filename = os.path.join(args.data,
                                      data_dirs.get('lci'),
                                      inputs.get('lci_activity_locations'))

stock_filename = os.path.join(args.data,
                              data_dirs.get('lci'),
                              inputs.get('stock_filename'))

emissions_lci_filename = os.path.join(args.data,
                                      data_dirs.get('lci'),
                                      inputs.get('emissions_lci_filename'))

traci_lci_filename = os.path.join(args.data,
                                  data_dirs.get('lci'),
                                  inputs.get('traci_lci_filename'))


state_electricity_lci_filename = os.path.join(args.data,
                                    data_dirs.get('lci'),
                                    inputs.get('state_electricity_lci_filename'))

national_electricity_lci_filename = os.path.join(args.data,
                                    data_dirs.get('lci'),
                                    inputs.get('natl_electricity_lci_filename'))

# FILENAMES FOR OUTPUT DATA
pathway_crit_history_filename = os.path.join(
    args.data,
    data_dirs.get('outputs'),
    outputs.get('pathway_criterion_history')
)

# Raw DES output filenames
component_counts_plot_filename = os.path.join(
    args.data,
    data_dirs.get('outputs'),
    outputs.get('component_counts_plot')
)
material_mass_plot_filename = os.path.join(
    args.data,
    data_dirs.get('outputs'),
    outputs.get('material_mass_plot')
)
count_cumulative_histories_filename = os.path.join(
    args.data,
    data_dirs.get('outputs'),
    outputs.get('count_cumulative_histories')
)
mass_cumulative_histories_filename = os.path.join(
    args.data,
    data_dirs.get('outputs'),
    outputs.get('mass_cumulative_histories')
)

## Read in datasets that are passed around as DataFrames or similar
component_material_mass = pd.read_csv(component_material_masses_filename)
technology_data = pd.read_csv(technology_data_filename)

## Define general model and scenario parameters
if use_computed_routes:
    routes = routes_computed_filename
else:
    routes = routes_custom_filename

states_to_filter = scenario.get('states_included', [])

component_total_mass = component_material_mass.groupby(
    by=['year','technology','component']
).sum(
    'mass_tonnes'
).reset_index()

circular_components = tech.get('circular_components')

start_year = model_run.get('start_year')

timesteps_per_year = model_run.get('timesteps_per_year')

# calculate des timesteps such that the model runs through the end of the
# end year rather than stopping at the beginning of the end year
des_timesteps = int(
    timesteps_per_year * (model_run.get('end_year') - start_year) + timesteps_per_year
)

# Get list of unique materials involved in the case study
materials = [tech.get('component_materials')[c] for c in circular_components]
material_list=[item for sublist in materials for item in sublist]

substitution_rate = tech.get('substitution_rates')

np.random.seed(scenario.get('seed', 13))

# Note that the step_cost file must be updated (or programmatically generated)
# to include all facility ids. Otherwise, cost graph can't run with the full
# computed data set.
if compute_locations:
    loc = ComputeLocations(
        start_year=model_run.get('start_year'),
        power_plant_locations=power_plant_locations_filename,
        landfill_locations=landfill_locations_filename,
        other_facility_locations=other_facility_locations_filename,
        transportation_graph=transportation_graph_filename,
        node_locations=node_locations_filename,
        lookup_facility_type=lookup_facility_type_filename,
        technology_data_filename=technology_data_filename,
        standard_scenarios_filename=capacity_proj_filename)
    loc.join_facilities(locations_output_file=locations_computed_filename)

# if the step_costs file is being generated, then all facilities of the same
# type will have the same cost models.
if generate_step_costs:
    step_costs_filename = os.path.join(args.data,
                                       data_dirs.get('inputs'),
                                       generated.get('step_costs'))
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
else:
    # If step_costs is not generated programatically, then the user must
    # supply a custom file.
    step_costs_filename = os.path.join(args.data,
                                       data_dirs.get('inputs'),
                                       inputs.get('step_costs'))


# Data filtering for states
states_to_filter = scen.get('states_to_filter', [])
if location_filtering:
    if not states_to_filter:
        print('Cannot filter data; no state list provided', flush=True)
    else:
        print(f'Filtering locations: {states_to_filter}',
              flush=True)
        filter_locations(locations_computed_filename,
                         technology_data_filename,
                         states_to_filter)
    # if the data is being filtered and a new routes file is NOT being
    # generated, then the existing routes file must also be filtered
    if not run_routes:
        print(f'Filtering routes: {states_to_filter}',
              flush=True)
        filter_routes(locations_computed_filename,
                      routes)

if run_routes:
    routes_computed = Router.get_all_routes(
        locations_file=locations_computed_filename,
        route_pair_file=route_pair_filename,
        distance_filtering=distance_filtering,
        transportation_graph=transportation_graph_filename,
        node_locations=node_locations_filename,
        routes_output_file = routes_computed_filename,
        routing_output_folder=subfolder_dict['routing_output_folder'])

print('Run routes completed in %d s' % np.round(time.time() - time0, 1),
      flush=True)

if initialize_costgraph:
    # Initialize the CostGraph using these parameter settings
    print('CostGraph starts at %d s' % np.round(time.time() - time0, 1),
          flush=True)
    netw = CostGraph(
        step_costs_file=step_costs_filename,
        fac_edges_file=fac_edges_filename,
        transpo_edges_file=transpo_edges_filename,
        locations_file=locations_computed_filename,
        routes_file=routes,
        sc_begin=pathways.get('sc_begin'),
        sc_end=pathways.get('sc_end'),
        year=model_run.get('start_year'),
        verbose=model_run.get('cg_verbose'),
        save_copy=model_run.get('save_cg_csv'),
        save_name=costgraph_csv_filename,
        pathway_crit_history_filename = pathway_crit_history_filename,
        circular_components = circular_components,
        component_initial_mass=component_total_mass.loc[
            component_total_mass.year == model_run.get('start_year'),
            'mass_tonnes'
        ].values[0],
        path_dict=pathways
    )
    print('CostGraph completed at %d s' % np.round(time.time() - time0, 1),
          flush=True)

    if pickle_costgraph:
        # Save the CostGraph object using pickle
        pickle.dump(netw, open(costgraph_pickle_filename, 'wb'))
        print('Cost graph pickled and saved', flush=True)

else:
    # Read in a previously generated CostGraph object
    print(f'Reading in CostGraph object at {np.round(time.time() - time0, 1)}',
          flush=True)

    netw = pickle.load(open(costgraph_pickle_filename, 'rb'))

    print(f'CostGraph object read in at {np.round(time.time() - time0, 1)}',
          flush=True)


# Electricity spatial mix level. Defaults to 'state' when not provided.
electricity_grid_spatial_level = scenario.get('electricity_grid_level', 'state')

if electricity_grid_spatial_level == 'state':
    dynamic_lci_filename = state_electricity_lci_filename
else:
    dynamic_lci_filename = national_electricity_lci_filename
# Prepare LCIA code
lca = PylcaCelavi(lca_results_filename=lca_results_filename,
                  lcia_des_filename=lcia_des_filename,
                  shortcutlca_filename=shortcutlca_filename,
                  intermediate_demand_filename=intermediate_demand_filename,
                  dynamic_lci_filename=dynamic_lci_filename,
                  electricity_grid_spatial_level = electricity_grid_spatial_level,
                  static_lci_filename=static_lci_filename,
                  uslci_filename=uslci_filename,
                  lci_activity_locations=lci_locations_filename,
                  stock_filename=stock_filename,
                  emissions_lci_filename=emissions_lci_filename,
                  traci_lci_filename=traci_lci_filename,
                  use_shortcut_lca_calculations=use_lcia_shortcut,
                  substitution_rate=substitution_rate)

# Get the start year and timesteps_per_year
start_year = model_run.get('start_year')
timesteps_per_year = model_run.get('timesteps_per_year')

# calculate des timesteps such that the model runs through the end of the
# end year rather than stopping at the beginning of the end year
des_timesteps = int(
    timesteps_per_year * (model_run.get('end_year') - start_year) + timesteps_per_year
)

# Get list of unique materials involved in the case study
materials = [tech.get('component_materials')[c] for c in circular_components]
material_list=[item for sublist in materials for item in sublist]

# Create the DES context and tie it to the CostGraph
context = Context(
    locations_filename=locations_computed_filename,
    step_costs_filename=step_costs_filename,
    component_material_masses_filename=component_material_masses_filename,
    possible_components=list(tech.get('component_list', []).keys()),
    possible_materials=material_list,
    cost_graph=netw,
    cost_graph_update_interval_timesteps=model_run.get('cg_update'),
    lca=lca,
    path_dict=pathways,
    min_year=start_year,
    max_timesteps=des_timesteps,
    timesteps_per_year=timesteps_per_year
)

print(f'Context initialized at {np.round(time.time() - time0, 1)} s', flush=True)

# Create the technology dataframe that will be used to populate
# the context with components.
components = []
for _, row in technology_data.iterrows():
    year = row['year']
    in_use_facility_id = int(row['facility_id'])
    manuf_facility_id = netw.find_upstream_neighbor(int(row['facility_id']))
    n_technology = int(row['n_technology'])

    for _ in range(n_technology):
        for c in circular_components:
            components.append({
                'year': year,
                'kind': c,
                'manuf_facility_id': manuf_facility_id,
                'in_use_facility_id': in_use_facility_id
            })

components = pd.DataFrame(components)

# Create the lifespan functions for the components.
lifespan_fns = {}

# By default, all components are assigned fixed lifetimes
for component in tech.get('component_list').keys():
    lifespan_fns[component] = \
        lambda steps = tech.get('component_fixed_lifetimes')[component],\
               convert=timesteps_per_year: steps * convert

# If fixed lifetimes are not being used, then apply the Weibull parameters
# to the circular component(s) only. All non-circular components keep their
# fixed lifetimes.
if not use_fixed_lifetime:
    for c in circular_components:
        lifespan_fns[c] = lambda : weibull_min.rvs(
            tech.get('component_weibull_params')[c]['K'],
            loc=tech.get('min_lifespan'),
            scale=tech.get('component_weibull_params')[c]['L'] -
                  tech.get('min_lifespan'),
            size=1
        )[0]

print(f'Components initialized at {np.round(time.time() - time0, 1)} s',flush=True)

# Populate the context with components.
context.populate(components, lifespan_fns)

print(f'Context populated with components at {np.round(time.time() - time0, 1)} s',
      flush=True)

print(f'Model run starting at {np.round(time.time() - time0, 1)} s',flush=True)

# Run the context
count_facility_inventories = context.run()

print(f'Creating diagnostic visualizations at '
      f'{np.round(time.time() - time0, 1)} s', flush=True)

# Plot the cumulative count levels of the count inventories
possible_component_list = list(tech.get('component_list', []).keys())
diagnostic_viz_counts = DiagnosticViz(
    facility_inventories=context.count_facility_inventories,
    output_plot_filename=component_counts_plot_filename,
    keep_cols=possible_component_list,
    start_year=start_year,
    timesteps_per_year=timesteps_per_year,
    component_count=tech.get('component_list'),
    var_name='unit',
    value_name='count'
)
count_cumulative_histories = \
    diagnostic_viz_counts.gather_and_melt_cumulative_histories()
count_cumulative_histories.to_csv(count_cumulative_histories_filename,
                                  index=False)
diagnostic_viz_counts.generate_plots()

# Plot the levels of the mass inventories
diagnostic_viz_mass = DiagnosticViz(
    facility_inventories=context.mass_facility_inventories,
    output_plot_filename=material_mass_plot_filename,
    keep_cols=possible_component_list,
    start_year=start_year,
    timesteps_per_year=timesteps_per_year,
    component_count=tech.get('component_list'),
    var_name='material',
    value_name='tonnes'
)
mass_cumulative_histories = \
    diagnostic_viz_mass.gather_and_melt_cumulative_histories()
mass_cumulative_histories.to_csv(mass_cumulative_histories_filename,
                                 index=False)
diagnostic_viz_mass.generate_plots()

# Postprocess and save CostGraph outputs
netw.save_costgraph_outputs()

# Join LCIA and locations computed and write the result to enable creation of
# maps
lcia_names = ['year', 'facility_id', 'material', 'stage', 'impact',
              'impact_value']
lcia_df = pd.read_csv(lcia_des_filename, names=lcia_names)
locations_df = pd.read_csv(locations_computed_filename)

locations_columns = [
    'facility_id',
    'facility_type',
    'lat',
    'long',
    'region_id_1',
    'region_id_2',
    'region_id_3',
    'region_id_4'
]

locations_select_df = locations_df.loc[:, locations_columns]
lcia_locations_df = lcia_df.merge(locations_select_df, how='inner',
                                  on='facility_id')

lcia_locations_df.to_csv(lca_results_filename, index=False)

# Print run finish message
print(f'FINISHED RUN at {np.round(time.time() - time0)} s',
      flush=True)
