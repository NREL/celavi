import sys
from numpy import random
import numpy as np
import secrets
import pandas as pd
import uuid
import pickle
import yaml
import os
import time
from celavi.pylca_celavi.liaison.montecarloforeground import mc_foreground
from celavi.pylca_celavi.liaison.lci_calculator import brightway,search_dictionary,lcia_traci_run,lcia_recipe_run, lcia_premise_gwp_run
from celavi.pylca_celavi.liaison.search_activity_ecoinvent_for_editing import search_activity_in_ecoinvent_for_editing



def main_run(lca_project,updated_project_name,results_filename,regional_sensitivity_flag,region,data_dir,primary_process,process_under_study,location_under_study,updated_database,functional_unit,inventory_filename,process_name_bridge,emission_name_bridge,bw):

    """
    This function defines the result arrays and then calls monte carlo analysis if required or just runs the 
    LCIA run once for analysis. 


    Parameters
    ----------
    project: str
        project name as provided by user        
    
    results_filename : str
        filename for the result         
    
    mc_foreground_flag : boolean 
        boolean for monte carlo simulation to operate

    lca_flag : boolean 
        boolean for Life cycle analysis to operate
        
    primary_process : str
       the process under LCA study  

    location_under_study : str
        location of the process under stidy

    updated_database : str
       database name for scenario and year
        
    mc_runs : int
       number of monte carlo runs       
        
    inventory_filename : str
        filename for the process foreground inventory  

    modification_inventory_filename: str
        filename for the process inventory that will be modified inside ecoinvent      
    
    process_name_bridge : str
        filename for the link between common process names and ecoinvent process names    
    
    emission_name_bridge : str
        filename for the link between common emission names and ecoinvent emission names
    
    location_name_bridge : str
       filename for the link between common location names and ecoinvent location names
    
    output_dir : str
       output directory for saving results       
    
    bw: module
       brightway2 module

    Returns
    -------
    None
    """
    

    
    
    print('\n')
    print(updated_database,flush=True)
    print("Staring LCA runs", flush=True)
    print('\n')
    'remove all uncertainty from the background with this command'
    #remove_background_uncertainty(db) 
    yr = updated_database[10:14]
    scenario = updated_database[15:]
    number = str(secrets.token_hex(8))
    mc_foreground_flag = False
    mc_runs = 0

    def lca_runner(db,r,mc_runs,mc_foreground_flag,lca_flag,functional_unit,process_under_study,location_under_study,run_filename):


            lcia_result = {}
            lcia_df = pd.DataFrame()
            lcia = []
            value = []
            unit = []
            year = []
            method = []
        
            """
            This function defines the result arrays and then calls monte carlo analysis if required or just runs the 
            LCIA run once for analysis. 
    
    
            Parameters
            ----------
            db : 
                ecoinvent database name under study with scenario and year        
            
            r : str
                blank for normal runs or numerical for monte carlo simulation number          
    
            Returns
            -------
            None
            """

            # This function creates a dictionary from ecoinvent for searching for activities.
            dictionary = search_dictionary(db,run_filename,mc_foreground_flag,mc_runs,process_name_bridge,emission_name_bridge,bw)                   
            run_filename = search_activity_in_ecoinvent_for_editing(dictionary,process_under_study,location_under_study,process_name_bridge,emission_name_bridge,run_filename,data_dir)
            dictionary = brightway(db,run_filename,mc_foreground_flag,mc_runs,process_name_bridge,emission_name_bridge,bw)
            print('Activity created and saved success',flush=True)



            result_dir1, n_lcias1 = lcia_traci_run(db, dictionary[process_under_study+'@'+location_under_study], float(functional_unit),
                                                   mc_foreground_flag, mc_runs, bw)
            result_dir2, n_lcias2 = lcia_recipe_run(db, dictionary[process_under_study+'@'+location_under_study], float(functional_unit),
                                                    mc_foreground_flag, mc_runs, bw)
            #result_dir3, n_lcias3 = lcia_premise_gwp_run(db, dictionary[process_under_study+'@'+location_under_study], float(functional_unit),
            #                                       mc_foreground_flag, mc_runs, bw)

            result_dir3 = {}
            n_lcias3 = 0
            temp1= pd.DataFrame.from_dict(result_dir1,orient='index')
            temp2= pd.DataFrame.from_dict(result_dir2,orient='index')
            temp3= pd.DataFrame.from_dict(result_dir3,orient='index')
            
            for count in range(0,n_lcias1):
                    #not implemented
                    monteC = False
                    if monteC:#not implemented
        
                            mc_runs = temp1['result'][0][count][1]
                            for mc in mc_runs:
                                    lcia.append(temp1['result'][0][count][0])
                                    value.append(mc)
                                    unit.append(temp1['result'][0][count][2])
                                    year.append(db)
                                    method.append('TRACI2.1')
                    
                    else:
        
                            lcia.append(temp1['result'][0][count][0])
                            value.append(temp1['result'][0][count][1])
                            unit.append(temp1['result'][0][count][2])
                            year.append(db)
                            method.append('TRACI2.1')
        
        
        
        
            for count in range(0,n_lcias2):
        
        
                    #not implemented
                    monteC = False
                    if monteC:#not implemented
        
                        mc_runs = temp2['result'][0][count][1]
                        for mc in mc_runs:
                                lcia.append(temp2['result'][0][count][0])
                                value.append(mc)
                                unit.append(temp2['result'][0][count][2])
                                year.append(db)
                                method.append('RECIPE')   
        
                    else:
        
                        lcia.append(temp2['result'][0][count][0])
                        value.append(temp2['result'][0][count][1])
                        unit.append(temp2['result'][0][count][2])
                        year.append(db)
                        method.append('RECIPE')
                          
            for count in range(0,n_lcias3):
        
        
                    #not implemented
                    monteC = False
                    if monteC:#not implemented
        
                        mc_runs = temp3['result'][0][count][1]
                        for mc in mc_runs:
                                lcia.append(temp3['result'][0][count][0])
                                value.append(mc)
                                unit.append(temp3['result'][0][count][2])
                                year.append(db)
                                method.append('IPCC 2013')   
        
                    else:
        
                        lcia.append(temp3['result'][0][count][0])
                        value.append(temp3['result'][0][count][1])
                        unit.append(temp3['result'][0][count][2])
                        year.append(db)
                        method.append('IPCC 2013')

                              
            
            lcia_df = pd.DataFrame(
                {'lcia': lcia,
                 'value': value,
                 'unit': unit,
                 'year': year,
                 'method': method     
                })    
            #lcia_df.to_csv(results_filename+str(r)+db+primary_process+'.csv',index = False)
            print('LCIA is written')
            #lcia_df.to_csv(results_filename+str(r)+db+primary_process+'.csv',index = False)
            return lcia_df


      
    if mc_foreground_flag:
         
        lcia_df = lca_runner(updated_database,r,mc_runs,mc_foreground_flag,True,functional_unit)
    

    elif regional_sensitivity_flag:

        file = inventory_filename
        file['process_location'] = location_under_study
        file['supplying_location'] = location_under_study
        print('Regional Sensitivity analysis starts')
        run_filename = os.path.join(data_dir,'sensitivity_regional'+updated_database+str(yr)+'.csv')
        file.to_csv(run_filename,index = False) 
        run_filename = file

        r = ''    
        lcia_df = lca_runner(updated_database,r,mc_runs,mc_foreground_flag,True,functional_unit)

    else:
        
        run_filename = inventory_filename
        r = ''
        lcia_df = lca_runner(updated_database,r,mc_runs,mc_foreground_flag,True,functional_unit,process_under_study,location_under_study,run_filename)

    return lcia_df
            


