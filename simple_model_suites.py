import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
from scipy.stats import weibull_min


from celavi.simple_model import Context

np.random.seed(123)

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
                   coarse_grind_loc: str, turb_recfacility_dist: float):

    inventory_list = ['landfill',
                      'virgin',
                      'recycle_to_raw',
                      'recycle_to_clinker',
                      'cost_history']

    for df_name in inventory_list:
        if df_name != 'cost_history':
            df_count = inventory_bundle[df_name + '_component_inventory'].rename(columns={'blade': 'blade count', 'foundation': 'foundation count'})
            df_mass = inventory_bundle[df_name + '_material_inventory'].rename(columns={'blade': 'blade mass', 'foundation': 'foundation mass'})
            new_df = pd.merge(left=df_count[['blade count', 'foundation count']], right=df_mass[['blade mass', 'foundation mass']],
                              left_index=True, right_index=True)
            filename='inventories.csv'

            new_df['year'] = new_df.index * 0.25 + 2000.0

        else:
            new_df = pd.DataFrame.from_dict(inventory_bundle[df_name]).groupby(['year']).mean()
            filename='cost-histories.csv'


        new_df['scenario'] = scenario_name
        new_df['coarse grinding location'] = coarse_grind_loc
        new_df['turbine to recycle facility distance'] = turb_recfacility_dist
        new_df['inventory'] = df_name


        if not os.path.isfile(filename):
            new_df.to_csv(filename,
                          header=True, mode='a+')
        else:
            new_df.to_csv(filename,
                          header=False, mode='a+')


def run_suite(turb_rec:float, coarse_grind:str):

    dist_df = pd.DataFrame(data=np.array([[0.0, 69.2, turb_rec, 204.4],
                                          [69.2, 0.0, 1.6, 4.8],
                                          [turb_rec,  1.6,  0.0,   217.3],
                                          [204.4, 4.8,  217.3, 0.0]]),
                           columns=['turbine', 'landfill',
                                    'recycling facility', 'cement plant'],
                           index=['turbine', 'landfill',
                                  'recycling facility', 'cement plant'])


    bau_cost_params = {'recycling_learning_rate': 0.05,    #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 121.28,   #USD/tonne, initial cost
                       'coarse_grinding_facility': 121.28, #USD/tonne, initial cost
                       'fine_grinding': 165.38,            #USD/tonne, initial cost
                       'onsite_size_red_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -191.02,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    mc_cost_params = {'recycling_learning_rate': 0.05,     #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 106.40,    #USD/tonne, initial cost
                       'coarse_grinding_facility': 106.40,  #USD/tonne, initial cost
                       'fine_grinding': 165.38,            #USD/tonne, initial cost
                       'onsite_size_red_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -191.02,      #USD/tonne
                       'rec_clink_revenue': -10.37,        #USD/tonne
                       'rec_rawmat_strategic_value': 0.0,  #USD/tonne
                       'rec_clink_strategic_value': 0.0}   #USD/tonne

    hc_cost_params = {'recycling_learning_rate': 0.05,     #unitless
                       'coarse_grinding_loc': coarse_grind, #'onsite' or 'facility'
                       'distances':dist_df,                #km
                       'coarse_grinding_onsite': 91.51,    #USD/tonne, initial cost
                       'coarse_grinding_facility': 91.51,  #USD/tonne, initial cost
                       'fine_grinding': 165.38,            #USD/tonne, initial cost
                       'onsite_size_red_cost': 27.56,      #USD/tonne
                       'shred_transpo_cost': 0.08,         #USD/tonne-km
                       'coarse_grind_yield': 1.0,          #unitless
                       'fine_grind_yield': 0.7,            #unitless
                       'rec_rawmat_revenue': -191.02,      #USD/tonne
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
                       turb_recfacility_dist=turb_rec)
        print("Postprocessing complete.\n")


# vary the km between the turbine location and the landfill
# vary the location of the coarse grinding
run_suite(turb_rec=9.0, coarse_grind='onsite')
run_suite(turb_rec=9.0, coarse_grind='facility')
run_suite(turb_rec=69.2, coarse_grind='onsite')
run_suite(turb_rec=69.2, coarse_grind='facility')
run_suite(turb_rec=765.0, coarse_grind='onsite')
run_suite(turb_rec=765.0, coarse_grind='facility')