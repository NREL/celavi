import pandas as pd
import numpy as np
import time

def model_celavi_lci_background(
    f_d,
    yr,
    fac_id,
    stage,
    material,
    route_id,
    state,
    uslci_tech_filename,
    uslci_emission_filename,
    uslci_process_filename,
    verbose
    ):

    """
    Runs the pollutant inventory calculations based on information provided by the DES interface.

    Creates the technology matrix and the final demand vector based on input data.
    Performs necessary checks before and after the LCA  calculation.
    
    Checks performed:
        1. Final demand by the foreground system is not zero. If the final demand is zero, this method
        returns an empty DataFrame and the simulation continues.
        2. Checks the LCA solver returned a non-empty DataFrame. If an empty DataFrame is returned,
        this method attaches column names to the DataFrame and the simulation continues.
    
    Parameters
    ----------
    f_d: pandas.DataFrame
        Dataframe from DES interface containing material flow information
    yr: int
        Model year
    fac_id: int
        Facility id
    stage: str
        Supply chain stage
    material: str
        Material being processed
    route_id: str
        Unique identifier for transportation route.
    state: str
        State in which LCA calculations are taking place.
    uslci_tech_filename: str
        Filename for the USLCI technology matrix. It contains the technology matrix from USLCI. 
    uslci_process_filename: str
        Filename for the USLCI process list matrix. It contains the list of processes in the USLCI.
    uslci_emission_filename: str
        Filename for the USLCI emissions list matrix. It contains the list of emissions from acttivities in the background process inventory. 
    verbose: int
        Toggles level of progress reporting provided by this method. Defaults to 0 (no reporting).
    
    Returns
    -------
    pd.DataFrame
        Mass pollutant flows for demand of material from a facility.
        Columns:
            - product: str
                Name of pollutant.
            - unit: str
                Pollutant flow units.
            - value: float
                Pollutant flow value.
            - year: int
                Model year.
            - facility_id: int
                Facility ID.
            - stage: str
                Supply chain stage at this facility.
            - material: str
                Name of material being processed.
            - route_id: str
                UUID for transportation route
            - state: str
                State in which facility is located.
    """

    def solver(tech_matrix,F,process_emissions):
        """
        Calculates the process scaling vector s by solving the Xs = F material balance equations. 

        Parameters
        ----------
        tech_matrix: Matrix
            Technology matrix generated from the background inventory.
        F: vector
            Final demand vector representing supply chain material and energy inputs.
        process: list
            List of process names corresponding to the scaling vector s.  
        process_emissions: str
            Filename for the process-level emissions dataframe
        
        Returns
        -------
        pd.DataFrame
            Mass pollutant flows calculated from the background process inventory for the final demand F.
            Columns:
                - product: int
                    Name of pollutant.
                - unit: int
                    Unit of pollutant flow.
                - value: float
                    Value of pollutant flow.
        """
        tm = tech_matrix.to_numpy()
        scv = np.linalg.solve(tm, F)
        scv_df = pd.DataFrame()
        scv_df['scaling vector'] = scv
        scv_df['process'] = uslci_process

        #Calculations for total emissions
        final_result = scv_df.merge(process_emissions, on = ['process'])
        final_result['total_emission'] = final_result['scaling vector'] * final_result['value']
        final_result['value'] = final_result['total_emission']
        em_result = final_result[['product','value','process','unit']]
        emissions_results_total = final_result.groupby(['product','unit'])['value'].agg('sum').reset_index()
      
        if not emissions_results_total.empty:
            return emissions_results_total
        else:
            return pd.DataFrame()

    
    def lca_runner_background(tech_matrix, F,i,l,j,k,route_id,state, final_demand_scaler,process_emissions,verbose):

        """
        Calls the solver function to perform LCIA calculations.
        
        Arranges and returns the pollutant results as a DataFrame. 
        
        Parameters
        ----------
        tech matrix: pd.Dataframe
            Technology materix representing the background inventory.
        F: final demand series vector
            Final demand vector of the supply chain material and energy inputs.
        yr: int
            Model year.
        i: int
            Facility ID.
        j: str
            Supply chain stage.
        k: str
            Material being processed.
        route_id: str
            Unique identifier for transportation route.
        state: str
            State in which facility is located.
        final_demand_scaler: int
            Scaling integer to avoid badly-scaled matrix calculations.
        verbose: int
            Controls the level of progress reporting from this method.
        
        Returns
        -------
        pd.DataFrame
            Mass pollutant flows calculated from USLCI for demand of material at a certain stage and from a facility.
            Columns:
                - flow name
                - flow unit
                - flow quantity
                - year
                - facility_id
                - stage
                - material
                - route_id
                - state
        """
        tim0 = time.time()
        res = solver(tech_matrix, F,process_emissions)
        res['value'] = res['value']*final_demand_scaler
        if not res.empty:
          
          res.loc[:,'year'] =  i
          res.loc[:,'facility_id'] =  l
          res.loc[:,'stage'] = j
          res.loc[:,'material'] = k
          res.loc[:,'route_id'] = route_id
          res.loc[:, 'state'] = state
          if verbose == 1:
            print(str(i) +' - '+j + ' - ' + k, flush = True)
    
        else:  
          print(f"pylca-opt-background emission failed for {k} at {j} in {i}", flush = True) 
          pass       
        
        if verbose == 1:
            print(str(time.time() - tim0) + ' ' + 'taken to do this run',flush=True)    
        
        return res
    

    process_emissions = pd.read_csv(uslci_emission_filename)
    #Creating the technology matrix for performing LCA caluclations
    tech_matrix = pd.read_csv(uslci_tech_filename,index_col ='conjoined_flownames')
    process_adder = pd.read_csv(uslci_process_filename)
    process_adder['product'] = process_adder['product'].str.lower()
    f_d['flow name'] = f_d['flow name'].str.lower()
    f_d = f_d.merge(process_adder, left_on = "flow name", right_on = "product")
    #This list of products and processes essentially help to determine the indexes and the products and processes
    #to which they belong. 
    uslci_products = pd.DataFrame(tech_matrix.index)
    uslci_process = list(tech_matrix.columns)

    f_d = f_d.drop_duplicates()
    f_d = f_d.sort_values(['year'])

    #Replace electricity    
    f_d['conjoined_flownames'] = f_d['conjoined_flownames'].str.lower()  
    #dataframe to debug connecting between foreground and background  
    uslci_products['conjoined_flownames'] = uslci_products['conjoined_flownames'].str.lower()  
    final_dem = uslci_products.merge(f_d, left_on='conjoined_flownames', right_on='conjoined_flownames', how='left')
    final_dem = final_dem.fillna(0)

    chksum = np.sum(final_dem['flow quantity'])
    if chksum == 0:
        if verbose == 1:
            print('Final demand construction failed. No value. csv file for error checking created. /n Check the intermediate demand file and final demand check file')
        return pd.DataFrame()
    #To make the solution easier
    elif chksum > 100000:
        final_demand_scaler = 100000
    elif chksum > 10000:
        final_demand_scaler = 10000
    elif chksum > 100:
        final_demand_scaler = 10
    else:
        final_demand_scaler = 0.1

    #print dataframe to debug connecting between foreground and background
    final_dem['flow quantity']= final_dem['flow quantity']/final_demand_scaler
    #To make the calculation easier
    F = final_dem['flow quantity'].to_numpy()
    res2 = lca_runner_background(tech_matrix,F,yr,fac_id,stage,material,route_id,state,final_demand_scaler,process_emissions,verbose)
    if len(res2.columns) != 9:
        print(f'model_celavi_lci: res has {len(res2.columns)}; needs 9 columns',
              flush=True)
        return pd.DataFrame(
            columns=['flow name','flow unit','flow quantity',
                     'year', 'facility_id', 'stage', 'material', 'route_id', 'state']
        )
    else:
        res2.columns = ['flow name','flow unit','flow quantity', 'year', 'facility_id', 'stage', 'material', 'route_id', 'state']
        return res2

