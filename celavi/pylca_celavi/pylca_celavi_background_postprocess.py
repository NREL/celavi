import pickle
import sys
import pandas as pd
import warnings
warnings.filterwarnings("ignore")
import os


def postprocessing(final_res,insitu):
    #Giving names to the columns for the final result file
    column_names = ['flow name','flow unit','flow quantity','year','facility_id','stage','material']
    final_res.columns = list(column_names)
    
   
    
    if insitu.empty == False:
        insitu.columns = list(column_names)
        #Adding up the insitu emission primariy for the cement manufacturing process
        final_res['flow name'] = final_res['flow name'].str.lower()
        
        column_names = ['flow name','flow unit','year','facility_id','stage','material']
        total_em = insitu.merge(final_res,on = column_names,how = 'outer')
        total_em = total_em.fillna(0)
        total_em['flow quantity'] = total_em['flow quantity_x'] + total_em['flow quantity_y']
        final_res = total_em.drop(columns = ['flow quantity_x','flow quantity_y'])
        
    return final_res


def impact_calculations(final_res):    
   
     
   
    traci = pd.read_csv('traci21.csv')
    traci = traci.fillna(0)
    impacts = list(traci.columns)
    valuevars = ['Global Warming Air (kg CO2 eq / kg substance)',
     'Acidification Air (kg SO2 eq / kg substance)',
     'HH Particulate Air (PM2.5 eq / kg substance)',
     'Eutrophication Air (kg N eq / kg substance)',
     'Eutrophication Water (kg N eq / kg substance)',
     'Ozone Depletion Air (kg CFC-11 eq / kg substance)',
     'Smog Air (kg O3 eq / kg substance)',
     'Ecotox. CF [CTUeco/kg], Em.airU, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.airC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.fr.waterC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.sea waterC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.nat.soilC, freshwater',
     'Ecotox. CF [CTUeco/kg], Em.agr.soilC, freshwater',
     'Human health CF  [CTUcancer/kg], Emission to urban air, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to urban air, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. rural air, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. rural air, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. freshwater, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. freshwater, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. sea water, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. sea water, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. natural soil, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. natural soil, non-canc.',
     'Human health CF  [CTUcancer/kg], Emission to cont. agric. Soil, cancer',
     'Human health CF  [CTUnoncancer/kg], Emission to cont. agric. Soil, non-canc.']
    
    
    traci_df = pd.melt(traci, id_vars=['CAS #','Formatted CAS #','Substance Name'], value_vars=valuevars, var_name='impacts', value_name='value')
    
    final_res['flow name'] =   final_res['flow name'].str.upper()                                 
    df_lcia = final_res.merge(traci_df, left_on = ['flow name'], right_on = ['Substance Name'])
    df_lcia['impact'] = df_lcia['flow quantity'] * df_lcia['value']
    df_lcia = df_lcia.groupby(['year','facility_id', 'material','stage','impacts'])['impact'].agg('sum').reset_index()
    
    return df_lcia                      
    #impacts = ['Global Warming Air (kg CO2 eq / kg substance)']   
    '''                                
    for im in valuevars:
       df =  traci_df[traci_df['impacts'] == im] 
       graph_df_lcia = final_lci_result.merge(df, left_on = ['flow name'], right_on = ['Substance Name'])
       
       graph_df_lcia = graph_df_lcia.groupby(['year', 'material','stage','scenario', 'coarse grinding location',
           'distance to recycling facility', 'distance to cement plant',
           'flow unit', 'impacts'])['impact'].agg('sum').reset_index()

    '''