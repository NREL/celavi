import argparse
import os
from routing import Router
from costgraph import CostGraph
from compute_locations import ComputeLocations

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
    verbose=2,
    blade_mass=50.0, #@todo update with actual value
    finegrind_cumul_initial=1.0,
    coarsegrind_cumul_initial=1.0,
    finegrind_initial_cost=80.0, #@todo update with actual value
    coarsegrind_initial_cost=60.0, #@todo update with actual value
    finegrind_learnrate=-0.05,
    coarsegrind_learnrate=-0.05
)

print(netw.choose_paths(),'\n')

netw.update_costs(
    year=2010.0,
    blade_mass=1500.0,
    finegrind_cumul=2000.0,
    coarsegrind_cumul=4000.0)

print(netw.choose_paths())
