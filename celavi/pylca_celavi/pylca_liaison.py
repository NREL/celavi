import pandas as pd
import numpy as np
import time
from celavi.pylca_celavi.liaison.liaison_model import main_run
import secrets
import random
import logging


def liaison_lci(
    f_d,
    yr,
    fac_id,
    stage,
    material,
    unit,
    route_id,
    state,
    verbose,
    bw
    ):
    """
    Creates the technology matrix for the foreground inventory and the final demand vector based on input data. 
    Performs necessary checks before and after the LCA calculation. 
    Checks performed 
    1. Final demand by the foreground system is not zero. If zero, returns empty dataframe and simulation continues without breaking code. 
    2. Checks the LCA solver returned a proper dataframe. If empty dataframe is returned, it attaches column names to the dataframe and code continues without breaking. 
    
    Parameters
    ----------
    f_d: pd.Dataframe
        Dataframe from DES interface containing foreground material flows.
    yr: int
        Model year.
    fac_id: int
        Facility id.
    stage: str
        Supply chain stage.
    material: str
        Material being processed.
    unit: str
        Unit of material processed
    route_id: str
        Unique identifier for transportation route.
    state: str
        State in which calculations are taking place.       
    verbose: int
        Controls the level of progress reporting from this method.

    Returns
    -------
    res2: pd.DataFrame
       Demand of materials by the foreground system to the background system in a properly arranged dataframe with all supplemental information.
       Columns are reorganized, column names are changed and column number check is performed before returning. 
       Columns:
            - flow name: str
            - flow unit: str
            - flow quantity: float
            - year: int
            - facility_id: int
            - stage: str
            - material: str
            - route_id: int
            - state: str
    """
    f_d = f_d.drop_duplicates()
    f_d = f_d.dropna()
    print(yr)
    print(fac_id)
    print(stage)
    print(material)
    print(route_id)
    print(state) 


    tim0 = time.time()

    # This part of the code helps to change the years if less than 2024 to 2024
    # Also since ReEDS mix and LCA project databases are not available for every year, we are 
    # trying to change the years to even numbers at 4 years gaps. We need to create the databases at every 2 year gap. 
    if yr<2024:
        year_from_celavi = 2024
    else:
        print('year to change',yr)
        if yr%2 == 0:
            year_from_celavi = yr
        else:
            year_from_celavi = yr-yr%2
    print('year changed from ',yr,year_from_celavi)
    
    # Sanity Check to make sure LCA dataframe from CELAVI only contains one row. 
    if len(f_d) > 1:
        print('ISSUE- More than one line in the input dataframe')
    else:
        f_d = f_d.reset_index()
        process_for_lca = f_d['flow name'][0]
        value_from_celavi = f_d['flow quantity'][0]


    # Not sure why I changed state to a list and then loop through the list. Can be changed to directly storing the variable. 
    state_from_celavi = [state]

    liaison_process_bridge_dir = "/kfs2/projects/celavicf/celavi-master/celavi-data/inputs/"
    liaison_process_bridge = pd.read_csv(liaison_process_bridge_dir+'liaison_process_bridge.csv')
    selected_process = liaison_process_bridge[liaison_process_bridge['Activities'] == stage]
    selected_process = selected_process[['Activities','Ecoinvent','Unit','Celavi Unit']].dropna()
    
    if len(selected_process) == 1:
        #Check passed
        selected_process = selected_process.reset_index()
        process_in_ecoinvent_for_lca_from_celavi = selected_process.loc[0,'Ecoinvent']
        unit_under_study = selected_process.loc[0,'Unit']
        celavi_unit = selected_process.loc[0,'Celavi Unit']

        # Validity check for unit
        if unit != celavi_unit:
            logging.error("Units from DES did not match units from Ecoinvent")

        #These data directories are relevant to LiAISON. 
        #inventory_to_be_built_from_celavi = pd.read_csv('/kfs2/shared-projects/liaison/liaison_reeds/data/inputs/example.csv')
        data_dir = "/kfs2/projects/celavicf/celavi-master/celavi-data/generated/"
        output_dir = "/kfs2/projects/celavicf/celavi-master/"

        #These are two ways in which LCA can be performed. 
        #1. One where the activity is present in Ecoinvent. We need to extract it, edit it and then do LCA.
        #2. The Activity does not exist in Ecoinvent at all. This has not been modeled yet as this will need csv files. 
        # For these activities we need to create the csv files and if these activities are not found in Ecoinvent, we should read the csv files. 
        # Right now, the dataframe being read is empty. 
        inventory_to_be_built_from_celavi = pd.DataFrame(columns=['process', 'flow', 'value', 'unit', 'input', 'year', 'comments', 'type',
               'process_location', 'supplying_location'])
        inventory_to_be_built_from_celavi = "additional_inventories"+".csv"
        
        # These project names match to the project names of HIPSTER and need to be added to the yaml file
        updated_project_name='Mid_Case'+str(year_from_celavi)
        updated_database='premise_base'
        lca_project='Mid_Case_celavi'+str(year_from_celavi)

        def correct_natural_land_transformation(bw) -> None:
            """
            Corrects the namation method in the Brightway2 database.
            Removes flows not related to specific land types in a whitelist.

            Parameters:
            -----------
            bw : module
                Brightway2 module loaded as a shortcut name.
            """
            lt_methods = [m for m in bw.methods if "natural land transformation" in m[1]]
            white_list = ["forest", "grassland, natural", "sea", "ocean", "inland waterbody", "lake, natural",
                          "river, natural", "seabed, natural", "shrub land", "snow", "unspecified", "wetland", "bare area"]
            # l_flows = [cf for lt_method in lt_methods for cf in bw.Method(lt_method).load() if any(n in bw.get_activity(cf[0])["name"] for n in white_list)]
            l_flows = []
            l_flow_dic = {}
            # Iterate through each impact assessment method
            for lt_method in lt_methods:
                method = bw.Method(lt_method)  # Load the method
                cf_data = method.load()  # Retrieve the characterization factors
                
                # Iterate through each characterization factor
                for cf in cf_data:
                    activity = bw.get_activity(cf[0])  # Get the activity associated with the CF
                    activity_code = activity['code']
                    activity_name = activity["name"]  # Extract the activity name
                    # print(cf,activity_name,2)
                    
                    
                    # Check if any of the names in white_list are in the activity name
                    if any(n in activity_name for n in white_list):
                        # l_flows.append(cf)  # Append the matching characterization factor
                        l_flow_dic[activity_code] = cf
            
            l_flows = []
            #adding the l_flows to a list in a unique manner
            for l_flow_key in l_flow_dic.keys():
                l_flows.append(l_flow_dic[l_flow_key])
            for lt_method in lt_methods:
                bw.Method(lt_method).write(l_flows)


        def correct_bigcc_copper_use(bw,db):
                """
                Correction of copper use by Biomass Gasification CC plants
                """
                list_dbs = [
                db
                ]

                list_acts = [
                "electricity production, at BIGCC power plant, no CCS",
                "electricity production, at BIGCC power plant, pre, pipeline 200km, storage 1000m",
                "electricity production, at BIGCC power plant, pre, pipeline 400km, storage 3000m",
                ]

                for db in list_dbs:
                    for ds in bw.Database(db):
                        if ds["name"] in list_acts:
                                for exc in ds.exchanges():
                                    if exc["name"] == "Construction, BIGCC power plant 450MW":
                                        #print("found exchange to correct")
                                        exc["amount"] = 1.01e-11
                                        exc.save()
            
        def reset_project(updated_project_name,number,project,updated_database,bw):
                
                """
                This function copies the project directory of a certain year and scenario, for example
                ecoinvent RCP 19 2030 and creates a copy of the project using a non repeatable name
                using 


                Parameters
                ----------
                updated_project_name: str
                    new project name
                
                number : str
                    random number generated by uuid to create no duplicate databases
                
                project : str 
                    generic project name
                    
                updated_database : module
                    new database to be used within the new project for LCA
           
                Returns
                -------
                project name : str
                    Name of the project
                """

                project_name = project+"_"+number
                try:
                  print('Trying to delete project',project_name)
                  bw.projects.delete_project(project_name,delete_dir = True)
                  print('Project deleted',flush=True)
                except:
                  print('Project does not exist',flush=True)
                  pass
                bw.projects.set_current(updated_project_name)
                print("Entered project for copying databases" + updated_project_name,flush = True)
                print("Databases in this project are",flush = True)
                print(bw.databases,flush = True)
                try:
                    bw.projects.copy_project(project_name,switch = False)
                    print('Project copied successfully',flush=True)
                except:
                    bw.projects.purge_deleted_directories()
                    bw.projects.copy_project(project_name,switch = False)
                    print('Project copied successfully after directory deleted',flush=True)    

                bw.projects.set_current(project_name)
                print("Current new project " + project_name,flush = True)
                print("Databases in this project are",flush = True)    
                print(project_name,flush = True)
                print(bw.databases,flush = True)
                print('Correcting Natural Land Transformation Recipe method', flush = True)
                correct_natural_land_transformation(bw)
                print('Correcting BIG CC copper use',flush = True)
                correct_bigcc_copper_use(bw,updated_database)
                return project_name
            
        number = str(secrets.token_hex(8))
        project_name = reset_project(updated_project_name,number,lca_project,updated_database,bw)

        # Sanity Check statements
        print(process_in_ecoinvent_for_lca_from_celavi,'to do lca for',flush=True)
        print(stage,material)

        #todo
        # Not sure why it was decided to have states as a list. Can be changed and the loop may be deleted
        for st in state_from_celavi:   

            res_df = main_run(lca_project=lca_project,
                     updated_project_name=updated_project_name,
                     year_of_study=year_from_celavi,
                     results_filename='Mid_Case'+str(year_from_celavi)+st,
                     mc_foreground_flag=False,
                     lca_flag=True,
                     region_sensitivity_flag=False,
                     edit_ecoinvent_user_controlled = True,
                     region=st,
                     data_dir=data_dir,
                     primary_process=process_in_ecoinvent_for_lca_from_celavi,
                     process_under_study=process_in_ecoinvent_for_lca_from_celavi, 
                     location_under_study=st,
                     unit_under_study=unit_under_study,
                     updated_database=updated_database, 
                     mc_runs=0,
                     functional_unit=value_from_celavi,
                     inventory_filename = inventory_to_be_built_from_celavi,
                     output_dir= output_dir,
                     bw=bw)
        try:
           #Projects are deleted to save disk space
           bw.projects.delete_project(bw.projects.current, delete_dir=True) 
           print('Deleted succesfully')
           bw.projects.purge_deleted_directories()
        except:
           print('There was an issue with deletion')  
           bw.projects.purge_deleted_directories()

        #Sanity Check if LCA calculations failed
        if res_df.empty:
            print('LCA calculations failed')
            sys.exit(0)

        res_df['year']  = yr
        res_df['facility_id'] = fac_id
        res_df['stage']   = stage
        res_df['material']  = material 
        res_df['route_id']   = route_id
        res_df['state'] = state


        print('Performed lca for ',stage,' ',material,' ', state)
        print(str(time.time()-tim0),' seconds for one lca calculation of ', str(yr), stage, material) 
        print("")
        print("")

    elif len(selected_process) == 0:
        print('Missing process. Skipping LCA calculations', stage)
        res_df = pd.DataFrame()

    else:
        print(selected_process)
        print("!!!!Issue - Bridge file")
    
    return res_df,value_from_celavi
    
    # Defining a list of processes for which LCA needs to be done. 
    # This is not required and will be deleted after integration with the glass recycling model of CELAVI
    # processes_list = ["glass wool mat production","glass wool mat production, without cullet"] 
    # random_number = random.randint(0,2)
    # process_in_ecoinvent_for_lca_from_celavi = processes_list[random_number]
    


    




