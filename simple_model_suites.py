import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy.stats import weibull_min

from celavi.simple_model import Context

np.random.seed(123)

# read in input data as-is
_lci_input = pd.read_csv('lci.csv')

# Melt to a dataframe with columns: input unit, input name, material,
# process, quantity
# ignore original index columns created when data was read in
lci_melt = pd.melt(_lci_input,
                   id_vars=['input unit', 'input name', 'material'],
                   value_vars=['manufacturing',
                               'coarse grinding', 'fine grinding',
                               'landfilling'],
                   var_name='process', value_name='quantity').dropna()

usgs = pd.read_csv("TX_input_data_with_masses.csv")

# drop any rows without years (should be none)
usgs.dropna(axis=0, subset=["year"], inplace=True)

# expand the dataset s.t. every turbine is one row
expand = pd.DataFrame(np.repeat(usgs.values,usgs['n_turbine'],axis=0))
expand.columns = usgs.columns
expand.drop(columns='n_turbine',inplace=True)

# remove raw input dataset
del usgs

# rename expanded dataset back to usgs
usgs = expand.copy()


components = []
for _, turbine in usgs.iterrows():
    xlong = turbine["xlong"]
    ylat = turbine["ylat"]
    year = turbine["year"]
    blade_mass_tonnes = int(turbine["blade_mass_tonnes"])
    foundation_mass_tonnes = int(turbine['foundation_mass_tonnes'])

    components.append({
        "kind": "blade",
        "xlong": xlong,
        "ylat": ylat,
        "year": year,
        "mass_tonnes": blade_mass_tonnes,
    })

    components.append({
        "kind": "blade",
        "xlong": xlong,
        "ylat": ylat,
        "year": year,
        "mass_tonnes": blade_mass_tonnes,
    })

    components.append({
        "kind": "blade",
        "xlong": xlong,
        "ylat": ylat,
        "year": year,
        "mass_tonnes": blade_mass_tonnes,
    })

    components.append({
        "kind": "foundation",
        "xlong": xlong,
        "ylat": ylat,
        "year": year,
        "mass_tonnes": foundation_mass_tonnes,
    })

components = pd.DataFrame(components)

# All lifespans in the model are in discrete timesteps
timesteps_per_year = 4
start_yr=2000
end_yr=2050

lifespans = [20 * timesteps_per_year]
landfill_inventories = {}
landfill_mass_inventories = {}
K = 2.2   # DES Weibull shape parameter from Aubryn's study
min_lifespan = 10 * timesteps_per_year  # From Faulstitch et al

for lifespan in lifespans:
    L = lifespan  # DES Weibull scale parameter

    lifespan_fns = {
        "blade": lambda: weibull_min.rvs(K, loc=min_lifespan, scale=L-min_lifespan, size=1)[0],
#         "blade": lambda: weibull_min.rvs(K, loc=0, scale=L, size=1)[0],
        "foundation": lambda: 50,
    }


