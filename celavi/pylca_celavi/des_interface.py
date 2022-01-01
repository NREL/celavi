import pandas as pd
from celavi.pylca_celavi.pylca_opt_foreground import model_celavi_lci
from celavi.pylca_celavi.insitu_emission import model_celavi_lci_insitu
import sys
import os
from celavi.pylca_celavi.pylca_opt_background import model_celavi_lci_background

# Concrete lifecycle inventory updater
from celavi.pylca_celavi.concrete_life_cycle_inventory_editor import concrete_life_cycle_inventory_updater

# Background LCA runs on the USLCI after the foreground process
from celavi.pylca_celavi.pylca_celavi_background_postprocess import postprocessing,impact_calculations


class PylcaCelavi:
    """    
    The PylcaCelavi class 
    - Provides an object which stores the files names required for performing LCA calculations
    - Calls the main functions required for performing LCIA calculations

    Parameters
    ----------
    lca_results_filename: str
        final_lcia_results.csv Stores final results. 
    
    shortcutlca_filename: str
        lca_db.csv Stores emission factors for short cut calculations
    
    dynamic_lci_filename: str
        elec_gen_dynamic_final.csv Inventory for dynamic electricity grid mix
    
    static_lci_filename: str
        foreground_process_inventory.csv Process inventory for foreground activities
    
    uslci_filename: str
        usnrellci_processesv2017_loc_debugged.p Background LCI inventory from USLCI
    
    stock_filename: str
        stock_filename.p Stock file to store GFRP at cement co processing plant for one year
    
    emissions_lci_filename: str
        emissions_inventory.csv Emissions LCI inventory file. 
    
    traci_lci_filename: str
        traci21.csv TRACI2.1 characterization factor file.
    """
    def __init__(self,
                 lca_results_filename,
                 shortcutlca_filename,
                 dynamic_lci_filename,
                 static_lci_filename,
                 uslci_filename,
                 stock_filename,
                 emissions_lci_filename,
                 traci_lci_filename,
                 use_shortcut_lca_calculations,
                 sand_substitution_rate,
                 coal_substitution_rate
                 ):
        
        """
        This function stores the filenames required for LCIA calculations as properties of an object. 
        
        Parameters
        ----------
        lca_results_filename: str
            filename for the lca results file

        shortcutlca_filename: str
            filename for the shortcut file for improving LCA calculations

        dynamic_lci_filename: str
            filename for the lca inventory dependent upon time

        static_lci_filename: str
            filename for the lca fixed inventory 

        uslci_filename: str
            filename of the USLCI background pickle file

        stock_filename: str
            filename for storage pickle variable

        emissions_lci_filename: str
            filename for emissions inventory

        traci_lci_filename: str
            filename for traci CF file

        use_shortcut_lca_calculations: str
            boolean flag for using lca shortcut performance improvement method
            
        sand_substitution_rate: float
            sand inventory substitution rate for concrete manufacture using GFRP
        
        coal_substitution_rate: float
            coal inventory substitution rate for concrete manufacture using GFRP
        """
        # filepaths for files used in the pylca calculations
        self.lca_results_filename = lca_results_filename
        self.shortcutlca_filename = shortcutlca_filename
        self.dynamic_lci_filename = dynamic_lci_filename
        self.static_lci_filename = static_lci_filename
        self.uslci_filename = uslci_filename
        self.stock_filename = stock_filename
        self.emissions_lci_filename = emissions_lci_filename
        self.traci_lci_filename = traci_lci_filename
        self.use_shortcut_lca_calculations = use_shortcut_lca_calculations
        self.sand_substitution_rate = sand_substitution_rate
        self.coal_substitution_rate = coal_substitution_rate
        
        #This is the final LCIA results file. Its created using the append function as CELAVI runs. 
        #Thus if there is a chance it exists we need to delete it
        try:
            os.remove(self.lca_results_filename)
            print('old lcia results file deleted')
        except FileNotFoundError:
            print('No existing results file:'+self.lca_results_filename)

    def lca_performance_improvement(self, df):
        """
        This function is used to bypass optimization based pylca celavi calculations
        It reads emission factor data from previous runs stored in a file
        and performs lca rapidly

        Needs to be reset after any significant update to data

        Parameters
        ----------
        df
            shortcut lca db filename
        
        Returns
        -------
        Based on availability of stored file, returns
        1.pd.DataFrame with lca calculations performed along with missing activities and processes not performed
        2.complete pd.DataFrame without any results if file doesn't exist
        """
        try:
            db= pd.read_csv(self.shortcutlca_filename)
            db.columns = ['year','stage','material','flow name','emission factor kg/kg']
            db = db.drop_duplicates()
            df2 = df.merge(db, on = ['year','stage','material'], how = 'outer',indicator = True)
            df_with_lca_entry = df2[df2['_merge'] == 'both'].drop_duplicates()
            
            
            df_with_no_lca_entry =  df2[df2['_merge'] == 'left_only']
            df_with_no_lca_entry = df_with_no_lca_entry.drop_duplicates()
            
            
            df_with_lca_entry['flow quantity'] = df_with_lca_entry['flow quantity'] * df_with_lca_entry['emission factor kg/kg']
            df_with_lca_entry = df_with_lca_entry[['flow name','flow unit','flow quantity','year','facility_id','stage','material']]
            result_shortcut = impact_calculations(df_with_lca_entry,self.traci_lci_filename)
            
            return df_with_no_lca_entry,result_shortcut
        
        except FileNotFoundError:
            
            print('No existing results file:'+self.shortcutlca_filename)        
            return df,pd.DataFrame()

    def pylca_run_main(self, df):
        """
        This function runs the individual pylca celavi functions for performing various calculations
        
        Parameters
        ----------
        df: pd.DataFrame
             Material flows from DES
        
        Returns
        -------
        pd.DataFrame
            LCIA results (also appends to csv file)
        """
        df = df[df['flow quantity'] != 0]
    
        res_df = pd.DataFrame()
        df=df.reset_index()
        lcia_mass_flow = pd.DataFrame()
    
        #This function breaks down the df sent from DES to individual rows with unique rows, facilityID, stage and materials.
        for index,row in df.iterrows():
            
            year = row['year']
            stage = row['stage']
            material = row['material']
            facility_id = row['facility_id']
            new_df = df[df['index'] == index]

            if self.use_shortcut_lca_calculations:
                #Calling the lca performance improvement function to do shortcut calculations. 
                df_with_no_lca_entry,result_shortcut = self.lca_performance_improvement(new_df)
    
            else:
                
                df_with_no_lca_entry = new_df
                result_shortcut = pd.DataFrame()

            if not df_with_no_lca_entry.empty:
                # Calculates the concrete lifecycle flow and emissions inventory
                df_static,df_emissions = concrete_life_cycle_inventory_updater(new_df, year, material, stage, self.static_lci_filename, self.stock_filename, self.emissions_lci_filename, self.sand_substitution_rate, self.coal_substitution_rate)
    
                if not df_static.empty:
    
                    working_df = df_with_no_lca_entry
                    working_df['flow name'] = working_df['material'] + ', ' + working_df['stage']
                    working_df= working_df[['flow name','flow quantity']]
    
                    # model_celavi_lci() is calculating foreground processes and dynamics of electricity mix.
                    # It calculates the LCI flows of the foreground process.
                    res = model_celavi_lci(working_df,year,facility_id,stage,material,df_static,self.dynamic_lci_filename)
    
                    # model_celavi_lci_insitu() calculating direct emissions from foreground
                    # processes.
                    emission = model_celavi_lci_insitu(working_df,year,facility_id,stage,material,df_emissions)
    
                    if not res.empty:
                        res = model_celavi_lci_background(res,year,facility_id,stage,material,self.uslci_filename)   
                        lci = postprocessing(res,emission)
                        res = impact_calculations(lci,self.traci_lci_filename)
                        res_df = pd.concat([res_df,res])
                        lcia_mass_flow = pd.concat([lci,lcia_mass_flow])
                        
                        
                        df_with_no_lca_entry = df_with_no_lca_entry.drop(['flow name'],axis = 1)
                        lca_db = df_with_no_lca_entry.merge(lcia_mass_flow,on = ['year','stage','material'])
                        lca_db['emission factor kg/kg'] = lca_db['flow quantity_y']/lca_db['flow quantity_x']   
                        lca_db = lca_db[['year','stage','material','flow name','emission factor kg/kg']]
                        lca_db = lca_db[lca_db['material'] != 'concrete']
                        lca_db['year'] = lca_db['year'].astype(int)
                        lca_db = lca_db.drop_duplicates()
                        lca_db.to_csv('lca_db.csv',mode = 'a',index = False, header = False)
        
            else:
                print(str(facility_id) + ' - ' + str(year) + ' - ' + stage + ' - ' + material + ' shortcut calculations done',flush = True)    

            res_df = pd.concat([res_df,result_shortcut])

        #Correcting the units for LCIA results. 
        for index,row in res_df.iterrows():
    
            a = row[4]
    
            try:
                split_string = a.split("/kg", 1)
                res_df = res_df.replace(a,split_string[0] + split_string[1])

            except:
                split_string = a.split("/ kg", 1)
                res_df = res_df.replace(a,split_string[0] + split_string[1])

           
        # The line below is just for debugging if needed
        res_df.to_csv('final_lcia_results_to_des.csv', mode='a', header=False, index=False)
    
        # This is the result that needs to be analyzed every timestep.
        return res_df
           
