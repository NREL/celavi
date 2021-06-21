import pandas as pd
from .pylca_opt_foreground import model_celavi_lci
from .insitu_emission import model_celavi_lci_insitu
import sys
from .pylca_opt_background import model_celavi_lci_background

# Concrete lifecycle inventory updater
from .concrete_life_cycle_inventory_editor import concrete_life_cycle_inventory_updater

# Background LCA runs on the USLCI after the foreground process
from .pylca_celavi_background_postprocess import postprocessing


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


def pylca_run_main(df):

    # '''ALICIA replace this part with the dataframe you are sending'''
    # '''Delete this line after integration'''
    # df  = pd.read_csv('data_for_lci_test.csv')
    
    df = df[df['flow quantity'] != 0]
    
   
    
    res_df = pd.DataFrame()
    df=df.reset_index()
    
    for index,row in df.iterrows():
        new_df = df[df['index'] == index]
        year = row['year']
        stage = row['stage']
        material = row['material']
        facility_id = row['facility_id']
    
    
    
    
        'Correcting life cycle inventory with material is concrete'
        # Calculates the concrete lifecycle flow and emissions inventory
        df_static,df_emissions = concrete_life_cycle_inventory_updater(new_df, year, material, stage)
     
        if not df_static.empty:
            new_df['flow name'] = new_df['material'] + ', ' + new_df['stage']
            new_df= new_df[['flow name','flow quantity']]

            # model_celavi_lci() is calculating foreground processes and dynamics of electricity mix.
            # It calculates the LCI flows of the foreground process.
            res = model_celavi_lci(new_df,year,facility_id,stage,material,df_static)

            # model_celavi_lci_insitu() calculating direct emissions from foreground
            # processes.
            emission = model_celavi_lci_insitu(new_df,year,facility_id,stage,material,df_emissions)

            if not res.empty:
                res = model_celavi_lci_background(res,year,facility_id,stage,material)               
                res = postprocessing(res,emission)            
                res_df = pd.concat([res_df,res])
    
    # The line below is just for debugging if needed
    # res_df.to_csv('final_lcia_results_to_des.csv',index = False)

    # This is the result that needs to be analyzed every timestep.
    return res_df
           

