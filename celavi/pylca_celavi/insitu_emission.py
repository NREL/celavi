# INSITU EMISSION CALCULATOR
import warnings
import pandas as pd
import numpy as np
def preprocessing(year,df_static):

    """
    This function preprocesses the process inventory before the LCA calculation. It joins the dynamic LCA
    inventory with the static LCA inventory. Removes dummy processes with no output from the inventory. 

    Parameters
    ----------
    year : str
        year of LCA calculation
    df_static : pd.DataFrame
        lca inventory static 

    
    Returns
    -------
    pd.DataFrame
       cleaned process inventory merged with dynamic data
    pd.DataFrame   
       inventory with no product flows

    """
    df = df_static
    df_input = df[df['input'] == True]
    df_output = df[df['input'] == False]
    df_input.loc[:, 'value'] = df_input.loc[:, 'value'] * (-1)
    df = pd.concat([df_input, df_output])
    
    # Removing flows without source
    # Dummy flows need to be removed.
    # This part removes the dummy flows and flows without any production processes from the X matrix.
    process_input_with_process = pd.unique(df_output['product'])
    df['indicator'] = df['product'].isin(process_input_with_process)
    process_df = df[df['indicator'] == True]
    df_with_all_other_flows = df[df['indicator'] == False]
    
    del process_df['indicator']
    del df_with_all_other_flows['indicator']
    
    process_df.loc[:, 'value'] = process_df.loc[:, 'value'].astype(np.float64)
    return process_df, df_with_all_other_flows


def solver(tech_matrix,F,process, df_with_all_other_flows):

    """
    This function houses the calculator to solve Xs = F. 
    Solves the Xs=F equation. 
    Solves the scaling vector.  

    Parameters
    ----------
    tech_matrix : numpy matrix
         technology matrix from the process inventory
    F : vector
         Final demand vector 
    process: list
         filename for the dynamic inventory   
    df_with_all_other_flows: pd.DataFrame
         lca inventory with no product flows

    
    Returns
    -------
    pd.DataFrame
        LCA results in the form of a dataframe after performing LCA calculations
        columns=['product', 'unit', 'value']
        These are mass pollutant flows calculated from USLCI for demand of material. 
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
    This function is used to replace pre 2020 electricity flows with the base electricity mix flow
    in the USLCI inventory Electricity, at Grid, US, 2010'
    

    Parameters
    ----------
    df: pd.DataFrame
        process inventory

    Returns
    -------
    pd.DataFrame
       process inventory with electricity flows before 2020 converted to the base electricity
       mix flow in USLCI. 
    """

    
    df = df.replace(to_replace='electricity', value='Electricity, at Grid, US, 2010')
    return df

def runner_insitu(tech_matrix,F,yr,i,j,k,state,final_demand_scaler,process,df_with_all_other_flows):

    """
    Runs the solver function and creates final data frame in proper format

    Parameters
    ----------
    tech matrix: pd.Dataframe
         technology matrix built from the process inventory. 
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
    state: str
        state in which LCA calculations are taking place
    final_demand_scaler: int
        scaling variable number to ease lca calculation
    process: list
        list of processes included in the technology matrix
    df_with_all_other_flows: pd.DataFrame
        Dataframe with flows in the inventory which do not have a production process. 
    

    Returns
    -------
    pd.DataFrame
        Returns the LCA reults in a properly arranged dataframe with all supplemental information
        LCA results in the form of a dataframe.
        columns=['product', 'unit', 'value',
                 'year', 'facility_id', 'stage', 'material', 'route_id', 'state']
        These are mass pollutant flows calculated from USLCI for demand of material at a certain stage and from a facility. 
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
       warnings.warn(f"Insitu emission calculation failed for {k} at {j} in {yr}")
    
    res = electricity_corrector_before20(res)
    res['route_id'] = None
    return res


def model_celavi_lci_insitu(f_d, yr, fac_id, stage, material, state, df_emissions):


    """
    This is used for calculating insitu emissions
    Creates technology matrix and final demand vector from inventory data
    Runs the PyLCA solver to perform LCA calculations
    Conforms results to a dataframe 

    Parameters
    ----------
    f_d: Dataframe 
    Dataframe from DES 
    
    yr: int
    Year of calculation

    fac_id: int
    Facility ID of facility being evaluated

    stage: str 
    Stage of facility being evaluated

    material: str
    material being evaluated

    df_emission: df
    Emissons inventory

    Returns
    -------
    pd.DataFrame
       Returns INSITU Final LCA results in the form of a dataframe after performing calculation checks
       columns=['flow name', 'flow unit', 'flow quantity',
                     'year', 'facility_id', 'stage', 'material', 'route_id', 'state']
       These are insitu mass pollutant flows calculated from USLCI for demand of material at a certain stage and from a facility. 
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
        warnings.warn('LCA emissions inventory does not exist for %s %s %s' % (str(yr), stage, material))
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
