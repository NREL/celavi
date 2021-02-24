import numpy as np
import pandas as pd
import os

from scipy.stats import weibull_min

from celavi.des import Context

np.random.seed(123)

# read in input data as-is
_lci_input = pd.read_csv('lci.csv')

# Melt to a dataframe with columns: flow unit, flow name, material, direction,
# process, quantity
# ignore original index columns created when data was read in
lci_melt = pd.melt(_lci_input,
                   id_vars=['flow unit', 'flow name', 'material', 'direction'],
                   value_vars=['manufacturing',
                               'recycle to clinker',
                               'recycle to raw material',
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

    # postprocess the virgin material inventory (inputs) to calculate
    # cumulative material flows by timestep
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
    rec_clinker_melt['process'] = 'recycle to clinker'

    rec_rawmat_mass = inventory_bundle['recycle_to_raw_material_inventory'][['blade']].rename(columns={'blade': 'glass fiber reinforced polymer'})
    rec_rawmat_mass['year'] = rec_rawmat_mass.index * 0.25 + 2000.0

    rec_rawmat_melt = pd.melt(rec_rawmat_mass, id_vars=['year'],
                               value_vars=['glass fiber reinforced polymer'],
                               var_name='material', value_name='cumul_mass')
    rec_rawmat_melt['mass'] = rec_rawmat_melt['cumul_mass'].diff()
    rec_rawmat_melt['process'] = 'recycle to raw material'

    landfill_mass = inventory_bundle['landfill_material_inventory'][['blade']].rename(columns={'blade': 'glass fiber reinforced polymer'})
    landfill_mass['year'] = landfill_mass.index * 0.25 + 2000.0

    landfill_melt = pd.melt(landfill_mass, id_vars=['year'],
                               value_vars=['glass fiber reinforced polymer'],
                               var_name='material', value_name='cumul_mass')
    landfill_melt['mass'] = landfill_melt['cumul_mass'].diff()
    landfill_melt['process'] = 'landfilling'

    # aggregate together the various inventories
    inventory = virgin_melt.append(rec_clinker_melt,
                                       ignore_index=True).append(rec_rawmat_melt,
                                                                 ignore_index=True).append(landfill_melt,
                                                                                           ignore_index=True)

    #.diff turns some initial mass values to negative instead of zero, so set
    # those to zero
    inventory.loc[inventory['mass'] < 0.0, 'mass'] = 0.0

    inventory['scenario'] = scenario_name
    inventory['coarse grinding location'] = coarse_grind_loc
    inventory['distance to recycling facility'] = turb_recfacility_dist
    inventory['distance to cement plant'] = turb_cement_loc

    inventory.sort_values(by=['process'],inplace=True)

    # create slightly altered copy of the inventories dataframe for saving
    inventory_save = inventory.copy()

    filename='inventories'

    if not os.path.isfile(filename + '.csv'):
        inventory_save.to_csv(filename + '.csv',
                              header=True, mode='a+',
                              index=False)
    else:
       inventory_save.to_csv(filename + '.csv',
                             header=False, mode='a+',
                             index=False)

    # calculate input file for pylca
    pylca_mat = inventory.merge(lci, how='outer', on=['material','process']).dropna()
    pylca_mat['flow quantity'] = pylca_mat['mass'] * pylca_mat['quantity']

    ## perform displacement calculations

    # convert years to integer: manufacturing only happens in integer valued
    # timesteps (ie 2000, 2001), so other EOL processes need to be summed to
    # the annual level to calculate offsets correctly
    pylca_mat['year'] = pylca_mat['year'].astype(int)
    pylca_mat = pylca_mat.groupby(['year', 'material', 'process', 'scenario',
                                   'coarse grinding location',
                                   'distance to recycling facility',
                                   'distance to cement plant',
                                   'flow unit', 'flow name', 'direction',
                                   'quantity'],as_index=False).sum().copy()

    # remove rows with zero flow quantity
    # these are inactive pathways and don't cause impacts
    pylca_mat = pylca_mat.loc[pylca_mat['flow quantity'] != 0].copy()

    # remove columns that we don't need for calculating impacts
    # BN that 'quantity' is the amount per ton material from the input LCI file,
    # not the total amount of input to the system
    pylca_mat.drop(columns=['cumul_mass', 'quantity'], inplace=True)

    for i in pylca_mat.year.unique():
        _yr_pylca = pylca_mat.loc[pylca_mat['year']==i]
        if 'recycle to clinker' in _yr_pylca.process.unique():
            # from Nagle et al: 1 kg blades can simultaneously displace 0.3
            # kg coal and 0.155 kg SiO2/sand and gravel
            _max_gfrp_coal = _yr_pylca.loc[(_yr_pylca['material']=='glass fiber reinforced polymer') &
                                               (_yr_pylca['process']=='recycle to clinker'),
                                               'mass'] * 0.3
            # blade mass in metric tons. 1000 kg blade material to displace 560 kg clinker material
            _max_gfrp_sandandgravel = _yr_pylca.loc[(_yr_pylca['material']=='glass fiber reinforced polymer') &
                                               (_yr_pylca['process']=='recycle to clinker'),
                                               'mass'] * 0.155
            # convert kg to metric ton, can displace max 30%
            _max_coal_capacity = _yr_pylca.loc[(_yr_pylca['material']=='concrete') &
                                               (_yr_pylca['process']=='manufacturing') &
                                               (_yr_pylca['flow name']=='coal'),
                                               'flow quantity'] / 1000.0
            # convert kg to metric ton, can displace max 15.4%
            _max_sandandgravel_capacity = _yr_pylca.loc[(_yr_pylca['material']=='concrete') &
                                                        (_yr_pylca['process']=='manufacturing') &
                                                        (_yr_pylca['flow name']=='sand and gravel'),
                                                        'flow quantity'] / 1000.0

            # if there is sufficient capcity to use all allowed gfrp as sand and gravel,
            # reduce the 'flow quantity' for sand and gravel by 15.5%
            if any(_max_sandandgravel_capacity.values >= _max_gfrp_sandandgravel.values):
                pylca_mat.loc[(pylca_mat['year']==i) &
                              (pylca_mat['material']=='concrete') &
                              (pylca_mat['process']=='manufacturing') &
                              (pylca_mat['flow name']=='sand and gravel'),
                              'flow quantity'] = pylca_mat.loc[(pylca_mat['year']==i) &
                                                               (pylca_mat['material']=='concrete') &
                                                               (pylca_mat['process']=='manufacturing') &
                                                               (pylca_mat['flow name']=='sand and gravel'),
                                                               'flow quantity'] - _max_gfrp_sandandgravel.values
            # if there is NOT sufficient capacity to use all allowed gfrp as
            # sand and gravel, reduce the sand and gravel 'flow quantity' by the maximum
            # amount - some clinker is left over but @note this is not currently
            # accounted for
            else:
                pylca_mat.loc[(pylca_mat['year']==i) &
                              (pylca_mat['material']=='concrete') &
                              (pylca_mat['process']=='manufacturing') &
                              (pylca_mat['flow name']=='sand and gravel'),
                              'flow quantity'] = (1-0.155) * pylca_mat.loc[(pylca_mat['year']==i) &
                                                                           (pylca_mat['material']=='concrete') &
                                                                           (pylca_mat['process']=='manufacturing') &
                                                                           (pylca_mat['flow name']=='sand and gravel'),
                                                                           'flow quantity']

            if any(_max_coal_capacity.values >= _max_gfrp_coal.values):
                pylca_mat.loc[(pylca_mat['year']==i) &
                              (pylca_mat['material']=='concrete') &
                              (pylca_mat['process']=='manufacturing') &
                              (pylca_mat['flow name']=='coal'),
                              'flow quantity'] = pylca_mat.loc[(pylca_mat['year']==i) &
                                                               (pylca_mat['material']=='concrete') &
                                                               (pylca_mat['process']=='manufacturing') &
                                                               (pylca_mat['flow name']=='coal'),
                                                               'flow quantity'] - _max_gfrp_coal.values
                pylca_mat.loc[(pylca_mat['year'] == i) &
                              (pylca_mat['material'] == 'concrete') &
                              (pylca_mat['process'] == 'manufacturing') &
                              (pylca_mat['flow name'] == 'carbon dioxide, fossil'),
                              'flow quantity'] = (1 - (_max_gfrp_coal.values / _max_coal_capacity.values) * 0.16) * pylca_mat.loc[(pylca_mat['year'] == i) &
                                                                                                                                  (pylca_mat['material'] == 'concrete') &
                                                                                                                                  (pylca_mat['process'] == 'manufacturing') &
                                                                                                                                  (pylca_mat['flow name'] == 'carbon dioxide, fossil'),
                                                                                                                                  'flow quantity']

            else:
                pylca_mat.loc[(pylca_mat['year']==i) &
                              (pylca_mat['material']=='concrete') &
                              (pylca_mat['process']=='manufacturing') &
                              (pylca_mat['flow name']=='coal'),
                              'flow quantity'] = (1 - 0.3) * pylca_mat.loc[(pylca_mat['year']==i) &
                                                                           (pylca_mat['material']=='concrete') &
                                                                           (pylca_mat['process']=='manufacturing') &
                                                                           (pylca_mat['flow name']=='coal'),
                                                                           'flow quantity']
                pylca_mat.loc[(pylca_mat['year'] == i) &
                              (pylca_mat['material'] == 'concrete') &
                              (pylca_mat['process'] == 'manufacturing') &
                              (pylca_mat['flow name'] == 'carbon dioxide, fossil'),
                              'flow quantity'] = (1 - 0.16) * pylca_mat.loc[(pylca_mat['year'] == i) &
                                                                            (pylca_mat['material'] == 'concrete') &
                                                                            (pylca_mat['process'] == 'manufacturing') &
                                                                            (pylca_mat['flow name'] == 'carbon dioxide, fossil'),
                                                                            'flow quantity']

    pylca_mat.drop(columns=['mass'],axis=1,inplace=True)
    # get the cost history file saved, and append transportation to the
    # pylca input file
    inventory_list = ['cost_history', 'transpo_eol']
    for df_name in inventory_list:
        # postprocess, melt and save the cost history
        if df_name == 'cost_history':
            new_df = pd.DataFrame.from_dict(inventory_bundle[df_name]).groupby(['year'],
                                                                               as_index=False).mean()
            new_df['scenario'] = scenario_name
            new_df['coarse grinding location'] = coarse_grind_loc
            new_df['distance to recycling facility'] = turb_recfacility_dist
            new_df['distance to cement plant'] = turb_cement_loc

            df_melt = pd.melt(new_df,
                              id_vars=['year', 'scenario',
                                       'coarse grinding location',
                                       'distance to recycling facility',
                                       'distance to cement plant'],
                              value_vars=['landfilling cost',
                                          'recycling to clinker cost',
                                          'recycling to raw material cost',
                                          'blade removal cost, per tonne',
                                          'blade removal cost, per blade',
                                          'blade mass, tonne',
                                          'coarse grinding cost',
                                          'fine grinding cost',
                                          'segment transpo cost',
                                          'landfill tipping fee'],
                              var_name='pathway', value_name='cost')

            filename='cost-histories.csv'

            if not os.path.isfile(filename):
                df_melt.to_csv(filename,
                               header=True, mode='a+',
                               index=False)
            else:
                df_melt.to_csv(filename,
                               header=False, mode='a+',
                               index=False)
        else:
            new_df = pd.DataFrame.from_dict(inventory_bundle[df_name]).groupby(['year'],
                                                                               as_index=False).sum()
            new_df['year'] = new_df['year'].astype(int)
            new_df = new_df.groupby(['year'], as_index=False).sum()
            new_df['scenario'] = scenario_name
            new_df['coarse grinding location'] = coarse_grind_loc
            new_df['distance to recycling facility'] = turb_recfacility_dist
            new_df['distance to cement plant'] = turb_cement_loc
            new_df['flow unit'] = 'tonne-km'
            new_df['flow name'] = 'transportation'
            new_df['direction'] = 'input'
            new_df['material'] = 'glass fiber reinforced polymer'
            new_df['process'] = 'transportation'
            new_df.rename(columns={'total eol transportation': "flow quantity"},
                          inplace=True)

            # append to the existing pylca input dataframe
            pylca_input = pylca_mat.copy().append(new_df, ignore_index=True)

            # save the pylca input dataframe as .csv
            filename = 'celavi-pylca-input'
            if not os.path.isfile(filename + '.csv'):
                pylca_input.to_csv(filename + '.csv',
                               header=True, mode='a+',
                               index=False)
            else:
                pylca_input.to_csv(filename + '.csv',
                               header=False, mode='a+',
                               index=False)


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