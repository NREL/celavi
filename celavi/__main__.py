import argparse
from celavi.costgraph import CostGraph

parser = argparse.ArgumentParser(description='Check CELAVI input data')
parser.add_argument('--locations', help='Path to locations file')
parser.add_argument('--step_costs', help='Path to step_costs file')
parser.add_argument('--fac_edges', help='Facility edges file')
parser.add_argument('--routes', help='Routes file')
parser.add_argument('--transpo_edges', help='Transportation edges file')
args = parser.parse_args()

netw = CostGraph(
    step_costs_file=args.step_costs,
    fac_edges_file=args.fac_edges,
    transpo_edges_file=args.transpo_edges,
    locations_file=args.locations,
    routes_file=args.routes,
    sc_begin= 'in use',
    sc_end=['landfilling', 'cement co-processing'],
    year=2000.0,
    max_dist=300.0,
    verbose=2
)

print(netw.choose_paths(),'\n')

netw.update_costs(
    year=2010.0,
    blade_mass=1500.0,
    cumul_finegrind=2000.0,
    cumul_coarsegrind=4000.0)

print(netw.choose_paths())
