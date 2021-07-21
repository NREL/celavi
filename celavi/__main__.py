import argparse
import os
from math import ceil
import matplotlib.pyplot as plt
from scipy.stats import weibull_min
import numpy as np
import pandas as pd
from routing import Router
from costgraph import CostGraph
from compute_locations import ComputeLocations
import time

parser = argparse.ArgumentParser(description='Execute CELAVI model')
parser.add_argument('--data', help='Path to the input and output data folder.')
args = parser.parse_args()

locations_filename = os.path.join(args.data, 'inputs', 'locations.csv')
locations_computed_filename = os.path.join(args.data, 'inputs', 'locations_computed.csv')
step_costs_filename = os.path.join(args.data, 'inputs', 'step_costs.csv')
fac_edges_filename = os.path.join(args.data, 'inputs', 'fac_edges.csv')
routes_filename = os.path.join(args.data, 'preprocessing', 'routes.csv')
transpo_edges_filename = os.path.join(args.data, 'inputs', 'transpo_edges.csv')
routes_computed_filename = os.path.join(args.data, 'preprocessing', 'routes_computed.csv')
lci_folder = os.path.join(args.data, 'pylca_celavi_data')
outputs_folder = os.path.join(args.data, 'outputs')
avg_blade_masses_filename = os.path.join(args.data, 'inputs', 'avgblademass.csv')

# TODO: The tiny data and national data should use the same filename.
# When that is the case, place that filename below.
turbine_data_filename = os.path.join(args.data, 'inputs', 'TX_input_data_with_masses.csv')

# Because the LCIA code has filenames hardcoded and cannot be reconfigured,
# change the working directory to the lci_folder to accommodate those read
# and write operations. Also, the Context must be imported down here after
# the working directory is changed because the LCIA will attempt to read
# files immediately.

os.chdir(lci_folder)
from des import Context

# if compute_locations is enabled (True), compute locations from raw input files (e.g., LMOP, US Wind Turbine Database)
compute_locations = False
use_computed_locations = True
# Note that the step_cost file must be updated (or programmatically generated)
# to include all facility ids. Otherwise, cost graph can't run with the full
# computed data set.
if compute_locations:
    loc = ComputeLocations()
    loc.join_facilities(locations_output_file=locations_computed_filename)

if use_computed_locations:
    locations = locations_computed_filename
else:
    locations = locations_filename

# if run_routes is enabled (True), compute routing distances between all input locations
run_routes = False
if run_routes:
    routes_computed = Router.get_all_routes(locations_file=locations_filename)
    # reset argument for routes file to use computed routes rather than user input
    args.routes = routes_computed_filename
else:
    routes = routes_filename

tim0 = time.time()
netw = CostGraph(
    step_costs_file=step_costs_filename,
    fac_edges_file=fac_edges_filename,
    transpo_edges_file=transpo_edges_filename,
    locations_file=locations_filename,
    routes_file=routes_filename,
    sc_begin= 'in use',
    sc_end=['landfilling', 'cement co-processing'],
    year=2000.0,
    max_dist=300.0,
    verbose=1,
    blade_mass=50.0, #@todo update with actual value
    finegrind_cumul_initial=1.0,
    coarsegrind_cumul_initial=1.0,
    finegrind_initial_cost=80.0, #@todo update with actual value
    coarsegrind_initial_cost=60.0, #@todo update with actual value
    finegrind_learnrate=-0.05,
    coarsegrind_learnrate=-0.05
)
print(str(time.time() - tim0) + ' ' + 'taken for Cost Graph run',flush=True)

import pickle 
import math 
file_pi = open('netw_pi.obj', 'wb') 
pickle.dump(netw, file_pi)


# Create the DES context and tie it to the CostGraph
tim0 = time.time()
context = Context(
    locations_filename=locations_filename,
    step_costs_filename=step_costs_filename,
    possible_items=["nacelle", "blade", "tower", "foundation"],
    cost_graph=netw,
    cost_graph_update_interval_timesteps=12,
    avg_blade_masses_filename=avg_blade_masses_filename
)


print(str(time.time() - tim0) + ' ' + 'taken for Context Creation',flush=True)
# Create the turbine dataframe that will be used to populate
# the context with components. Repeat the creation of blades
# 3 times for each turbine.


tim0 = time.time()
turbine_data = pd.read_csv(turbine_data_filename)
components = []
for _, row in turbine_data.iterrows():
    year = row['year']
    blade_mass_tonnes = row['Glass Fiber:Blade']
    foundation_mass_tonnes = row['foundation_mass_tonnes']
    facility_id = int(row['facility_id'])
    n_turbine = int(row['n_turbine'])

    for _ in range(n_turbine):
        for _ in range(3):
            components.append({
                'year': year,
                'kind': 'blade',
                'mass_tonnes': blade_mass_tonnes,
                'facility_id': facility_id
            })

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

# Populate the context with components.
context.populate(components, lifespan_fns)
print(str(time.time() - tim0) + ' ' + 'data prepared for context run',flush=True)


# Run the context
tim0 = time.time()
print('DES and Pylca Starting',flush = True)
result = context.run()
print(str(time.time() - tim0) + ' ' + 'DES and Pylca completed',flush=True)



# Output .csv files of the mass flows of each mass inventory.
mass_facility_inventories = result["mass_facility_inventories"]
for facility_name, facility in mass_facility_inventories.items():
    output_filename = os.path.join(outputs_folder, f'{facility_name}.csv')
    output_filename = output_filename.replace(' ', '_')
    facility.transaction_history.to_csv(output_filename, index_label='timestep')

# After PyLCA / DES integration is complete, the next 3 lines should be
# eliminated
data_for_lci_filename = os.path.join(outputs_folder, 'data_for_lci.csv')
data_for_lci_df = pd.DataFrame(context.data_for_lci)
data_for_lci_df.to_csv(data_for_lci_filename, index=False)

# Plot the cumulative count levels of the inventories
count_facility_inventory_items = list(result["mass_facility_inventories"].items())
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
    ax.set_ylabel("tonnes")
plot_output_path = os.path.join(outputs_folder, 'blade_counts.png')
plt.savefig(plot_output_path)

