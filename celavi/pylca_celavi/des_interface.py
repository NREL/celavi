import pandas as pd
from celavi.pylca_celavi.pylca_opt_foreground import model_celavi_lci
from celavi.pylca_celavi.insitu_emission import model_celavi_lci_insitu
import os
from celavi.pylca_celavi.pylca_opt_background import model_celavi_lci_background

# Concrete lifecycle inventory updater
from celavi.pylca_celavi.concrete_life_cycle_inventory_editor import (
    concrete_life_cycle_inventory_updater,
)

# Postprocessing to perform life cycle impact analysis
from celavi.pylca_celavi.pylca_celavi_background_postprocess import (
    postprocessing,
    impact_calculations,
)


class PylcaCelavi:
    def __init__(
        self,
        lcia_des_filename,
        shortcutlca_filename,
        intermediate_demand_filename,
        dynamic_lci_filename,
        electricity_grid_spatial_level,
        static_lci_filename,
        uslci_tech_filename,
        uslci_emission_filename,
        uslci_process_filename,
        stock_filename,
        emissions_lci_filename,
        traci_lci_filename,
        use_shortcut_lca_calculations,
        verbose,
        substitution_rate,
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
        intermediate_demand_filename: str
            Path to file that stores the final demand vector every time the LCIA 
            calculations are run. For debugging purposes only.
        dynamic_lci_filename: str
            Path to the LCI dataset which changes with time.
        electricity_grid_spatial_level: str
            Specification of grid spatial level used for lca calculations. Must be
            "state" or "national".
        static_lci_filename: str
            Path to the LCI dataset which does not change with time.
        uslci_filename: str
            Path to the U.S. LCI dataset pickle file.
        stock_filename: str
            Filename for storage pickle variable.
        emissions_lci_filename: str
            Filename for emissions inventory.
        traci_lci_filename: str
           Filename for TRACI 2.0 characterization factor dataset.
        use_shortcut_lca_calculations: Boolean
            Boolean flag for using previously calculating impact data or running the
            optimization code to re-calculate impacts.
        verbose: int
            0 to suppress detailed print statements
            1 to allow print statements
        substitution_rate: Dict
            Dictionary of material name: substitution rates for materials displaced by the
            circular component.
        run: int
            Model run. Defaults to zero.
        """
        # filepaths for files used in the pylca calculations
        self.lcia_des_filename = lcia_des_filename
        self.shortcutlca_filename = shortcutlca_filename
        self.intermediate_demand_filename = intermediate_demand_filename
        self.dynamic_lci_filename = dynamic_lci_filename
        self.electricity_grid_spatial_level = electricity_grid_spatial_level
        self.static_lci_filename = static_lci_filename
        self.uslci_tech_filename = uslci_tech_filename
        self.uslci_emission_filename = uslci_emission_filename
        self.uslci_process_filename = uslci_process_filename
        self.stock_filename = stock_filename
        self.emissions_lci_filename = emissions_lci_filename
        self.traci_lci_filename = traci_lci_filename
        self.use_shortcut_lca_calculations = use_shortcut_lca_calculations
        self.verbose = verbose
        self.substitution_rate = substitution_rate
        self.run = run

        # The results file should be removed if present. The LCA results are appended to the results file. 
        try:
            os.remove(self.lcia_des_filename)
            if self.verbose == 1:
                print(f"PylcaCelavi: Deleted {self.lcia_des_filename}")
        except FileNotFoundError:
            if self.verbose == 1:
                print(f"PyLCIA: {self.lcia_des_filename} not found")

    def lca_performance_improvement(self, df, state, electricity_grid_spatial_level):
        """
        This function is used to bypass pylca celavi calculations
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

        electricity_grid_spatial_level : str
            Specification of grid spatial level used for lca calculations. Must be "state" or "national".
        
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
            if electricity_grid_spatial_level != 'state':
                db= pd.read_csv(self.shortcutlca_filename)
                db.columns = ['year', 'stage', 'material', 'flow name', 'emission factor kg/kg']
                db = db.drop_duplicates()
                df2 = df.merge(db, on = ['year', 'stage', 'material'], how = 'outer',indicator = True)
                df_with_lca_entry = df2[df2['_merge'] == 'both'].drop_duplicates()
            else:
                db= pd.read_csv(self.shortcutlca_filename)
                db.columns = ['year', 'stage', 'material', 'state','flow name', 'emission factor kg/kg']
                db = db.drop_duplicates()
                df2 = df.merge(db, on = ['year', 'stage', 'material','state'], how = 'outer',indicator = True)
                df_with_lca_entry = df2[df2['_merge'] == 'both'].drop_duplicates()   

            
            df_with_no_lca_entry =  df2[df2['_merge'] == 'left_only']
            df_with_no_lca_entry = df_with_no_lca_entry.drop_duplicates()
            
            try:
                df_with_no_lca_entry = df_with_no_lca_entry[['year', 'facility_id', 'flow quantity', 'stage', 'state', 'material', 'flow unit']]  
            except:
                df_with_no_lca_entry = df_with_no_lca_entry[['year', 'facility_id', 'flow quantity', 'stage', 'material', 'flow unit']]  

            df_with_lca_entry['flow quantity'] = df_with_lca_entry['flow quantity'] * df_with_lca_entry['emission factor kg/kg']
            df_with_lca_entry = df_with_lca_entry[['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material', 'route_id','state']]
            result_shortcut = impact_calculations(df_with_lca_entry,self.traci_lci_filename)
            
            return df_with_no_lca_entry, result_shortcut

        except FileNotFoundError:

            if self.verbose == 1:
                print("No existing shortcut LCA file:" + self.shortcutlca_filename)
            return df, pd.DataFrame()

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

            # This function breaks down the df sent from DES to individual rows with unique rows, facilityID, stage and materials.
            for index, row in df_s.iterrows():
                year = row["year"]
                stage = row["stage"]
                material = row["material"]
                facility_id = row["facility_id"]
                route_id = row["route_id"]
                state = row["state"]
                new_df = df_s[df_s["index"] == index]

                if self.use_shortcut_lca_calculations:
                    #Calling the lca performance improvement function to do shortcut calculations. 
                    df_with_no_lca_entry,result_shortcut = self.lca_performance_improvement(new_df,state,self.electricity_grid_spatial_level)
                    df_with_no_lca_entry['route_id'] = route_id #the lca performance improvement removes routes id. 
                else:
                    df_with_no_lca_entry = new_df
                    result_shortcut = pd.DataFrame()

                if not df_with_no_lca_entry.empty:
                    # Calculates the concrete lifecycle flow and emissions inventory
                    df_static, df_emissions = concrete_life_cycle_inventory_updater(
                        new_df,
                        year,
                        material,
                        stage,
                        self.static_lci_filename,
                        self.stock_filename,
                        self.emissions_lci_filename,
                        self.substitution_rate,
                    )

                    if not df_static.empty:

                        working_df = df_with_no_lca_entry
                        working_df["flow name"] = (
                            working_df["material"] + ", " + working_df["stage"]
                        )
                        working_df = working_df[["flow name", "flow quantity"]]

                        if sum(working_df["flow quantity"]) != 0:

                            # model_celavi_lci() is calculating foreground processes and dynamics of electricity mix.
                            # It calculates the LCI flows of the foreground process.
                            res = model_celavi_lci(
                                working_df,
                                year,
                                facility_id,
                                stage,
                                material,
                                route_id,
                                state,
                                df_static,
                                self.dynamic_lci_filename,
                                self.electricity_grid_spatial_level,
                                self.intermediate_demand_filename,
                                self.verbose,
                            )
                            # model_celavi_lci_insitu() calculating direct emissions from foreground
                            # processes.
                            emission = model_celavi_lci_insitu(
                                working_df,
                                year,
                                facility_id,
                                stage,
                                material,
                                state,
                                df_emissions,
                                self.verbose,
                            )
                            if not res.empty:                            
                                res = model_celavi_lci_background(res,year,facility_id,stage,material,route_id,state,self.uslci_tech_filename,self.uslci_emission_filename,self.uslci_process_filename,self.verbose)
                                lci = postprocessing(res,emission,self.verbose)
                                res = impact_calculations(lci,self.traci_lci_filename)
                                res_df = pd.concat([res_df,res])

                                lcia_mass_flow = lci
                                del df_with_no_lca_entry['route_id']
                                del lcia_mass_flow['route_id']
                                
                                df_with_no_lca_entry = df_with_no_lca_entry.drop(['flow name'],axis = 1)
                                lca_db = df_with_no_lca_entry.merge(lcia_mass_flow,on = ['year','stage','material','state'])
                                lca_db['emission factor kg/kg'] = lca_db['flow quantity_y']/lca_db['flow quantity_x']  
                                
                                if self.electricity_grid_spatial_level == 'state':
                                    lca_db['state'] = state
                                    lca_db = lca_db[['year','stage','material','state','flow name','emission factor kg/kg']]
                                else: 
                                    lca_db = lca_db[['year','stage','material','flow name','emission factor kg/kg']]

                                lca_db = lca_db[lca_db['material'] != 'concrete']
                                lca_db['year'] = lca_db['year'].astype(int)
                                lca_db = lca_db.drop_duplicates()
                                lca_db.to_csv(
                                    self.shortcutlca_filename,
                                    mode="a",
                                    index=False,
                                    header=False,
                                )
                            else:
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
    
                res_df = pd.concat([res_df,result_shortcut])
        
        #Correcting the units for LCIA results. 
        for index,row in res_df.iterrows():
            a = row['impacts']
            try:
                split_string = a.split("/kg", 1)
                res_df = res_df.replace(a, split_string[0] + split_string[1])

            except:
                split_string = a.split("/ kg", 1)
                res_df = res_df.replace(a, split_string[0] + split_string[1])

        # The line below is just for debugging if needed
        res_df["run"] = self.run
        res_df.to_csv(self.lcia_des_filename, mode='a', header=False, index=False)
        # This is the result that needs to be analyzed every timestep.
        return res_df
