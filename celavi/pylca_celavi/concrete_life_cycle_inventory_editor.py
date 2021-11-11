import pandas as pd


def concrete_life_cycle_inventory_updater(fd_cur2,yr,k,stage):
    
    """Modifies static LCI based on availability of GFRP at the cement processing stage 
    and demand of concrete in the system"""
    
    """GFRP may or may not be available in the system every year. If GFRP is available when 
    concrete required a stock variable is ceated to store GFRP and used in later years 
    for cement co processing"""
    
    """
    Parameters
    __________
    df row from DES model with material, quantity, year, stage etc. 
    substitution rate of sand, coal and emissions change due to use of GFRP in cement co processing. 
    
    Returns
    _______
    updated static inventory with changes due to concrete demand and GFRP availability.
    emissions inventory
    """
    
    
    
    
    sand_substitution_rate = 0.15
    coal_substitution_rate = 0.30

    if k == 'glass fiber reinforced polymer' and stage == 'cement co-processing':
        fd_cur2 = fd_cur2.reset_index()
        fd_cur2.to_pickle('gfrp_cement_coprocess_stock.pickle',compression = None)
        return pd.DataFrame(), pd.DataFrame()


    #The problem of concrete emission where emission is dependant upon the value of glass fiber availalbe in the system'
    elif k == 'concrete':
        df_static = pd.read_csv('foreground_process_inventory.csv')
        year_of_concrete_demand = yr

        # Reading gfrp storage variable in pickle from previous runs
        gfrp_storage = pd.read_pickle('gfrp_cement_coprocess_stock.pickle')
        year_of_storage = gfrp_storage['year'][0]

        # Subtracting the year of demand and storage
        # Only 1 year of storage is allowed
        if year_of_concrete_demand - year_of_storage < 1:
            available_gfrp = gfrp_storage['flow quantity'][0]

        else:
            available_gfrp = 0

        req_conc_df = fd_cur2[fd_cur2['material'] == k].reset_index()
        required_concrete = req_conc_df['flow quantity'][0]

        # sand update
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

        df_static.loc[((df_static['product'] == 'sand and gravel') & (df_static['process'] == 'concrete, cement co-processing')),'value'] =   new_sand_inventory_factor

        # coal update
        required_coal = required_concrete*0.0096291
        '0.009629 is the amount of coal required for 1kg concrete'

        coal_can_be_substituted = required_coal * coal_substitution_rate

        'if less GFRP is available than what can be substituted then complete GFRP can be used to substitute'
        if available_gfrp <= coal_can_be_substituted:
            coal_substituted = available_gfrp
        else:
           coal_substituted = coal_can_be_substituted

        required_coal = required_coal - coal_substituted
        'subtracting the amount of GFRP available with a substitution factor'

        new_coal_inventory_factor = required_coal/required_concrete
        df_static.loc[((df_static['product'] == 'coal, raw') & (df_static['process'] == 'concrete, cement co-processing')),'value'] =   new_coal_inventory_factor
        'updating inventory'

        # carbon dioxide update
        new_co2_emission_factor = 0.00092699/0.0096291 * new_coal_inventory_factor
        # These numbers are all obtained from the inventory which says that the use of 0.0096291 kg coal will cause 0.000926 kg Co2 emission
        # This co2 emission only includes the coal combustion impact factor. Other fuels need to be added separately
        df_emissions = pd.read_csv('emissions_inventory.csv')
        df_emissions.loc[((df_emissions['product'] == 'carbon dioxide') & (df_emissions['process'] == 'concrete, in use')),'value'] = new_co2_emission_factor
        return df_static,df_emissions

    else:

        df_static = pd.read_csv('foreground_process_inventory.csv')
        df_emissions = pd.read_csv('emissions_inventory.csv')
        return df_static,df_emissions
