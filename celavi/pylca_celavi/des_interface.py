# TODO: Add a short module docstring above the code to:
#  1) provide authors, date of creation
#  2) give a high level description (2-3 lines) of what the module does
#  3) write any other relevant information

# TODO: if sys is not used, consider removing
import pandas as pd
from celavi.pylca_celavi.pylca_opt_foreground import model_celavi_lci
from celavi.pylca_celavi.insitu_emission import model_celavi_lci_insitu
import sys
import os
from celavi.pylca_celavi.pylca_opt_background import model_celavi_lci_background

# Concrete lifecycle inventory updater
from celavi.pylca_celavi.concrete_life_cycle_inventory_editor import concrete_life_cycle_inventory_updater

# Background LCA runs on the USLCI after the foreground process
from celavi.pylca_celavi.pylca_celavi_background_postprocess import postprocessing, impact_calculations


# TODO: Consider detailing what "something" is in "something for debugging
#  purposes"
"""
concrete_life_cycle_inventory_updater() reads:
    - foreground_process_inventory.csv (needs only to be read once)
    - emissions_inventory.csv  (needs only to be read once)
    
concrete_life_cycle_inventory_updater() writes:
    - gfrp_cement_coprocess_stock.pickle (for the stock variable, may be overwritten at every timestep)
    
model_celavi_lci() reads:
    - dynamic_secondary_lci_foreground.csv (needs only to be read once)
    
model_celavi_lci() writes:
    - intermediate_demand.csv (for debugging, overwritten at every timestep)
    
model_celavi_lci_insitu() uses no files.

model_celavi_lci_background() reads:
    - usnrellci_processesv2017_loc_debugged.pickle (needs only to be read once)
    - location.csv (needs only to be read once)
    
model_celavi_lci_background() writes:
    - something for debugging purposes.
    
postprocessing() reads:
    - traci21.csv (needs only to be read once)
    
postprocessing() writes:
    - nothing
"""


try:
    os.remove('final_lcia_results_to_des.csv')
    print('old lcia results file deleted')
except:
    pass
    


def lca_performance_improvement(df):
    # TODO: add docstrings to explain input variables and what the function
    #  does.
    try:
        db = pd.read_csv('lca_db.csv')
        db.columns = ['year', 'stage', 'material', 'flow name', 'emission factor kg/kg']
        db = db.drop_duplicates()
        df2 = df.merge(db, on=['year', 'stage', 'material'], how='outer', indicator=True)
        # TODO: consider adding a comment line to explain operation below
        df_with_lca_entry = df2[df2['_merge'] == 'both'].drop_duplicates()


        # TODO: consider adding a comment line to explain operation below
        df_with_no_lca_entry = df2[df2['_merge'] == 'left_only']
        df_with_no_lca_entry = df_with_no_lca_entry.drop_duplicates()
        
        
        df_with_lca_entry['flow quantity'] = df_with_lca_entry['flow quantity'] * df_with_lca_entry['emission factor kg/kg']
        df_with_lca_entry = df_with_lca_entry[['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material']]
        result_shortcut = impact_calculations(df_with_lca_entry)
        
        return df_with_no_lca_entry, result_shortcut
    except:
        return df, pd.DataFrame()


def pylca_run_main(df):
    # TODO: add docstrings to explain input variables and what the function
    #  does.
    df = df[df['flow quantity'] != 0]    

    res_df = pd.DataFrame()
    df = df.reset_index()
    lcia_mass_flow = pd.DataFrame()

    for index, row in df.iterrows():
        
        year = row['year']
        stage = row['stage']
        material = row['material']
        facility_id = row['facility_id']
        new_df = df[df['index'] == index]
        df_with_no_lca_entry, result_shortcut = lca_performance_improvement(new_df)

        if not df_with_no_lca_entry.empty:
            # Correcting life cycle inventory with material is concrete
            # Calculates the concrete lifecycle flow and emissions inventory
            df_static, df_emissions = concrete_life_cycle_inventory_updater(new_df, year, material, stage)

            if not df_static.empty:

                working_df = df_with_no_lca_entry
                working_df['flow name'] = working_df['material'] + ', ' + working_df['stage']
                working_df = working_df[['flow name', 'flow quantity']]

                # model_celavi_lci() is calculating foreground processes and dynamics of electricity mix.
                # It calculates the LCI flows of the foreground process.
                res = model_celavi_lci(working_df, year, facility_id, stage, material, df_static)

                # model_celavi_lci_insitu() calculating direct emissions from foreground
                # processes.
                emission = model_celavi_lci_insitu(working_df, year, facility_id, stage, material, df_emissions)

                if not res.empty:
                    res = model_celavi_lci_background(res, year, facility_id, stage, material)
                    lci = postprocessing(res, emission)
                    res = impact_calculations(lci)
                    res_df = pd.concat([res_df, res])
                    lcia_mass_flow = pd.concat([lci, lcia_mass_flow])


                    df_with_no_lca_entry = df_with_no_lca_entry.drop(['flow name'], axis = 1)
                    lca_db = df_with_no_lca_entry.merge(lcia_mass_flow, on=['year', 'stage', 'material'])
                    lca_db['emission factor kg/kg'] = lca_db['flow quantity_y'] / lca_db['flow quantity_x']
                    lca_db = lca_db[['year', 'stage', 'material', 'flow name', 'emission factor kg/kg']]
                    lca_db = lca_db[lca_db['material'] != 'concrete']
                    lca_db['year'] = lca_db['year'].astype(int)
                    lca_db = lca_db.drop_duplicates()
                    lca_db.to_csv('lca_db.csv', mode='a', index=False, header=False)

        else:
                print(str(facility_id) + ' - ' + str(year) + ' - ' + stage + ' - ' + material + ' shortcut calculations done', flush=True)
                

        res_df = pd.concat([res_df, result_shortcut])

    

    #Correcting the units for LCIA results. 
    for index, row in res_df.iterrows():

        # TODO: Consider adding a comment line. Why row[4]? Why not row[3] or
        #  row[n]?
        a = row[4]

        try:
            split_string = a.split("/kg", 1)
            res_df = res_df.replace(a, split_string[0] + split_string[1])
            # TODO: consider removing commented lines below
            #res_df.iloc[index,[4]] = split_string[0] + split_string[1]
            #print(split_string)
        except:
            split_string = a.split("/ kg", 1)
            res_df = res_df.replace(a, split_string[0] + split_string[1])
            # TODO: consider removing commented lines below
            #res_df.iloc[index,[4]] = split_string[0] + split_string[1]





    # TODO: consider removing commented lines below
    #res_df.to_csv('final_lcia_results_to_des.csv', header=False, index=False)
       
    # The line below is just for debugging if needed
    res_df.to_csv('final_lcia_results_to_des.csv', mode='a', header=False, index=False)

    # This is the result that needs to be analyzed every timestep.
    return res_df
           