def postprocess_df(inventory_bundle,
                   scenario_name: str,
                   coarse_grind_loc: str,
                   turb_recfacility_dist: float,
                   turb_cement_loc: float,
                   lci=lci_melt):
    """

    """

    # postprocess the virgin material inventory (inputs) to calculate LCI by timestep
    virgin_mass = -1.0 * inventory_bundle['virgin_material_inventory'][['blade', 'foundation']].rename(columns={'blade': 'glass fiber reinforced polymer', 'foundation': 'concrete'})
    virgin_mass['year'] =  virgin_mass.index * 0.25 + 2000.0

    virgin_melt = pd.melt(virgin_mass, id_vars=['year'],
                               value_vars=['glass fiber reinforced polymer',
                                           'concrete'],
                               var_name='material', value_name='cumul_mass')
    virgin_melt['mass'] = virgin_melt['cumul_mass'].diff()
    virgin_melt['process'] = 'manufacturing'

    rec_clinker_mass = inventory_bundle['recycle_to_clinker_material_inventory'][['blade']].rename(columns={'blade': 'glass fiber reinforced polymer'})
    rec_clinker_mass['year'] = rec_clinker_mass.index * 0.25 + 2000.0

    rec_clinker_melt = pd.melt(rec_clinker_mass, id_vars=['year'],
                               value_vars=['glass fiber reinforced polymer'],
                               var_name='material', value_name='cumul_mass')
    rec_clinker_melt['mass'] = rec_clinker_melt['cumul_mass'].diff()
    rec_clinker_melt['process'] = 'coarse grinding'

    rec_rawmat_mass = inventory_bundle['recycle_to_raw_material_inventory'][['blade']].rename(columns={'blade': 'glass fiber reinforced polymer'})
    rec_rawmat_mass['year'] = rec_rawmat_mass.index * 0.25 + 2000.0

    rec_rawmat_melt = pd.melt(rec_rawmat_mass, id_vars=['year'],
                               value_vars=['glass fiber reinforced polymer'],
                               var_name='material', value_name='cumul_mass')
    rec_rawmat_melt['mass'] = rec_rawmat_melt['cumul_mass'].diff()
    rec_rawmat_melt['process'] = 'fine grinding'

    landfill_mass = inventory_bundle['landfill_material_inventory'][['blade']].rename(columns={'blade': 'glass fiber reinforced polymer'})
    landfill_mass['year'] = landfill_mass.index * 0.25 + 2000.0

    landfill_melt = pd.melt(landfill_mass, id_vars=['year'],
                               value_vars=['glass fiber reinforced polymer'],
                               var_name='material', value_name='cumul_mass')
    landfill_melt['mass'] = landfill_melt['cumul_mass'].diff()
    landfill_melt['process'] = 'landfilling'

    # aggregate together the various inventories
    inventory_lci = virgin_melt.append(rec_clinker_melt,
                                       ignore_index=True).append(rec_rawmat_melt,
                                                                 ignore_index=True).append(landfill_melt,
                                                                                           ignore_index=True)
    inventory_lci.loc[inventory_lci['mass'] < 0.0, 'mass'] = 0.0

    inventory_lci['scenario'] = scenario_name
    inventory_lci['coarse grinding location'] = coarse_grind_loc
    inventory_lci['distance to recycling facility'] = turb_recfacility_dist
    inventory_lci['distance to cement plant'] = turb_cement_loc

    filename='inventories'

    if not os.path.isfile(filename + '.csv'):
        inventory_lci.to_csv(filename + '.csv',
                      header=True, mode='a+')
    else:
       inventory_lci.to_csv(filename + '.csv',
                      header=False, mode='a+')


    lci_out = inventory_lci.merge(lci, how='outer', on=['material','process']).dropna()
    lci_out['input quantity'] = lci_out['mass'] * lci_out['quantity']

    filename='celavi-results-lci'

    if not os.path.isfile(filename + '.csv'):
        lci_out.to_csv(filename + '.csv',
                      header=True, mode='a+')
    else:
       lci_out.to_csv(filename + '.csv',
                      header=False, mode='a+')

    # find the rows where process = coarse grinding (only gfrp has this process)
    # pull the years from these rows

    # rec_clinker_mass = inventory_bundle['recycle_to_clinker_material_inventory'].rename(columns={'blade': 'blade mass', 'foundation': 'foundation mass'})
    # rec_rawmat_mass = inventory_bundle['recycle_to_raw_material_inventory'].rename(columns={'blade': 'blade mass', 'foundation': 'foundation mass'})
    # landfill_mass = inventory_bundle['landfill_material_inventory'].rename(columns={'blade': 'blade mass', 'foundation': 'foundation mass'})

    inventory_list = ['cost_history',
                      'transpo_eol']

    for df_name in inventory_list:
        if df_name == 'cost_history':
            new_df = pd.DataFrame.from_dict(inventory_bundle[df_name]).groupby(['year']).mean()
            filename='cost-histories.csv'
        else:
            new_df = pd.DataFrame.from_dict(inventory_bundle[df_name]).groupby(['year']).sum()
            filename='transpo-eol.csv'


        new_df['scenario'] = scenario_name
        new_df['coarse grinding location'] = coarse_grind_loc
        new_df['distance to recycling facility'] = turb_recfacility_dist
        new_df['distance to cement plant'] = turb_cement_loc
        new_df['inventory'] = df_name

        if not os.path.isfile(filename):
            new_df.to_csv(filename,
                          header=True, mode='a+')
        else:
            new_df.to_csv(filename,
                          header=False, mode='a+')

