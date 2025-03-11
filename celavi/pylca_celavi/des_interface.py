import pandas as pd
from celavi.pylca_celavi.pylca_liaison import liaison_lci
import os
import secrets
#todo
#This directory needs to be read as a yaml file to be removed from being hardcoded. 
os.environ['BRIGHTWAY2_DIR']= "/kfs2/shared-projects/liaison/env/hipster/"
print('Importing brightway module.....',flush=True)
import brightway2 as bw
print('Imported',flush= True)

#todo
#We need to remove several variables that are unnecessary now. 
#We need to add the data directory
class PylcaCelavi:
    def __init__(
        self,
        data_dir,
        liaison_params,
        lcia_des_filename,
        shortcutlca_filename,
        use_shortcut_lca_calculations,
        verbose,
        run=0,
    ):
        """
        Stores filenames in self and deletes old interface file if it exists.
        
        Parameters
        ----------
        lcia_des_filename: str
            Path to file that stores calculated impacts for passing back to the
            discrete event simulation.
        shortcutlca_filename: str
            Path to file where previously calculated impacts are stored. This file
            can be used instead of re-calculating impacts from the inventory.
        use_shortcut_lca_calculations: Boolean
            Boolean flag for using previously calculating impact data or running the
            optimization code to re-calculate impacts.
        verbose: int
            0 to suppress detailed print statements
            1 to allow print statements
        run: int
            Model run. Defaults to zero.
        """
        # filepaths for files used in the pylca calculations
        self.lcia_des_filename = lcia_des_filename
        self.shortcutlca_filename = shortcutlca_filename
        self.use_shortcut_lca_calculations = use_shortcut_lca_calculations
        self.verbose = verbose
        self.run = run

        # The results file should be removed if present. The LCA results are appended to the results file. 
        try:
            os.remove(self.lcia_des_filename)
            if self.verbose == 1:
                print(f"PylcaCelavi: Deleted {self.lcia_des_filename}")
        except FileNotFoundError:
            if self.verbose == 1:
                print(f"PyLCIA: {self.lcia_des_filename} not found")

    def lca_performance_improvement(self, df, state):
        """
        This function is used to bypass pylca liaison calculations
        It reads emission factor data from previous runs stored in a file
        and performs lca faster.

        The stored file needs to be reset after any significant update to data.

        Parameters
        ----------
        df: pandas.DataFrame
            Material flow and process information provided by the DES.
            Columns:
                - year: int
                    Model year.
                - stage: str
                    Activity in the system
                - material: str
                    Material flowing through the particular system activity
                - state: str
                    Optional state identifier. Required only if electricity_grid_spatial_level is "state".
                - route_id: str
                    UUID for the route along which transportation occurs. None for non-transportation activities.
        
        state : str
            State identifier. Currently not used

        Returns
        -------
        pandas.DataFrame, pandas.DataFrame
            Emission results using the shortcut calculations and another dataframe with the flows that do not have any emission results.
            Columns:
                - year: int
                    Model year.
                - stage: str
                    Supply chain stage.
                - material: str
                    Material being processed.
                - state: str
                    State in which process exists.
                - route_id: str
                    UUID of transportation route.

        pandas.DataFrame
            Pollutant flows from the shortcut LCA file, or an empty DataFrame if the shortcut file doesn't exist.
            Columns:
                - flow name: str
                    Pollutant name.
                - flow unit: str
                    Unit of pollutant flow.
                - flow quantity: float
                    Pollutant flow quantity.
                - year: int
                    Model year.
                - facility_id: int
                    Facility ID.
                - stage: str
                    Supply chain stage.
                - state: str
                    State where facility is located.
                - material: str
                    Material being processed.
                - route_id: str
                    UUID of transportation route.
        """
      
        
        
        try:
            shortcutlca_df = pd.read_csv(self.shortcutlca_filename)
            shortcutlca_df.columns = ['lcia','value','unit','year','method','facility_id','stage','material','route_id','state']
            df[['stage','year','material','state','facility_id','route_id']] = df[['stage','year','material','state','facility_id','route_id']].astype('str')
            shortcutlca_df[['stage','year','material','state','facility_id','route_id']] = shortcutlca_df[['stage','year','material','state','facility_id','route_id']].astype('str')
            del shortcutlca_df['route_id']
            df2 = df.merge(shortcutlca_df,left_on=['stage','year','material','state','facility_id'],right_on = ['stage','year','material','state','facility_id'],indicator=True,how = 'outer')
            df_with_no_lca_entry =  df2[df2['_merge'] == 'left_only']
            df_results = df2[df2['_merge'] == 'both']
            if df_results.empty:
                print("Missing from shortcut ",df['stage'],df['year'],df['state'])
            df_results['value'] = df_results['flow quantity'] * df_results['value']
            df_results = df_results[['lcia','value','unit','year','method','facility_id','stage','material','route_id','state']]
            
            return df_with_no_lca_entry,df_results

        except FileNotFoundError:
            
            shortcutlca_df= pd.DataFrame()
            #shortcutlca_df.columns = ['lcia','value','unit','year','method','facility_id','stage','material','route_id','state']
            df_with_no_lca_entry = df


            if self.verbose == 1:
                print("No existing shortcut LCA file:" + self.shortcutlca_filename)
            
            return df_with_no_lca_entry,pd.DataFrame()


    def pylca_run_main(self, df, verbose=0):
        """
        This function runs the individual pylca celavi functions for performing LCA relevant calculations.
        
        Parameters
        ----------
        df: pandas.DataFrame
            Material flows from DES.
        
        Returns
        -------
        res_df: pd.DataFrame
            LCIA results (also appends to csv file)

            Columns:
                - year: int
                - facility_id: int
                - material: str
                - route_id: str
                - state: str
                - stage: str
                - impacts: str
                - impact: float
        """
        df = df[df["flow quantity"] != 0]
        res_df = pd.DataFrame()
        df = df.reset_index()
        lcia_mass_flow = pd.DataFrame()
        states = list(pd.unique(df["state"]))

        # The LCA needs to be done for every region separately. Thus separating the states in the dataframe.
        for st in states:
            df_s = df[df["state"] == st]
            # Changing the state name from "XX to US-XX"
            df_s['state'] = "US-"+df_s['state']
            # This function breaks down the df sent from DES to individual rows with unique rows, facilityID, stage and materials.
            for index, row in df_s.iterrows():
                #CHECK THIS PART
                year = row["year"]
                stage = row["stage"]
                material = row["material"]
                facility_id = row["facility_id"]
                route_id = str(row["route_id"]) 
                state = row["state"]
                unit = row["flow unit"]
                new_df = df_s[df_s["index"] == index]
                #Update years before 2024 since LCI not available
                if year < 2024:
                    original_year = year
                    new_year = 2024
                    new_df['year'] = new_year
                else:
                    new_year = year
                    original_year = year

                if self.use_shortcut_lca_calculations:
                    #Calling the lca performance improvement function to do shortcut calculations. 
                    df_with_no_lca_entry,result_shortcut = self.lca_performance_improvement(new_df,state)
                    df_with_no_lca_entry['route_id'] = str(route_id) #the lca performance improvement removes routes id. 
                else:
                    df_with_no_lca_entry = new_df
                    result_shortcut = pd.DataFrame()

                res_calculated = pd.DataFrame()
                if not df_with_no_lca_entry.empty:
                        working_df = df_with_no_lca_entry
                        working_df["flow name"] = (
                            working_df["material"] + ", " + working_df["stage"]
                        )
                        working_df = working_df[["flow name", "flow quantity"]]

                        if sum(working_df["flow quantity"]) != 0:

                            # liaison_lci() is calculating foreground processes and dynamics of electricity mix.
                            # It calculates the LCI flows of the foreground process.
                            res,quantity = liaison_lci(
                                working_df,
                                new_year,
                                facility_id,
                                stage,
                                material,
                                unit,
                                route_id,
                                state,
                                self.verbose,
                                bw
                            )

                            if not res.empty:

                                lca_db = res
                                lca_db['year'] = lca_db['year'].astype(int)
                                lca_db['value'] = lca_db['value']/quantity
                                lca_db = lca_db.drop_duplicates()
                                lca_db.to_csv(
                                    self.shortcutlca_filename,
                                    mode="a",
                                    index=False,
                                    header=False,
                                )
                                res['year'] = original_year
                                res_calculated = res

                            elif res.empty:
                                if verbose > 0:
                                    print(
                                        f"Empty dataframe returned from pylcia foreground for {year} {stage} {material}"
                                    )

                        else:
                            if verbose > 0:
                                print(
                                    "Final demand for %s %s %s is zero"
                                    % (str(year), stage, material)
                                )

                else:
                    if self.verbose == 1:
                        print(str(facility_id) + ' - ' + str(year) + ' - ' + stage + ' - ' + material + ' shortcut calculations done',flush = True)

    
                result_shortcut['comment'] = "shortcut calculations"
                res_calculated['comment'] = "full calculations"
                res_df = pd.concat([res_df,result_shortcut,res_calculated])
        
        if not res_df.empty:

            res_df["run"] = self.run
            res_df['impacts'] = res_df['lcia']
            res_df['impact'] = res_df['value']
            res_df['year'] = original_year
            res_df2 = res_df[['year','facility_id','material','route_id','stage','state','impacts','impact','unit','run','comment']]
            res_df2.to_csv(self.lcia_des_filename, mode='a', header=False, index=False)
            #res_df2.to_csv('results_checked_to_be_deleted.csv',mode='a', header=False, index=False)


        else:
            res_df2 = pd.DataFrame()
        # This is the result that needs to be analyzed every timestep.
        return res_df2
