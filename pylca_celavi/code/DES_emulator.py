import pandas as pd
from pylca_opt_foreground_multi import model_celavi_lci
from insitu_emission import model_celavi_lci_insitu
import sys
from pylca_opt_celavi_integrated_uslci_multi import model_celavi_lci_background
from concrete_life_cycle_inventory_editor import concrete_life_cycle_inventory_updater
from pylca_celavi_background_postprocess import postprocessing

#Reading Results data 
df  = pd.read_csv('data_for_lci.csv')

df = df[df['flow quantity'] != 0]

#Units are in tonne chaging to kg as units in lci inventory as all based on kg

df['flow quantity'] = df['flow quantity'] * 1000


year = list(pd.unique(df['year']))


sand_substitution_rate = 0.15
coal_substitution_rate = 0.30


res_df = pd.DataFrame()
df=df.reset_index()

for index,row in df.iterrows():
    new_df = df[df['index'] == index]
    year = row['year']
    stage = row['stage']
    material = row['material']




    'Correcting life cycle inventory with material is concrete'
    df_static,df_emissions = concrete_life_cycle_inventory_updater(new_df, year, material, stage, sand_substitution_rate,coal_substitution_rate)
   
    if df_static.empty == False:
        
        new_df['flow name'] = new_df['material'] + ', ' + new_df['stage']
        new_df= new_df[['flow name','flow quantity']]
        
        res = model_celavi_lci(new_df,year,stage,material,df_static)
        emission = model_celavi_lci_insitu(new_df,year,stage,material,df_emissions)
        
        if res.empty == False:
            res = model_celavi_lci_background(res,year,stage,material)               
            res = postprocessing(res,emission)            
            res_df = pd.concat([res_df,res])
            
    
                
            
           

