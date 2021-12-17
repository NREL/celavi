# TODO: Add a short module docstring above the code to:
#  1) provide authors, date of creation
#  2) give a high level description (2-3 lines) of what the module does
#  3) write any other relevant information

import pandas as pd

"""
This module models a stock variable for concrete.

I do not need to create a concrete stock variable in the DES.

The only file that this creates is the pickle file between years.
"""


def concrete_life_cycle_inventory_updater(fd_cur2, yr, k, stage):
    # TODO: add docstrings to explain input variables and what the function
    #  does.

    # TODO: consider having sand_substitution_rate and coal_substitution_rate
    #  as inputs of the function (and assign default values). Also consider
    #  adding those two rates as user inputs (with defaults values) and place
    #  them in the config file.
    sand_substitution_rate = 0.15
    coal_substitution_rate = 0.30

    if k == 'glass fiber reinforced polymer' and stage == 'cement co-processing':
        fd_cur2 = fd_cur2.reset_index()
        fd_cur2.to_pickle('gfrp_cement_coprocess_stock.pickle', compression=None)
        return pd.DataFrame(), pd.DataFrame()


    # The problem of concrete emission where emission is dependant upon the value of glass fiber available in the system'
    elif k == 'concrete':
        # TODO: consider explaining how "foreground_process_inventory.csv" is
        #  loaded since it seems to be in another directory than this module
        #  (../celavi-data/pylca_celavi_data instead of
        #  ../celavi/celavi/pylca_celavi)
        df_static = pd.read_csv('foreground_process_inventory.csv')
        year_of_concrete_demand = yr

        # Reading gfrp storage variable in pickle from previous runs
        gfrp_storage = pd.read_pickle('gfrp_cement_coprocess_stock.pickle')
        year_of_storage = gfrp_storage['year'][0]

        # Subtracting the year of demand and storage
        # Only 1 year of storage is allowed
        # TODO: consider having storage as an input of the function with a
        #  default value and possibly a user input defined in the config file.
        if year_of_concrete_demand - year_of_storage < 1:
            available_gfrp = gfrp_storage['flow quantity'][0]

        else:
            available_gfrp = 0

        req_conc_df = fd_cur2[fd_cur2['material'] == k].reset_index()
        required_concrete = req_conc_df['flow quantity'][0]

        # sand update
        # TODO: consider replacing 0.84 by an input of the function (e.g.,
        #  concrete_sand_requirement) and assign 0.84 as the default value.
        #  Also consider adding concrete_sand_requirement as a user input
        #  (with defaults value) and place it in the config file.
        required_sand = required_concrete * 0.84
        # 0.84 is the amount of sand required for 1kg concrete

        sand_can_be_substituted = required_sand * sand_substitution_rate

        # if less GFrp is available than what can be substituted then complete GFRP can be used to substitute
        if available_gfrp <= sand_can_be_substituted:
            sand_substituted = available_gfrp
        else:
            sand_substituted = sand_can_be_substituted

        required_sand = required_sand - sand_substituted

        new_sand_inventory_factor = required_sand/required_concrete
        # updating the inventory

        # TODO: consider adding a comment line regarding what file to use and
        #  where it is located. In the "develop" celavi-data repo, the
        #  foreground_process_inventory.csv does not contain a process named
        #  'concrete, cement co-processing'. (I see "concrete, in use").
        #  Or maybe I am misunderstanding something.
        df_static.loc[((df_static['product'] == 'sand and gravel') & (df_static['process'] == 'concrete, cement co-processing')), 'value'] = new_sand_inventory_factor

        # coal update
        # TODO: consider replacing 0.0096291 by an input of the function
        #  and assign 0.0096291 as the default value. Also consider adding as
        #  a user input (with defaults value) and place it in the config file.
        required_coal = required_concrete * 0.0096291
        '0.009629 is the amount of coal required for 1kg concrete'

        coal_can_be_substituted = required_coal * coal_substitution_rate

        'if less GFRP is available than what can be substituted then complete GFRP can be used to substitute'
        if available_gfrp <= coal_can_be_substituted:
            coal_substituted = available_gfrp
        else:
           coal_substituted = coal_can_be_substituted

        required_coal = required_coal - coal_substituted
        'subtracting the amount of GFRP available with a substitution factor'

        new_coal_inventory_factor = required_coal / required_concrete
        # TODO: consider adding a comment line regarding what file to use and
        #  where it is located. In the "develop" celavi-data repo, the
        #  foreground_process_inventory.csv does not contain a process named
        #  'concrete, cement co-processing'. (I see "concrete, in use").
        #  Or maybe I am misunderstanding something.
        df_static.loc[((df_static['product'] == 'coal, raw') & (df_static['process'] == 'concrete, cement co-processing')), 'value'] = new_coal_inventory_factor
        'updating inventory'

        # carbon dioxide update
        # TODO: consider replacing magic numbers by inputs of the function.
        #  Also consider adding them as user inputs (with defaults values) and
        #  place it in the config file.
        new_co2_emission_factor = 0.00092699 / 0.0096291 * new_coal_inventory_factor
        # These numbers are all obtained from the inventory which says that the use of 0.0096291 kg coal will cause 0.000926 kg Co2 emission
        # This co2 emission only includes the coal combustion impact factor. Other fuels need to be added separately
        df_emissions = pd.read_csv('emissions_inventory.csv')
        df_emissions.loc[((df_emissions['product'] == 'carbon dioxide') & (df_emissions['process'] == 'concrete, in use')), 'value'] = new_co2_emission_factor
        return df_static, df_emissions

    else:

        df_static = pd.read_csv('foreground_process_inventory.csv')
        df_emissions = pd.read_csv('emissions_inventory.csv')
        return df_static, df_emissions
