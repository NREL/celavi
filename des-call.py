import argparse
import os
from math import ceil

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import weibull_min


# Before other modules are loaded, working directory must be changed and
# command line must be parsed.

# Setup the command line parsing
parser = argparse.ArgumentParser(description='Check CELAVI input data')
parser.add_argument('--locations', help='Path to locations file')
parser.add_argument('--step_costs', help='Path to step_costs file')
parser.add_argument('--fac_edges', help='Facility edges file')
parser.add_argument('--routes', help='Routes file')
parser.add_argument('--transpo_edges', help='Transportation edges file')
parser.add_argument('--turbine_data', help='Data with turbine configurations and locations')
parser.add_argument('--avg_blade_masses', help='Data of average blade masses for each year.')
parser.add_argument('--outputs', help='Folder/directory where output .csv files should be written')
parser.add_argument('--lci', help='Input and output folder for LCIA calculations.')
args = parser.parse_args()

# Because the LCIA code has filenames hardcoded and cannot be reconfigured,
# change the working directory to the lci_folder to accommodate those read
# and write operations.

os.chdir(args.lci)


from celavi.des import Context
from celavi.costgraph import CostGraph

# Create the cost graph
netw = CostGraph(
    step_costs_file=args.step_costs,
    fac_edges_file=args.fac_edges,
    transpo_edges_file=args.transpo_edges,
    locations_file=args.locations,
    routes_file=args.routes,
    sc_end=['landfilling', 'cement co-processing'],
    year=2000.0,
    max_dist=300.0
)

# This is where I will launch the LCIA subprocess and pass it into the DES

# Create the DES context and tie it to the CostGraph
context = Context(
    locations_filename=args.locations,
    step_costs_filename=args.step_costs,
    possible_items=["nacelle", "blade", "tower", "foundation"],
    cost_graph=netw,
    cost_graph_update_interval_timesteps=12,
    avg_blade_masses_filename=args.avg_blade_masses
)

# Create the turbine dataframe that will be used to populate
# the context with components. Repeat the creation of blades
# 3 times for each turbine.

turbine_data = pd.read_csv(args.turbine_data)
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

# Run the context
result = context.run()

# Output .csv files of the mass flows of each mass inventory.
mass_facility_inventories = result["mass_facility_inventories"]
outputs = args.outputs
for facility_name, facility in mass_facility_inventories.items():
    output_filename = os.path.join(outputs, f'{facility_name}.csv')
    output_filename = output_filename.replace(' ', '_')
    facility.transaction_history.to_csv(output_filename, index_label='timestep')

# After PyLCA / DES integration is complete, the next 3 lines should be
# eliminated
data_for_lci_filename = os.path.join(outputs, 'data_for_lci.csv')
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
plot_output_path = os.path.join(outputs, 'blade_counts.png')
plt.savefig(plot_output_path)
