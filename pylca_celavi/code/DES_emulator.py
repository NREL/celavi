import pandas as pd
from pylca_opt_foreground import model_celavi_lci
from insitu_emission import model_celavi_lci_insitu
import sys
from pylca_opt_background import model_celavi_lci_background
from concrete_life_cycle_inventory_editor import concrete_life_cycle_inventory_updater
from pylca_celavi_background_postprocess import postprocessing



def pylca_run_main(df=None):

    '''ALICIA replace this part with the dataframe you are sending'''
    '''Delete this line after integration'''
    df  = pd.read_csv('data_for_lci_test.csv')
    
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
        df_static,df_emissions = concrete_life_cycle_inventory_updater(new_df, year, material, stage)
     
        if df_static.empty == False:
            
            new_df['flow name'] = new_df['material'] + ', ' + new_df['stage']
            new_df= new_df[['flow name','flow quantity']]
            
            res = model_celavi_lci(new_df,year,facility_id,stage,material,df_static)
            emission = model_celavi_lci_insitu(new_df,year,facility_id,stage,material,df_emissions)
    
            if res.empty == False:
                res = model_celavi_lci_background(res,year,facility_id,stage,material)               
                res = postprocessing(res,emission)            
                res_df = pd.concat([res_df,res])
    
          
    res_df.to_csv('final_lcia_results_to_des.csv',index = False)
    return res_df
           