def run_once(scenario:str, turb_rec:float, turb_cement:float, coarse_grind:str):

    dist_df = pd.DataFrame(data=np.array([[0.0, 69.2, turb_rec, turb_cement, turb_cement],
                                          [69.2, 0.0, 1.6, 4.8, 4.8],
                                          [turb_rec,  1.6,  0.0,   217.3, 217.3],
                                          [turb_cement, 4.8,  217.3, 0.0, 0.0],
                                          [turb_cement, 4.8, 217.3, 0.0, 0.0]]),
                           columns=['turbine', 'landfill', 'recycling facility', 'cement plant', 'next use facility'],
                           index=['turbine', 'landfill', 'recycling facility', 'cement plant', 'next use facility'])


    bau_cost_params = {'recycling_learning_rate': 0.05,    #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 121.28,   #USD/tonne, initial cost
                       'coarse_grinding_facility': 121.28, #USD/tonne, initial cost
                       'fine_grinding': 165.38,            #USD/tonne, initial cost
                       'onsite_segmenting_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -242.56,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    mc_cost_params = {'recycling_learning_rate': 0.05,     #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 106.40,    #USD/tonne, initial cost
                       'coarse_grinding_facility': 106.40,  #USD/tonne, initial cost
                       'fine_grinding': 143.33,            #USD/tonne, initial cost
                       'onsite_segmenting_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -272.88,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    hc_cost_params = {'recycling_learning_rate': 0.05,     #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 91.51,    #USD/tonne, initial cost
                       'coarse_grinding_facility': 91.51,  #USD/tonne, initial cost
                       'fine_grinding': 121.28,            #USD/tonne, initial cost
                       'onsite_segmenting_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -303.20,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    if scenario == 'bau':
        params=bau_cost_params
    elif scenario == 'mc':
        params=mc_cost_params
    elif scenario == 'hc':
        params=hc_cost_params
    else:
        params=bau_cost_params

    print("Scenario " + scenario + ':\n')

    # create the Context
    print("Creating Context...\n")
    context = Context(min_year=start_yr, max_timesteps=timesteps_per_year*(end_yr-start_yr)+1,
                      cost_params=params)
    context.populate(components, lifespan_fns)
    print("Context created.\n")

    # run the DES model and get all material inventories
    print("Model run starting...\n")
    all_inventories = context.run()
    print("Model run complete.\n")

    print("Postprocessing files...\n")
    postprocess_df(inventory_bundle=all_inventories,
                   scenario_name=scenario,
                   coarse_grind_loc=coarse_grind,
                   turb_recfacility_dist=turb_rec,
                   turb_cement_loc=turb_cement)
    print("Postprocessing complete.\n")

def run_suite(turb_rec:float, turb_cement:float, coarse_grind:str):

    dist_df = pd.DataFrame(data=np.array([[0.0, 69.2, turb_rec, turb_cement, turb_cement],
                                          [69.2, 0.0, 1.6, 4.8, 4.8],
                                          [turb_rec,  1.6,  0.0,   217.3, 217.3],
                                          [turb_cement, 4.8,  217.3, 0.0, 0.0],
                                          [turb_cement, 4.8, 217.3, 0.0, 0.0]]),
                           columns=['turbine', 'landfill', 'recycling facility', 'cement plant', 'next use facility'],
                           index=['turbine', 'landfill', 'recycling facility', 'cement plant', 'next use facility'])

    bau_cost_params = {'recycling_learning_rate': 0.05,    #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 121.28,   #USD/tonne, initial cost
                       'coarse_grinding_facility': 121.28, #USD/tonne, initial cost
                       'fine_grinding': 165.38,            #USD/tonne, initial cost
                       'onsite_segmenting_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -242.56,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    mc_cost_params = {'recycling_learning_rate': 0.05,     #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 106.40,    #USD/tonne, initial cost
                       'coarse_grinding_facility': 106.40,  #USD/tonne, initial cost
                       'fine_grinding': 143.33,            #USD/tonne, initial cost
                       'onsite_segmenting_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -272.88,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    hc_cost_params = {'recycling_learning_rate': 0.05,     #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 91.51,    #USD/tonne, initial cost
                       'coarse_grinding_facility': 91.51,  #USD/tonne, initial cost
                       'fine_grinding': 121.28,            #USD/tonne, initial cost
                       'onsite_segmenting_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -303.20,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    for scenario in ['bau', 'mc', 'hc']:
        if scenario == 'bau':
            params=bau_cost_params
        elif scenario == 'mc':
            params=mc_cost_params
        elif scenario == 'hc':
            params=hc_cost_params
        else:
            params=bau_cost_params

        print("Scenario " + scenario + ':\n')

        # create the Context
        print("Creating Context...\n")
        context = Context(min_year=start_yr, max_timesteps=timesteps_per_year*(end_yr-start_yr)+1,
                          cost_params=params)
        context.populate(components, lifespan_fns)
        print("Context created.\n")

        # run the DES model and get all material inventories
        print("Model run starting...\n")
        all_inventories = context.run()
        print("Model run complete.\n")

        print("Postprocessing files...\n")
        postprocess_df(inventory_bundle=all_inventories,
                       scenario_name=scenario,
                       coarse_grind_loc=coarse_grind,
                       turb_recfacility_dist=turb_rec,
                       turb_cement_loc=turb_cement)
        print("Postprocessing complete.\n")


# scenario def for debugging
run_once(scenario='bau', turb_rec=51.0, turb_cement=204.0, coarse_grind='onsite')

# vary the km between the turbine location and the landfill
# vary the location of the coarse grinding
run_suite(turb_rec=9.0, turb_cement=187.0, coarse_grind='onsite')
run_suite(turb_rec=9.0, turb_cement=187.0, coarse_grind='facility')
run_suite(turb_rec=51.0, turb_cement=204.0,coarse_grind='onsite')
run_suite(turb_rec=51.0, turb_cement=204.0, coarse_grind='facility')
run_suite(turb_rec=765.0, turb_cement=803.0, coarse_grind='onsite')
run_suite(turb_rec=765.0, turb_cement=803.0, coarse_grind='facility')