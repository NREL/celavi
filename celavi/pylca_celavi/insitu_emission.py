import pandas as pd
import numpy as np
def preprocessing(year,df_emission):
    """
    This function preprocesses the emissions database for foregound system before calculation. 
    It creates a product only database for technology matrix construction.
    Removes any dummy flows from the database.

    Parameters
    ----------
    year : str
        year of LCA calculation
    df_emission : pandas dataframe
        emission inventory
    
    Returns
    -------
    product_df: pandas dataframe
        An inventory with only product flows for creating the technology product matrix
    df_with_all_other_flows: pandas dataframe   
       inventory with no product flows
    """
    df = df_emission
    df_input = df[df['input'] == True]
    df_output = df[df['input'] == False]
    df_input.loc[:, 'value'] = df_input.loc[:, 'value'] * (-1)
    df = pd.concat([df_input, df_output])
    
    # Removing flows without source
    # Dummy flows need to be removed.
    # This part removes the dummy flows and flows without any production processes from the X matrix.
    process_input_with_process = pd.unique(df_output['product'])
    df['indicator'] = df['product'].isin(process_input_with_process)
    product_df = df[df['indicator'] == True]
    df_with_all_other_flows = df[df['indicator'] == False]
    
    del product_df['indicator']
    del df_with_all_other_flows['indicator']
    
    product_df.loc[:, 'value'] = product_df.loc[:, 'value'].astype(np.float64)
    return product_df, df_with_all_other_flows


def solver(tech_matrix, F, process, df_with_all_other_flows):
    """
    This function houses the calculator to solve Xs = F for calculating insitu emissions. 
    Solves the Xs=F equation. Solves the scaling vector.  

    Parameters
    ----------
    tech_matrix: numpy matrix
         technology matrix from the products inventory
    F: numpy array
         Final demand vector 
    process: list
         list of processes in the emissions inventory   
    df_with_all_other_flows: pandas dataFrame
         lca inventory with no product flows

    Returns
    -------
    results_total: pandas dataframe
        emissions as a dataframe after performing insitu emissions calculations
        These are insitu mass pollutant flows calculated for demand of material by foreground processes. 
        
        Columns:
           - product: str
           - unit: str
           - value: float
    """
    tm = tech_matrix.to_numpy()
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
    This function is used to replace pre 2020 electricity flows in the emissions inventory with the base electricity mix flow
    in the USLCI inventory Electricity, at Grid, US, 2010'
    
    Parameters
    ----------
    df: pd.DataFrame
        Background process inventory. Columns are derived from the background LCI database being used.

    Returns
    -------
    df: pd.DataFrame
       process inventory with electricity flows before 2020 converted to the base electricity
       mix flow in USLCI. 
    """
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df

def runner_insitu(
    tech_matrix,
    F,
    yr,
    i,
    j,
    k,
    state,
    final_demand_scaler,
    process,
    df_with_all_other_flows
    ):
    """
    Runs the solver function for the insitu emissions and creates foreground emissions data frame in proper format.

    Parameters
    ----------
    tech matrix: pandas dataframe
         technology matrix built from the emissions inventory. 
    F: final demand series vector
         final demand of the foreground system
    yr: int
        Model year
    i: int
        facility ID
    j: str
        Name of supply chain stage
    k: str
        Name of material
    state: str
        State where the facility is located.
    final_demand_scaler: int
        Integer for scaling final demand and avoiding badly scaled matrix calculations.
    process: list
        List of processes included in the technology matrix
    df_with_all_other_flows: pd.DataFrame
        Dataframe with flows in the inventory which do not have a production process. 
    
    Returns
    -------
    res: pandas dataframe
        Emission results in the form of a dataframe.
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
    res['value'] = res['value']*final_demand_scaler
    if  not res.empty:        
       res.loc[:,'year'] =  yr
       res.loc[:,'facility_id'] = i
       res.loc[:,'stage'] = j
       res.loc[:,'material'] = k
       res.loc[:,'state'] = state
    else:        
       print(f"Insitu emission calculation failed for {k} at {j} in {yr}")
    
    res = electricity_corrector_before20(res)
    res['route_id'] = None
    return res


def model_celavi_lci_insitu(f_d, yr, fac_id, stage, material, state, df_emissions, verbose):
    """
    Creates a product only technology matrix for scaling vector calculations. 
    Runs the solver to perform insitu emissions calculations. Conforms emission results to a dataframe. Performs column checks and renames columns .
    Returns the emissions dataframe.

    Parameters
    ----------
    f_d: pandas dataframe 
        Dataframe from DES 
    yr: int
        Model year.
    fac_id: int
        Facility ID of facility being evaluated
    stage: str 
        Supply chain stage.
    material: str
        material being evaluated
    df_emission: pandas dataframe
        Emissons inventory

    Returns
    -------
    res: pandas dataframe
       Insitu emissions dataframe with modified column names after checking column number. 
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
    # Incorporating dynamics lci database
    process_df, df_with_all_other_flows = preprocessing(int(yr), df_emissions)
    # Creating the technology matrix for performing LCA calculations
    tech_matrix = process_df.pivot(index='product', columns='process', values='value')
    tech_matrix = tech_matrix.fillna(0)
    # This list of products and processes essentially help to determine the indexes and the products and processes
    # to which they belong.
    products = list(tech_matrix.index)
    process = list(tech_matrix.columns)
    product_df = pd.DataFrame(products)
    final_dem = product_df.merge(f_d, left_on=0, right_on='flow name', how='left')
    final_dem = final_dem.fillna(0)
    chksum = np.sum(final_dem['flow quantity'])
    F = final_dem['flow quantity']
    if chksum <= 0:
        if verbose == 1:
            print('LCA emissions inventory does not exist for %s %s %s' % (str(yr), stage, material))
        return pd.DataFrame()
        #Returns blank dataframe if not inventory is present
    
    elif chksum > 100000:
            final_demand_scaler = 10000
    elif chksum > 10000:
            final_demand_scaler = 1000
    elif chksum > 100:
            final_demand_scaler = 10
    else:
            final_demand_scaler = 1

    # Dividing by scaling value to solve scaling issues
    F = F / final_demand_scaler

    res = runner_insitu(tech_matrix, F, yr, fac_id, stage, material, state, final_demand_scaler, process, df_with_all_other_flows)
    if len(res.columns) != 9:
        print(f'model_celavi_lci: res has {len(res.columns)}; needs 9 columns',
              flush=True)
        return pd.DataFrame(columns = ['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material','route_id', 'state'])
    else:
        res.columns = ['flow name', 'flow unit', 'flow quantity', 'year', 'facility_id', 'stage', 'material','route_id','state']
        return res
