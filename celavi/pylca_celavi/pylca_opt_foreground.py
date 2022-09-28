import pandas as pd
import numpy as np


#Reading in static and dynamics lca databases


#We are integrating static lca with dynamics lca over here. 
def preprocessing(year,state,df_static,dynamic_lci_filename,electricity_grid_spatial_level):

    """
    This function preprocesses the foreground process inventory before the LCA calculation. It joins the dynamic LCA
    inventory with the static LCA inventory. Removes dummy processes with no output from the inventory. 

    Parameters
    ----------
    year : str
         year of LCA calculation
    state : str
         state of Facility
    df_static : pd.DataFrame
         lca inventory static 
    dynamic_lci_filename: str
         filename for the dynamic inventory   
    
    Returns
    -------
    process_df: pd.DataFrame
        cleaned process inventory merged with dynamic data
    
    df_with_all_other_flows: pd.DataFrame    
        inventory with no product flows
        
        Columns:
            - flow name: str
            - flow unit: str
            - flow quantity: float
            - year: int
            - facility_id: int
            - stage: str
            - material: str
            - route_id: int
            - state:str

    """
    
    #Reading in dynamics LCA databases
    df_dynamic = pd.read_csv(dynamic_lci_filename) 
    if electricity_grid_spatial_level == 'state':
        df_dynamic_year = df_dynamic[(df_dynamic['year'] == year) & (df_dynamic['state'] == state)]
        df_dynamic_year = df_dynamic_year.drop('state',axis = 1)
    else:
        df_dynamic_year = df_dynamic[(df_dynamic['year'] == year)]
    
    frames = [df_static,df_dynamic_year]
    df = pd.concat(frames)
    df_input = df[df['input'] == True]
    df_output = df[df['input'] == False]
    
    df_input.loc[:,'value'] = df_input.loc[:,'value']  * (-1)
    df = pd.concat([df_input,df_output])


    process_input_with_process  =  pd.unique(df_output['product'])

    df['indicator'] = df['product'].isin(process_input_with_process)
    process_df = df[df['indicator'] == True]
    df_with_all_other_flows = df[df['indicator'] == False]
    
    del process_df['indicator']
    del df_with_all_other_flows['indicator']
    
    process_df.loc[:,'value'] = process_df.loc[:,'value'].astype(np.float64)

    return process_df,df_with_all_other_flows


def solver(tech_matrix,F,process, df_with_all_other_flows):

    """
    This function solves Xs = F where X is the tech matrix for the foreground process inventory.
    Solves the Xs=F equation. 
    Solves the scaling vector.  

    Parameters
    ----------
    tech_matrix : numpy matrix
         technology matrix from the foreground process inventory
    F : vector
         Final demand vector 
    process: list
         filename for the dynamic inventory   
    df_with_all_other_flows: pd.DataFrame
         lca inventory with no product flows

    
    Returns
    -------
    results_total: pd.DataFrame
        LCA results for foreground system in the form of a dataframe after performing LCA calculations
        These are mass input flows to USLCI calculated for demand of material. No emission flows are included in this calculation. 

        Columns:
           - product: str
           - unit: str
           - value: float
        
    """

    tm= tech_matrix.to_numpy()
    scv = np.linalg.solve(tm, F)

    scaling_vector = pd.DataFrame()
    scaling_vector['process'] = process
    scaling_vector['scaling_factor'] = scv

    results_df = df_with_all_other_flows.merge(scaling_vector, on=['process'], how='left')

    results_df['value'] = abs(results_df['value']) * results_df['scaling_factor']
    results_df = results_df[results_df['value'] > 0]
    results_df = results_df.fillna(0)
    results_total = results_df.groupby(by=['product', 'unit'])['value'].agg(sum).reset_index()

    return results_total


