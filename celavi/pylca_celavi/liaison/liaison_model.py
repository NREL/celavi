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
from celavi.pylca_celavi.liaison.lci_calculator import liaison_calc,search_dictionary,search_index_reader,lcia_traci_run,lcia_recipe_run, lcia_premise_gwp_run
from celavi.pylca_celavi.liaison.search_activity_ecoinvent import search_activity_in_ecoinvent
from celavi.pylca_celavi.liaison.edit_activity_ecoinvent import modify_electricity_grid_mix_and_solar_glass_removal,module_required_for_solar_glass,module_installation_for_solar_glass,window_frame,landfilling_functional_unit,module_disassembly_glass_content


def main_run(lca_project,updated_project_name,year_of_study,results_filename,mc_foreground_flag,lca_flag,region_sensitivity_flag,edit_ecoinvent_user_controlled,region,data_dir,input_dir,primary_process,process_under_study,location_under_study,unit_under_study,updated_database,mc_runs,functional_unit,inventory_filename,output_dir,bw):

    """
    This function defines the result arrays and then calls monte carlo analysis if required or just runs the 
    LCIA run once for analysis. 


    Parameters
    ----------
    lca_project: str
        project name as provided by user  

    updated_project_name: str
        updated project name for the updated databases  
    
    year_of_study: str
        year of analysis
        
    results_filename : str
        filename for the result         
    
    mc_foreground_flag : boolean 
        boolean for monte carlo simulation to operate

    lca_flag : boolean 
        boolean for Life cycle analysis to operate

    region_sensitivity_flag: boolean
        boolean for regional sensitivity analysis

    region: str
        name of region for sensitivity analysis
        
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

    def lca_runner(db,r,mc_runs,mc_foreground_flag,lca_flag,functional_unit,run_filename):


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
            db : str
                ecoinvent database name under study with scenario and year        
            
            r : str
                blank for normal runs or numerical for monte carlo simulation number          
    
            Returns
            -------
            None
            """

            # This function creates a dictionary from ecoinvent for searching for activities.
            process_dictionary = search_dictionary(db,bw)                   
            # This function searches for the primary process under study in ecoinvent. If found we extract it. 
            # dictionary or string
            searched_item = search_activity_in_ecoinvent(process_dictionary,process_under_study,location_under_study,unit_under_study,run_filename,data_dir)
            
            if type(searched_item) == str:
                # Reading from the inventory csv files
                print('Using the provided inventory files',flush = True)
                print('Reading from ' + run_filename,flush = True)
                inventory = pd.read_csv(run_filename) #dataframe
                # Updating the location in the additional inventories file
                inventory['process_location'] = location_under_study
                inventory['supplying_location'] = location_under_study
                #inventory is a dataframe
                process_dictionary = liaison_calc(db,inventory,bw)
                functional_unit =  module_disassembly_glass_content(process_under_study,year_of_study,functional_unit,input_dir)

            else:
                inventory = searched_item  #dictionary
                # Activity may be edited according to user preferences
                if edit_ecoinvent_user_controlled  == True:  

                    #inventory here has to be a dictionary. So if we read inventory from csv file we cannot edit it.             
                    
                    #Editing the functional unit for solar module manufacturing
                    functional_unit = module_required_for_solar_glass(inventory,year_of_study,functional_unit,input_dir)

                    #Editing the functional unit for solar module installation
                    functional_unit = module_installation_for_solar_glass(inventory,year_of_study,functional_unit,input_dir)

                    # Editing the functional unit for window frame manufacturing
                    functional_unit = window_frame(inventory,year_of_study,functional_unit)

                    # Editing the functional unit for landfilling
                    functional_unit = landfilling_functional_unit(inventory,functional_unit)
                    
                    #Editing electricity grid mix for all processes so that electricity is obtained from the state grid from ReEDS grid mix data
                    run_filename = modify_electricity_grid_mix_and_solar_glass_removal(inventory,year_of_study,location_under_study,data_dir)
                    
                    print('Activity edited according to user prereferences and saved success',flush=True)  
                    #run_filename is a dataframe.
                    process_dictionary = liaison_calc(db,run_filename,bw)

            if lca_flag: 

                activity_lca = search_index_reader(process_under_study,location_under_study,unit_under_study,process_dictionary)
                result_dir1,n_lcias1 = lcia_traci_run(db,activity_lca,functional_unit,mc_foreground_flag,mc_runs,bw)
                result_dir2,n_lcias2 = lcia_recipe_run(db,activity_lca,functional_unit,mc_foreground_flag,mc_runs,bw)
                #result_dir3,n_lcias3 = lcia_premise_gwp_run(db,dictionary[process_under_study],1,mc_foreground_flag,mc_runs,bw)
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
                
                #lcia_df.to_csv(output_dir+results_filename+str(r)+db+primary_process+'.csv',index = False)
                print("LCA performed succesfully", flush= True)

                save_project = False
                if save_project == True:
                
                        time0 = time.time()
                        try:
                                import bw2io
                                bw2io.backup.backup_project_directory(project_name)
                                print(bw2io.backup.backup_project_directory(project_name))
                                print('saved successfully', flush = True)
                                print('Time taken for saving project'+str(time.time() - time0))


                        except:
                                print('failed to backup project')

                return lcia_df
       
      
    if mc_foreground_flag:
         
        lca_runner(updated_database,r,mc_runs,mc_foreground_flag,lca_flag,functional_unit)
    

    elif region_sensitivity_flag:

        file = pd.read_csv(inventory_filename)
        file['process_location'] = region
        file['supplying_location'] = region
        print('Regional Sensitivity analysis starts')
        run_filename = os.path.join(data_dir,'sensitivity_regional'+updated_database+str(yr)+'.csv')
        file.to_csv(run_filename,index = False)
        r = ''    
        lca_runner(updated_database,r,mc_runs,mc_foreground_flag,lca_flag,functional_unit)

    else:
        
        run_filename = inventory_filename
        r = ''
        lcia_df = lca_runner(updated_database,r,mc_runs,mc_foreground_flag,lca_flag,functional_unit,run_filename)
        return lcia_df
            
    try:
        bw.projects.delete_project(bw.projects.current, delete_dir=True) 
        print('Deleted succesfully')
        #bw.projects.purge_deleted_directories()
    except:
        print('There was an issue with deletion')
        #bw.projects.purge_deleted_directories()

