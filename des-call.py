import argparse
from math import ceil

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from celavi.des import Context
from celavi.costgraph import CostGraph

parser = argparse.ArgumentParser(description='Check CELAVI input data')
parser.add_argument('--locations', help='Path to locations file')
parser.add_argument('--step_costs', help='Path to step_costs file')
parser.add_argument('--fac_edges', help='Facility edges file')
parser.add_argument('--routes', help='Routes file')
parser.add_argument('--transpo_edges', help='Transportation edges file')
parser.add_argument('--turbine_data', help='Data with turbine configurations and locations.')
args = parser.parse_args()

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

context = Context(
    locations_filename=args.locations,
    step_costs_filename=args.step_costs,
    possible_items=["nacelle", "blade", "tower", "foundation"],
    cost_graph=netw
)

turbine_data = pd.read_csv(args.turbine_data)
components = []
for _, row in turbine_data.iterrows():
    xlong = row['xlong']
    ylat = row['ylat']
    year = row['year']
    blade_mass_tonnes = row['blade_mass_tonnes']
    foundation_mass_tonnes = row['foundation_mass_tonnes']
    n_turbine = int(row['n_turbine'])

    for _ in range(n_turbine):
        for _ in range(3):
            components.append({
                'xlong': xlong,
                'ylat': ylat,
                'year': year,
                'kind': 'blade',
                'mass_tonnes': blade_mass_tonnes
            })
        # components.append({
        #     'xlong': xlong,
        #     'ylat': ylat,
        #     'year': year,
        #     'kind': 'foundation',
        #     'mass_tonnes': foundation_mass_tonnes
        # })

components = pd.DataFrame(components)

timesteps_per_year = 12
lifespan_fns = {
    "nacelle": lambda: 30 * timesteps_per_year,
    "blade": lambda: 20 * timesteps_per_year,
    "foundation": lambda: 50 * timesteps_per_year,
    "tower": lambda: 50 * timesteps_per_year,
}

context.populate(components, lifespan_fns)
result = context.run()

count_facility_inventory_items = list(result["count_facility_inventories"].items())
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
plt.show()