def electricity_corrector_before20(df):
    """
    This function is used to replace pre 2020 electricity flows in the foreground inventory with the base electricity mix flow
    from the USLCI inventory "Electricity, at Grid, US, 2010" 

    Parameters
    ----------
    df: pd.DataFrame
        process inventory

    Returns
    -------
    df: pd.DataFrame
        process inventory with electricity flows before 2020 converted to the base electricity
        mix flow in USLCI.

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
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df


def lca_runner_foreground(tech_matrix,F,yr,i,j,k,route_id,state,final_demand_scaler,process,df_with_all_other_flows,intermediate_demand_filename,verbose):    
    
    """
    Calls the LCA solver function for the foreground inventory and arranges and stores the results into a proper pandas dataframe. 
    
    Parameters
    ----------
    tech matrix: pd.Dataframe
         technology matrix built from the foreground process inventory. 
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
        UUID identifying the transportation route
    state: str
        state in which LCA calculations are taking place
    final_demand_scaler: int
        scaling variable number to ease calculation
    process: list
        list of processes included in the technology matrix
    df_with_all_other_flows: pd.DataFrame
        Dataframe with flows in the inventory which do not have a production process. 

    Returns
    -------
    res: pd.DataFrame
        Returns the final LCA reults in a properly arranged dataframe with all supplemental information
        LCA results in the form of a dataframe.
        These are mass input flows to USLCI calculated for demand of material at a certain stage and from a facility. No emission flows are included in this calculation. 

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

    res = pd.DataFrame()
    res = solver(tech_matrix, F, process, df_with_all_other_flows)         
    res['value'] = res['value'] * final_demand_scaler
    res = res[res['value'] > 1e-07]
    if not res.empty:

       res.loc[:, 'year'] = yr
       res.loc[:, 'facility_id'] = i
       res.loc[:, 'stage'] = j
       res.loc[:, 'material'] = k
       res.loc[:, 'route_id'] = route_id
       res.loc[:, 'state'] = state
       res = electricity_corrector_before20(res)
       # Intermediate demand is not required by the framewwork, but it is useful
       # for debugging.
       res.to_csv(intermediate_demand_filename, mode='a', header=False, index=False)    
       return res
    
    else:        
       print(f"pylca-opt-foreground emission failed  for {k} at {j} in {yr}")


def model_celavi_lci(f_d,yr,fac_id,stage,material,route_id,state,df_static,dynamic_lci_filename,electricity_grid_spatial_level,intermediate_demand_filename,verbose):

    """
    Main function of this module is to receive information from DES interface and run the supporting LCA functions. 
    Creates the technology matrix for the foreground inventory and the final demand vector based on input data. 
    Performs necessary checks before and after the LCA calculation. 
    Checks performed 
    1. Final demand by the foreground system is not zero. If zero returns empty dataframe and simulation continues without breaking code. 
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
        state in which LCA calculations are taking place
    df_static: pd.Dataframe
      static foreground LCA inventory
    dynamic_lci_filename: str
      filename for the dynamic LCA inventory

    Returns
    -------
    res2: pd.DataFrame
       Final LCA results in the form of a dataframe after performing calculation checks
       These are mass input flows to USLCI calculated for demand of material at a certain stage and from a facility. No emission flows are included in this calculation. 
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
    # Running LCA for all years as obtained from CELAVI
    #Incorporating dynamics lci database
    process_df,df_with_all_other_flows = preprocessing(int(yr),state,df_static,dynamic_lci_filename,electricity_grid_spatial_level)
    #Creating the technoology matrix for performing LCA caluclations
    tech_matrix = process_df.pivot(index = 'product', columns = 'process', values = 'value' )
    tech_matrix = tech_matrix.fillna(0)
    # This list of products and processes essentially help to determine the indexes and the products and processes
    # to which they belong.
    products = list(tech_matrix.index)
    process = list(tech_matrix.columns)
    product_df = pd.DataFrame(products)
    final_dem = product_df.merge(f_d, left_on=0, right_on='flow name', how='left')
    final_dem = final_dem.fillna(0)
    chksum = np.sum(final_dem['flow quantity'])
    if chksum <= 0:
        if verbose == 1:
            print('LCA inventory does not exist for %s %s %s' % (str(yr), stage, material))
        return pd.DataFrame()
    #To make the calculation easier
    elif chksum > 100000:
        final_demand_scaler = 10000
    elif chksum > 10000:
        final_demand_scaler = 1000
    elif chksum > 100:
        final_demand_scaler = 10
    else:
        final_demand_scaler = 1
        
    F = final_dem['flow quantity']
    # Dividing by scaling value to solve scaling issues
    F = F / final_demand_scaler
    
    res2 = lca_runner_foreground(tech_matrix, F, yr, fac_id, stage, material, route_id, state, final_demand_scaler, process, df_with_all_other_flows,intermediate_demand_filename,verbose)
    if len(res2.columns) != 9:
        print(f'model_celavi_lci: res has {len(res2.columns)}; needs 9 columns',
              flush=True)
        return pd.DataFrame(
            columns=['flow name', 'flow unit', 'flow quantity',
                     'year', 'facility_id', 'stage', 'material', 'route_id', 'state']
        )
    else:
        res2.columns = ['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material', 'route_id', 'state']
        return res2
