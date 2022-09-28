import pandas as pd
import numpy as np
import time

def model_celavi_lci_background(f_d, yr, fac_id, stage,material, route_id, state, uslci_tech_filename,uslci_emission_filename,uslci_process_filename,verbose
                                ):

    """
    Main function of this module which receives information from DES interface and runs the supporting calculation functions for the LCA backgroung system using the USLCI inventory. 
    Creates the technology matrix for the background system inventory and the final demand vector based on input data. 
    Performs necessary checks before and after the LCA  calculation. 
    
    Checks performed 
    1. Final demand to the background LCA system by the foreground system is not zero. If zero returns empty dataframe and simulation continues without breaking code. 
    2. Checks the LCA solver returned a proper dataframe. If empty dataframe is returned, it attaches column names to the dataframe and code continues without breaking.
    
    Parameters
    ----------
    f_d: pd.Dataframe
      Dataframe from DES interface containing material flow information
    yr: int
      year of analysis
    fac_id: int
      facility id
    stage: str
      stage of analysis
    material: str
      material of LCA analysis
    route_id: str
        Unique identifier for transportation route.
    state: str
        State in which LCA calculations are taking place.
    uslci_tech_filename: str
      filename for the USLCI technology matrix. It contains the technology matrix from USLCI. 
    uslci_process_filename: str
      filename for the USLCI process list matrix. It contains the list of processes in the USLCI.
    uslci_emission_filename: str
      filename for the USLCI emissions list matrix. It contains the list of emissions from acttivities in the USLCI. 
    verbose: int
      verbose parameter for toggling print of LCA calculation steps. Default 0 no printout
    
    Returns
    -------
    res2: pd.DataFrame
       Final LCA results from the background LCA calculation in the form of a dataframe after performing calculation checks
       These are mass pollutant flows calculated from USLCI for demand of material at a certain stage and from a facility. 
       Columns:
            - product: str
            - unit: str
            - value: float
            - year: int
            - facility_id: int
            - stage: str
            - material: str
            - route_id: int
            - state: str

      
    """

    def solver(tech_matrix,F,process_emissions):
        
        """
        This function houses the LCA solver for the background system to solve Xs = F. 
        Solves the Xs=F equation. 
        Solves the scaling vector.  

        Parameters
        ----------
        tech_matrix : numpy matrix
             technology matrix from the background process inventory
        F : vector
             Final demand vector 
        process_emissions: str
             filename for the emissions dataframe
        
        Returns
        -------
        pd.DataFrame
            LCA results for the background system in the form of a dataframe after performing LCA calculations
            These are mass pollutant flows calculated from USLCI for demand of material. 

            Columns:
               - product: str
               - unit: str
               - value: float

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
        Calls the solver function for the background system inventory and arranges and stores the results into a proper pandas dataframe. 
        
        Parameters
        ----------
        tech matrix: pd.Dataframe
             technology matrix built from the backgroud process inventory. 
        F: final demand series vector
             final demand of the LCA problem
        yr: int
             year of analysis
        i: int
             facility ID
        j: str
            stage
        k: str
            material
        route_id: str
            Unique identifier for transportation route.
        state: str
            state in which LCA calculations are taking place
        final_demand_scaler: int
            scaling variable number to ease calculation


        Returns
        -------
        pd.DataFrame
            Returns the background LCA reults in a properly arranged dataframe with all supplemental information
            LCA results in the form of a dataframe.
            These are mass pollutant flows calculated from USLCI for demand of material at a certain stage and from a facility. 
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
