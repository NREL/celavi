from costgraph import CostGraph

netw = CostGraph(
    step_costs_file='../../celavi-data/inputs/step_costs.csv',
    fac_edges_file='../../celavi-data/inputs/fac_edges.csv',
    transpo_edges_file='../../celavi-data/inputs/transpo_edges.csv',
    locations_file='../../celavi-data/inputs/locations.csv',
    routes_file='../../celavi-data/preprocessing/routes.csv',
    sc_begin= 'in use',
    sc_end=['landfilling', 'cement co-processing'],
    year=2000.0,
    max_dist=300.0
)

print(netw.choose_paths(),'\n')

netw.update_costs(
    year=2010.0,
    blade_mass=1500.0,
    cumul_finegrind=2000.0,
    cumul_coarsegrind=4000.0)

print(netw.choose_paths())